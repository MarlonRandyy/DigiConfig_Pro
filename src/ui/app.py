# ============================================================
# app.py — DigiConfig Pro v2.1
# Mejoras: sidebar animado suave, UX/UI mejorado, sin bugs de hover
# ============================================================
import customtkinter as ctk
import tkinter as tk
import os
import sys
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

import src.ui.tema as tema_mod
from src.core import modelos_manager

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Constantes de navegación ──────────────────────────────────
NAV_ITEMS = [
    ("dashboard",     "Dashboard",       "⊡",  "PRINCIPAL"),
    ("configuracion", "Configurar ONU",  "⚙",  "PRINCIPAL"),
    ("modelos",       "Modelos XML",     "◫",  "GESTIÓN"),
    ("historial",     "Historial",       "≡",  "GESTIÓN"),
    ("escaneo",       "Escanear ONU",    "📷", "GESTIÓN"),
    ("guia",          "Guía de Usuario", "📘", "GESTIÓN"),
]

# ── Constantes de animación ───────────────────────────────────
ANCHO_COLAPSADO  = 64
ANCHO_EXPANDIDO  = 232
PASO_ANIMACION   = 18   # px por frame
DELAY_MS         = 12   # ms entre frames (~80 fps)
DELAY_COLAPSO_MS = 120  # retardo antes de colapsar (evita parpadeo)


def _separador(parent, T):
    ctk.CTkFrame(
        parent, height=1, fg_color=T.borde, corner_radius=0
    ).pack(fill="x", padx=14, pady=5)


# ═══════════════════════════════════════════════════════════════
class App:
# ═══════════════════════════════════════════════════════════════

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("DigiConfig Pro — Digicable")
        self.root.geometry("1200x730")
        self.root.minsize(980, 640)

        # ── Estado ───────────────────────────────────────────
        self.onu_info        = {}
        self.modelos         = modelos_manager.cargar()
        self._modo_oscuro    = True
        self._nav_btns       = {}
        self._pantalla       = None
        self._destino_act    = "dashboard"

        # ── Animación del sidebar ────────────────────────────
        self._sidebar_ancho  = ANCHO_COLAPSADO   # ancho actual (int)
        self._anim_job       = None              # after() en curso
        self._colapso_job    = None              # retardo de colapso
        self._expandido      = False             # estado lógico

        self._prep_assets()
        self._build_ui()

    # ── Preparar assets ──────────────────────────────────────
    def _prep_assets(self):
        assets = os.path.join(ROOT, "assets")
        os.makedirs(assets, exist_ok=True)
        for nombre in ("digicable_azul.png", "digicable_naranja.png"):
            src = os.path.join(ROOT, nombre)
            dst = os.path.join(assets, nombre)
            if os.path.exists(src) and not os.path.exists(dst):
                import shutil
                shutil.copy2(src, dst)

    # ── Construcción del UI ───────────────────────────────────
    def _build_ui(self):
        T = tema_mod.Tema
        self.root.configure(fg_color=T.bg)

        # Sidebar fijo colapsado al inicio
        self.sidebar = ctk.CTkFrame(
            self.root, width=ANCHO_COLAPSADO,
            corner_radius=0, fg_color=T.sidebar
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Hover: bind en el frame raíz para capturar enter/leave global
        self.sidebar.bind("<Enter>", self._on_sidebar_enter)
        self.sidebar.bind("<Leave>", self._on_sidebar_leave)

        self._build_sidebar_widgets()

        # Área de contenido (derecha)
        self.area = ctk.CTkFrame(self.root, corner_radius=0, fg_color=T.bg)
        self.area.pack(side="left", fill="both", expand=True)

        # Topbar
        self.topbar = ctk.CTkFrame(
            self.area, height=58, corner_radius=0,
            fg_color=T.topbar, border_width=1, border_color=T.borde
        )
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)
        self._build_topbar()

        # Contenedor de pantallas
        self.contenido = ctk.CTkFrame(
            self.area, corner_radius=0, fg_color=T.bg
        )
        self.contenido.pack(fill="both", expand=True)

        self.navegar(self._destino_act)

    # ══════════════════════════════════════════════════════════
    #  SIDEBAR — WIDGETS
    # ══════════════════════════════════════════════════════════
    def _build_sidebar_widgets(self):
        T = tema_mod.Tema

        # Limpiar widgets anteriores
        for w in self.sidebar.winfo_children():
            w.destroy()
        self._nav_btns.clear()

        # ─── Logo ─────────────────────────────────────────────
        logo_frame = ctk.CTkFrame(
            self.sidebar, fg_color="transparent", height=68
        )
        logo_frame.pack(fill="x", pady=(8, 0))
        logo_frame.pack_propagate(False)

        logo_path = os.path.join(
            ROOT, "assets",
            "digicable_naranja.png" if self._modo_oscuro else "digicable_azul.png"
        )
        if os.path.exists(logo_path):
            img = ctk.CTkImage(Image.open(logo_path), size=(30, 30))
            ctk.CTkLabel(logo_frame, image=img, text="").pack(
                side="left", padx=(17, 8), pady=8
            )
            # Guardar referencia para que GC no la elimine
            logo_frame._img_ref = img

        # Textos (se muestran/ocultan con la animación)
        self._logo_text_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        # No se empaqueta aquí; se controla en _apply_sidebar_state()

        ctk.CTkLabel(
            self._logo_text_frame,
            text="DigiConfig Pro",
            font=("Segoe UI", 13, "bold"),
            text_color="#ffffff"
        ).pack(anchor="w", pady=(14, 0))

        ctk.CTkLabel(
            self._logo_text_frame,
            text="Digicable · v2.0",
            font=("Segoe UI", 9),
            text_color="gray"
        ).pack(anchor="w")

        _separador(self.sidebar, T)

        # ─── Botones de navegación ────────────────────────────
        seccion_actual = None
        for key, texto, icono, seccion in NAV_ITEMS:
            # Encabezado de sección
            if seccion != seccion_actual:
                seccion_actual = seccion
                if seccion != "PRINCIPAL":
                    _separador(self.sidebar, T)
                lbl = ctk.CTkLabel(
                    self.sidebar, text=seccion,
                    font=("Segoe UI", 9, "bold"),
                    text_color=T.texto_dim
                )
                lbl.pack(anchor="w", padx=18, pady=(6, 2))
                # Guardamos para poder ocultar/mostrar
                lbl._nav_key = f"_sec_{seccion}"

            activo = (key == self._destino_act)
            btn = ctk.CTkButton(
                self.sidebar,
                text=icono,           # Siempre empieza como icono
                anchor="center",
                fg_color=T.nav_active_bg if activo else "transparent",
                hover_color=T.nav_active_bg if activo else T.nav_hover_bg,
                text_color="#ffffff" if activo else T.texto_muted,
                font=("Segoe UI", 13, "bold") if activo else ("Segoe UI", 13),
                height=44,
                corner_radius=T.r_btn,
                command=lambda k=key: self.navegar(k)
            )
            btn.pack(fill="x", padx=8, pady=2)
            # Guardamos metadatos del botón
            btn._nav_texto = texto
            btn._nav_icono = icono
            btn._nav_key   = key
            self._nav_btns[key] = btn

        # ─── Spacer + footer ONU ─────────────────────────────
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(
            fill="both", expand=True
        )
        _separador(self.sidebar, T)

        self._onu_footer = ctk.CTkFrame(
            self.sidebar, fg_color=T.surface2, corner_radius=T.r_chip
        )
        self._onu_footer.pack(fill="x", padx=8, pady=(4, 12))

        self.lbl_led = ctk.CTkLabel(
            self._onu_footer, text="⬤",
            font=("Segoe UI", 10), text_color=T.led_off
        )
        self.lbl_led.pack(side="left", padx=(10, 4), pady=10)

        self._onu_texto = ctk.CTkLabel(
            self._onu_footer,
            text="Sin ONU",
            font=("Segoe UI", 10),
            text_color=T.texto_muted
        )
        # Se muestra/oculta con la animación

        # Vincular hover a TODOS los hijos del sidebar
        self._bind_hover_recursivo(self.sidebar)

    def _bind_hover_recursivo(self, widget):
        """Propaga los eventos Enter/Leave a todos los hijos del sidebar."""
        widget.bind("<Enter>", self._on_sidebar_enter, add="+")
        widget.bind("<Leave>", self._on_sidebar_leave, add="+")
        for child in widget.winfo_children():
            self._bind_hover_recursivo(child)

    # ══════════════════════════════════════════════════════════
    #  ANIMACIÓN SIDEBAR
    # ══════════════════════════════════════════════════════════

    def _on_sidebar_enter(self, event=None):
        """Cancela colapso pendiente y lanza expansión."""
        if self._colapso_job:
            self.root.after_cancel(self._colapso_job)
            self._colapso_job = None
        if not self._expandido:
            self._animar_sidebar(expandir=True)

    def _on_sidebar_leave(self, event=None):
        """
        Solo colapsa si el cursor sale REALMENTE del sidebar.
        Evita el bug de colapso al pasar sobre botones hijos.
        """
        # Coordenadas del cursor y del sidebar
        try:
            cx = self.root.winfo_pointerx()
            cy = self.root.winfo_pointery()
            sx = self.sidebar.winfo_rootx()
            sy = self.sidebar.winfo_rooty()
            sw = self.sidebar.winfo_width()
            sh = self.sidebar.winfo_height()
        except Exception:
            return

        dentro = (sx <= cx < sx + sw) and (sy <= cy < sy + sh)
        if dentro:
            return  # El cursor sigue dentro — ignorar

        if self._expandido:
            # Retardo para evitar parpadeo al cruzar bordes de widgets hijos
            if self._colapso_job:
                self.root.after_cancel(self._colapso_job)
            self._colapso_job = self.root.after(
                DELAY_COLAPSO_MS, self._iniciar_colapso
            )

    def _iniciar_colapso(self):
        self._colapso_job = None
        # Verificación final antes de colapsar
        try:
            cx = self.root.winfo_pointerx()
            cy = self.root.winfo_pointery()
            sx = self.sidebar.winfo_rootx()
            sy = self.sidebar.winfo_rooty()
            sw = self.sidebar.winfo_width()
            sh = self.sidebar.winfo_height()
            if (sx <= cx < sx + sw) and (sy <= cy < sy + sh):
                return  # Cursor volvió — cancelar
        except Exception:
            return
        self._animar_sidebar(expandir=False)

    def _animar_sidebar(self, expandir: bool):
        """Mueve el sidebar suavemente hacia el ancho destino."""
        if self._anim_job:
            self.root.after_cancel(self._anim_job)
            self._anim_job = None

        destino = ANCHO_EXPANDIDO if expandir else ANCHO_COLAPSADO

        # Mostrar/ocultar textos ANTES de expandir (o DESPUÉS de colapsar)
        if expandir:
            self._apply_sidebar_state(expandido=True)

        def _step():
            if not self.sidebar.winfo_exists():
                return
            actual = self._sidebar_ancho
            if expandir:
                nuevo = min(actual + PASO_ANIMACION, destino)
            else:
                nuevo = max(actual - PASO_ANIMACION, destino)

            self._sidebar_ancho = nuevo
            self.sidebar.configure(width=nuevo)

            if nuevo != destino:
                self._anim_job = self.root.after(DELAY_MS, _step)
            else:
                self._anim_job = None
                self._expandido = expandir
                if not expandir:
                    self._apply_sidebar_state(expandido=False)

        _step()

    def _apply_sidebar_state(self, expandido: bool):
        """
        Muestra u oculta los textos del sidebar y adapta los botones.
        Se llama al inicio de la expansión y al final del colapso.
        """
        T = tema_mod.Tema

        # Textos del logo
        if hasattr(self, "_logo_text_frame"):
            try:
                if expandido:
                    self._logo_text_frame.pack(side="left", fill="both", expand=True)
                else:
                    self._logo_text_frame.pack_forget()
            except Exception:
                pass

        # Texto del footer ONU
        if hasattr(self, "_onu_texto"):
            try:
                if expandido:
                    self._onu_texto.pack(side="left", pady=10, padx=(0, 8))
                else:
                    self._onu_texto.pack_forget()
            except Exception:
                pass

        # Etiquetas de sección y textos de botones
        for widget in self.sidebar.winfo_children():
            self._toggle_seccion_labels(widget, expandido)

        # Botones: icono solo ↔ icono + texto
        for key, btn in self._nav_btns.items():
            try:
                if not btn.winfo_exists():
                    continue
                activo = (key == self._destino_act)
                if expandido:
                    btn.configure(
                        text=f"  {btn._nav_icono}  {btn._nav_texto}",
                        anchor="w",
                        font=("Segoe UI", 12, "bold") if activo else ("Segoe UI", 12),
                    )
                else:
                    btn.configure(
                        text=btn._nav_icono,
                        anchor="center",
                        font=("Segoe UI", 14, "bold") if activo else ("Segoe UI", 14),
                    )
            except Exception:
                pass

    def _toggle_seccion_labels(self, widget, mostrar: bool):
        """Muestra/oculta etiquetas de sección en el sidebar."""
        try:
            if isinstance(widget, ctk.CTkLabel) and hasattr(widget, "_nav_key"):
                if widget._nav_key.startswith("_sec_"):
                    if mostrar:
                        widget.pack(anchor="w", padx=18, pady=(6, 2))
                    else:
                        widget.pack_forget()
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════
    #  TOPBAR
    # ══════════════════════════════════════════════════════════
    def _build_topbar(self):
        T = tema_mod.Tema
        for w in self.topbar.winfo_children():
            w.destroy()

        # Título a la izquierda
        self.lbl_titulo = ctk.CTkLabel(
            self.topbar,
            text="Dashboard de Conexión",
            font=("Segoe UI", 15, "bold"),
            text_color=T.texto
        )
        self.lbl_titulo.place(x=24, rely=0.5, anchor="w")

        # Controles a la derecha
        right = ctk.CTkFrame(self.topbar, fg_color="transparent")
        right.place(relx=0.99, rely=0.5, anchor="e")

        # Badge ONU
        self.badge_onu = ctk.CTkLabel(
            right,
            text="● Sin ONU",
            font=("Segoe UI", 10, "bold"),
            fg_color=T.surface2,
            text_color=T.texto_muted,
            corner_radius=T.r_pill,
            padx=14, pady=5
        )
        self.badge_onu.pack(side="left", padx=(0, 10))

        # Botón modo claro/oscuro
        icono_modo = "☾  Oscuro" if self._modo_oscuro else "☀  Claro"
        self.btn_modo = ctk.CTkButton(
            right,
            text=icono_modo,
            fg_color=T.surface2,
            hover_color=T.borde2,
            text_color=T.texto_muted,
            border_width=1,
            border_color=T.borde,
            height=34,
            corner_radius=T.r_pill,
            font=("Segoe UI", 11, "bold"),
            command=self._toggle_modo
        )
        self.btn_modo.pack(side="left", padx=(0, 8))

    # ══════════════════════════════════════════════════════════
    #  TOGGLE MODO CLARO / OSCURO
    # ══════════════════════════════════════════════════════════
    def _toggle_modo(self):
        self._modo_oscuro = not self._modo_oscuro
        if self._modo_oscuro:
            tema_mod.Tema = tema_mod.TemaOscuro
            ctk.set_appearance_mode("dark")
        else:
            tema_mod.Tema = tema_mod.TemaClaro
            ctk.set_appearance_mode("light")

        T = tema_mod.Tema
        self.root.configure(fg_color=T.bg)
        self.sidebar.configure(fg_color=T.sidebar)
        self.area.configure(fg_color=T.bg)
        self.topbar.configure(fg_color=T.topbar, border_color=T.borde)
        self.contenido.configure(fg_color=T.bg)

        # Reconstruir sidebar (re-bindea el hover también)
        self._build_sidebar_widgets()
        # Restaurar estado expandido si corresponde
        if self._expandido:
            self._apply_sidebar_state(expandido=True)

        self._build_topbar()
        self.navegar(self._destino_act, rebuild=True)

    # ══════════════════════════════════════════════════════════
    #  NAVEGACIÓN
    # ══════════════════════════════════════════════════════════
    def navegar(self, destino: str, rebuild: bool = False):
        from src.ui.pantalla_dashboard      import PantallaDashboard
        from src.ui.pantalla_configuracion  import PantallaConfiguracion
        from src.ui.pantalla_modelos        import PantallaModelos
        from src.ui.pantalla_historial      import PantallaHistorial
        from src.ui.pantalla_guia           import PantallaGuia

        try:
            from src.ui.pantalla_escaneo import PantallaEscaneo
        except ImportError as e:
            print(f"[Escaneo] Librerías no disponibles: {e}")
            PantallaEscaneo = None

        TITULOS = {
            "dashboard":     "Dashboard de Conexión",
            "configuracion": "Configurar ONU",
            "modelos":       "Librería de Modelos XML",
            "historial":     "Historial de Instalaciones",
            "escaneo":       "Escanear ONU (QR / Código de barras)",
            "guia":          "Manual y Procedimientos",
        }
        PANTALLAS = {
            "dashboard":     PantallaDashboard,
            "configuracion": PantallaConfiguracion,
            "modelos":       PantallaModelos,
            "historial":     PantallaHistorial,
            "escaneo":       PantallaEscaneo,
            "guia":          PantallaGuia,
        }

        self._destino_act = destino
        T = tema_mod.Tema

        # ── Actualizar botones ────────────────────────────────
        for k, btn in self._nav_btns.items():
            try:
                if not btn.winfo_exists():
                    continue
                activo = (k == destino)
                btn.configure(
                    fg_color=T.nav_active_bg if activo else "transparent",
                    hover_color=T.nav_active_bg if activo else T.nav_hover_bg,
                    text_color="#ffffff" if activo else T.texto_muted,
                    font=("Segoe UI", 12, "bold") if activo else ("Segoe UI", 12),
                )
                # Actualizar texto según estado expandido/colapsado
                if self._expandido:
                    btn.configure(
                        text=f"  {btn._nav_icono}  {btn._nav_texto}",
                        anchor="w"
                    )
                else:
                    btn.configure(
                        text=btn._nav_icono,
                        anchor="center"
                    )
            except Exception:
                pass

        # ── Actualizar título ─────────────────────────────────
        if hasattr(self, "lbl_titulo"):
            try:
                self.lbl_titulo.configure(
                    text=TITULOS.get(destino, "DigiConfig Pro")
                )
            except Exception:
                pass

        # ── Limpiar pantalla anterior ─────────────────────────
        for w in list(self.contenido.winfo_children()):
            try:
                if hasattr(w, "cerrar"):
                    w.cerrar()
                if hasattr(w, "detener_camara"):
                    w.detener_camara()
                w.pack_forget()
                w.after(0, w.destroy)  # destruir en el siguiente ciclo
            except Exception as e:
                print(f"[Nav] Error al limpiar widget: {e}")

        # ── Instanciar nueva pantalla ─────────────────────────
        cls = PANTALLAS.get(destino)
        if cls is None:
            if destino == "escaneo":
                from src.utils.notificaciones import mostrar_mensaje
                mostrar_mensaje(
                    "Instala opencv-python y pyzbar para usar el escáner.",
                    "error"
                )
            return

        try:
            p = cls(self.contenido, app=self)
            p.pack(fill="both", expand=True)
            self._pantalla = p
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                from src.utils.notificaciones import mostrar_mensaje
                mostrar_mensaje(f"Error al abrir '{destino}': {e}", "error")
            except Exception:
                pass

    # ══════════════════════════════════════════════════════════
    #  CALLBACKS ONU
    # ══════════════════════════════════════════════════════════
    def set_onu_detectada(self, info: dict):
        self.onu_info = info
        nombre = info.get("nombre_display", "ONU Detectada")[:26]
        T = tema_mod.Tema
        try:
            self.lbl_led.configure(text_color=T.led_on)
            if hasattr(self, "_onu_texto"):
                self._onu_texto.configure(text=nombre, text_color=T.verde)
            self.badge_onu.configure(
                text="● ONU Conectada",
                fg_color=T.verde_soft,
                text_color=T.verde
            )
        except Exception:
            pass

    def set_onu_perdida(self):
        self.onu_info = {}
        T = tema_mod.Tema
        try:
            self.lbl_led.configure(text_color=T.led_off)
            if hasattr(self, "_onu_texto"):
                self._onu_texto.configure(
                    text="Sin ONU", text_color=T.texto_muted
                )
            self.badge_onu.configure(
                text="● Sin ONU",
                fg_color=T.surface2,
                text_color=T.texto_muted
            )
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════
    def run(self):
        self.root.mainloop()