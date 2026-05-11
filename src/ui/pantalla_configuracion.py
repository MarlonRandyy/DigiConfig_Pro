# ============================================================
# pantalla_configuracion.py — Instalación XML + progreso live
# ============================================================
import customtkinter as ctk
import threading, time, os
from tkinter import filedialog

import src.ui.tema as tema_mod
from src.core.instalador import InstaladorONU
from src.core import historial as hist
from src.utils import notificaciones


def T(): return tema_mod.Tema


class PantallaConfiguracion(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T().bg, corner_radius=0)
        self.app        = app
        self._instalando = False
        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=T().bg, corner_radius=0)
        scroll.pack(fill="both", expand=True)
        p = {"padx": 22, "pady": (0, 14)}

        # ── Card ONU seleccionada ─────────────────────────────
        info = self.app.onu_info
        card_onu = ctk.CTkFrame(
            scroll, fg_color=T().surface,
            corner_radius=T().r_card,
            border_width=1,
            border_color=T().verde if info else T().borde)
        card_onu.pack(fill="x", padx=22, pady=(18, 14))

        ctk.CTkFrame(card_onu, height=3, fg_color=T().verde if info else T().borde,
                     corner_radius=0).pack(fill="x")
        ctk.CTkLabel(card_onu, text="ONU a configurar",
                     font=("Segoe UI", 10, "bold"),
                     text_color=T().texto_dim).pack(
            anchor="w", padx=18, pady=(12, 4))

        if info:
            txt = (f"  {info.get('nombre_display','?')}\n"
                   f"MAC: {info.get('mac','?')}  ·  IP: {info.get('ip','?')}")
            col = T().verde
        else:
            txt = "  Sin ONU detectada — ve al Dashboard y conecta una ONU."
            col = T().amarillo

        ctk.CTkLabel(card_onu, text=txt,
                     font=("Segoe UI", 12),
                     text_color=col,
                     justify="left").pack(anchor="w", padx=18, pady=(0, 14))

        # ── Card selección modelo + XML ───────────────────────
        card_xml = ctk.CTkFrame(
            scroll, fg_color=T().surface,
            corner_radius=T().r_card,
            border_width=1, border_color=T().borde)
        card_xml.pack(fill="x", **p)

        ctk.CTkLabel(card_xml, text="Archivo de configuración",
                     font=("Segoe UI", 10, "bold"),
                     text_color=T().texto_dim).pack(
            anchor="w", padx=18, pady=(12, 8))

        fila = ctk.CTkFrame(card_xml, fg_color="transparent")
        fila.pack(fill="x", padx=18, pady=(0, 14))

        ctk.CTkLabel(fila, text="Modelo:",
                     font=("Segoe UI", 11),
                     text_color=T().texto_muted,
                     width=70).pack(side="left")

        modelos_ids = list(self.app.modelos.keys())
        self.combo_modelo = ctk.CTkComboBox(
            fila, values=modelos_ids, width=240,
            fg_color=T().surface2,
            border_color=T().borde,
            button_color=T().accent,
            dropdown_fg_color=T().surface2,
            text_color=T().texto,
            command=self._auto_xml)
        modelo_detectado = (info or {}).get("modelo_id", "")
        self.combo_modelo.set(
            modelo_detectado if modelo_detectado in modelos_ids
            else (modelos_ids[0] if modelos_ids else ""))
        self.combo_modelo.pack(side="left", padx=(0, 10))

        fila2 = ctk.CTkFrame(card_xml, fg_color="transparent")
        fila2.pack(fill="x", padx=18, pady=(0, 14))
        ctk.CTkLabel(fila2, text="XML:",
                     font=("Segoe UI", 11),
                     text_color=T().texto_muted,
                     width=70).pack(side="left")
        self.entry_xml = ctk.CTkEntry(
            fila2, width=300, fg_color=T().surface2,
            border_color=T().borde, text_color=T().texto)
        self.entry_xml.pack(side="left", padx=(0, 8))
        ctk.CTkButton(fila2, text="Examinar...",
                      fg_color=T().surface2,
                      hover_color=T().borde,
                      text_color=T().texto_muted,
                      border_width=1, border_color=T().borde,
                      height=32, corner_radius=T().r_btn,
                      font=("Segoe UI", 11),
                      width=100,
                      command=self._examinar_xml).pack(side="left")
        self._auto_xml(self.combo_modelo.get())

        # ── Card consola ──────────────────────────────────────
        card_log = ctk.CTkFrame(
            scroll, fg_color=T().surface,
            corner_radius=T().r_card,
            border_width=1, border_color=T().borde)
        card_log.pack(fill="x", **p)

        ctk.CTkLabel(card_log, text="Consola de instalación",
                     font=("Segoe UI", 10, "bold"),
                     text_color=T().texto_dim).pack(
            anchor="w", padx=18, pady=(12, 6))

        self.txt_log = ctk.CTkTextbox(
            card_log, height=190,
            font=("Consolas", 11),
            fg_color=T().surface2,
            text_color=T().verde,
            border_width=1, border_color=T().borde,
            corner_radius=T().r_chip)
        self.txt_log.pack(fill="x", padx=18)
        self.txt_log.insert("end", "Sistema listo. Esperando inicio de instalación...\n")
        self.txt_log.configure(state="disabled")

        # Progreso
        prog_info = ctk.CTkFrame(card_log, fg_color="transparent")
        prog_info.pack(fill="x", padx=18, pady=(10, 4))
        self.lbl_prog_txt = ctk.CTkLabel(
            prog_info, text="Progreso",
            font=("Segoe UI", 10), text_color=T().texto_muted)
        self.lbl_prog_txt.pack(side="left")
        self.lbl_prog_pct = ctk.CTkLabel(
            prog_info, text="0%",
            font=("Segoe UI", 10, "bold"), text_color=T().accent)
        self.lbl_prog_pct.pack(side="right")

        self.barra = ctk.CTkProgressBar(
            card_log, height=8,
            progress_color=T().accent,
            fg_color=T().borde,
            corner_radius=T().r_pill)
        self.barra.set(0)
        self.barra.pack(fill="x", padx=18, pady=(0, 16))

        # ── Botón instalar ────────────────────────────────────
        self.btn_instalar = ctk.CTkButton(
            scroll, text="▶  Iniciar instalación",
            fg_color=T().accent,
            hover_color=T().accent_hover,
            text_color="#ffffff",
            height=50, corner_radius=T().r_btn,
            font=("Segoe UI", 14, "bold"),
            command=self._iniciar)
        self.btn_instalar.pack(fill="x", padx=22, pady=(0, 18))

    def _auto_xml(self, modelo_id: str):
        datos = self.app.modelos.get(modelo_id, {})
        self.entry_xml.delete(0, "end")
        self.entry_xml.insert(0, datos.get("firmware_xml", ""))

    def _examinar_xml(self):
        r = filedialog.askopenfilename(
            title="Seleccionar XML",
            filetypes=[("XML", "*.xml"), ("Todos", "*.*")])
        if r:
            self.entry_xml.delete(0, "end")
            self.entry_xml.insert(0, r)

    def _log(self, msg: str):
        def _w():
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", msg + "\n")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")
        self.after(0, _w)

    def _set_pct(self, pct: int):
        def _w():
            self.barra.set(pct / 100)
            self.lbl_prog_pct.configure(text=f"{pct}%")
            self.lbl_prog_txt.configure(
                text="Instalando..." if 0 < pct < 100 else
                     "Completado" if pct == 100 else "Progreso")
        self.after(0, _w)

    def _iniciar(self):
        if self._instalando:
            return
        modelo_id = self.combo_modelo.get()
        ruta_xml  = self.entry_xml.get().strip()
        datos_mod = self.app.modelos.get(modelo_id)
        if not datos_mod:
            self._log("❌ Modelo no encontrado en la BD.")
            return
        if not ruta_xml or not os.path.exists(ruta_xml):
            self._log("❌ Archivo XML no válido o no encontrado.")
            return

        self._instalando = True
        self.btn_instalar.configure(state="disabled",
                                    text="Instalando...")
        self.barra.set(0)
        t0 = time.time()

        def _proc():
            inst = InstaladorONU(
                datos_modelo=datos_mod,
                ruta_xml=ruta_xml,
                callback_log=self._log,
                callback_progreso=self._set_pct)
            res = inst.instalar()
            dur = time.time() - t0
            onu = self.app.onu_info
            hist.guardar_registro(
                modelo_id=modelo_id,
                nombre_display=datos_mod.get("nombre_display", "?"),
                mac=onu.get("mac", "?"),
                gpon_sn=onu.get("gpon_sn", "?"),
                ip_final=datos_mod.get("ip_configurada", "?"),
                xml_usado=ruta_xml,
                exito=res.exito,
                tiempo_seg=dur)
            if res.exito:
                notificaciones.instalacion_exitosa(
                    datos_mod.get("nombre_display", "ONU"),
                    datos_mod.get("ip_configurada", "?"))
            else:
                notificaciones.error_instalacion(res.mensaje)
            self._instalando = False
            self.after(0, lambda: self.btn_instalar.configure(
                state="normal",
                text="✓ Completado — Instalar otra"
                if res.exito else "▶  Reintentar instalación",
                fg_color=T().verde if res.exito else T().rojo))
        threading.Thread(target=_proc, daemon=True).start()
