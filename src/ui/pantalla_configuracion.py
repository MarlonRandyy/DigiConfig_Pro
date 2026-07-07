# ============================================================
# pantalla_configuracion.py — Instalación XML + progreso live
# Versión optimizada con validaciones, logs detallados y UI fluida
# ============================================================
import customtkinter as ctk
import threading
import time
import os
from tkinter import filedialog, messagebox
from PIL import Image

import src.ui.tema as tema_mod
from src.core.instalador import InstaladorONU
from src.core import historial as hist
from src.utils import notificaciones


def T():
    return tema_mod.Tema


class PantallaConfiguracion(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T().bg, corner_radius=0)
        self.app = app
        self._instalando = False
        self._modelo_actual = None
        self._build_ui()

    # ──────────────────────────────────────────────────────────
    #  CONSTRUCCIÓN DE LA INTERFAZ
    # ──────────────────────────────────────────────────────────
    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=T().bg, corner_radius=0)
        scroll.pack(fill="both", expand=True)
        p = {"padx": 22, "pady": (0, 14)}

        # ── Card ONU seleccionada ─────────────────────────────
        self.card_onu = ctk.CTkFrame(
            scroll, fg_color=T().surface,
            corner_radius=T().r_card,
            border_width=1, border_color=T().borde)
        self.card_onu.pack(fill="x", padx=22, pady=(18, 14))

        self.franja_onu = ctk.CTkFrame(
            self.card_onu, height=3, fg_color=T().borde, corner_radius=0)
        self.franja_onu.pack(fill="x")

        ctk.CTkLabel(self.card_onu, text="ONU a configurar",
                     font=("Segoe UI", 10, "bold"),
                     text_color=T().texto_dim).pack(
            anchor="w", padx=18, pady=(12, 4))

        # Contenedor para info de ONU + imagen del modelo
        onu_row = ctk.CTkFrame(self.card_onu, fg_color="transparent")
        onu_row.pack(fill="x", padx=18, pady=(0, 14))

        self.lbl_onu_info = ctk.CTkLabel(
            onu_row, text="  Sin ONU detectada — ve al Dashboard y conecta una ONU.",
            font=("Segoe UI", 12), text_color=T().amarillo, justify="left")
        self.lbl_onu_info.pack(side="left", fill="both", expand=True)

        # Imagen del modelo (se muestra al seleccionar modelo)
        self.img_modelo_label = ctk.CTkLabel(onu_row, text="", width=80, height=60)
        self.img_modelo_label.pack(side="right", padx=(10, 0))

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

        # Fila modelo
        fila = ctk.CTkFrame(card_xml, fg_color="transparent")
        fila.pack(fill="x", padx=18, pady=(0, 8))
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
            command=self._on_modelo_seleccionado)
        info = self.app.onu_info
        modelo_detectado = info.get("modelo_id", "") if info else ""
        self.combo_modelo.set(
            modelo_detectado if modelo_detectado in modelos_ids
            else (modelos_ids[0] if modelos_ids else ""))
        self.combo_modelo.pack(side="left", padx=(0, 10))

        # Etiquetas informativas del modelo (fabricante, upload, reinicio)
        self.lbl_info_modelo = ctk.CTkLabel(
            fila, text="", font=("Segoe UI", 10), text_color=T().texto_muted)
        self.lbl_info_modelo.pack(side="left", padx=(10, 0))

        # Fila XML
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
            card_log, height=200,
            font=("Consolas", 11),
            fg_color=T().surface2,
            text_color=T().verde,
            border_width=1, border_color=T().borde,
            corner_radius=T().r_chip)
        self.txt_log.pack(fill="x", padx=18)
        self.txt_log.insert("end", "✅ Sistema listo. Esperando inicio de instalación...\n")
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

        # Actualizar estado inicial
        self._actualizar_estado_onu()
        self._on_modelo_seleccionado(self.combo_modelo.get())

    # ──────────────────────────────────────────────────────────
    #  ACTUALIZACIÓN DE ESTADO
    # ──────────────────────────────────────────────────────────
    def _actualizar_estado_onu(self):
        info = self.app.onu_info
        if info:
            txt = (f"  {info.get('nombre_display', '?')}\n"
                   f"MAC: {info.get('mac', '?')}  ·  IP: {info.get('ip', '?')}")
            self.lbl_onu_info.configure(text=txt, text_color=T().verde)
            self.franja_onu.configure(fg_color=T().verde)
            self.card_onu.configure(border_color=T().verde)
            self._validar_boton()
        else:
            self.lbl_onu_info.configure(
                text="  Sin ONU detectada — ve al Dashboard y conecta una ONU.",
                text_color=T().amarillo)
            self.franja_onu.configure(fg_color=T().borde)
            self.card_onu.configure(border_color=T().borde)
            self.btn_instalar.configure(state="disabled", fg_color=T().borde)

    def _validar_boton(self):
        """Habilita el botón solo si hay ONU, modelo seleccionado y XML válido."""
        if not self.app.onu_info:
            self.btn_instalar.configure(state="disabled", fg_color=T().borde)
            return
        modelo_id = self.combo_modelo.get()
        if not modelo_id or modelo_id not in self.app.modelos:
            self.btn_instalar.configure(state="disabled", fg_color=T().borde)
            return
        ruta_xml = self.entry_xml.get().strip()
        if not ruta_xml or not os.path.exists(ruta_xml):
            self.btn_instalar.configure(state="disabled", fg_color=T().borde)
            return
        self.btn_instalar.configure(state="normal", fg_color=T().accent)

    # ──────────────────────────────────────────────────────────
    #  SELECCIÓN DE MODELO
    # ──────────────────────────────────────────────────────────
    def _on_modelo_seleccionado(self, modelo_id: str):
        """Cuando se selecciona un modelo, actualiza XML, info y imagen."""
        datos = self.app.modelos.get(modelo_id, {})
        self._modelo_actual = datos

        # XML
        self.entry_xml.delete(0, "end")
        self.entry_xml.insert(0, datos.get("firmware_xml", ""))

        # Información adicional del modelo
        fabricante = datos.get("fabricante", "?")
        campo_upload = datos.get("campo_upload", "config")
        ruta_upload = datos.get("ruta_upload", "/")
        tiempo_reinicio = datos.get("tiempo_reinicio", 60)
        self.lbl_info_modelo.configure(
            text=f"{fabricante} · Upload: {campo_upload} · Ruta: {ruta_upload} · Reinicio: {tiempo_reinicio}s"
        )

        # Imagen del modelo
        img_path = datos.get("imagen", "")
        if img_path and os.path.exists(img_path):
            try:
                raw = Image.open(img_path)
                raw.thumbnail((80, 60), Image.LANCZOS)
                img = ctk.CTkImage(light_image=raw, dark_image=raw, size=(80, 60))
                self.img_modelo_label.configure(image=img, text="")
                self.img_modelo_label._img_ref = img
            except Exception:
                self.img_modelo_label.configure(image=None, text="🖼️")
        else:
            self.img_modelo_label.configure(image=None, text="🖼️")

        self._validar_boton()

    # ──────────────────────────────────────────────────────────
    #  EXAMINAR XML
    # ──────────────────────────────────────────────────────────
    def _examinar_xml(self):
        r = filedialog.askopenfilename(
            title="Seleccionar XML",
            filetypes=[("XML", "*.xml"), ("Todos", "*.*")])
        if r:
            self.entry_xml.delete(0, "end")
            self.entry_xml.insert(0, r)
            self._validar_boton()

    # ──────────────────────────────────────────────────────────
    #  LOG Y PROGRESO
    # ──────────────────────────────────────────────────────────
    def _log(self, msg: str, tipo: str = "info"):
        """Agrega un mensaje a la consola con emoji según el tipo."""
        emoji = {"info": "ℹ️", "exito": "✅", "error": "❌", "warning": "⚠️"}.get(tipo, "ℹ️")
        def _w():
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", f"{emoji} {msg}\n")
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

    # ──────────────────────────────────────────────────────────
    #  INICIAR INSTALACIÓN
    # ──────────────────────────────────────────────────────────
    def _iniciar(self):
        if self._instalando:
            return

        # ── Validaciones previas ─────────────────────────────────
        if not self.app.onu_info:
            self._log("No hay ONU detectada. Conecta una ONU en el Dashboard.", "error")
            return

        modelo_id = self.combo_modelo.get()
        ruta_xml = self.entry_xml.get().strip()
        datos_mod = self.app.modelos.get(modelo_id)
        if not datos_mod:
            self._log("Modelo no encontrado en la base de datos.", "error")
            return

        if not ruta_xml or not os.path.exists(ruta_xml):
            self._log("Archivo XML no válido o no encontrado.", "error")
            return

        # Verificar que el XML no esté vacío
        try:
            if os.path.getsize(ruta_xml) < 100:
                self._log("El archivo XML parece estar vacío o es muy pequeño.", "warning")
                if not messagebox.askyesno("Advertencia", 
                                           "El archivo XML parece estar vacío. ¿Deseas continuar de todas formas?"):
                    return
        except Exception:
            pass

        # ── CONFIRMACIÓN DEL USUARIO ────────────────────────────
        onu_mac = self.app.onu_info.get("mac", "MAC desconocida")
        nombre_modelo = datos_mod.get("nombre_display", modelo_id)
        msg = (f"¿Confirmas instalar '{nombre_modelo}' en la ONU detectada?\n\n"
               f"MAC: {onu_mac}\n"
               f"IP de fábrica: {datos_mod.get('ip_fabrica', '?')}\n"
               f"IP final: {datos_mod.get('ip_configurada', '?')}\n"
               f"Campo de upload: {datos_mod.get('campo_upload', 'config')}\n"
               f"Tiempo de reinicio: {datos_mod.get('tiempo_reinicio', 60)}s\n\n"
               "Esta acción modificará la configuración del equipo.")
        if not messagebox.askyesno("Confirmar instalación", msg):
            self._log("Instalación cancelada por el usuario.", "warning")
            return

        # ── Mostrar MAC en consola ──────────────────────────────
        self._log(f"🔧 Configurando ONU MAC: {onu_mac}")
        self._log(f"📄 Modelo: {nombre_modelo}")

        # ── Iniciar instalación ──────────────────────────────────
        self._instalando = True
        self.btn_instalar.configure(state="disabled", text="Instalando...", fg_color=T().borde)
        self.barra.set(0)
        t0 = time.time()

        res = None

        def _proc():
            nonlocal res
            try:
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
                        datos_mod.get("ip_configurada", "?"),
                        datos_mod.get("clave_final", "digicable19"))
                    self._log(f"✅ Instalación completada en {dur:.1f}s", "exito")
                else:
                    self._log(f"❌ Error: {res.mensaje}", "error")
                    if res.detalle:
                        self._log(f"Detalle: {res.detalle}", "error")
            except Exception as e:
                self._log(f"Error inesperado: {e}", "error")
                import traceback
                traceback.print_exc()
            finally:
                self._instalando = False
                exito = res.exito if res is not None else False
                self.after(0, lambda: self._finalizar_instalacion(exito))

        threading.Thread(target=_proc, daemon=True).start()

    def _finalizar_instalacion(self, exito: bool):
        self.btn_instalar.configure(
            state="normal",
            text="✓ Completado — Instalar otra" if exito else "▶  Reintentar instalación",
            fg_color=T().verde if exito else T().rojo)
        self._validar_boton()  # restablece el estado del botón