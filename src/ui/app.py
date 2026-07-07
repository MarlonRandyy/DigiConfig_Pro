# ============================================================
# app.py — DigiConfig Pro v3.1 (Mejorado)
# Modo oscuro fijo, sidebar siempre expandido, navegación fluida
# ============================================================
import customtkinter as ctk
import os
import sys
import traceback
import threading
from PIL import Image

# ── Ruta raíz (soporte para ejecutable PyInstaller) ──────────
if getattr(sys, 'frozen', False):
    ROOT = sys._MEIPASS
else:
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

sys.path.insert(0, ROOT)

import src.ui.tema as tema_mod
from src.core import modelos_manager

# ── Configuración inicial de CustomTkinter ──────────────────
ctk.set_appearance_mode("dark")          # Solo modo oscuro
ctk.set_default_color_theme("dark-blue")
ctk.set_widget_scaling(1.0)              # Escalado base para pantallas HD

# ── Constantes de navegación ──────────────────────────────────
NAV_ITEMS = [
    ("dashboard",     "Dashboard",       "📊", "PRINCIPAL"),
    ("configuracion", "Configurar ONU",  "🛠", "PRINCIPAL"),
    ("modelos",       "Modelos XML",     "🧱", "GESTIÓN"),
    ("historial",     "Historial",       "📋", "GESTIÓN"),
    ("escaneo",       "Escanear ONU",    "🔍", "GESTIÓN"),
    ("guia",          "Guía de Usuario", "📖", "GESTIÓN"),
]

ANCHO_SIDEBAR = 220  # Ancho fijo, siempre expandido

def _separador(parent, T):
    """Línea separadora en el sidebar."""
    ctk.CTkFrame(parent, height=1, fg_color=T.borde, corner_radius=0).pack(fill="x", padx=14, pady=5)


class App:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("DigiConfig Pro — Digicable")
        self.root.geometry("1200x730")
        self.root.minsize(980, 640)  # Tamaño mínimo para evitar recortes

        # ── Estado ────────────────────────────────────────────
        self.onu_info = {}
        self.modelos = {}
        self._nav_btns = {}
        self._sec_labels = []
        self._pantalla = None
        self._destino_act = "dashboard"

        # ── Referencias a widgets del sidebar ─────────────────
        self._logo_label = None
        self._lbl_led = None
        self._onu_texto = None
        self.badge_onu = None

        self._prep_assets()
        self._build_ui()
        self._cargar_modelos_async()  # Carga en segundo plano

    # ──────────────────────────────────────────────────────────
    #  CARGA ASÍNCRONA DE MODELOS (no bloquea la UI)
    # ──────────────────────────────────────────────────────────
    def _cargar_modelos_async(self):
        """
        Carga los modelos en un hilo separado para no bloquear la interfaz.
        Si falla la carga, se deja un diccionario vacío y se muestra un mensaje.
        """
        def tarea():
            try:
                self.modelos = modelos_manager.cargar()
                print(f"[App] ✅ Modelos cargados: {len(self.modelos)} disponibles")
            except Exception as e:
                print(f"[App] ❌ Error al cargar modelos: {e}")
                self.modelos = {}
        threading.Thread(target=tarea, daemon=True).start()

    # ──────────────────────────────────────────────────────────
    #  PREPARACIÓN DE ASSETS
    # ──────────────────────────────────────────────────────────
    def _prep_assets(self):
        """Asegura que los assets (imágenes) estén disponibles."""
        assets = os.path.join(ROOT, "assets")
        os.makedirs(assets, exist_ok=True)
        # Usar la versión azul para modo oscuro (contrasta bien)
        src = os.path.join(ROOT, "digicable_azul.png")
        dst = os.path.join(assets, "digicable_azul.png")
        if os.path.exists(src) and not os.path.exists(dst):
            import shutil
            shutil.copy2(src, dst)

    # ──────────────────────────────────────────────────────────
    #  CONSTRUCCIÓN UI
    # ──────────────────────────────────────────────────────────
    def _build_ui(self):
        T = tema_mod.Tema
        self.root.configure(fg_color=T.bg)

        # ── Sidebar (siempre expandido) ──────────────────────
        self.sidebar = ctk.CTkFrame(
            self.root, width=ANCHO_SIDEBAR, corner_radius=0, fg_color=T.sidebar
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar_widgets()

        # ── Área principal ────────────────────────────────────
        self.area = ctk.CTkFrame(self.root, corner_radius=0, fg_color=T.bg)
        self.area.pack(side="left", fill="both", expand=True)

        # ── Topbar ────────────────────────────────────────────
        self.topbar = ctk.CTkFrame(
            self.area, height=58, corner_radius=0,
            fg_color=T.topbar, border_width=1, border_color=T.borde
        )
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)
        self._build_topbar()

        # ── Contenedor de pantallas ──────────────────────────
        self.contenido = ctk.CTkFrame(self.area, corner_radius=0, fg_color=T.bg)
        self.contenido.pack(fill="both", expand=True)

        # Cargar la pantalla inicial
        self.navegar(self._destino_act)

    # ──────────────────────────────────────────────────────────
    #  SIDEBAR – CONSTRUCCIÓN
    # ──────────────────────────────────────────────────────────
    def _build_sidebar_widgets(self):
        T = tema_mod.Tema
        for w in self.sidebar.winfo_children():
            w.destroy()
        self._nav_btns.clear()
        self._sec_labels.clear()

        # ─── Logo ─────────────────────────────────────────────
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=68)
        logo_frame.pack(fill="x", pady=(8, 0))
        logo_frame.pack_propagate(False)

        logo_path = os.path.join(ROOT, "assets", "digicable_azul.png")
        if os.path.exists(logo_path):
            try:
                img = ctk.CTkImage(Image.open(logo_path), size=(30, 30))
                self._logo_label = ctk.CTkLabel(logo_frame, image=img, text="")
                self._logo_label.pack(side="left", padx=(17, 8), pady=8)
                logo_frame._img_ref = img
            except Exception as e:
                print(f"[App] Error cargando logo: {e}")

        logo_text_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_text_frame.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            logo_text_frame, text="DigiConfig Pro",
            font=("Segoe UI", 13, "bold"), text_color="#ffffff"
        ).pack(anchor="w", pady=(14, 0))
        ctk.CTkLabel(
            logo_text_frame, text="Digicable - Soporte Técnico",
            font=("Segoe UI", 9), text_color="gray"
        ).pack(anchor="w")

        _separador(self.sidebar, T)

        # ─── Botones de navegación ────────────────────────────
        seccion_actual = None
        for key, texto, icono, seccion in NAV_ITEMS:
            if seccion != seccion_actual:
                seccion_actual = seccion
                if seccion != "PRINCIPAL":
                    _separador(self.sidebar, T)
                lbl = ctk.CTkLabel(
                    self.sidebar, text=seccion,
                    font=("Segoe UI", 9, "bold"), text_color=T.texto_dim
                )
                lbl.pack(anchor="w", padx=18, pady=(6, 2))
                lbl._nav_key = f"_sec_{seccion}"
                self._sec_labels.append(lbl)

            activo = (key == self._destino_act)
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icono}  {texto}",
                anchor="w",
                fg_color=T.nav_active_bg if activo else "transparent",
                hover_color=T.nav_active_bg if activo else T.nav_hover_bg,
                text_color="#ffffff" if activo else T.texto_muted,
                font=("Segoe UI", 12, "bold") if activo else ("Segoe UI", 12),
                height=44,
                corner_radius=T.r_btn,
                command=lambda k=key: self.navegar(k)
            )
            btn.pack(fill="x", padx=8, pady=2)
            btn._nav_key = key
            btn._nav_icono = icono
            btn._nav_texto = texto
            self._nav_btns[key] = btn

        # ─── Footer ONU ───────────────────────────────────────
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)
        _separador(self.sidebar, T)

        self._onu_footer = ctk.CTkFrame(
            self.sidebar, fg_color=T.surface2, corner_radius=T.r_chip
        )
        self._onu_footer.pack(fill="x", padx=8, pady=(4, 12))

        self._lbl_led = ctk.CTkLabel(
            self._onu_footer, text="⬤",
            font=("Segoe UI", 10), text_color=T.led_off
        )
        self._lbl_led.pack(side="left", padx=(10, 4), pady=10)

        self._onu_texto = ctk.CTkLabel(
            self._onu_footer, text="Sin ONU",
            font=("Segoe UI", 10), text_color=T.texto_muted
        )
        self._onu_texto.pack(side="left", pady=10, padx=(0, 8))

    # ──────────────────────────────────────────────────────────
    #  TOPBAR
    # ──────────────────────────────────────────────────────────
    def _build_topbar(self):
        T = tema_mod.Tema
        for w in self.topbar.winfo_children():
            w.destroy()

        self.lbl_titulo = ctk.CTkLabel(
            self.topbar, text="Dashboard de Conexión",
            font=("Segoe UI", 15, "bold"), text_color=T.texto
        )
        self.lbl_titulo.place(x=24, rely=0.5, anchor="w")

        # Indicador de estado ONU en la topbar (derecha)
        right = ctk.CTkFrame(self.topbar, fg_color="transparent")
        right.place(relx=0.99, rely=0.5, anchor="e")

        self.badge_onu = ctk.CTkLabel(
            right, text="● Sin ONU",
            font=("Segoe UI", 10, "bold"),
            fg_color=T.surface2,
            text_color=T.texto_muted,
            corner_radius=T.r_pill,
            padx=14, pady=5
        )
        self.badge_onu.pack(side="left", padx=(0, 10))

    # ──────────────────────────────────────────────────────────
    #  NAVEGACIÓN (optimizada, sin parámetro rebuild)
    # ──────────────────────────────────────────────────────────
    def navegar(self, destino: str):
        """
        Navega a la pantalla especificada.
        Destruye la pantalla anterior de forma segura y crea la nueva.
        """
        from src.ui.pantalla_dashboard import PantallaDashboard
        from src.ui.pantalla_configuracion import PantallaConfiguracion
        from src.ui.pantalla_modelos import PantallaModelos
        from src.ui.pantalla_historial import PantallaHistorial
        from src.ui.pantalla_guia import PantallaGuia

        try:
            from src.ui.pantalla_escaneo import PantallaEscaneo
        except ImportError as e:
            print(f"[Escaneo] Librerías no disponibles: {e}")
            PantallaEscaneo = None

        TITULOS = {
            "dashboard": "Dashboard de Conexión",
            "configuracion": "Configurar ONU",
            "modelos": "Librería de Modelos XML",
            "historial": "Historial de Instalaciones",
            "escaneo": "Escanear ONU (QR / Código de barras)",
            "guia": "Manual y Procedimientos",
        }
        PANTALLAS = {
            "dashboard": PantallaDashboard,
            "configuracion": PantallaConfiguracion,
            "modelos": PantallaModelos,
            "historial": PantallaHistorial,
            "escaneo": PantallaEscaneo,
            "guia": PantallaGuia,
        }

        self._destino_act = destino

        # ── Actualizar botones del sidebar ────────────────────
        T = tema_mod.Tema
        for key, btn in self._nav_btns.items():
            activo = (key == destino)
            btn.configure(
                fg_color=T.nav_active_bg if activo else "transparent",
                hover_color=T.nav_active_bg if activo else T.nav_hover_bg,
                text_color="#ffffff" if activo else T.texto_muted,
                font=("Segoe UI", 12, "bold") if activo else ("Segoe UI", 12),
            )
            btn.configure(text=f"  {btn._nav_icono}  {btn._nav_texto}", anchor="w")

        # ── Actualizar título ─────────────────────────────────
        if hasattr(self, "lbl_titulo"):
            self.lbl_titulo.configure(text=TITULOS.get(destino, "DigiConfig Pro"))

        # ── Limpiar pantalla anterior ─────────────────────────
        self._limpiar_pantalla_actual()

        # ── Instanciar nueva pantalla ─────────────────────────
        cls = PANTALLAS.get(destino)
        if cls is None:
            if destino == "escaneo":
                print("[Nav] Módulo de escaneo no disponible")
                self.navegar("dashboard")
            return

        try:
            p = cls(self.contenido, app=self)
            p.pack(fill="both", expand=True)
            self._pantalla = p
            print(f"[Nav] ✅ Pantalla '{destino}' cargada correctamente")
        except Exception as e:
            print(f"[Nav] ❌ ERROR al cargar '{destino}':")
            traceback.print_exc()
            # Redirigir a dashboard en caso de error crítico
            self.navegar("dashboard")

    def _limpiar_pantalla_actual(self):
        """Detiene y destruye la pantalla actual de forma segura."""
        if self._pantalla:
            try:
                if hasattr(self._pantalla, "cerrar"):
                    self._pantalla.cerrar()
                if hasattr(self._pantalla, "detener_camara"):
                    self._pantalla.detener_camara()
            except Exception as e:
                print(f"[Nav] Error al cerrar pantalla: {e}")

        for w in list(self.contenido.winfo_children()):
            try:
                w.pack_forget()
                w.destroy()
            except Exception as e:
                print(f"[Nav] Error al destruir widget: {e}")

        self.contenido.update_idletasks()

    # ──────────────────────────────────────────────────────────
    #  CALLBACKS ONU (con verificación de existencia)
    # ──────────────────────────────────────────────────────────
    def set_onu_detectada(self, info: dict):
        self.onu_info = info
        nombre = info.get("nombre_display", "ONU Detectada")[:26]
        T = tema_mod.Tema
        try:
            if self._lbl_led and self._lbl_led.winfo_exists():
                self._lbl_led.configure(text_color=T.led_on)
            if self._onu_texto and self._onu_texto.winfo_exists():
                self._onu_texto.configure(text=nombre, text_color=T.verde)
            if hasattr(self, "badge_onu") and self.badge_onu.winfo_exists():
                self.badge_onu.configure(
                    text="● ONU Conectada",
                    fg_color=T.verde_soft,
                    text_color=T.verde
                )
        except Exception as e:
            print(f"[ONU] Error al actualizar estado detectada: {e}")

    def set_onu_perdida(self):
        self.onu_info = {}
        T = tema_mod.Tema
        try:
            if self._lbl_led and self._lbl_led.winfo_exists():
                self._lbl_led.configure(text_color=T.led_off)
            if self._onu_texto and self._onu_texto.winfo_exists():
                self._onu_texto.configure(text="Sin ONU", text_color=T.texto_muted)
            if hasattr(self, "badge_onu") and self.badge_onu.winfo_exists():
                self.badge_onu.configure(
                    text="● Sin ONU",
                    fg_color=T.surface2,
                    text_color=T.texto_muted
                )
        except Exception as e:
            print(f"[ONU] Error al actualizar estado perdida: {e}")

    # ──────────────────────────────────────────────────────────
    #  EJECUCIÓN
    # ──────────────────────────────────────────────────────────
    def run(self):
        self.root.mainloop()