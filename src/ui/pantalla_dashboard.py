# ============================================================
# pantalla_dashboard.py — Dashboard de conexión (optimizado y mejorado)
# ============================================================
import customtkinter as ctk
import os
import threading
from tkinter import messagebox
from PIL import Image

import src.ui.tema as tema_mod
from src.core.detector import DetectorONU
from src.core import historial as hist
from src.utils import notificaciones


def T():
    return tema_mod.Tema


def _chip(parent, label, value, color=None):
    """Chip de información con color opcional."""
    f = ctk.CTkFrame(parent, fg_color=T().surface2,
                     corner_radius=T().r_chip,
                     border_width=1, border_color=T().borde)
    f.pack(side="left", padx=(0, 8), pady=4)
    ctk.CTkLabel(f, text=label,
                 font=("Segoe UI", 9, "bold"),
                 text_color=T().texto_dim).pack(anchor="w", padx=10, pady=(6, 0))
    ctk.CTkLabel(f, text=value,
                 font=("Consolas", 11, "bold"),
                 text_color=color or T().texto).pack(anchor="w", padx=10, pady=(0, 6))
    return f


def _kpi(parent, label, value, color):
    """Crea un KPI y retorna el label del valor para actualizarlo después."""
    f = ctk.CTkFrame(parent, fg_color=T().surface,
                     corner_radius=T().r_chip,
                     border_width=1, border_color=T().borde)
    f.pack(side="left", expand=True, fill="x", padx=(0, 8))
    
    val_lbl = ctk.CTkLabel(f, text=value,
                           font=("Segoe UI", 22, "bold"),
                           text_color=color)
    val_lbl.pack(pady=(10, 0))
    
    ctk.CTkLabel(f, text=label,
                 font=("Segoe UI", 9, "bold"),
                 text_color=T().texto_dim).pack(pady=(0, 10))
    
    return val_lbl


class PantallaDashboard(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T().bg, corner_radius=0)
        self.app = app
        self.detector = DetectorONU(
            modelos_db=app.modelos,
            callback_detectada=self._onu_detectada,
            callback_perdida=self._onu_perdida,
        )
        self._modelo_detectado = None  # Guardar modelo para mostrar información
        self._build_ui()
        self._actualizar_kpis()
        self.detector.iniciar()

    # ── Construcción de la interfaz ──────────────────────────
    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=T().bg, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=0, pady=0)
        self._scroll = scroll

        pad = {"padx": 22, "pady": (0, 14)}

        # ── Card de estado de la ONU ─────────────────────────
        self.card_onu = ctk.CTkFrame(
            scroll, fg_color=T().surface,
            corner_radius=T().r_card,
            border_width=1, border_color=T().borde)
        self.card_onu.pack(fill="x", padx=22, pady=(18, 14))

        # Barra superior de estado (color dinámico)
        self.franja = ctk.CTkFrame(
            self.card_onu, height=4,
            fg_color=T().borde, corner_radius=0)
        self.franja.pack(fill="x")

        top = ctk.CTkFrame(self.card_onu, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(16, 8))

        # ── Columna izquierda: información principal ─────────
        left_col = ctk.CTkFrame(top, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True)

        # Badge de estado (LED virtual)
        self.lbl_badge = ctk.CTkLabel(
            left_col, text="⬤ SIN CONEXIÓN",
            font=("Segoe UI", 10, "bold"),
            fg_color=T().surface2,
            text_color=T().texto_muted,
            corner_radius=T().r_pill, padx=12, pady=4)
        self.lbl_badge.pack(anchor="w")

        # Nombre del modelo o estado
        self.lbl_nombre = ctk.CTkLabel(
            left_col, text="Esperando ONU...",
            font=("Segoe UI", 20, "bold"),
            text_color=T().texto)
        self.lbl_nombre.pack(anchor="w", pady=(8, 2))

        # Subtítulo (información adicional)
        self.lbl_sub = ctk.CTkLabel(
            left_col,
            text="Conecta la ONU por cable de red para comenzar.",
            font=("Segoe UI", 11),
            text_color=T().texto_muted)
        self.lbl_sub.pack(anchor="w")

        # ── Imagen del modelo (placeholder) ──────────────────
        self.lbl_img_modelo = ctk.CTkLabel(
            top, text="📷", font=("Segoe UI", 28),
            width=100, height=70)
        self.lbl_img_modelo.pack(side="right", padx=(16, 0))

        # ── Chips de información (se muestran al detectar) ──
        self.chips_frame = ctk.CTkFrame(
            self.card_onu, fg_color="transparent")
        self.chips_frame.pack_forget()  # Oculto inicialmente

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

        # Botón de escaneo manual (fuera de la card)
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
        self.kpi_total = _kpi(kpi_row, "Total instaladas", "0", T().accent2)
        self.kpi_hoy = _kpi(kpi_row, "Configuradas hoy", "0", T().verde)
        self.kpi_errores = _kpi(kpi_row, "Errores", "0", T().rojo)
        self.kpi_tasa = _kpi(kpi_row, "Tasa de éxito", "0%", T().accent)

        # ── Pie de página (información adicional) ────────────
        footer = ctk.CTkLabel(
            scroll,
            text="💡 Para configurar una ONU, primero debe ser detectada en esta pantalla.",
            font=("Segoe UI", 9),
            text_color=T().texto_dim)
        footer.pack(pady=(10, 5))

    # ── Actualización de KPIs ─────────────────────────────────
    def _actualizar_kpis(self):
        stats = hist.estadisticas()
        try:
            self.kpi_total.configure(text=str(stats.get("total", 0)))
            self.kpi_hoy.configure(text=str(stats.get("hoy", 0)))
            self.kpi_errores.configure(text=str(stats.get("errores", 0)))
            self.kpi_tasa.configure(text=f"{stats.get('tasa_exito', 0)}%")
        except Exception as e:
            print(f"[Dashboard] Error actualizando KPIs: {e}")

    # ── Callbacks del detector ────────────────────────────────
    def _onu_detectada(self, info: dict):
        print(f"[Dashboard] ONU detectada: {info}")
        self.app.onu_info = info
        self._modelo_detectado = info.get("modelo_id", "DESCONOCIDO")
        self.after(0, lambda: self._ui_detectada(info))
        self.after(0, self._actualizar_kpis)
        notificaciones.onu_detectada(
            info.get("nombre_display", "ONU"),
            info.get("mac", "?"))

    def _onu_perdida(self):
        self.app.set_onu_perdida()
        self._modelo_detectado = None
        self.after(0, self._ui_perdida)
        self.after(0, self._actualizar_kpis)
        notificaciones.onu_desconectada()

    # ── Actualización de la UI en detección ──────────────────
    def _ui_detectada(self, info: dict):
        if not self.winfo_exists():
            return

        try:
            nombre = info.get("nombre_display", "ONU Detectada")
            fab = info.get("fabricante", "?")
            ip = info.get("ip", "?")
            mac = info.get("mac", "?")
            sn = info.get("gpon_sn", "?")
            modelo_id = info.get("modelo_id", "DESCONOCIDO")

            # Actualizar badge y colores
            self.lbl_badge.configure(
                text="⬤ ONU DETECTADA",
                fg_color=T().verde_soft,
                text_color=T().verde)
            self.lbl_nombre.configure(text=nombre, text_color=T().texto)
            self.lbl_sub.configure(
                text=f"Fabricante: {fab}  ·  IP: {ip}  ·  Modelo: {modelo_id}",
                text_color=T().verde)
            self.franja.configure(fg_color=T().verde)
            self.card_onu.configure(border_color=T().verde)

            # Mostrar chips de información
            if self.chips_frame.winfo_exists():
                for w in self.chips_frame.winfo_children():
                    w.destroy()
                _chip(self.chips_frame, "MAC", mac, T().texto)
                _chip(self.chips_frame, "GPON SN", sn, T().texto)
                _chip(self.chips_frame, "IP", ip, T().texto)
                self.chips_frame.pack(fill="x", padx=20, pady=(0, 4))

            # Mostrar imagen del modelo (si existe)
            ruta = info.get("imagen", "")
            if ruta and os.path.exists(ruta) and self.lbl_img_modelo.winfo_exists():
                try:
                    raw_img = Image.open(ruta)
                    img = ctk.CTkImage(raw_img, size=(90, 66))
                    self.lbl_img_modelo.configure(image=img, text="")
                    self.lbl_img_modelo.img_ref = img
                except Exception:
                    self.lbl_img_modelo.configure(image=None, text="📷")
            else:
                self.lbl_img_modelo.configure(image=None, text="📷")

            # Activar botón de configuración
            if self.btn_configurar.winfo_exists():
                self.btn_configurar.configure(state="normal", fg_color=T().accent)

            # Actualizar estado en la app principal
            self.app.set_onu_detectada(info)

        except Exception as e:
            print(f"[Dashboard] Error en UI detectada: {e}")

    # ── Actualización de UI en pérdida de ONU ────────────────
    def _ui_perdida(self):
        if not self.winfo_exists():
            return
        try:
            self.lbl_badge.configure(
                text="⬤ SIN CONEXIÓN",
                fg_color=T().surface2,
                text_color=T().texto_muted)
            self.lbl_nombre.configure(
                text="Esperando ONU...",
                text_color=T().texto)
            self.lbl_sub.configure(
                text="Conecta la ONU por cable de red para comenzar.",
                text_color=T().texto_muted)
            self.franja.configure(fg_color=T().borde)
            self.card_onu.configure(border_color=T().borde)
            self.chips_frame.pack_forget()
            self.lbl_img_modelo.configure(image=None, text="📷")
            self.btn_configurar.configure(state="disabled")
        except Exception:
            pass

    # ── Escaneo manual ────────────────────────────────────────
    def _escaneo_manual(self):
        self.btn_escanear.configure(text="◎  Escaneando...", state="disabled")

        def _buscar():
            info = self.detector.escaneo_manual()
            if not self.winfo_exists():
                return
            if info:
                self._onu_detectada(info)
            else:
                self.after(0, lambda: self.lbl_sub.configure(
                    text="No se encontró ONU en la red. Verifica el cable y la IP.",
                    text_color=T().rojo))
            self.after(0, lambda: self.btn_escanear.configure(
                text="◎  Buscar ONU manualmente", state="normal"))

        threading.Thread(target=_buscar, daemon=True).start()

    def destroy(self):
        try:
            self.detector.detener()
        except Exception:
            pass
        super().destroy()