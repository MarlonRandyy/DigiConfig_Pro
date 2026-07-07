# ============================================================
# instalador.py — Instalación XML dinámica para múltiples modelos
# Login → Upload XML → (Opcional: Reset POST) → Reinicio → Verificación
# ============================================================
import requests
import time
import os
from requests.auth import HTTPBasicAuth

TIMEOUT_REQ = 8
INTENTOS_VERIF = 10


class ResultadoInstalacion:
    def __init__(self, exito: bool, mensaje: str, detalle: str = ""):
        self.exito = exito
        self.mensaje = mensaje
        self.detalle = detalle

    def __repr__(self):
        estado = "✅ ÉXITO" if self.exito else "❌ ERROR"
        return f"{estado}: {self.mensaje}"


class InstaladorONU:
    """
    Maneja el proceso completo de instalación de una ONU.
    Todos los parámetros se leen desde datos_modelo.
    """

    def __init__(self, datos_modelo: dict, ruta_xml: str,
                 callback_log=None, callback_progreso=None):
        self.datos = datos_modelo
        self.ruta_xml = ruta_xml
        self.callback_log = callback_log
        self.callback_pct = callback_progreso

        # ── Parámetros básicos ──────────────────────────────
        self.ip_fabrica = datos_modelo.get("ip_fabrica", "192.168.1.1")
        self.ip_final = datos_modelo.get("ip_configurada", "192.168.100.1")
        self.usuario_fab = datos_modelo.get("usuario_fabrica", "admin")
        self.clave_fab = datos_modelo.get("clave_fabrica", "admin")
        self.usuario_final = datos_modelo.get("usuario_final", "admin")
        self.clave_final = datos_modelo.get("clave_final", "admin")
        self.ruta_upload = datos_modelo.get("ruta_upload", "/")
        self.ruta_reset = datos_modelo.get("ruta_reset", "/")

        # ── Parámetros dinámicos (desde el registro) ────────
        self.campo_upload = datos_modelo.get("campo_upload", "config")
        self.tiempo_reinicio = int(datos_modelo.get("tiempo_reinicio", 60))

        # ── Parámetros avanzados ─────────────────────────────
        self.login_tipo = datos_modelo.get("login_tipo", "basic")
        self.texto_verificacion = datos_modelo.get("texto_verificacion", "logout")
        self.data_reset = datos_modelo.get("data_reset", {"action": "restore", "confirm": "1"})

        # ── Campos extra del formulario de upload ─────────────
        self.campos_extra_upload = datos_modelo.get("campos_extra_upload", {})

        # ── NUEVO: Controlar si se debe enviar un POST de reset ──
        # Si el modelo NO reinicia automáticamente tras el upload,
        # activar esta opción para forzar el reinicio vía POST.
        # Se configura en el modelo como "reset_despues_upload": true
        self.reset_despues_upload = datos_modelo.get("reset_despues_upload", False)

        # Datos para el POST de reset (si se necesita)
        self.data_reset_extra = datos_modelo.get("data_reset_extra", {})

        self.sesion = requests.Session()

    # ──────────────────────────────────────────────────────────
    #  LOGS Y PROGRESO
    # ──────────────────────────────────────────────────────────
    def _log(self, msg: str):
        if self.callback_log:
            self.callback_log(msg)

    def _pct(self, val: int):
        if self.callback_pct:
            self.callback_pct(val)

    # ──────────────────────────────────────────────────────────
    #  PROCESO PRINCIPAL
    # ──────────────────────────────────────────────────────────
    def instalar(self) -> ResultadoInstalacion:
        """Ejecuta el flujo completo de instalación."""

        # Paso 1: Verificar XML
        self._log("📂 Verificando archivo de configuración...")
        if not os.path.exists(self.ruta_xml):
            return ResultadoInstalacion(False, "Archivo XML no encontrado", self.ruta_xml)
        self._pct(10)

        # Paso 2: Login
        self._log(f"🔑 Conectando a {self.ip_fabrica}...")
        if not self._hacer_login():
            return ResultadoInstalacion(False, "Fallo de autenticación",
                                        f"No se pudo hacer login en {self.ip_fabrica}")
        self._log("✅ Login exitoso")
        self._pct(25)

        # Paso 3: Subir XML
        self._log(f"📤 Subiendo archivo (campo: '{self.campo_upload}')...")
        if not self._subir_xml():
            return ResultadoInstalacion(False, "Error al subir el archivo XML",
                                        f"El campo '{self.campo_upload}' no fue aceptado")
        self._log("✅ Archivo subido correctamente")
        self._pct(50)

        # ── NUEVO: Paso 3.5 – Reset POST (si está configurado) ──
        if self.reset_despues_upload:
            self._log("🔄 Enviando comando de reset (forzado)...")
            if not self._resetear_onu():
                return ResultadoInstalacion(False, "Error al enviar comando de reset",
                                            "El POST de reset no fue aceptado por la ONU")
            self._log("✅ Comando de reset enviado")
            # Ajustar progreso para reflejar que estamos en la fase de reinicio
            self._pct(55)

        # Paso 4: Esperar reinicio
        self._log(f"⏳ Esperando reinicio ({self.tiempo_reinicio}s)...")
        for i in range(self.tiempo_reinicio):
            time.sleep(1)
            pct = 50 + int((i / self.tiempo_reinicio) * 35)
            # Si se hizo reset forzado, el progreso empieza en 55
            if self.reset_despues_upload:
                pct = 55 + int((i / self.tiempo_reinicio) * 30)
            self._pct(pct)
            if i % 10 == 0 and i > 0:
                self._log(f"   ...{self.tiempo_reinicio - i}s restantes")
        self._pct(85 if not self.reset_despues_upload else 85)

        # Paso 5: Verificar
        self._log(f"🔍 Verificando acceso en {self.ip_final}...")
        if not self._verificar_configuracion():
            return ResultadoInstalacion(False,
                                        "ONU no responde en IP configurada",
                                        f"No se pudo acceder a {self.ip_final}")
        self._log(f"✅ Verificación exitosa en {self.ip_final}")
        self._pct(100)

        return ResultadoInstalacion(True,
                                    "Instalación completada exitosamente",
                                    f"IP: {self.ip_final} | Usuario: {self.usuario_final}")

    # ──────────────────────────────────────────────────────────
    #  LOGIN (CON VALIDACIÓN POR CONTENIDO)
    # ──────────────────────────────────────────────────────────
    def _hacer_login(self) -> bool:
        urls = [
            f"http://{self.ip_fabrica}/",
            f"http://{self.ip_fabrica}/login.asp",
            f"http://{self.ip_fabrica}/html/ssw/en/",
        ]

        if self.login_tipo == "basic":
            for url in urls:
                try:
                    r = self.sesion.get(
                        url,
                        auth=HTTPBasicAuth(self.usuario_fab, self.clave_fab),
                        timeout=TIMEOUT_REQ
                    )
                    if self._es_login_exitoso(r):
                        return True
                except Exception:
                    continue

        # Fallback a formulario
        for url in urls:
            try:
                r = self.sesion.post(
                    url,
                    data={"Username": self.usuario_fab, "Password": self.clave_fab},
                    timeout=TIMEOUT_REQ
                )
                if self._es_login_exitoso(r):
                    return True
            except Exception:
                continue

        return False

    def _es_login_exitoso(self, r) -> bool:
        if r.status_code not in (200, 302, 301):
            return False
        if r.status_code in (302, 301):
            return True
        if r.status_code == 200:
            html = r.text.lower()
            indicadores = ["logout", "dashboard", "admin", "configuration", "status", "system"]
            rechazo = ["login", "username", "password", "authentication failed"]
            if any(p in html for p in indicadores) and not any(p in html for p in rechazo):
                return True
        return False

    # ──────────────────────────────────────────────────────────
    #  SUBIR XML (CON CAMPO DINÁMICO)
    # ──────────────────────────────────────────────────────────
    def _subir_xml(self) -> bool:
        url = f"http://{self.ip_fabrica}{self.ruta_upload}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }

        # Construir campos extra con los valores obligatorios
        data_extra = self.campos_extra_upload.copy() if self.campos_extra_upload else {}
        data_extra.setdefault("load", "Restore")          # ← ¡El botón que faltaba!
        data_extra.setdefault("submit-url", "/saveconf.asp")

        self._log(f"   URL upload: {url}")
        self._log(f"   Campo XML: '{self.campo_upload}'")
        self._log(f"   Datos extra: {data_extra}")

        # Intentar hasta 2 veces con recreación de sesión
        for intento in range(2):
            try:
                with open(self.ruta_xml, "rb") as f:
                    archivos = {
                        self.campo_upload: (os.path.basename(self.ruta_xml), f, "text/xml")
                    }
                    r = self.sesion.post(
                        url,
                        files=archivos,
                        data=data_extra,
                        headers=headers,
                        timeout=TIMEOUT_REQ * 3  # 24 segundos
                    )
                    self._log(f"   Respuesta upload: HTTP {r.status_code}")
                    if r.status_code in (200, 302, 204):
                        return True
                    # Si devuelve 200 pero con error en el contenido, lo mostramos
                    if r.status_code == 200 and "error" in r.text.lower():
                        self._log(f"   Mensaje de error del servidor: {r.text[:200]}")
                    return False
            except requests.exceptions.ConnectionError as e:
                self._log(f"   Error de conexión (intento {intento+1}): {e}")
                if intento == 0:
                    # Recrear sesión y volver a loguear
                    self._log("   Recreando sesión y reintentando login...")
                    self.sesion = requests.Session()
                    if not self._hacer_login():
                        self._log("   Falló el login en el reintento")
                        return False
                    time.sleep(2)  # Esperar antes del segundo intento
                else:
                    return False
            except Exception as e:
                self._log(f"   Error en upload: {e}")
                return False
        return False

    # ──────────────────────────────────────────────────────────
    #  NUEVO: RESET POST (para modelos que no reinician solos)
    # ──────────────────────────────────────────────────────────
    def _resetear_onu(self) -> bool:
        """
        Envía un POST al endpoint de reset para forzar el reinicio.
        Usa self.ruta_reset si está definida, o self.ruta_upload si no.
        Los datos del POST se toman de self.data_reset (con posibilidad
        de sobrescribir con self.data_reset_extra).
        """
        # Si no hay ruta de reset específica, usar la misma de upload
        url_reset = f"http://{self.ip_fabrica}{self.ruta_reset if self.ruta_reset != '/' else self.ruta_upload}"
        # Combinar data_reset con data_reset_extra (sobrescribiendo si hay conflicto)
        data_final = self.data_reset.copy()
        data_final.update(self.data_reset_extra)

        self._log(f"   URL reset: {url_reset}")
        self._log(f"   Datos reset: {data_final}")

        try:
            r = self.sesion.post(url_reset, data=data_final, timeout=TIMEOUT_REQ * 2)
            self._log(f"   Respuesta reset: HTTP {r.status_code}")
            # Aceptar códigos de éxito comunes
            return r.status_code in (200, 302, 204)
        except Exception as e:
            self._log(f"   Error en reset: {e}")
            return False

    # ──────────────────────────────────────────────────────────
    #  VERIFICACIÓN FINAL (CON CONTENIDO)
    # ──────────────────────────────────────────────────────────
    def _verificar_configuracion(self) -> bool:
        url = f"http://{self.ip_final}/"
        for intento in range(INTENTOS_VERIF):
            try:
                r = requests.get(
                    url,
                    auth=HTTPBasicAuth(self.usuario_final, self.clave_final),
                    timeout=TIMEOUT_REQ
                )
                if self._es_login_exitoso(r):
                    return True
            except Exception:
                pass
            time.sleep(3)
            self._log(f"   Intento {intento+1}/{INTENTOS_VERIF}...")
        return False

    # ──────────────────────────────────────────────────────────
    #  RESET DE FÁBRICA (DINÁMICO, PARA USO MANUAL)
    # ──────────────────────────────────────────────────────────
    def reset_fabrica(self) -> ResultadoInstalacion:
        self._log("⚠️  Iniciando reset de fábrica...")
        if not self._hacer_login():
            return ResultadoInstalacion(False, "No se pudo hacer login para el reset")

        url_reset = f"http://{self.ip_fabrica}{self.ruta_reset}"
        try:
            r = self.sesion.post(url_reset, data=self.data_reset, timeout=TIMEOUT_REQ)
            if r.status_code in (200, 302, 204):
                self._log("✅ Reset enviado. Esperando reinicio...")
                return ResultadoInstalacion(True, "Reset de fábrica enviado")
        except Exception as e:
            return ResultadoInstalacion(False, f"Error al enviar reset: {e}")
        return ResultadoInstalacion(False, "Reset no confirmado por la ONU")