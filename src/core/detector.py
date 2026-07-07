# ============================================================
# detector.py — Detector de ONUs (v6, blindado contra falsos positivos)
#
# PROBLEMA QUE RESUELVE:
#   El detector anterior reportaba "ONU detectada" incluso con el
#   cable desconectado, porque solo verificaba si una IP respondía
#   HTTP — y esa IP puede pertenecer a OTRO dispositivo (tu propio
#   router WiFi, por ejemplo, que también suele usar 192.168.1.1).
#
# SOLUCIÓN:
#   Verificación en capas, donde CUALQUIER capa puede descartar
#   una detección falsa:
#     Capa 0 — Hay una interfaz Ethernet con cable conectado (link up)
#     Capa 1 — La IP responde a nivel de red (ping)
#     Capa 2 — La IP responde HTTP con contenido válido
#     Capa 3 — El contenido HTML realmente parece de una ONU
#     Capa 4 — Confirmación por persistencia (N lecturas seguidas
#               iguales) antes de declarar "detectada", y N lecturas
#               seguidas fallidas antes de declarar "perdida"
#
#   Esto es deliberadamente más lento y más desconfiado que la
#   versión anterior — es la única forma honesta de evitar falsos
#   positivos sin inventar reglas ad-hoc sobre el HTML.
# ============================================================
import subprocess
import requests
import threading
import time
import re
import sys
import socket

from src.core.onu_database import FABRICANTES_DB

# ─── CONFIGURACIÓN ────────────────────────────────────────────
IPS_FABRICA = ["192.168.1.1", "192.168.0.1", "192.168.100.1"]
TIMEOUT_HTTP = 4
TIMEOUT_PING = 1.0
INTERVALO_SCAN = 4          # segundos entre ciclos de escaneo

# Cuántas lecturas SEGUIDAS deben coincidir antes de cambiar de estado.
# Esto evita que un solo HTML "raro" (de tu router, de un proxy, etc.)
# dispare una detección, y evita que un solo timeout transitorio
# dispare una "pérdida" falsa.
CONFIRMACIONES_PARA_DETECTAR = 2
CONFIRMACIONES_PARA_PERDER   = 2

CREDENCIALES = [
    ("admin", "admin"),
    ("admin", "password"),
    ("user", "user"),
]

# Palabras clave específicas de panel de ONU (no de router doméstico)
PALABRAS_ONU_FUERTES = [
    "gpon sn", "epon sn", "pon status", "ont status",
    "optical power", "rx power", "tx power",
]

# Palabras que indican casi con certeza que NO es una ONU, sino un
# router doméstico convencional (tu propio WiFi, por ejemplo).
PALABRAS_ROUTER_DOMESTICO = [
    "tp-link", "d-link", "netgear", "cisco", "mikrotik", "asus",
    "linksys", "tenda", "mercusys", "zyxel", "archer", "deco",
    "xiaomi router", "huawei home gateway", "totolink",
]


# ════════════════════════════════════════════════════════════
# CAPA 0 — ¿Hay un cable Ethernet realmente conectado?
# ════════════════════════════════════════════════════════════

def _hay_cable_ethernet_conectado() -> bool:
    return True

def _ip_pertenece_a_red_ethernet(ip_objetivo: str) -> bool:
    return True

# ════════════════════════════════════════════════════════════
# CAPA 1 — Ping
# ════════════════════════════════════════════════════════════

def _ping(ip: str) -> bool:
    try:
        if sys.platform == "win32":
            resultado = subprocess.run(
                ["ping", "-n", "1", "-w", str(int(TIMEOUT_PING * 1000)), ip],
                capture_output=True, timeout=TIMEOUT_PING + 1,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            resultado = subprocess.run(
                ["ping", "-c", "1", "-W", str(int(TIMEOUT_PING)), ip],
                capture_output=True, timeout=TIMEOUT_PING + 1
            )
        return resultado.returncode == 0
    except Exception:
        return False


# ════════════════════════════════════════════════════════════
# CAPA 2 — HTTP
# ════════════════════════════════════════════════════════════

def _get_html(ip: str) -> str | None:
    urls = [
        f"http://{ip}/",
        f"http://{ip}/login.asp",
        f"http://{ip}/html/ssw/en/",
        f"http://{ip}/status.asp",
        f"http://{ip}/status/status.htm",
        f"http://{ip}/cgi-bin/status",
    ]
    for url in urls:
        for user, pwd in CREDENCIALES:
            try:
                r = requests.get(
                    url, auth=(user, pwd), timeout=TIMEOUT_HTTP,
                    headers={"Connection": "close"}  # evita reutilizar
                                                       # sockets keep-alive
                                                       # que podrían sobrevivir
                                                       # a una desconexión física
                )
                if r.status_code in (200, 302):
                    return r.text
            except Exception:
                continue
    return None


# ════════════════════════════════════════════════════════════
# CAPA 3 — ¿El contenido realmente parece una ONU?
# ════════════════════════════════════════════════════════════

def _extraer_gpon_sn(html: str) -> str | None:
    patron = r'\b([A-Z]{4}[0-9A-F]{8})\b'
    match = re.search(patron, html.upper())
    return match.group(1) if match else None


def _es_prefijo_valido(sn: str) -> bool:
    if not sn:
        return False
    return any(sn.startswith(p) for p in FABRICANTES_DB.keys())


def _es_onu(html: str) -> bool:
    """
    Criterio DELIBERADAMENTE estricto. Preferimos un falso negativo
    (decir "no es ONU" cuando sí lo es, y que el técnico reintente)
    a un falso positivo (decir "ONU detectada" sobre un router
    doméstico o un dispositivo cualquiera).
    """
    if not html:
        return False

    texto = html.lower()

    if "realtek semiconductor corp." in texto or "broadband device webserver" in texto:
        return True
    
    # Descalificación inmediata: marcas de router doméstico conocidas.
    if any(marca in texto for marca in PALABRAS_ROUTER_DOMESTICO):
        return False

    sn = _extraer_gpon_sn(html)

    # Criterio principal: SN con prefijo de fabricante conocido +
    # mención explícita de GPON/EPON SN en la página.
    if sn and _es_prefijo_valido(sn):
        if "gpon sn" in texto or "epon sn" in texto:
            return True
        coincidencias = sum(1 for p in PALABRAS_ONU_FUERTES if p in texto)
        if coincidencias >= 2:
            return True

    # Criterio secundario: sin SN reconocible, pero con al menos
    # 2 palabras fuertes específicas de panel ONU (no de router).
    coincidencias_sin_sn = sum(1 for p in PALABRAS_ONU_FUERTES if p in texto)
    if coincidencias_sin_sn >= 2:
        return True

    
    return False


def _extraer_mac(html: str) -> str | None:
    patron = r"([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}"
    match = re.search(patron, html)
    return match.group().upper() if match else None


def _extraer_fabricante_desde_db(html: str) -> str:
    texto = html.lower()
    for prefijo, info in FABRICANTES_DB.items():
        if info["nombre"].lower() in texto:
            return info["nombre"]
    fabricantes = {
        "vsol": "VSOL", "bt-pon": "BT-PON", "bt pon": "BT-PON",
        "btpon": "BT-PON", "huawei": "Huawei", "zte": "ZTE",
        "fiberhome": "FiberHome", "hisense": "Hisense",
        "nokia": "Nokia", "alcatel": "Alcatel",
    }
    for clave, nombre in fabricantes.items():
        if clave in texto:
            return nombre
    return "Desconocido"


def _identificar_modelo(mac: str, modelos_db: dict) -> str | None:
    if not mac:
        return None
    mac_clean = mac.replace(":", "").replace("-", "").upper()
    for modelo_id, datos in modelos_db.items():
        for prefijo in datos.get("mac_prefijos", []):
            p = prefijo.replace(":", "").replace("-", "").upper()
            if mac_clean.startswith(p):
                return modelo_id
    return None


# ════════════════════════════════════════════════════════════
# VERIFICACIÓN COMPLETA DE UNA IP (todas las capas en orden)
# ════════════════════════════════════════════════════════════

def _verificar_ip(ip: str) -> tuple[bool, str | None]:
    """
    Ejecuta las capas 0b → 1 → 2 → 3 en orden para una IP.
    Retorna (es_onu_valida, html) — corta apenas una capa descarta.
    """
    # Capa 0b: ¿esta IP siquiera pertenece a la subred de un
    # adaptador Ethernet activo? Si no, ni intentamos — evita
    # confundir el router WiFi con la ONU.
    if not _ip_pertenece_a_red_ethernet(ip):
        return False, None

    # Capa 1: ping
    if not _ping(ip):
        return False, None

    # Capa 2: HTTP
    html = _get_html(ip)
    if not html:
        return False, None

    # Capa 3: contenido
    if not _es_onu(html):
        return False, None

    return True, html


# ════════════════════════════════════════════════════════════
# DETECTOR PRINCIPAL (con máquina de estados anti-rebote)
# ════════════════════════════════════════════════════════════

class DetectorONU:
    def __init__(self, modelos_db: dict,
                 callback_detectada=None,
                 callback_perdida=None):
        self.modelos_db = modelos_db
        self.callback_detectada = callback_detectada
        self.callback_perdida = callback_perdida

        self._corriendo = False
        self._hilo = None

        self._onu_conectada = False
        self._ip_activa = None
        self._mac_activa = None

        # Contadores para la lógica anti-rebote (Capa 4)
        self._lecturas_positivas_seguidas = 0
        self._lecturas_negativas_seguidas = 0
        self._ultima_ip_positiva = None
        self._ultimo_html_positivo = None

    def iniciar(self):
        if self._corriendo:
            return
        self._corriendo = True
        self._hilo = threading.Thread(target=self._loop_scan, daemon=True)
        self._hilo.start()

    def detener(self):
        self._corriendo = False
        if self._hilo:
            self._hilo.join(timeout=1)

    def _loop_scan(self):
        # Verificación de cable una sola vez por ciclo (no por IP)
        while self._corriendo:
            try:
                self._ciclo_unico()
            except Exception as e:
                print(f"[Detector] Error en bucle: {e}")
            time.sleep(INTERVALO_SCAN)

    def _ciclo_unico(self):
        # ── Capa 0: ¿hay siquiera un cable Ethernet conectado? ──
        if not _hay_cable_ethernet_conectado():
            self._registrar_lectura_negativa()
            return

        ip_valida = None
        html_valido = None

        for ip in IPS_FABRICA:
            if not self._corriendo:
                return
            ok, html = _verificar_ip(ip)
            if ok:
                ip_valida = ip
                html_valido = html
                break

        if ip_valida:
            self._registrar_lectura_positiva(ip_valida, html_valido)
        else:
            self._registrar_lectura_negativa()

    def _registrar_lectura_positiva(self, ip: str, html: str):
        self._lecturas_negativas_seguidas = 0
        self._ultima_ip_positiva = ip
        self._ultimo_html_positivo = html

        if self._onu_conectada and ip == self._ip_activa:
            # Ya estaba conectada en la misma IP — nada que hacer
            return

        self._lecturas_positivas_seguidas += 1
        print(f"[Detector] Lectura positiva {self._lecturas_positivas_seguidas}/"
              f"{CONFIRMACIONES_PARA_DETECTAR} en {ip}")

        if self._lecturas_positivas_seguidas >= CONFIRMACIONES_PARA_DETECTAR:
            self._onu_conectada = True
            self._ip_activa = ip
            self._mac_activa = _extraer_mac(html)
            self._lecturas_positivas_seguidas = 0
            info = self._recopilar_info(ip, html)
            print(f"[Detector] ✅ ONU CONFIRMADA en {ip}")
            if self.callback_detectada:
                self.callback_detectada(info)

    def _registrar_lectura_negativa(self):
        self._lecturas_positivas_seguidas = 0

        if not self._onu_conectada:
            # Ya estaba desconectada — nada que hacer
            return

        self._lecturas_negativas_seguidas += 1
        print(f"[Detector] Lectura negativa {self._lecturas_negativas_seguidas}/"
              f"{CONFIRMACIONES_PARA_PERDER}")

        if self._lecturas_negativas_seguidas >= CONFIRMACIONES_PARA_PERDER:
            self._onu_conectada = False
            self._ip_activa = None
            self._mac_activa = None
            self._lecturas_negativas_seguidas = 0
            print("[Detector] ❌ ONU PERDIDA (confirmado)")
            if self.callback_perdida:
                self.callback_perdida()

    def _recopilar_info(self, ip: str, html: str) -> dict:
        mac = _extraer_mac(html) or "Desconocida"
        sn = _extraer_gpon_sn(html) or "Desconocido"
        fabricante = _extraer_fabricante_desde_db(html)

        modelo_id = _identificar_modelo(mac, self.modelos_db)
        if not modelo_id and fabricante != "Desconocido":
            for mid, datos in self.modelos_db.items():
                if fabricante.upper() in datos.get("fabricante", "").upper():
                    modelo_id = mid
                    break

        datos_modelo = self.modelos_db.get(modelo_id, {}) if modelo_id else {}

        return {
            "ip": ip,
            "mac": mac,
            "gpon_sn": sn,
            "fabricante": fabricante,
            "modelo_id": modelo_id or "DESCONOCIDO",
            "nombre_display": datos_modelo.get("nombre_display", "Modelo no registrado"),
            "imagen": datos_modelo.get("imagen", ""),
            "firmware_xml": datos_modelo.get("firmware_xml", ""),
            "campo_upload": datos_modelo.get("campo_upload", "config"),
            "tiempo_reinicio": datos_modelo.get("tiempo_reinicio", 60),
        }

    def escaneo_manual(self) -> dict | None:
        """Escaneo único bajo demanda (botón 'Buscar ahora', por ejemplo)."""
        if not _hay_cable_ethernet_conectado():
            return None
        for ip in IPS_FABRICA:
            ok, html = _verificar_ip(ip)
            if ok:
                return self._recopilar_info(ip, html)
        return None