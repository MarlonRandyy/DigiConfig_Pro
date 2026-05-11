import customtkinter as ctk

class PantallaGuia(ctk.CTkScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._configurar_estilos()
        self._construir_ui()

    def _configurar_estilos(self):
        # Colores
        self.color_bg_card = "#1e293b" if self.app._modo_oscuro else "#f8fafc"
        self.color_borde = "#334155" if self.app._modo_oscuro else "#e2e8f0"
        self.color_acento = "#3b82f6"
        self.color_info = "#60a5fa"
        self.color_advertencia = "#fbbf24"
        
        # Fuentes
        self.font_h1 = ("Segoe UI", 32, "bold")
        self.font_h2 = ("Segoe UI", 22, "bold")
        self.font_h3 = ("Segoe UI", 16, "bold")
        self.font_body = ("Segoe UI", 13)
        self.font_code = ("Consolas", 12)

    def _construir_ui(self):
        # --- ENCABEZADO PRINCIPAL ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 10))
        
        ctk.CTkLabel(header, text="🚀 DigiConfig Pro: Manual Maestro", font=self.font_h1, text_color=self.color_acento).pack(anchor="w")
        ctk.CTkLabel(header, text="Guía técnica para el aprovisionamiento y gestión de inventario en la nube.", 
                     font=self.font_body, text_color="#94a3b8").pack(anchor="w")

        # --- SECCIÓN 1: EL ECOSISTEMA DE ESCANEO ---
        self._seccion_introduccion_escaneo()

        # --- SECCIÓN 2: GOOGLE SHEETS PASO A PASO ---
        self._seccion_google_sheets_pro()

        # --- SECCIÓN 3: PROGRAMACIÓN MULTI-MODELO ---
        self._seccion_programacion_onu()

        # Footer
        ctk.CTkLabel(self, text="Soporte Técnico Digicable v2.0", font=("Segoe UI", 10), text_color="gray").pack(pady=30)

    def _seccion_introduccion_escaneo(self):
        card = self._crear_contenedor_seccion("📷 El Módulo de Escaneo Inteligente", self.color_acento)
        
        texto_intro = (
            "Este módulo no es solo una cámara; es un gestor de base de datos en tiempo real. "
            "Al escanear una ONU, el sistema realiza tres acciones simultáneas:\n\n"
            "• Identifica el Serial (SN) y modelo.\n"
            "• Clasifica el equipo bajo el membrete configurado.\n"
            "• Sincroniza la información con tu hoja de cálculo global."
        )
        ctk.CTkLabel(card, text=texto_intro, font=self.font_body, justify="left", wraplength=750).pack(anchor="w", padx=20, pady=10)

        # Sub-detalles Pro
        detalles_frame = ctk.CTkFrame(card, fg_color="transparent")
        detalles_frame.pack(fill="x", padx=20, pady=10)

        # Membrete y Edición
        self._item_lista(detalles_frame, "🏷️ Membrete Personalizable", "Puedes editar el título del lote (ej. 'LOTE_MAYO_2026') directamente en la pantalla de escaneo antes de empezar. Todos los registros llevarán esta marca.")
        self._item_lista(detalles_frame, "✏️ Edición de Celdas", "Si el escáner comete un error, puedes hacer DOBLE CLIC en la tabla de resultados para corregir el dato antes de que se envíe a la nube.")
        self._item_lista(detalles_frame, "📄 Paginación (50/100)", "Para evitar lentitud, el sistema divide los links de los registros. Puedes alternar entre ver grupos de 50 o 100 registros para una revisión más fluida.")

    def _seccion_google_sheets_pro(self):
        card = self._crear_contenedor_seccion("☁️ Configuración de Google Sheets (Nivel Experto)", "#10b981")
        
        pasos = [
            ("Crear el JSON", "Ve a Google Cloud Console, crea un Service Account, genera una llave JSON y descárgala. Este archivo es la 'llave' que permite a DigiConfig escribir en tu nombre."),
            ("Importar Key", "En DigiConfig, usa el botón 'Importar JSON'. El software leerá el correo electrónico interno de la cuenta de servicio (ej: service-account@proyecto.iam.gserviceaccount.com)."),
            ("El Vínculo Vital", "IMPORTANTE: Copia ese correo de la cuenta de servicio, ve a tu Google Sheet en el navegador y dale permisos de 'EDITOR'. Sin este paso, recibirás error 403."),
            ("ID del Spreadsheet", "Copia el código alfanumérico largo de la URL de tu Sheet. Pégalo en DigiConfig. Ahora la app sabe exactamente en qué libro escribir.")
        ]

        for i, (p, d) in enumerate(pasos, 1):
            f = ctk.CTkFrame(card, fg_color="transparent")
            f.pack(fill="x", padx=25, pady=5)
            ctk.CTkLabel(f, text=f"{i}", fg_color="#10b981", text_color="white", width=25, corner_radius=12).pack(side="left", padx=(0,10))
            ctk.CTkLabel(f, text=f"{p}:", font=("Segoe UI", 13, "bold")).pack(side="left")
            ctk.CTkLabel(f, text=d, font=self.font_body, wraplength=550, justify="left").pack(side="left", padx=5)

    def _seccion_programacion_onu(self):
        card = self._crear_contenedor_seccion("⚙️ Programación Multi-Modelo", self.color_advertencia)
        
        intro = (
            "El motor de DigiConfig reconoce automáticamente el hardware conectado. "
            "Soporta configuraciones para FiberHome, Huawei y ZTE bajo el estándar de Digicable."
        )
        ctk.CTkLabel(card, text=intro, font=self.font_body, padx=20).pack(anchor="w", pady=5)

        modelos = ctk.CTkFrame(card, fg_color="#0f172a", corner_radius=10)
        modelos.pack(fill="x", padx=20, pady=10)

        info_modelos = (
            "• HG6143D / HG6145F: Acceso vía 192.168.1.1 -> Inyección de Config XML -> Reinicio -> IP 192.169.100.1\n"
            "• EG8145V5 / HS8546V5: Proceso de Telnet automático para seteo de WAN y perfiles de voz.\n"
            "• Modo Recuperación: Si el proceso falla, el software intentará un 'Hard Reset' remoto para limpiar la caché de la ONU."
        )
        ctk.CTkLabel(modelos, text=info_modelos, font=self.font_code, text_color=self.color_info, justify="left", padx=15, pady=15).pack()

    # --- FUNCIONES DE APOYO ---
    def _crear_contenedor_seccion(self, titulo, color):
        frame = ctk.CTkFrame(self, fg_color=self.color_bg_card, border_width=1, border_color=self.color_borde, corner_radius=15)
        frame.pack(fill="x", padx=40, pady=15)
        
        lbl = ctk.CTkLabel(frame, text=titulo, font=self.font_h2, text_color=color)
        lbl.pack(anchor="w", padx=20, pady=(20, 10))
        
        return frame

    def _item_lista(self, master, titulo, desc):
        f = ctk.CTkFrame(master, fg_color="transparent")
        f.pack(fill="x", pady=5)
        ctk.CTkLabel(f, text=titulo, font=("Segoe UI", 13, "bold"), text_color=self.color_info).pack(anchor="w")
        ctk.CTkLabel(f, text=desc, font=self.font_body, wraplength=700, justify="left").pack(anchor="w", padx=10)