import os
import gspread
from google.oauth2.service_account import Credentials
from src.utils.config_manager import leer_dato

# ─── CONFIGURACIÓN DE RUTAS ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROYECTO_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
CRED_PATH = os.path.join(PROYECTO_ROOT, "src", "core", "secure_creds", "credentials.json")

class SheetsManager:
    def __init__(self, spreadsheet_id: str = None):
        self.spreadsheet_id = spreadsheet_id.strip() if spreadsheet_id else leer_dato("google_sheet_id")
        self._gc = None
        self._libro = None

    def conectar(self) -> tuple[bool, str]:
        """Establece conexión con la API de Google Sheets."""
        if not self.spreadsheet_id:
            return False, "Error: ID de Sheet no configurado."
        if not os.path.exists(CRED_PATH):
            return False, "Error: No se encontró credentials.json"
            
        try:
            creds = Credentials.from_service_account_file(
                CRED_PATH, 
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
            )
            self._gc = gspread.authorize(creds)
            self._libro = self._gc.open_by_key(self.spreadsheet_id)
            return True, f"Conectado a: {self._libro.title}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def _get_coordenadas(self, celda_str):
        """Convierte 'B2' en (fila=2, col=2)."""
        col_letra = "".join(filter(str.isalpha, celda_str)).upper()
        fila = int("".join(filter(str.isdigit, celda_str)))
        col = 0
        for char in col_letra:
            col = col * 26 + (ord(char) - ord('A') + 1)
        return fila, col

    def _col_to_letra(self, n):
        """Convierte número de columna a letra (1 -> A, 2 -> B)."""
        letra = ""
        while n > 0:
            n, residuo = divmod(n - 1, 26)
            letra = chr(65 + residuo) + letra
        return letra

    def _preparar_hoja_nueva(self, hoja, celda_inicio):
        """Dibuja el membrete y aplica formato básico."""
        fila_i, col_i = self._get_coordenadas(celda_inicio)
        titulos = ["NÚMERO", "ETIQUETA / PRECINTO", "MAC", "SERIAL (PON SN)", "PON", "CLIENTE", "OBSERVACIÓN"]
        
        col_fin_letra = self._col_to_letra(col_i + len(titulos) - 1)
        rango = f"{celda_inicio}:{col_fin_letra}{fila_i}"
        
        hoja.update(range_name=rango, values=[titulos])
        hoja.format(rango, {
            "textFormat": {"bold": True},
            "horizontalAlignment": "CENTER",
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
        })

    def registrar_onu(self, mac: str, serial: str, precinto: str = "", pon: str = "") -> dict:
        """Registra una ONU con precisión quirúrgica y paginación automática."""
        try:
            if not self._libro:
                exito, msg = self.conectar()
                if not exito: return {"status": "error", "mensaje": msg}
            
            # 1. Obtener parámetros dinámicos
            celda_inicio = leer_dato("celda_inicio", "B2")
            limite = int(leer_dato("limite_lote", 100))
            f_base, c_base = self._get_coordenadas(celda_inicio)

            # 2. Localizar hoja y contar registros
            hojas = self._libro.worksheets()
            hoja_actual = hojas[-1]
            
            # Leemos la columna donde deberían estar los IDs
            # Se usa el c_base para leer exactamente la columna del membrete 'NÚMERO'
            datos_columna = hoja_actual.col_values(c_base)
            ids_registrados = [int(n) for n in datos_columna if str(n).isdigit()]
            total_onus = len(ids_registrados)

            # 3. Gestión de Lotes (Paginación)
            if total_onus >= limite:
                nombre_nueva = f"Lote {len(hojas) + 1}"
                hoja_actual = self._libro.add_worksheet(title=nombre_nueva, rows="1000", cols="20")
                self._preparar_hoja_nueva(hoja_actual, celda_inicio)
                total_onus = 0
                ids_registrados = []

            # 4. Preparar datos y coordenadas de escritura
            fila_destino = f_base + total_actual + 1 if 'total_actual' in locals() else f_base + total_onus + 1
            nuevo_id = max(ids_registrados) + 1 if ids_registrados else 1
            
            # Normalización
            mac_clean = str(mac).upper().replace(":", "").replace("-", "").strip()
            
            # Fila de datos alineada con los 7 títulos del membrete
            fila_datos = [
                nuevo_id, 
                str(precinto).upper(), 
                mac_clean, 
                str(serial).upper().strip(), 
                str(pon).upper().strip(), 
                "", "" # Cliente y Observación
            ]

            # 5. Escritura Laser (Update)
            letra_inicio = self._col_to_letra(c_base)
            letra_fin = self._col_to_letra(c_base + len(fila_datos) - 1)
            rango_exacto = f"{letra_inicio}{fila_destino}:{letra_fin}{fila_destino}"
            
            hoja_actual.update(range_name=rango_exacto, values=[fila_datos], value_input_option="USER_ENTERED")

            return {
                "status": "registrado",
                "mensaje": f"✅ Guardado en {hoja_actual.title} ({rango_exacto})",
                "datos": {"id": nuevo_id, "rango": rango_exacto}
            }

        except Exception as e:
            return {"status": "error", "mensaje": f"Fallo en motor: {str(e)}"}

    def probar_conexion(self) -> tuple[bool, str]:
        try:
            if not self._libro: return self.conectar()
            self._libro.fetch_sheet_metadata()
            return True, "Conexión activa"
        except:
            return self.conectar()