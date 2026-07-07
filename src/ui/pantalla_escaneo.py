# ============================================================
# pantalla_escaneo.py - Módulo de escáner profesional optimizado
# DigiConfig Pro v2.0 - Cámara fluida, buffer 2 etiquetas, UI mejorada
# ============================================================

import customtkinter as ctk
import cv2
import threading
import time
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from PIL import Image

from src.core.sheets_manager import SheetsManager
from src.utils.config_manager import leer_dato, guardar_dato, importar_credenciales
from src.core.parser_onu import parsear_codigo

class PantallaEscaneo(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # --- Control de destrucción (para evitar errores al cambiar de pantalla) ---
        self._destruida = False

        # --- Estado de la cámara ---
        self.camara_activa = False
        self.cap = None
        self.hilo_camara = None
        self.running = False

        # --- Buffer para equipos de dos etiquetas ---
        self.buffer = {"mac": None, "serial": None, "timestamp": 0}
        self.TIMEOUT_BUFFER = 5

        # --- Estado de registro ---
        self.bloqueado = False
        self.mac_actual = ""
        self.serial_actual = ""

        # --- Control de duplicados en sesión ---
        self.registrados_recientes = set()
        self.MAX_CACHE = 100

        # --- Motor de Sheets ---
        self.sheets_mgr = SheetsManager()
        self.sheets_ok = False
        self._conexion_activa = False

        # --- Variables persistentes ---
        self.var_sheet_id = ctk.StringVar(value=leer_dato("google_sheet_id"))
        self.var_celda = ctk.StringVar(value=leer_dato("celda_inicio", "B2"))
        self.var_limite = ctk.StringVar(value=str(leer_dato("limite_lote", 100)))
        self.var_camara_idx = ctk.IntVar(value=leer_dato("last_camera_index", 0))

        # --- UI: panel de ajustes colapsado por defecto ---
        self.panel_ajustes = False
        self._construir_ui()
        self.frame_der.grid_remove()     # ocultar panel derecho

        # --- Conectar a Sheets si ya hay ID ---
        if self.var_sheet_id.get():
            self._intentar_conexion_silenciosa()
        else:
            self.lbl_info_libro.configure(text="Estado: Sin configurar", text_color="#f97316")

        # --- Timer para limpiar buffer ---
        self.after(1000, self._revisar_buffer)

    # ------------------------------------------------------------------
    # CONSTRUCCIÓN DE LA INTERFAZ (completa)
    # ------------------------------------------------------------------
    def _construir_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.cont = ctk.CTkFrame(self, fg_color="transparent")
        self.cont.grid(row=0, column=0, sticky="nsew")
        self.cont.grid_columnconfigure(0, weight=1)
        self.cont.grid_rowconfigure(0, weight=1)

        # --- LADO IZQUIERDO: cámara, estado y controles ---
        self.frame_izq = ctk.CTkFrame(self.cont, fg_color="transparent")
        self.frame_izq.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Barra superior con botón de ajustes
        bar = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(bar, text="📷 ESCÁNER PROFESIONAL", font=("Segoe UI", 22, "bold")).pack(side="left")
        self.btn_ajustes = ctk.CTkButton(bar, text="⚙️ AJUSTES", width=100, command=self._toggle_ajustes, fg_color="#3b82f6")
        self.btn_ajustes.pack(side="right")

        # Barra de estado del buffer
        self.buffer_frame = ctk.CTkFrame(self.frame_izq, fg_color="#1e293b", height=50, corner_radius=8)
        self.buffer_frame.pack(fill="x", pady=5)
        self.buffer_label = ctk.CTkLabel(self.buffer_frame, text="📦 Buffer: -- / --", font=("Segoe UI", 12), text_color="#94a3b8")
        self.buffer_label.pack(pady=5)

        # Visor de cámara
        self.frame_cam = ctk.CTkFrame(self.frame_izq, fg_color="#000000", corner_radius=15, border_width=2, border_color="#1e293b")
        self.frame_cam.pack(fill="both", expand=True, pady=5)
        self.lbl_cam = ctk.CTkLabel(self.frame_cam, text="SISTEMA LISTO\nPRESIONE INICIAR", font=("Segoe UI", 14))
        self.lbl_cam.pack(fill="both", expand=True)
        self.overlay = ctk.CTkLabel(self.frame_cam, text="", font=("Segoe UI", 36, "bold"), fg_color="transparent")
        self.overlay.place(relx=0.5, rely=0.5, anchor="center")

        # Controles de cámara
        c_box = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        c_box.pack(pady=10)
        self.btn_play = ctk.CTkButton(c_box, text="▶ INICIAR ESCÁNER", fg_color="#22c55e", hover_color="#16a34a", height=40, command=self._iniciar_camara)
        self.btn_play.pack(side="left", padx=10)
        self.btn_stop = ctk.CTkButton(c_box, text="⏹ DETENER", fg_color="#ef4444", hover_color="#dc2626", height=40, command=self._detener_camara)
        self.btn_stop.pack(side="left", padx=10)
        self.btn_clear_buffer = ctk.CTkButton(c_box, text="🧹 LIMPIAR BUFFER", fg_color="#f59e0b", hover_color="#d97706", height=40, command=self._limpiar_buffer)
        self.btn_clear_buffer.pack(side="left", padx=10)

        # Log de eventos
        self.log_box = ctk.CTkTextbox(self.frame_izq, height=120, font=("Consolas", 12), border_width=1)
        self.log_box.pack(fill="x", pady=5)

        # --- LADO DERECHO: panel de ajustes (colapsable) ---
        self.frame_der = ctk.CTkFrame(self.cont, width=320, border_width=1, border_color="#334155")
        self.frame_der.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(self.frame_der, text="CONFIGURACIÓN", font=("Segoe UI", 16, "bold")).pack(pady=(20, 15))

        # Importar credenciales JSON
        ctk.CTkLabel(self.frame_der, text="Acceso a Google API:", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=25)
        self.btn_load_json = ctk.CTkButton(self.frame_der, text="📂 IMPORTAR KEY (JSON)", fg_color="#334155", hover_color="#475569", command=self._seleccionar_credenciales)
        self.btn_load_json.pack(fill="x", padx=25, pady=(5, 10))

        ctk.CTkFrame(self.frame_der, height=1, fg_color="#334155").pack(fill="x", padx=30, pady=15)

        # Celda de inicio
        ctk.CTkLabel(self.frame_der, text="Celda de Inicio (ej: B2):").pack(anchor="w", padx=25)
        self.ent_celda = ctk.CTkEntry(self.frame_der, textvariable=self.var_celda, placeholder_text="B2")
        self.ent_celda.pack(fill="x", padx=25, pady=(0, 15))

        # Límite de lote
        ctk.CTkLabel(self.frame_der, text="ONUs por Hoja (Límite):").pack(anchor="w", padx=25)
        self.ent_limite = ctk.CTkEntry(self.frame_der, textvariable=self.var_limite, placeholder_text="100")
        self.ent_limite.pack(fill="x", padx=25, pady=(0, 15))

        # Google Sheet ID
        ctk.CTkLabel(self.frame_der, text="Google Sheet ID:").pack(anchor="w", padx=25)
        self.entry_sheet = ctk.CTkEntry(self.frame_der, textvariable=self.var_sheet_id)
        self.entry_sheet.pack(fill="x", padx=25, pady=(0, 20))

        # Botón guardar y conectar
        self.btn_save = ctk.CTkButton(self.frame_der, text="💾 APLICAR Y CONECTAR", font=("Segoe UI", 13, "bold"), height=45, command=self._guardar_todo)
        self.btn_save.pack(fill="x", padx=25, pady=10)

        self.lbl_info_libro = ctk.CTkLabel(self.frame_der, text="Estado: Offline", text_color="#64748b")
        self.lbl_info_libro.pack(pady=20, padx=25)

    # ------------------------------------------------------------------
    # MÉTODOS DE CÁMARA (OPTIMIZADOS)
    # ------------------------------------------------------------------
    def _iniciar_camara(self):
        if self.camara_activa:
            return
        if self.hilo_camara and self.hilo_camara.is_alive():
            self._detener_camara()

        self.cap = cv2.VideoCapture(self.var_camara_idx.get(), cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self._log("❌ Error hardware: Cámara no disponible. Verifique que no esté en uso.")
            return
        # Resolución equilibrada: 800x600 (fluida y nítida)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        self.camara_activa = True
        self.running = True
        self.btn_play.configure(state="disabled")
        self.hilo_camara = threading.Thread(target=self._loop_camara, daemon=True)
        self.hilo_camara.start()
        self._log("📷 Cámara iniciada (800x600, DirectShow)")

    def _loop_camara(self):
        frame_skip = 2          # decodificar cada 2 frames
        frame_count = 0
        img_ctk = None
        ultima_actualizacion = 0

        while self.running and self.cap is not None and not self._destruida:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame_count += 1

            # Decodificación (cada 'frame_skip' frames)
            if frame_count % frame_skip == 0:
                try:
                    codigos = pyzbar.decode(frame, symbols=[ZBarSymbol.CODE128, ZBarSymbol.QRCODE])
                    for c in codigos:
                        texto = c.data.decode("utf-8").strip()
                        if texto:
                            self.after(0, lambda t=texto: self._procesar_lectura(t))
                except Exception as e:
                    self.after(0, lambda: self._log(f"⚠️ Error en decodificación: {e}"))

            # Actualizar visor a ~30 fps
            ahora = time.time()
            if ahora - ultima_actualizacion >= 0.033:
                ultima_actualizacion = ahora
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                if img_ctk is None:
                    img_ctk = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(800, 600))
                else:
                    img_ctk.configure(light_image=pil_img, dark_image=pil_img)
                self.after(0, lambda: self._actualizar_visor(img_ctk))

            time.sleep(0.01)

        if self.cap:
            self.cap.release()
            self.cap = None
        self.after(0, lambda: self._log("🔴 Cámara detenida"))

    def _actualizar_visor(self, img):
        if self._destruida or not self.winfo_exists():
            return
        if self.camara_activa and img is not None:
            try:
                self.lbl_cam.configure(image=img, text="")
                self._ultima_img = img
            except Exception:
                pass

    def _detener_camara(self):
        self.running = False
        self.camara_activa = False
        if self.hilo_camara and self.hilo_camara.is_alive():
            self.hilo_camara.join(timeout=1.0)
        self.hilo_camara = None
        if self.cap:
            self.cap.release()
            self.cap = None
        try:
            self.lbl_cam.configure(image=None, text="SISTEMA DETENIDO")
        except Exception:
            pass
        self.btn_play.configure(state="normal")
        self._log("🛑 Cámara detenida correctamente")

    # ------------------------------------------------------------------
    # PROCESAMIENTO DE LECTURAS Y CONTROL DE DUPLICADOS
    # ------------------------------------------------------------------
    def _procesar_lectura(self, texto):
        if self.bloqueado or self._destruida:
            return

        datos = parsear_codigo(texto)
        ahora = time.time()

        if ahora - self.buffer["timestamp"] > self.TIMEOUT_BUFFER:
            if self.buffer["mac"] or self.buffer["serial"]:
                self._log("⏰ Timeout: buffer limpiado automáticamente")
            self._limpiar_buffer()

        actualizado = False
        if datos["mac"]:
            self.buffer["mac"] = datos["mac"]
            self.buffer["timestamp"] = ahora
            actualizado = True
            self._log(f"📡 MAC capturada: {datos['mac']}")
        if datos["serial"]:
            self.buffer["serial"] = datos["serial"]
            self.buffer["timestamp"] = ahora
            actualizado = True
            self._log(f"🔢 SN capturado: {datos['serial']}")

        if actualizado:
            self._actualizar_estado_buffer()

        if self.buffer["mac"] and self.buffer["serial"]:
            clave = f"{self.buffer['mac']}|{self.buffer['serial']}"
            if clave in self.registrados_recientes:
                self._log("⚠️ Equipo ya registrado en esta sesión, omitiendo.")
                self._limpiar_buffer()
                return
            self.mac_actual = self.buffer["mac"]
            self.serial_actual = self.buffer["serial"]
            self._enviar_a_nube(clave)

    def _enviar_a_nube(self, clave_duplicado=None):
        self.bloqueado = True
        self.overlay.configure(text="🛰️ REGISTRANDO...", text_color="#60a5fa")

        def tarea():
            try:
                res = self.sheets_mgr.registrar_onu(
                    mac=self.mac_actual,
                    serial=self.serial_actual,
                    precinto="",
                    pon="GPON"
                )
                self.after(0, lambda: self._finalizar_registro(res["status"], res.get("mensaje", ""), clave_duplicado))
            except Exception as e:
                self.after(0, lambda: self._finalizar_registro("error", str(e), None))

        threading.Thread(target=tarea, daemon=True).start()

    def _finalizar_registro(self, estado, mensaje, clave):
        if estado == "registrado":
            self.overlay.configure(text="✅ ÉXITO", text_color="#4ade80")
            self._log(f"REGISTRADO: {self.mac_actual} → {mensaje}")
            if clave:
                self.registrados_recientes.add(clave)
                if len(self.registrados_recientes) > self.MAX_CACHE:
                    self.registrados_recientes = set(list(self.registrados_recientes)[-self.MAX_CACHE:])
            self._limpiar_buffer()
        elif estado == "duplicado":
            self.overlay.configure(text="⚠️ DUPLICADO", text_color="#fbbf24")
            self._log(f"OMITIDO: {mensaje}")
        else:
            self.overlay.configure(text="❌ ERROR", text_color="#f87171")
            self._log(f"FALLO: {mensaje}")

        self.after(2000, self._reset_ciclo)

    def _reset_ciclo(self):
        self.overlay.configure(text="")
        self.mac_actual = ""
        self.serial_actual = ""
        self.bloqueado = False

    # ------------------------------------------------------------------
    # GESTIÓN DE BUFFER
    # ------------------------------------------------------------------
    def _actualizar_estado_buffer(self):
        if self._destruida:
            return
        mac_str = self.buffer["mac"] if self.buffer["mac"] else "---"
        sn_str = self.buffer["serial"] if self.buffer["serial"] else "---"
        try:
            self.buffer_label.configure(text=f"📦 Buffer: MAC={mac_str} | SN={sn_str}")
        except Exception:
            pass

    def _limpiar_buffer(self):
        self.buffer = {"mac": None, "serial": None, "timestamp": 0}
        self._actualizar_estado_buffer()
        self._log("🧹 Buffer limpiado")

    def _revisar_buffer(self):
        if self._destruida:
            return
        ahora = time.time()
        if self.buffer["timestamp"] > 0 and (ahora - self.buffer["timestamp"]) > self.TIMEOUT_BUFFER:
            if self.buffer["mac"] or self.buffer["serial"]:
                self._log("⚠️ Buffer expirado, limpiando...")
                self._limpiar_buffer()
        self.after(1000, self._revisar_buffer)

    # ------------------------------------------------------------------
    # CONFIGURACIÓN Y CONEXIÓN
    # ------------------------------------------------------------------
    def _intentar_conexion_silenciosa(self):
        """Conecta a Sheets solo si no hay conexión activa."""
        if self._conexion_activa:
            return
        self.lbl_info_libro.configure(text="⚡ Conectando...", text_color="#60a5fa")
        
        def hilo():
            ok, msg = self.sheets_mgr.conectar()
            self.sheets_ok = ok
            self._conexion_activa = ok
            color = "#4ade80" if ok else "#f87171"
            
            # --- NUEVO: Programar la actualización de forma segura ---
            def actualizar():
                # Verificar que la pantalla no haya sido destruida
                if self._destruida or not self.winfo_exists():
                    return
                self.lbl_info_libro.configure(text=f"STATUS: {msg}", text_color=color)
                if ok:
                    self._log("✅ Conexión a Google Sheets establecida (persistente)")
                else:
                    self._log(f"❌ Error de conexión: {msg}")
            
            # Ejecutar la actualización en el hilo principal
            self.after(0, actualizar)
        
        threading.Thread(target=hilo, daemon=True).start()

    def _guardar_todo(self):
        guardar_dato("google_sheet_id", self.var_sheet_id.get().strip())
        guardar_dato("celda_inicio", self.var_celda.get().strip())
        guardar_dato("limite_lote", int(self.var_limite.get().strip() or 100))
        self._conexion_activa = False
        self.sheets_mgr._hoja_cache = None
        self._intentar_conexion_silenciosa()
        self._log("⚙️ Ajustes guardados. Conexión renovada.")

    def _seleccionar_credenciales(self):
        from tkinter import filedialog
        ruta = filedialog.askopenfilename(title="Seleccionar credenciales JSON", filetypes=[("JSON files", "*.json")])
        if ruta:
            exito, msg = importar_credenciales(ruta)
            if exito:
                self._log("✅ Archivo JSON importado con éxito.")
                self._conexion_activa = False
                self._intentar_conexion_silenciosa()
            else:
                self._log(f"❌ Error al importar JSON: {msg}")
        else:
            self._log("⚠️ No se seleccionó ningún archivo.")

    def _log(self, msg):
        if self._destruida:
            return
        ts = time.strftime("%H:%M:%S")
        try:
            self.log_box.insert("1.0", f"[{ts}] {msg}\n")
            self.log_box.see("1.0")
        except Exception:
            pass

    def _toggle_ajustes(self):
        if self.panel_ajustes:
            self.frame_der.grid_remove()
            self.panel_ajustes = False
        else:
            self.frame_der.grid()
            self.panel_ajustes = True

    def cerrar(self):
        self._destruida = True
        self._detener_camara()