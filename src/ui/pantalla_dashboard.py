# ============================================================
# pantalla_dashboard.py — Dashboard de conexión (nuevo estilo)
# ============================================================
import customtkinter as ctk
import tkinter as tk
import threading, os
from PIL import Image

import src.ui.tema as tema_mod
from src.core.detector import DetectorONU
from src.utils import notificaciones


def T():
    return tema_mod.Tema


def _chip(parent, label, value):
    """Mini chip de info (etiqueta + valor monoespacio)."""
    f = ctk.CTkFrame(parent, fg_color=T().surface2,
                     corner_radius=T().r_chip,
                     border_width=1, border_color=T().borde)
    f.pack(side="left", padx=(0, 8), pady=4)
    ctk.CTkLabel(f, text=label,
                 font=("Segoe UI", 9, "bold"),
                 text_color=T().texto_dim).pack(anchor="w", padx=10, pady=(6, 0))
    ctk.CTkLabel(f, text=value,
                 font=("Consolas", 11, "bold"),
                 text_color=T().texto).pack(anchor="w", padx=10, pady=(0, 6))
    return f


def _kpi(parent, label, value, color):
    f = ctk.CTkFrame(parent, fg_color=T().surface,
                     corner_radius=T().r_chip,
                     border_width=1, border_color=T().borde)
    f.pack(side="left", expand=True, fill="x", padx=(0, 8))
    ctk.CTkLabel(f, text=value,
                 font=("Segoe UI", 22, "bold"),
                 text_color=color).pack(pady=(10, 0))
    ctk.CTkLabel(f, text=label,
                 font=("Segoe UI", 9, "bold"),
                 text_color=T().texto_dim).pack(pady=(0, 10))


class PantallaDashboard(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T().bg, corner_radius=0)
        self.app      = app
        self.detector = DetectorONU(
            modelos_db=app.modelos,
            callback_detectada=self._onu_detectada,
            callback_perdida=self._onu_perdida,
        )
        self._build_ui()
        self.detector.iniciar()

    # ── Build ─────────────────────────────────────────────────
    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=T().bg, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=0, pady=0)
        self._scroll = scroll

        pad = {"padx": 22, "pady": (0, 14)}

        # ── Card estado ONU ───────────────────────────────────
        self.card_onu = ctk.CTkFrame(
            scroll, fg_color=T().surface,
            corner_radius=T().r_card,
            border_width=1, border_color=T().borde)
        self.card_onu.pack(fill="x", padx=22, pady=(18, 14))

        # Franja top accent (oculta hasta detectar)
        self.franja = ctk.CTkFrame(
            self.card_onu, height=3,
            fg_color=T().borde, corner_radius=0)
        self.franja.pack(fill="x")

        top = ctk.CTkFrame(self.card_onu, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(16, 8))

        # Izquierda: LED + nombre
        left_col = ctk.CTkFrame(top, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True)

        self.lbl_badge = ctk.CTkLabel(
            left_col, text="SIN CONEXIÓN",
            font=("Segoe UI", 9, "bold"),
            fg_color=T().surface2,
            text_color=T().texto_muted,
            corner_radius=T().r_pill, padx=10, pady=3)
        self.lbl_badge.pack(anchor="w")

        self.lbl_nombre = ctk.CTkLabel(
            left_col, text="Esperando ONU...",
            font=("Segoe UI", 20, "bold"),
            text_color=T().texto)
        self.lbl_nombre.pack(anchor="w", pady=(8, 2))

        self.lbl_sub = ctk.CTkLabel(
            left_col,
            text="Conecta una ONU por cable de red para comenzar.",
            font=("Segoe UI", 11),
            text_color=T().texto_muted)
        self.lbl_sub.pack(anchor="w")

        # Imagen modelo
        self.lbl_img_modelo = ctk.CTkLabel(
            top, text="", width=100, height=70)
        self.lbl_img_modelo.pack(side="right", padx=(16, 0))

        # Chips de info (se muestran al detectar)
        self.chips_frame = ctk.CTkFrame(
            self.card_onu, fg_color="transparent")

        # ── Botones de acción ─────────────────────────────────
        btn_frame = ctk.CTkFrame(
            self.card_onu, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 16))

        self.btn_configurar = ctk.CTkButton(
            btn_frame, text="⚙  Configurar ONU",
            fg_color=T().accent,
            hover_color=T().accent_hover,
            text_color="#ffffff",
            height=44, corner_radius=T().r_btn,
            font=("Segoe UI", 13, "bold"),
            state="disabled",
            command=lambda: self.app.navegar("configuracion"))
        self.btn_configurar.pack(
            side="left", expand=True, fill="x", padx=(0, 8))

        self.btn_reset = ctk.CTkButton(
            btn_frame, text="↺  Restaurar fábrica",
            fg_color=T().rojo_soft,
            hover_color=T().rojo,
            text_color=T().rojo,
            height=44, corner_radius=T().r_btn,
            font=("Segoe UI", 12, "bold"),
            state="disabled",
            border_width=1, border_color=T().rojo,
            command=self._reset_fabrica)
        self.btn_reset.pack(side="left", expand=True, fill="x")

        # ── Botón escanear ────────────────────────────────────
        self.btn_escanear = ctk.CTkButton(
            scroll,
            text="◎  Buscar ONU manualmente",
            fg_color=T().surface,
            hover_color=T().surface2,
            text_color=T().texto_muted,
            border_width=1, border_color=T().borde,
            height=38, corner_radius=T().r_btn,
            font=("Segoe UI", 11),
            command=self._escaneo_manual)
        self.btn_escanear.pack(fill="x", **pad)

        # ── KPIs ──────────────────────────────────────────────
        kpi_row = ctk.CTkFrame(scroll, fg_color="transparent")
        kpi_row.pack(fill="x", **pad)
        _kpi(kpi_row, "Total instaladas", "0", T().accent2)
        _kpi(kpi_row, "Configuradas hoy",  "0", T().verde)
        _kpi(kpi_row, "Errores",            "0",  T().rojo)
        _kpi(kpi_row, "Tasa de éxito",     "0%", T().accent)

    # ── Callbacks detector ────────────────────────────────────
    def _onu_detectada(self, info: dict):
        self.app.onu_info = info
        self.after(0, lambda: self._ui_detectada(info))
        notificaciones.onu_detectada(
            info.get("nombre_display", "ONU"),
            info.get("mac", "?"))

    def _onu_perdida(self):
        self.app.set_onu_perdida()
        self.after(0, self._ui_perdida)
        notificaciones.onu_desconectada()

    def _ui_detectada(self, info: dict):
    # --- PROTECCIÓN ANTI-CRASH ---
    # Si el widget ya no existe (cambio de pestaña), salimos silenciosamente
        if not self.winfo_exists():
            return

        try:
            nombre = info.get("nombre_display", "ONU Detectada")
            fab    = info.get("fabricante", "?")
            ip     = info.get("ip", "?")
            mac    = info.get("mac", "?")
            sn     = info.get("gpon_sn", "?")

            # Badge verde
            # Verificamos lbl_badge específicamente por ser el primero en jerarquía
            if self.lbl_badge.winfo_exists():
                self.lbl_badge.configure(
                    text="ONU DETECTADA",
                    fg_color=T().verde_soft,
                    text_color=T().verde)
                
                self.lbl_nombre.configure(text=nombre, text_color=T().texto)
                self.lbl_sub.configure(
                    text=f"Fabricante: {fab}  ·  IP: {ip}",
                    text_color=T().verde)
                self.franja.configure(fg_color=T().verde)
                self.card_onu.configure(border_color=T().verde)

            # Chips - Manejo seguro de borrado
            if self.chips_frame.winfo_exists():
                for w in self.chips_frame.winfo_children():
                    w.destroy()
                
                _chip(self.chips_frame, "MAC Address",  mac)
                _chip(self.chips_frame, "GPON Serial",  sn)
                _chip(self.chips_frame, "IP de fábrica", ip)
                self.chips_frame.pack(fill="x", padx=20, pady=(0, 4))

            # Imagen modelo - Renderizado seguro
            ruta = info.get("imagen", "")
            if ruta and os.path.exists(ruta) and self.lbl_img_modelo.winfo_exists():
                try:
                    # Usar Image.LANCZOS para mayor calidad en el reescalado
                    raw_img = Image.open(ruta)
                    img = ctk.CTkImage(raw_img, size=(90, 66))
                    self.lbl_img_modelo.configure(image=img)
                    self.lbl_img_modelo.img_ref = img # Evita que el recolector de basura la borre
                except Exception:
                    pass

            # Botones
            if self.btn_configurar.winfo_exists():
                self.btn_configurar.configure(
                    state="normal",
                    fg_color=T().accent)
                self.btn_reset.configure(state="normal")
            
            # Notificar a la app principal
            self.app.set_onu_detectada(info)

        except Exception as e:
            # Si algo falla en la actualización de UI, lo ignoramos para no tumbar la app
            print(f"Error de actualización de UI (Dashboard): {e}")
            
    def _ui_perdida(self):
        self.lbl_badge.configure(
            text="SIN CONEXIÓN",
            fg_color=T().surface2,
            text_color=T().texto_muted)
        self.lbl_nombre.configure(
            text="Esperando ONU...",
            text_color=T().texto)
        self.lbl_sub.configure(
            text="Conecta una ONU por cable de red para comenzar.",
            text_color=T().texto_muted)
        self.franja.configure(fg_color=T().borde)
        self.card_onu.configure(border_color=T().borde)
        self.chips_frame.pack_forget()
        self.lbl_img_modelo.configure(image=None)
        self.btn_configurar.configure(state="disabled")
        self.btn_reset.configure(state="disabled")

    def _escaneo_manual(self):
        self.btn_escanear.configure(
            text="◎  Escaneando...", state="disabled")
        def _buscar():
            info = self.detector.escaneo_manual()
            if info:
                self._onu_detectada(info)
            else:
                self.after(0, lambda: self.lbl_sub.configure(
                    text="No se encontró ONU en la red.",
                    text_color=T().rojo))
            self.after(0, lambda: self.btn_escanear.configure(
                text="◎  Buscar ONU manualmente", state="normal"))
        threading.Thread(target=_buscar, daemon=True).start()

    def _reset_fabrica(self):
        if not self.app.onu_info:
            return
        from tkinter import messagebox
        if not messagebox.askyesno(
            "Restaurar fábrica",
            "¿Restaurar la ONU a valores de fábrica?\n"
            "Esta acción borrará la configuración actual."
        ):
            return
        from src.core.instalador import InstaladorONU
        datos = self.app.modelos.get(
            self.app.onu_info.get("modelo_id", ""), {})
        if not datos:
            return
        res = InstaladorONU(datos, "").reset_fabrica()
        from tkinter import messagebox as mb
        (mb.showinfo if res.exito else mb.showerror)(
            "Reset", res.mensaje)

    def destroy(self):
        try: self.detector.detener()
        except Exception: pass
        super().destroy()
