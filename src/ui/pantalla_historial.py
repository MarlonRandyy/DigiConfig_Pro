# ============================================================
# pantalla_historial.py — Historial + KPIs + filtros + exportar
# Versión optimizada con búsqueda por MAC/SN y formato legible
# ============================================================
import customtkinter as ctk
from tkinter import filedialog, messagebox

import src.ui.tema as tema_mod
from src.core import historial as hist


def T():
    return tema_mod.Tema


class PantallaHistorial(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T().bg, corner_radius=0)
        self.app = app
        self._registros_cache = []  # caché local para filtros
        self._pagina_actual = 0
        self._registros_por_pagina = 50
        self._build_ui()
        self._refrescar()

    # ──────────────────────────────────────────────────────────
    #  FUNCIÓN PARA FORMATEAR MAC (solo visual)
    # ──────────────────────────────────────────────────────────
    @staticmethod
    def _formatear_mac(mac: str) -> str:
        """Convierte MAC sin separadores a formato XX:XX:XX:XX:XX:XX para mostrar."""
        if not mac or len(mac) != 12:
            return mac
        return ":".join([mac[i:i+2] for i in range(0, 12, 2)])

    # ──────────────────────────────────────────────────────────
    #  CONSTRUCCIÓN DE LA INTERFAZ
    # ──────────────────────────────────────────────────────────
    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=T().bg, corner_radius=0)
        scroll.pack(fill="both", expand=True)
        p = {"padx": 22, "pady": (0, 14)}

        # ── KPIs ──────────────────────────────────────────────
        self.kpi_row = ctk.CTkFrame(scroll, fg_color="transparent")
        self.kpi_row.pack(fill="x", padx=22, pady=(18, 14))

        self.kpi_labels = {}
        for lbl, key, color in [
            ("Total instaladas", "total", T().accent2),
            ("Configuradas hoy", "hoy", T().verde),
            ("Errores", "errores", T().rojo),
            ("Tasa de éxito", "tasa_exito", T().accent),
        ]:
            f = ctk.CTkFrame(self.kpi_row, fg_color=T().surface,
                             corner_radius=T().r_chip,
                             border_width=1, border_color=T().borde)
            f.pack(side="left", expand=True, fill="x", padx=(0, 10))
            val_lbl = ctk.CTkLabel(f, text="0",
                                   font=("Segoe UI", 22, "bold"),
                                   text_color=color)
            val_lbl.pack(pady=(10, 0))
            ctk.CTkLabel(f, text=lbl,
                         font=("Segoe UI", 9, "bold"),
                         text_color=T().texto_dim).pack(pady=(0, 10))
            self.kpi_labels[key] = val_lbl

        # ── Toolbar ───────────────────────────────────────────
        toolbar = ctk.CTkFrame(scroll, fg_color=T().surface,
                               corner_radius=T().r_card,
                               border_width=1, border_color=T().borde)
        toolbar.pack(fill="x", **p)
        tb = ctk.CTkFrame(toolbar, fg_color="transparent")
        tb.pack(fill="x", padx=16, pady=10)

        # Filtro por modelo
        ctk.CTkLabel(tb, text="Modelo:",
                     font=("Segoe UI", 11),
                     text_color=T().texto_muted).pack(side="left")

        self._filtro_mod = ctk.StringVar(value="Todos")
        self.combo_modelos = ctk.CTkComboBox(
            tb, values=["Todos"],
            variable=self._filtro_mod,
            width=180, height=32,
            fg_color=T().surface2,
            border_color=T().borde,
            button_color=T().accent,
            dropdown_fg_color=T().surface2,
            text_color=T().texto,
            command=lambda _: self._aplicar_filtros()
        )
        self.combo_modelos.pack(side="left", padx=(6, 16))

        # Filtro por resultado
        ctk.CTkLabel(tb, text="Resultado:",
                     font=("Segoe UI", 11),
                     text_color=T().texto_muted).pack(side="left")
        self._filtro_res = ctk.StringVar(value="Todos")
        ctk.CTkComboBox(
            tb, values=["Todos", "✓ Éxito", "✗ Error"],
            variable=self._filtro_res,
            width=130, height=32,
            fg_color=T().surface2,
            border_color=T().borde,
            button_color=T().accent,
            dropdown_fg_color=T().surface2,
            text_color=T().texto,
            command=lambda _: self._aplicar_filtros()
        ).pack(side="left", padx=(6, 0))

        # ── BÚSQUEDA POR MAC/SN (NUEVO) ──────────────────────
        ctk.CTkLabel(tb, text="Buscar:",
                     font=("Segoe UI", 11),
                     text_color=T().texto_muted).pack(side="left", padx=(16, 4))
        self.entry_buscar = ctk.CTkEntry(
            tb, width=180,
            placeholder_text="MAC o SN...",
            fg_color=T().surface2,
            border_color=T().borde,
            text_color=T().texto)
        self.entry_buscar.pack(side="left", padx=(0, 8))
        self.entry_buscar.bind("<KeyRelease>", lambda e: self._aplicar_filtros())

        # Botones derecha
        ctk.CTkButton(
            tb, text="⟳ Refrescar",
            fg_color=T().surface2,
            hover_color=T().borde,
            text_color=T().texto_muted,
            border_width=1, border_color=T().borde,
            height=32, corner_radius=T().r_btn,
            font=("Segoe UI", 11),
            command=self._refrescar
        ).pack(side="right", padx=(8, 0))

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
        for txt, w in [("Fecha / Hora", 110), ("Modelo", 180),
                       ("MAC", 170), ("GPON SN", 150),
                       ("Tiempo", 70), ("Resultado", 110)]:
            ctk.CTkLabel(enc, text=txt,
                         font=("Segoe UI", 9, "bold"),
                         text_color=T().texto_dim,
                         width=w).pack(side="left", padx=6, pady=8)

        self.tabla_scroll = ctk.CTkScrollableFrame(
            self.tabla_cont, fg_color="transparent", height=300)
        self.tabla_scroll.pack(fill="x")

        # ── Paginación (controles abajo) ─────────────────────
        pag_frame = ctk.CTkFrame(self.tabla_cont, fg_color="transparent")
        pag_frame.pack(fill="x", pady=8)
        self.lbl_pagina = ctk.CTkLabel(
            pag_frame, text="Página 1 de 1",
            font=("Segoe UI", 10), text_color=T().texto_muted)
        self.lbl_pagina.pack(side="left", padx=10)

        ctk.CTkButton(
            pag_frame, text="◀ Anterior",
            fg_color=T().surface2, text_color=T().texto_muted,
            border_width=1, border_color=T().borde,
            height=28, corner_radius=T().r_btn,
            font=("Segoe UI", 10),
            command=self._pagina_anterior
        ).pack(side="right", padx=5)
        ctk.CTkButton(
            pag_frame, text="Siguiente ▶",
            fg_color=T().surface2, text_color=T().texto_muted,
            border_width=1, border_color=T().borde,
            height=28, corner_radius=T().r_btn,
            font=("Segoe UI", 10),
            command=self._pagina_siguiente
        ).pack(side="right", padx=5)

        # Mensaje de carga inicial
        ctk.CTkLabel(self.tabla_scroll,
                     text="Cargando datos...",
                     font=("Segoe UI", 11),
                     text_color=T().texto_muted).pack(pady=20)

    # ──────────────────────────────────────────────────────────
    #  REFRESCAR DATOS
    # ──────────────────────────────────────────────────────────
    def _refrescar(self):
        """Recarga todos los datos desde el historial y actualiza la UI."""
        try:
            self._registros_cache = hist.cargar_todos()
            if not isinstance(self._registros_cache, list):
                self._registros_cache = []
        except Exception as e:
            print(f"[Historial] Error al cargar: {e}")
            self._registros_cache = []

        # Actualizar lista de modelos en el filtro
        nombres = sorted({r.get("nombre_display", "?") for r in self._registros_cache})
        self.combo_modelos.configure(values=["Todos"] + list(nombres))
        if self._filtro_mod.get() not in self.combo_modelos.cget("values"):
            self._filtro_mod.set("Todos")

        # Actualizar KPIs
        stats = hist.estadisticas()
        self.kpi_labels["total"].configure(text=str(stats.get("total", 0)))
        self.kpi_labels["hoy"].configure(text=str(stats.get("hoy", 0)))
        self.kpi_labels["errores"].configure(text=str(stats.get("errores", 0)))
        self.kpi_labels["tasa_exito"].configure(text=f"{stats.get('tasa_exito', 0)}%")

        # Resetear página y aplicar filtros
        self._pagina_actual = 0
        self._aplicar_filtros()

    # ──────────────────────────────────────────────────────────
    #  FILTRADO Y PAGINACIÓN (con búsqueda por MAC/SN)
    # ──────────────────────────────────────────────────────────
    def _aplicar_filtros(self):
        """Aplica los filtros actuales (modelo, resultado, búsqueda) y muestra la página."""
        mod = self._filtro_mod.get()
        res = self._filtro_res.get()
        busqueda = self.entry_buscar.get().strip().upper()

        # Filtrar
        filtrados = [
            r for r in self._registros_cache
            if (mod == "Todos" or r.get("nombre_display") == mod)
            and (res == "Todos" or ("Éxito" in res) == ("Éxito" in r.get("resultado", "")))
            and (busqueda == "" or
                 busqueda in r.get("mac", "").upper() or
                 busqueda in r.get("gpon_sn", "").upper())
        ]

        # Calcular páginas
        total = len(filtrados)
        total_paginas = max(1, (total + self._registros_por_pagina - 1) // self._registros_por_pagina)
        if self._pagina_actual >= total_paginas:
            self._pagina_actual = total_paginas - 1
        if self._pagina_actual < 0:
            self._pagina_actual = 0

        inicio = self._pagina_actual * self._registros_por_pagina
        fin = min(inicio + self._registros_por_pagina, total)
        pagina_regs = filtrados[inicio:fin]

        # Actualizar tabla
        self._cargar_tabla(pagina_regs, total, inicio, fin)

    def _cargar_tabla(self, registros, total, inicio, fin):
        """Llena la tabla con los registros de la página actual (MAC formateada)."""
        for w in self.tabla_scroll.winfo_children():
            w.destroy()

        if not registros:
            ctk.CTkLabel(self.tabla_scroll,
                         text="No hay registros para los filtros seleccionados.",
                         font=("Segoe UI", 11),
                         text_color=T().texto_muted).pack(pady=20)
            self.lbl_pagina.configure(text="Página 0 de 0")
            return

        # Mostrar rango de registros
        total_paginas = max(1, (total + self._registros_por_pagina - 1) // self._registros_por_pagina)
        self.lbl_pagina.configure(
            text=f"Página {self._pagina_actual + 1} de {total_paginas}"
            f"  |  Mostrando {inicio + 1}-{fin} de {total}"
        )

        for i, reg in enumerate(registros):
            exito = "Éxito" in reg.get("resultado", "")
            col_res = T().verde if exito else T().rojo
            bg = T().surface if i % 2 == 0 else T().surface2

            fila = ctk.CTkFrame(self.tabla_scroll, fg_color=bg,
                                corner_radius=T().r_chip)
            fila.pack(fill="x", pady=1)

            # Franja lateral
            ctk.CTkFrame(fila, width=3, fg_color=col_res,
                         corner_radius=0).pack(side="left", fill="y")

            # MAC formateada para mostrar
            mac_raw = reg.get("mac", "")
            mac_mostrar = self._formatear_mac(mac_raw) if mac_raw else "N/A"

            fecha_hora = f"{reg.get('fecha', '')} {reg.get('hora', '')}"
            for txt, w in [
                (fecha_hora, 110),
                (reg.get("nombre_display", "?"), 180),
                (mac_mostrar, 170),
                (reg.get("gpon_sn", "?"), 150),
                (f"{reg.get('tiempo_seg', 0):.0f}s", 70),
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

    # ──────────────────────────────────────────────────────────
    #  PAGINACIÓN
    # ──────────────────────────────────────────────────────────
    def _pagina_anterior(self):
        if self._pagina_actual > 0:
            self._pagina_actual -= 1
            self._aplicar_filtros()

    def _pagina_siguiente(self):
        # Calcular total de páginas para el conjunto filtrado actual
        mod = self._filtro_mod.get()
        res = self._filtro_res.get()
        busqueda = self.entry_buscar.get().strip().upper()
        filtrados = [
            r for r in self._registros_cache
            if (mod == "Todos" or r.get("nombre_display") == mod)
            and (res == "Todos" or ("Éxito" in res) == ("Éxito" in r.get("resultado", "")))
            and (busqueda == "" or
                 busqueda in r.get("mac", "").upper() or
                 busqueda in r.get("gpon_sn", "").upper())
        ]
        total_paginas = max(1, (len(filtrados) + self._registros_por_pagina - 1) // self._registros_por_pagina)
        if self._pagina_actual + 1 < total_paginas:
            self._pagina_actual += 1
            self._aplicar_filtros()

    # ──────────────────────────────────────────────────────────
    #  EXPORTAR Y LIMPIAR
    # ──────────────────────────────────────────────────────────
    def _exportar(self):
        ruta = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="DigiConfig_Historial.csv")
        if ruta:
            ok = hist.exportar_csv(ruta)
            if ok:
                messagebox.showinfo("Exportar", f"Historial exportado a:\n{ruta}")
            else:
                messagebox.showerror("Exportar", "No se pudo exportar el historial.")

    def _limpiar(self):
        if messagebox.askyesno("Limpiar historial",
                               "¿Borrar todos los registros del historial?\nEsta acción no se puede deshacer."):
            ok = hist.limpiar_historial()
            if ok:
                self._refrescar()
                messagebox.showinfo("Limpiar", "Historial limpiado correctamente.")
            else:
                messagebox.showerror("Limpiar", "Error al limpiar el historial.")

    # ──────────────────────────────────────────────────────────
    #  MÉTODO DE CIERRE
    # ──────────────────────────────────────────────────────────
    def cerrar(self):
        """Limpia recursos si es necesario."""
        pass