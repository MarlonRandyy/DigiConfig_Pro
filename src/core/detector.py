# ============================================================
# detector.py — Detecta ONUs conectadas en la red local
# Hace ping a las IPs típicas de ONU y lee MAC/SN del HTML
# ============================================================
import subprocess
import requests
import threading
import time
import json
import os
from bs4 import BeautifulSoup

# IPs típicas de fábrica de las ONUs
IPS_FABRICA = ["192.168.1.1", "192.168.0.1", "192.168.100.1"]

TIMEOUT_HTTP  = 4   # segundos para requests
INTERVALO_SCAN = 3  # segundos entre escaneos


def _ping(ip: str) -> bool:
    """Retorna True si la IP responde a ping."""
    try:
        resultado = subprocess.run(
            ["ping", "-n", "1", "-w", "1000", ip],
            capture_output=True, timeout=3
        )
        return resultado.returncode == 0
    except Exception:
        return False


def _get_html(ip: str, usuario: str = "admin", clave: str = "admin") -> str | None:
    """Intenta hacer login básico y retorna el HTML de la página raíz."""
    urls_intentar = [
        f"http://{ip}/",
        f"http://{ip}/login.asp",
        f"http://{ip}/html/ssw/en/",
    ]
    for url in urls_intentar:
        try:
            r = requests.get(url, auth=(usuario, clave), timeout=TIMEOUT_HTTP)
            if r.status_code in (200, 302):
                return r.text
        except Exception:
            continue
    return None


def _extraer_info_html(html: str) -> dict:
    """Parsea el HTML para extraer MAC, SN, modelo y fabricante."""
    info = {
        "mac": "Desconocida",
        "gpon_sn": "Desconocido",
        "modelo_raw": "Desconocido",
        "fabricante": "Desconocido",
    }
    if not html:
        return info

    soup = BeautifulSoup(html, "html.parser")
    texto = soup.get_text().lower()

    # Detectar fabricante por palabras clave en el HTML
    fabricantes = {
        "vsol": "VSOL",
        "bt-pon": "BT-PON",
        "bt pon": "BT-PON",
        "btpon": "BT-PON",
        "huawei": "Huawei",
        "zte": "ZTE",
        "fiberhome": "FiberHome",
        "hisense": "Hisense",
    }
    for clave_fab, nombre_fab in fabricantes.items():
        if clave_fab in texto:
            info["fabricante"] = nombre_fab
            break

    # Intentar extraer MAC de campos comunes
    import re
    patron_mac = r"([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}"
    macs = re.findall(patron_mac, html)
    if macs:
        # Tomar la primera MAC que no sea broadcast
        for m in macs:
            mac_completa = re.search(
                r"[0-9A-Fa-f]{2}(?:[:\-][0-9A-Fa-f]{2}){5}", html
            )
            if mac_completa:
                info["mac"] = mac_completa.group().upper()
                break

    # Intentar extraer GPON SN (patrón típico: 4 letras + 8 hex)
    patron_sn = r"[A-Z]{4}[0-9A-F]{8}"
    sn_match = re.search(patron_sn, html.upper())
    if sn_match:
        info["gpon_sn"] = sn_match.group()

    return info


def _identificar_modelo_por_mac(mac: str, modelos_db: dict) -> str | None:
    """Identifica el modelo comparando prefijo de MAC con la base de datos."""
    if not mac or mac == "Desconocida":
        return None
    mac_clean = mac.replace(":", "").replace("-", "").upper()
    for modelo_id, datos in modelos_db.items():
        for prefijo in datos.get("mac_prefijos", []):
            p = prefijo.replace(":", "").replace("-", "").upper()
            if mac_clean.startswith(p):
                return modelo_id
    return None


class DetectorONU:
    """
    Escanea la red cada N segundos buscando ONUs conectadas.
    Llama a callback_detectada(info_dict) cuando encuentra una.
    Llama a callback_perdida() cuando desaparece.
    """

    def __init__(self, modelos_db: dict,
                 callback_detectada=None,
                 callback_perdida=None):
        self.modelos_db       = modelos_db
        self.callback_detectada = callback_detectada
        self.callback_perdida   = callback_perdida
        self._corriendo       = False
        self._hilo            = None
        self._ip_activa       = None
        self._onu_conectada   = False

    def iniciar(self):
        """Inicia el hilo de escaneo en background."""
        self._corriendo = True
        self._hilo = threading.Thread(target=self._loop_scan, daemon=True)
        self._hilo.start()

    def detener(self):
        """Detiene el hilo de escaneo."""
        self._corriendo = False

    def _loop_scan(self):
        while self._corriendo:
            ip_encontrada = None
            for ip in IPS_FABRICA:
                if _ping(ip):
                    ip_encontrada = ip
                    break

            if ip_encontrada and not self._onu_conectada:
                # ONU recién conectada
                self._onu_conectada = True
                self._ip_activa     = ip_encontrada
                info = self._recopilar_info(ip_encontrada)
                if self.callback_detectada:
                    self.callback_detectada(info)

            elif not ip_encontrada and self._onu_conectada:
                # ONU desconectada
                self._onu_conectada = False
                self._ip_activa     = None
                if self.callback_perdida:
                    self.callback_perdida()

            time.sleep(INTERVALO_SCAN)

    def _recopilar_info(self, ip: str) -> dict:
        """Construye el dict completo de información de la ONU detectada."""
        html = _get_html(ip)
        info_html = _extraer_info_html(html or "")

        modelo_id = _identificar_modelo_por_mac(info_html["mac"], self.modelos_db)

        # Si no detectó por MAC, intentar por fabricante del HTML
        if not modelo_id and info_html["fabricante"] != "Desconocido":
            fab = info_html["fabricante"].upper()
            for mid, datos in self.modelos_db.items():
                if fab in datos.get("fabricante", "").upper():
                    modelo_id = mid
                    break

        datos_modelo = self.modelos_db.get(modelo_id, {}) if modelo_id else {}

        return {
            "ip": ip,
            "mac": info_html["mac"],
            "gpon_sn": info_html["gpon_sn"],
            "fabricante": info_html["fabricante"],
            "modelo_id": modelo_id or "DESCONOCIDO",
            "nombre_display": datos_modelo.get("nombre_display", "Modelo no registrado"),
            "imagen": datos_modelo.get("imagen", ""),
            "firmware_xml": datos_modelo.get("firmware_xml", ""),
        }

    def escaneo_manual(self) -> dict | None:
        """Escaneo único bajo demanda. Retorna info o None."""
        for ip in IPS_FABRICA:
            if _ping(ip):
                return self._recopilar_info(ip)
        return None
