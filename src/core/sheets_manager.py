# ============================================================
# sheets_manager.py - Gestor Google Sheets de alto rendimiento
# DigiConfig Pro v2.0 - Celda variable, lote dinámico, caché
# Soporta 7 columnas: NÚMERO, ETIQUETA/PRECINTO, MAC, SN, PON, CLIENTE, OBSERVACIÓN
# ============================================================

import os
import re
import time
import gspread
from google.oauth2.service_account import Credentials
from src.utils.config_manager import leer_dato, guardar_dato

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROYECTO_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
CRED_PATH = os.path.join(PROYECTO_ROOT, "src", "core", "secure_creds", "credentials.json")

class SheetsManager:
    
    # ------------------------------------------------------------------
    # Funciones auxiliares de conversión de columnas (independientes de gspread)
    # ------------------------------------------------------------------
    @staticmethod
    def _col_letter(col):
        """Convierte número de columna (1-based) a letras (ej. 1 -> A, 28 -> AB)"""
        letra = ""
        while col > 0:
            col, resto = divmod(col - 1, 26)
            letra = chr(65 + resto) + letra
        return letra

    @staticmethod
    def _col_letter_to_index(col_letter):
        """Convierte letras de columna (ej. 'B') a número 1-based (ej. 2)"""
        index = 0
        for ch in col_letter:
            index = index * 26 + (ord(ch.upper()) - ord('A') + 1)
        return index

    # ------------------------------------------------------------------
    # Inicialización y conexión
    # ------------------------------------------------------------------
    def __init__(self, spreadsheet_id: str = None):
        self.spreadsheet_id = (spreadsheet_id or leer_dato("google_sheet_id")).strip()
        self._gc = None
        self._libro = None
        self._hoja_actual = None
        self._ultima_fila = None
        self._proximo_id = None
        self._columna_inicio = None
        self._fila_cabecera = None
        self._limite_lote = None
        self._celda_inicio = None
        self._hoja_cache_key = None
        self._max_reintentos = 3

    def conectar(self) -> tuple[bool, str]:
        if not self.spreadsheet_id:
            return False, "ID de Sheet no configurado."
        if not os.path.exists(CRED_PATH):
            return False, "credentials.json no encontrado."
        try:
            creds = Credentials.from_service_account_file(
                CRED_PATH,
                scopes=["https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive"]
            )
            self._gc = gspread.authorize(creds)
            self._libro = self._gc.open_by_key(self.spreadsheet_id)
            return True, f"Conectado a {self._libro.title}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def _parse_celda(self, celda: str):
        """Devuelve (col_letter, fila) a partir de una celda como 'B2'."""
        match = re.match(r'([A-Z]+)(\d+)', celda.strip().upper())
        if not match:
            raise ValueError(f"Formato de celda inválido: {celda}")
        col_letra = match.group(1)
        fila = int(match.group(2))
        return col_letra, fila

    def _obtener_hoja(self, forzar_recalculo=False):
        """Devuelve la hoja activa (última hoja del libro por defecto)."""
        if not self._libro:
            return None

        celda_inicio_actual = leer_dato("celda_inicio", "B2")
        limite_actual = int(leer_dato("limite_lote", 100))

        hojas = self._libro.worksheets()
        if not hojas:
            return None
        hoja = hojas[-1]
        nombre_hoja = hoja.title

        cache_key = (nombre_hoja, celda_inicio_actual)
        if not forzar_recalculo and self._hoja_cache_key == cache_key:
            return hoja

        try:
            col_letra, fila_cabecera = self._parse_celda(celda_inicio_actual)
        except ValueError as e:
            raise RuntimeError(f"Configuración de celda inválida: {e}")

        self._columna_inicio = self._col_letter_to_index(col_letra)
        self._fila_cabecera = fila_cabecera
        self._celda_inicio = celda_inicio_actual
        self._limite_lote = limite_actual

        col_vals = hoja.col_values(self._columna_inicio)
        datos_ids = col_vals[self._fila_cabecera:]

        ultima_fila = self._fila_cabecera
        proximo_id = 1
        for idx, val in enumerate(datos_ids, start=self._fila_cabecera + 1):
            if val == "":
                ultima_fila = idx - 1
                break
            if val.isdigit():
                proximo_id = max(proximo_id, int(val) + 1)
            ultima_fila = idx
        else:
            ultima_fila = self._fila_cabecera + len(datos_ids)

        self._ultima_fila = ultima_fila
        self._proximo_id = proximo_id
        self._hoja_cache_key = cache_key
        self._hoja_actual = hoja
        return hoja

    def _crear_nueva_hoja_con_cabecera(self):
        """Crea una nueva hoja con la cabecera de 7 columnas en la celda de inicio."""
        nuevo_nombre = f"Lote {len(self._libro.worksheets()) + 1}"
        nueva_hoja = self._libro.add_worksheet(title=nuevo_nombre, rows="1000", cols="20")

        titulos = ["NÚMERO", "ETIQUETA / PRECINTO", "MAC", "SERIAL (PON SN)", "PON", "CLIENTE", "OBSERVACIÓN"]
        col_letra, fila_cab = self._parse_celda(self._celda_inicio)
        col_inicio = self._col_letter_to_index(col_letra)
        col_fin_letra = self._col_letter(col_inicio + len(titulos) - 1)
        rango_cabecera = f"{col_letra}{fila_cab}:{col_fin_letra}{fila_cab}"
        nueva_hoja.update(range_name=rango_cabecera, values=[titulos])
        nueva_hoja.format(rango_cabecera, {
            "textFormat": {"bold": True},
            "horizontalAlignment": "CENTER",
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
        })
        return nueva_hoja

    def registrar_onu(self, mac: str, serial: str, precinto: str = "", pon: str = "") -> dict:
        """Registra una ONU con escritura rápida y paginación automática. Incluye las 7 columnas."""
        for intento in range(self._max_reintentos):
            try:
                if not self._libro:
                    ok, _ = self.conectar()
                    if not ok:
                        return {"status": "error", "mensaje": "No conectado"}

                hoja = self._obtener_hoja(forzar_recalculo=False)
                if not hoja:
                    return {"status": "error", "mensaje": "No hay hoja disponible"}

                filas_ocupadas = self._ultima_fila - self._fila_cabecera
                if filas_ocupadas >= self._limite_lote:
                    hoja = self._crear_nueva_hoja_con_cabecera()
                    self._hoja_cache_key = None
                    hoja = self._obtener_hoja(forzar_recalculo=True)
                    if not hoja:
                        return {"status": "error", "mensaje": "Error al crear nueva hoja"}

                id_actual = self._proximo_id
                self._proximo_id += 1
                mac_clean = mac.upper().replace(":", "").replace("-", "").strip()
                serial_clean = serial.upper().strip()

                # Fila de 7 columnas: ID, precinto, MAC, SN, PON, CLIENTE, OBSERVACIÓN
                fila_valores = [id_actual, precinto.upper(), mac_clean, serial_clean, pon.upper(), "", ""]

                fila_destino = self._ultima_fila + 1
                col_inicio = self._columna_inicio
                col_fin = col_inicio + len(fila_valores) - 1
                rango = f"{self._col_letter(col_inicio)}{fila_destino}:{self._col_letter(col_fin)}{fila_destino}"
                hoja.update(range_name=rango, values=[fila_valores], value_input_option="USER_ENTERED")

                self._ultima_fila = fila_destino

                return {
                    "status": "registrado",
                    "mensaje": f"OK en {hoja.title} - ID {id_actual}",
                    "datos": {"id": id_actual, "rango": rango}
                }

            except gspread.exceptions.APIError as e:
                time.sleep(0.5 * (intento + 1))
                continue
            except Exception as e:
                return {"status": "error", "mensaje": f"Fallo: {str(e)}"}

        return {"status": "error", "mensaje": "Máximos reintentos alcanzados"}

    def probar_conexion(self) -> tuple[bool, str]:
        try:
            if not self._libro:
                return self.conectar()
            hoja = self._obtener_hoja(forzar_recalculo=True)
            if hoja:
                return True, "Conexión activa y estructura validada"
            return False, "No se pudo acceder a la hoja"
        except Exception as e:
            return False, str(e)