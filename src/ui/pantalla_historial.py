# ============================================================
# pantalla_historial.py — Historial + KPIs + filtros + exportar
# ============================================================
import customtkinter as ctk
from tkinter import filedialog, messagebox

import src.ui.tema as tema_mod
from src.core import historial as hist


def T(): return tema_mod.Tema


class PantallaHistorial(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T().bg, corner_radius=0)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=T().bg, corner_radius=0)
        scroll.pack(fill="both", expand=True)
        p = {"padx": 22, "pady": (0, 14)}

        stats = hist.estadisticas()

        # ── KPIs ──────────────────────────────────────────────
        kpi_row = ctk.CTkFrame(scroll, fg_color="transparent")
        kpi_row.pack(fill="x", padx=22, pady=(18, 14))
        for lbl, val, color in [
            ("Total instaladas",  str(stats["total"]),      T().accent2),
            ("Configuradas hoy",  str(stats["hoy"]),        T().verde),
            ("Errores",           str(stats["errores"]),    T().rojo),
            ("Tasa de éxito",     f"{stats['tasa_exito']}%",T().accent),
        ]:
            f = ctk.CTkFrame(kpi_row, fg_color=T().surface,
                              corner_radius=T().r_chip,
                              border_width=1, border_color=T().borde)
            f.pack(side="left", expand=True, fill="x", padx=(0, 10))
            ctk.CTkLabel(f, text=val,
                         font=("Segoe UI", 22, "bold"),
                         text_color=color).pack(pady=(10, 0))
            ctk.CTkLabel(f, text=lbl,
                         font=("Segoe UI", 9, "bold"),
                         text_color=T().texto_dim).pack(pady=(0, 10))

        # ── Toolbar ───────────────────────────────────────────
        toolbar = ctk.CTkFrame(scroll, fg_color=T().surface,
                                corner_radius=T().r_card,
                                border_width=1, border_color=T().borde)
        toolbar.pack(fill="x", **p)
        tb = ctk.CTkFrame(toolbar, fg_color="transparent")
        tb.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(tb, text="Modelo:",
                     font=("Segoe UI", 11),
                     text_color=T().texto_muted).pack(side="left")

        todos = hist.cargar_todos()
        nombres = sorted({r.get("nombre_display","?") for r in todos})
        self._filtro_mod = ctk.StringVar(value="Todos")
        ctk.CTkComboBox(
            tb, values=["Todos"] + list(nombres),
            variable=self._filtro_mod,
            width=220, height=32,
            fg_color=T().surface2,
            border_color=T().borde,
            button_color=T().accent,
            dropdown_fg_color=T().surface2,
            text_color=T().texto,
            command=lambda _: self._cargar_tabla(todos)
        ).pack(side="left", padx=(6, 16))

        ctk.CTkLabel(tb, text="Resultado:",
                     font=("Segoe UI", 11),
                     text_color=T().texto_muted).pack(side="left")
        self._filtro_res = ctk.StringVar(value="Todos")
        ctk.CTkComboBox(
            tb, values=["Todos", "✓ Éxito", "✗ Error"],
            variable=self._filtro_res,
            width=140, height=32,
            fg_color=T().surface2,
            border_color=T().borde,
            button_color=T().accent,
            dropdown_fg_color=T().surface2,
            text_color=T().texto,
            command=lambda _: self._cargar_tabla(todos)
        ).pack(side="left", padx=(6, 0))

        # Botones derecha
        ctk.CTkButton(
            tb, text="↓ Exportar CSV",
            fg_color=T().verde,
            text_color="#ffffff",
            height=32, corner_radius=T().r_btn,
            font=("Segoe UI", 11, "bold"),
            command=self._exportar
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            tb, text="Limpiar",
            fg_color=T().rojo_soft,
            text_color=T().rojo,
            border_width=1, border_color=T().rojo,
            height=32, corner_radius=T().r_btn,
            font=("Segoe UI", 11),
            command=self._limpiar
        ).pack(side="right")

        # ── Tabla ─────────────────────────────────────────────
        self.tabla_cont = ctk.CTkFrame(
            scroll, fg_color=T().surface,
            corner_radius=T().r_card,
            border_width=1, border_color=T().borde)
        self.tabla_cont.pack(fill="x", **p)

        # Encabezado fijo
        enc = ctk.CTkFrame(self.tabla_cont, fg_color=T().surface2,
                            corner_radius=0)
        enc.pack(fill="x")
        for txt, w in [("Fecha / Hora", 110), ("Modelo", 190),
                        ("MAC", 160), ("GPON SN", 150),
                        ("Tiempo", 70), ("Resultado", 110)]:
            ctk.CTkLabel(enc, text=txt,
                         font=("Segoe UI", 9, "bold"),
                         text_color=T().texto_dim,
                         width=w).pack(side="left", padx=6, pady=8)

        self.tabla_scroll = ctk.CTkScrollableFrame(
            self.tabla_cont, fg_color="transparent", height=300)
        self.tabla_scroll.pack(fill="x")
        self._cargar_tabla(todos)

    def _cargar_tabla(self, todos=None):
        if todos is None:
            todos = hist.cargar_todos()
        for w in self.tabla_scroll.winfo_children():
            w.destroy()

        mod = self._filtro_mod.get()
        res = self._filtro_res.get()
        regs = [r for r in todos
                if (mod == "Todos" or r.get("nombre_display") == mod)
                and (res == "Todos" or
                     ("Éxito" in res) == ("Éxito" in r.get("resultado","")))]

        if not regs:
            ctk.CTkLabel(self.tabla_scroll,
                         text="Sin registros para los filtros seleccionados.",
                         font=("Segoe UI", 11),
                         text_color=T().texto_muted).pack(pady=20)
            return

        for i, reg in enumerate(regs):
            exito   = "Éxito" in reg.get("resultado","")
            col_res = T().verde if exito else T().rojo
            bg      = T().surface if i % 2 == 0 else T().surface2

            fila = ctk.CTkFrame(self.tabla_scroll, fg_color=bg,
                                 corner_radius=T().r_chip)
            fila.pack(fill="x", pady=1)

            # Franja lateral de color
            ctk.CTkFrame(fila, width=3, fg_color=col_res,
                         corner_radius=0).pack(side="left", fill="y")

            fecha_hora = f"{reg.get('fecha','')} {reg.get('hora','')}"
            for txt, w in [
                (fecha_hora,                          110),
                (reg.get("nombre_display","?"),       190),
                (reg.get("mac","?"),                  160),
                (reg.get("gpon_sn","?"),              150),
                (f"{reg.get('tiempo_seg',0):.0f}s",   70),
            ]:
                ctk.CTkLabel(fila, text=txt,
                             font=("Segoe UI", 10),
                             text_color=T().texto,
                             width=w).pack(side="left", padx=6, pady=8)

            badge = ctk.CTkLabel(
                fila,
                text="✓ Éxito" if exito else "✗ Error",
                font=("Segoe UI", 9, "bold"),
                fg_color=T().verde_soft if exito else T().rojo_soft,
                text_color=col_res,
                corner_radius=T().r_pill, padx=10, pady=3)
            badge.pack(side="left", padx=6)

    def _exportar(self):
        ruta = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV","*.csv")],
            initialfile="DigiConfig_Historial.csv")
        if ruta:
            ok = hist.exportar_csv(ruta)
            (messagebox.showinfo if ok else messagebox.showerror)(
                "Exportar", f"Guardado en:\n{ruta}" if ok
                else "No se pudo exportar el historial.")

    def _limpiar(self):
        if messagebox.askyesno("Limpiar historial",
                               "¿Borrar todos los registros?"):
            hist.limpiar_historial()
            self._cargar_tabla([])
