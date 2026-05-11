import customtkinter as ctk
import cv2
import threading
import time
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from PIL import Image

# Importaciones de lógica interna
from src.core.sheets_manager import SheetsManager
from src.utils.config_manager import leer_dato, guardar_dato, importar_credenciales
from src.core.parser_onu import parsear_codigo

class PantallaEscaneo(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # Estado y Lógica
        self.camara_activa = False
        self.cap = None
        self.bloqueado = False
        self.mac_actual = ""
        self.serial_actual = ""
        self.ultimo_id = ""
        
        # Inicializar motor de precisión
        self.sheets_mgr = SheetsManager()
        self.sheets_ok = False

        # Variables UI persistentes
        self.var_sheet_id = ctk.StringVar(value=leer_dato("google_sheet_id"))
        self.var_celda = ctk.StringVar(value=leer_dato("celda_inicio", "B2"))
        self.var_limite = ctk.StringVar(value=str(leer_dato("limite_lote", 100)))
        self.var_camara_idx = ctk.IntVar(value=leer_dato("last_camera_index", 0))
        
        self.panel_ajustes = True
        self._construir_ui()
        
        if self.var_sheet_id.get():
            self._intentar_conexion_silenciosa()

    def _construir_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.cont = ctk.CTkFrame(self, fg_color="transparent")
        self.cont.grid(row=0, column=0, sticky="nsew")
        self.cont.grid_columnconfigure(0, weight=1)
        self.cont.grid_rowconfigure(0, weight=1)

        # --- IZQUIERDA (CÁMARA Y RESULTADOS) ---
        self.frame_izq = ctk.CTkFrame(self.cont, fg_color="transparent")
        self.frame_izq.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Barra Superior
        bar = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(bar, text="📷 ESCÁNER PROFESIONAL", font=("Segoe UI", 22, "bold")).pack(side="left")
        ctk.CTkButton(bar, text="⚙️ AJUSTES", width=100, command=self._toggle_ajustes, fg_color="#3b82f6").pack(side="right")

        # Status Bar (Lectura en tiempo real)
        self.status_bar = ctk.CTkFrame(self.frame_izq, fg_color="#0f172a", height=70, corner_radius=10)
        self.status_bar.pack(fill="x", pady=5)
        self.status_bar.pack_propagate(False)

        self.lbl_mac = ctk.CTkLabel(self.status_bar, text="MAC: ---", font=("Consolas", 18, "bold"), text_color="#94a3b8")
        self.lbl_mac.pack(side="left", padx=25)
        self.lbl_sn = ctk.CTkLabel(self.status_bar, text="SERIAL: ---", font=("Consolas", 18, "bold"), text_color="#94a3b8")
        self.lbl_sn.pack(side="left", padx=25)

        # Visor
        self.frame_cam = ctk.CTkFrame(self.frame_izq, fg_color="#000000", corner_radius=15, border_width=2, border_color="#1e293b")
        self.frame_cam.pack(fill="both", expand=True, pady=5)
        self.lbl_cam = ctk.CTkLabel(self.frame_cam, text="SISTEMA LISTO\nPRESIONE INICIAR", font=("Segoe UI", 14))
        self.lbl_cam.pack(fill="both", expand=True)

        self.overlay = ctk.CTkLabel(self.frame_cam, text="", font=("Segoe UI", 36, "bold"), fg_color="transparent")
        self.overlay.place(relx=0.5, rely=0.5, anchor="center")

        # Controles Cámara
        c_box = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        c_box.pack(pady=10)
        self.btn_play = ctk.CTkButton(c_box, text="▶ INICIAR ESCÁNER", fg_color="#22c55e", hover_color="#16a34a", height=40, command=self._iniciar_camara)
        self.btn_play.pack(side="left", padx=10)
        self.btn_stop = ctk.CTkButton(c_box, text="⏹ DETENER", fg_color="#ef4444", hover_color="#dc2626", height=40, command=self._detener_camara)
        self.btn_stop.pack(side="left", padx=10)

        self.log_box = ctk.CTkTextbox(self.frame_izq, height=120, font=("Consolas", 12), border_width=1)
        self.log_box.pack(fill="x", pady=5)

       # --- DERECHA (AJUSTES QUIRÚRGICOS) ---
        self.frame_der = ctk.CTkFrame(self.cont, width=320, border_width=1, border_color="#334155")
        self.frame_der.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.frame_der, text="CONFIGURACIÓN DE TABLA", font=("Segoe UI", 16, "bold")).pack(pady=(20, 15))

        # --- SECCIÓN DE CREDENCIALES (NUEVO) ---
        ctk.CTkLabel(self.frame_der, text="Acceso a Google API:", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=25)
        self.btn_load_json = ctk.CTkButton(
            self.frame_der, 
            text="📂 IMPORTAR KEY (JSON)", 
            fg_color="#334155", 
            hover_color="#475569",
            command=self._seleccionar_credenciales # Llama a la lógica de importar
        )
        self.btn_load_json.pack(fill="x", padx=25, pady=(5, 10))

        # Línea divisoria para separar la llave del destino
        ctk.CTkFrame(self.frame_der, height=1, fg_color="#334155").pack(fill="x", padx=30, pady=15)

        # Posición de Tabla
        ctk.CTkLabel(self.frame_der, text="Celda de Inicio (ej: B2):").pack(anchor="w", padx=25)
        self.ent_celda = ctk.CTkEntry(self.frame_der, textvariable=self.var_celda, placeholder_text="B2")
        self.ent_celda.pack(fill="x", padx=25, pady=(0, 15))

        # Límite de Lote
        ctk.CTkLabel(self.frame_der, text="ONUs por Hoja (Límite):").pack(anchor="w", padx=25)
        self.ent_limite = ctk.CTkEntry(self.frame_der, textvariable=self.var_limite, placeholder_text="100")
        self.ent_limite.pack(fill="x", padx=25, pady=(0, 15))

        # ID Sheet
        ctk.CTkLabel(self.frame_der, text="Google Sheet ID:").pack(anchor="w", padx=25)
        self.entry_sheet = ctk.CTkEntry(self.frame_der, textvariable=self.var_sheet_id)
        self.entry_sheet.pack(fill="x", padx=25, pady=(0, 20))
        
        self.btn_save = ctk.CTkButton(self.frame_der, text="💾 APLICAR Y CONECTAR", font=("Segoe UI", 13, "bold"), height=45, command=self._guardar_todo)
        self.btn_save.pack(fill="x", padx=25, pady=10)
        
        self.lbl_info_libro = ctk.CTkLabel(self.frame_der, text="Estado: Offline", text_color="#64748b")
        self.lbl_info_libro.pack(pady=20, padx=25)

    # --- LÓGICA DE ESCANEO ---

    def _loop_camara(self):
        # Optimización de rendimiento: bajar ligeramente la resolución para procesar más rápido
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        while self.camara_activa:
            ret, frame = self.cap.read()
            if not ret: break

            # Detección ultra-rápida limitada a tipos específicos
            codigos = pyzbar.decode(frame, symbols=[ZBarSymbol.CODE128, ZBarSymbol.QRCODE])
            for c in codigos:
                texto = c.data.decode("utf-8").strip()
                if texto:
                    self.after(0, lambda t=texto: self._procesar_lectura(t))

            # Conversión eficiente para UI
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(frame_rgb)
            ctk_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(720, 450))
            self.after(0, self._actualizar_visor, ctk_img)
            time.sleep(0.001) # Reducción de latencia al mínimo

    def _procesar_lectura(self, texto):
        if self.bloqueado: return
        
        datos = parsear_codigo(texto)
        cambio = False
        
        if datos["mac"] and datos["mac"] != self.mac_actual:
            self.mac_actual = datos["mac"]
            self.lbl_mac.configure(text=f"MAC: {self.mac_actual}", text_color="#4ade80")
            cambio = True
            
        if datos["serial"] and datos["serial"] != self.serial_actual:
            self.serial_actual = datos["serial"]
            self.lbl_sn.configure(text=f"SN: {self.serial_actual}", text_color="#4ade80")
            cambio = True

        # Si tenemos ambos datos, disparamos el envío
        if self.mac_actual and self.serial_actual:
            key = f"{self.mac_actual}-{self.serial_actual}"
            if key != self.ultimo_id:
                self.bloqueado = True
                self.ultimo_id = key
                self._enviar_a_nube()

    def _enviar_a_nube(self):
        self.overlay.configure(text="🛰️ REGISTRANDO...", text_color="#60a5fa")
        def tarea():
            try:
                res = self.sheets_mgr.registrar_onu(
                    mac=self.mac_actual, 
                    serial=self.serial_actual,
                    pon="GPON" # Opcional: pasar detección desde parser
                )
                self.after(0, lambda: self._finalizar_registro(res["status"], res.get("mensaje", "")))
            except Exception as e:
                self.after(0, lambda: self._finalizar_registro("error", str(e)))

        threading.Thread(target=tarea, daemon=True).start()

    def _finalizar_registro(self, estado, mensaje):
        if estado == "registrado":
            self.overlay.configure(text="✅ ÉXITO", text_color="#4ade80")
            self._log(f"REGISTRADO: {self.mac_actual} -> {mensaje}")
        elif estado == "duplicado":
            self.overlay.configure(text="⚠️ DUPLICADO", text_color="#fbbf24")
            self._log(f"OMITIDO: {mensaje}")
        else:
            self.overlay.configure(text="❌ ERROR", text_color="#f87171")
            self._log(f"FALLO: {mensaje}")
        
        # Pausa para que el usuario vea el resultado antes de limpiar
        self.after(2000, self._reset_ciclo)

    def _guardar_todo(self):
        """Guarda todos los ajustes y reconecta el motor."""
        guardar_dato("google_sheet_id", self.var_sheet_id.get().strip())
        guardar_dato("celda_inicio", self.var_celda.get().strip())
        guardar_dato("limite_lote", int(self.var_limite.get().strip() or 100))
        
        self._log("⚙️ Ajustes guardados. Reconectando...")
        self._intentar_conexion_silenciosa()

    # --- MÉTODOS DE SOPORTE (Se mantienen de tu lógica pero optimizados) ---
    def _iniciar_camara(self):
        if self.camara_activa: return
        self.cap = cv2.VideoCapture(self.var_camara_idx.get())
        if not self.cap.isOpened():
            self._log("❌ Error hardware: Cámara no lista.")
            return
        self.camara_activa = True
        self.btn_play.configure(state="disabled")
        threading.Thread(target=self._loop_camara, daemon=True).start()

    def _detener_camara(self):
        self.camara_activa = False
        if self.cap: self.cap.release()
        self.lbl_cam.configure(image=None, text="SISTEMA DETENIDO")
        self.btn_play.configure(state="normal")

    def _actualizar_visor(self, img):
        if self.camara_activa:
            self.lbl_cam.configure(image=img, text="")

    def _intentar_conexion_silenciosa(self):
        self.lbl_info_libro.configure(text="⚡ Sincronizando...", text_color="#60a5fa")
        def hilo():
            ok, msg = self.sheets_mgr.conectar()
            self.sheets_ok = ok
            color = "#4ade80" if ok else "#f87171"
            self.after(0, lambda: self.lbl_info_libro.configure(text=f"STATUS: {msg}", text_color=color))
        threading.Thread(target=hilo, daemon=True).start()

    def _log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.log_box.insert("1.0", f"[{ts}] {msg}\n")

    def _reset_ciclo(self):
        self.overlay.configure(text="")
        self.mac_actual = ""
        self.serial_actual = ""
        self.lbl_mac.configure(text="MAC: ---", text_color="#94a3b8")
        self.lbl_sn.configure(text="SERIAL: ---", text_color="#94a3b8")
        self.bloqueado = False

    def _toggle_ajustes(self):
        if self.panel_ajustes: self.frame_der.grid_remove()
        else: self.frame_der.grid()
        self.panel_ajustes = not self.panel_ajustes
    
    # ══════════════════════════════════════════════════════════════════════════
    # LÓGICA DE CREDENCIALES (FALTANTE)
    # ══════════════════════════════════════════════════════════════════════════

    def _seleccionar_credenciales(self):
        """Abre un explorador de archivos para importar el JSON de Google."""
        from tkinter import filedialog
        
        ruta = filedialog.askopenfilename(
            title="Seleccionar credenciales JSON", 
            filetypes=[("JSON files", "*.json")]
        )
        
        if ruta:
            # Llamamos a la función del config_manager que ya tenemos
            exito, msg = importar_credenciales(ruta)
            if exito:
                self._log("✅ Archivo JSON importado con éxito.")
                self._intentar_conexion_silenciosa() # Reconecta automáticamente
            else:
                self._log(f"❌ Error al importar JSON: {msg}")
        else:
            self._log("⚠️ No se seleccionó ningún archivo.")