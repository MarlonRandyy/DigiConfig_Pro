# ============================================================
# instalador.py — Instala el archivo .xml en la ONU
# Login → Upload XML → Reinicio → Verificación
# ============================================================
import requests
import time
import os
from requests.auth import HTTPBasicAuth

TIMEOUT_REQ    = 8    # segundos por request
ESPERA_REINICIO = 60  # segundos a esperar que la ONU reinicie
INTENTOS_VERIF  = 10  # intentos de verificación post-reinicio


class ResultadoInstalacion:
    def __init__(self, exito: bool, mensaje: str, detalle: str = ""):
        self.exito   = exito
        self.mensaje = mensaje
        self.detalle = detalle

    def __repr__(self):
        estado = "✅ ÉXITO" if self.exito else "❌ ERROR"
        return f"{estado}: {self.mensaje}"


class InstaladorONU:
    """
    Maneja el proceso completo de instalación de una ONU.
    Uso:
        inst = InstaladorONU(datos_modelo, ruta_xml)
        for log in inst.instalar():
            print(log)  # logs en tiempo real
    """

    def __init__(self, datos_modelo: dict, ruta_xml: str,
                 callback_log=None, callback_progreso=None):
        self.datos        = datos_modelo
        self.ruta_xml     = ruta_xml
        self.callback_log = callback_log        # fn(str) para logs en UI
        self.callback_pct = callback_progreso   # fn(int 0-100) para barra

        self.ip_fabrica    = datos_modelo.get("ip_fabrica", "192.168.1.1")
        self.ip_final      = datos_modelo.get("ip_configurada", "192.168.100.1")
        self.usuario_fab   = datos_modelo.get("usuario_fabrica", "admin")
        self.clave_fab     = datos_modelo.get("clave_fabrica", "admin")
        self.usuario_final = datos_modelo.get("usuario_final", "admin")
        self.clave_final   = datos_modelo.get("clave_final", "digicable19")
        self.ruta_upload   = datos_modelo.get("ruta_upload", "/")
        self.ruta_reset    = datos_modelo.get("ruta_reset", "/")

        self.sesion = requests.Session()

    def _log(self, msg: str):
        if self.callback_log:
            self.callback_log(msg)

    def _pct(self, val: int):
        if self.callback_pct:
            self.callback_pct(val)

    def instalar(self) -> ResultadoInstalacion:
        """Proceso completo paso a paso."""

        # ── Paso 1: Verificar que el XML existe ──────────────
        self._log("📂 Verificando archivo de configuración...")
        if not os.path.exists(self.ruta_xml):
            return ResultadoInstalacion(False, "Archivo XML no encontrado", self.ruta_xml)
        self._pct(10)

        # ── Paso 2: Login ─────────────────────────────────────
        self._log(f"🔑 Conectando a {self.ip_fabrica}...")
        ok_login = self._hacer_login()
        if not ok_login:
            return ResultadoInstalacion(False, "Fallo de autenticación",
                                        f"No se pudo hacer login en {self.ip_fabrica}")
        self._log("✅ Login exitoso")
        self._pct(25)

        # ── Paso 3: Subir XML ─────────────────────────────────
        self._log("📤 Subiendo archivo de configuración...")
        ok_upload = self._subir_xml()
        if not ok_upload:
            return ResultadoInstalacion(False, "Error al subir el archivo XML",
                                        "Revisar ruta de upload del modelo")
        self._log("✅ Archivo subido correctamente")
        self._pct(50)

        # ── Paso 4: Esperar reinicio ──────────────────────────
        self._log(f"⏳ Esperando reinicio de la ONU ({ESPERA_REINICIO}s)...")
        for i in range(ESPERA_REINICIO):
            time.sleep(1)
            pct = 50 + int((i / ESPERA_REINICIO) * 35)
            self._pct(pct)
            if i % 10 == 0 and i > 0:
                self._log(f"   ...{ESPERA_REINICIO - i}s restantes")
        self._pct(85)

        # ── Paso 5: Verificar en IP final ─────────────────────
        self._log(f"🔍 Verificando acceso en {self.ip_final}...")
        ok_verif = self._verificar_configuracion()
        if not ok_verif:
            return ResultadoInstalacion(False,
                                        "ONU no responde en IP configurada",
                                        f"No se pudo acceder a {self.ip_final} con {self.usuario_final}/{self.clave_final}")
        self._log(f"✅ Verificación exitosa en {self.ip_final}")
        self._pct(100)

        return ResultadoInstalacion(True,
                                    "Instalación completada exitosamente",
                                    f"IP: {self.ip_final} | Usuario: {self.usuario_final} | Clave: {self.clave_final}")

    def _hacer_login(self) -> bool:
        """Intenta hacer login con credenciales de fábrica."""
        urls = [
            f"http://{self.ip_fabrica}/",
            f"http://{self.ip_fabrica}/login.asp",
            f"http://{self.ip_fabrica}/html/ssw/en/",
        ]
        for url in urls:
            try:
                # Intentar HTTP Basic Auth
                r = self.sesion.get(
                    url,
                    auth=HTTPBasicAuth(self.usuario_fab, self.clave_fab),
                    timeout=TIMEOUT_REQ
                )
                if r.status_code in (200, 302, 301):
                    return True

                # Intentar POST de formulario
                r2 = self.sesion.post(
                    url,
                    data={"Username": self.usuario_fab, "Password": self.clave_fab},
                    timeout=TIMEOUT_REQ
                )
                if r2.status_code in (200, 302):
                    return True
            except Exception:
                continue
        return False

    def _subir_xml(self) -> bool:
        """Sube el archivo XML al endpoint de configuración."""
        url_upload = f"http://{self.ip_fabrica}{self.ruta_upload}"
        try:
            with open(self.ruta_xml, "rb") as f:
                archivos = {"config": (os.path.basename(self.ruta_xml), f, "text/xml")}
                r = self.sesion.post(url_upload, files=archivos, timeout=TIMEOUT_REQ * 2)
                return r.status_code in (200, 302, 204)
        except Exception as e:
            self._log(f"   Detalle error: {e}")
            return False

    def _verificar_configuracion(self) -> bool:
        """Verifica que la ONU responde en la IP final con las credenciales correctas."""
        url = f"http://{self.ip_final}/"
        for intento in range(INTENTOS_VERIF):
            try:
                r = requests.get(
                    url,
                    auth=HTTPBasicAuth(self.usuario_final, self.clave_final),
                    timeout=TIMEOUT_REQ
                )
                if r.status_code in (200, 302):
                    return True
            except Exception:
                pass
            time.sleep(3)
            self._log(f"   Intento {intento+1}/{INTENTOS_VERIF}...")
        return False

    def reset_fabrica(self) -> ResultadoInstalacion:
        """Envía el comando de restaurar a valores de fábrica."""
        self._log("⚠️  Iniciando reset de fábrica...")
        ok_login = self._hacer_login()
        if not ok_login:
            return ResultadoInstalacion(False, "No se pudo hacer login para el reset")

        url_reset = f"http://{self.ip_fabrica}{self.ruta_reset}"
        try:
            r = self.sesion.post(url_reset,
                                 data={"action": "restore", "confirm": "1"},
                                 timeout=TIMEOUT_REQ)
            if r.status_code in (200, 302):
                self._log("✅ Comando de reset enviado. Esperando reinicio...")
                return ResultadoInstalacion(True, "Reset de fábrica enviado")
        except Exception as e:
            return ResultadoInstalacion(False, f"Error al enviar reset: {e}")
        return ResultadoInstalacion(False, "Reset no confirmado por la ONU")
