# ============================================================
# pantalla_modelos.py — Gestión de modelos de ONU
# Con selección de fabricante, autocompletado y campos avanzados
# ============================================================
import customtkinter as ctk
import os
from tkinter import filedialog, messagebox
from PIL import Image

import src.ui.tema as tema_mod
from src.core import modelos_manager
from src.core import onu_database


def T():
    return tema_mod.Tema


class PantallaModelos(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T().bg, corner_radius=0)
        self.app = app
        self._build_ui()

    # ──────────────────────────────────────────────────────────
    #  INTERFAZ PRINCIPAL
    # ──────────────────────────────────────────────────────────
    def _build_ui(self):
        main = ctk.CTkFrame(self, fg_color=T().bg)
        main.pack(fill="both", expand=True, padx=22, pady=18)

        # ── Panel izquierdo (lista de modelos) ──────────────
        left = ctk.CTkFrame(main, fg_color=T().surface,
                            corner_radius=T().r_card,
                            border_width=1, border_color=T().borde,
                            width=280)
        left.pack(side="left", fill="y", padx=(0, 14))
        left.pack_propagate(False)

        hdr_l = ctk.CTkFrame(left, fg_color="transparent")
        hdr_l.pack(fill="x", padx=14, pady=(14, 8))
        ctk.CTkLabel(hdr_l, text="Modelos registrados",
                     font=("Segoe UI", 12, "bold"),
                     text_color=T().texto).pack(side="left")
        ctk.CTkButton(
            hdr_l, text="+ Nuevo",
            fg_color=T().accent,
            hover_color=T().accent_hover,
            text_color="#ffffff",
            height=28, corner_radius=T().r_btn,
            font=("Segoe UI", 10, "bold"),
            width=70,
            command=self._form_nuevo
        ).pack(side="right")

        ctk.CTkFrame(left, height=1, fg_color=T().borde,
                     corner_radius=0).pack(fill="x", padx=12)

        self.lista = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.lista.pack(fill="both", expand=True, padx=8, pady=8)

        # ── Panel derecho (detalle del modelo) ──────────────
        self.panel = ctk.CTkFrame(main, fg_color=T().surface,
                                  corner_radius=T().r_card,
                                  border_width=1, border_color=T().borde)
        self.panel.pack(side="left", fill="both", expand=True)

        self._cargar_lista()

    # ──────────────────────────────────────────────────────────
    #  LISTA DE MODELOS
    # ──────────────────────────────────────────────────────────
    def _cargar_lista(self):
        for w in self.lista.winfo_children():
            w.destroy()
        modelos = modelos_manager.cargar()
        if not modelos:
            ctk.CTkLabel(self.lista, text="Sin modelos.\nUsa + Nuevo.",
                         font=("Segoe UI", 11),
                         text_color=T().texto_muted).pack(pady=20)
            return
        for mid, datos in modelos.items():
            self._btn_modelo(mid, datos)

    def _btn_modelo(self, mid, datos):
        btn = ctk.CTkButton(
            self.lista,
            text=datos.get("nombre_display", mid),
            anchor="w",
            fg_color=T().surface2,
            hover_color=T().borde,
            text_color=T().texto,
            height=40, corner_radius=T().r_btn,
            font=("Segoe UI", 11),
            command=lambda m=mid: self._ver_detalle(m))
        btn.pack(fill="x", pady=2)

    # ──────────────────────────────────────────────────────────
    #  VISTA DE DETALLE (con todos los campos)
    # ──────────────────────────────────────────────────────────
    def _ver_detalle(self, mid: str):
        for w in self.panel.winfo_children():
            w.destroy()
        datos = modelos_manager.obtener(mid)
        if not datos:
            return

        ctk.CTkFrame(self.panel, height=3,
                     fg_color=T().accent, corner_radius=0).pack(fill="x")

        header = ctk.CTkFrame(self.panel, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))

        img_path = datos.get("imagen", "")
        if img_path and os.path.exists(img_path):
            try:
                raw_img = Image.open(img_path)
                img_ctk = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=(80, 60))
                lbl_img = ctk.CTkLabel(header, image=img_ctk, text="")
                lbl_img.pack(side="left", padx=(0, 16))
                lbl_img._img_ref = img_ctk
            except Exception:
                pass

        info_frame = ctk.CTkFrame(header, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(info_frame,
                     text=datos.get("nombre_display", mid),
                     font=("Segoe UI", 16, "bold"),
                     text_color=T().accent).pack(anchor="w")
        ctk.CTkLabel(info_frame,
                     text=f"ID: {mid}",
                     font=("Consolas", 10),
                     text_color=T().texto_dim).pack(anchor="w")

        ctk.CTkFrame(self.panel, height=1, fg_color=T().borde,
                     corner_radius=0).pack(fill="x", padx=20, pady=8)

        # Lista de campos a mostrar (con los nuevos)
        campos = [
            ("Fabricante",       datos.get("fabricante", "")),
            ("IP de fábrica",    datos.get("ip_fabrica", "")),
            ("IP configurada",   datos.get("ip_configurada", "")),
            ("Usuario fábrica",  datos.get("usuario_fabrica", "")),
            ("Clave fábrica",    datos.get("clave_fabrica", "")),
            ("Usuario final",    datos.get("usuario_final", "")),
            ("Clave final",      datos.get("clave_final", "")),
            ("Campo de upload",  datos.get("campo_upload", "config")),
            ("Ruta de upload",   datos.get("ruta_upload", "/")),
            ("Datos extra",      datos.get("data_extra", {}).__str__()),
            ("Tiempo reinicio",  f"{datos.get('tiempo_reinicio', 60)} segundos"),
            ("XML",              datos.get("firmware_xml", "")),
            ("Notas",            datos.get("notas", "")),
        ]
        for lbl, val in campos:
            f = ctk.CTkFrame(self.panel, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(f, text=f"{lbl}:",
                         font=("Segoe UI", 10, "bold"),
                         text_color=T().texto_muted,
                         width=140).pack(side="left")
            ctk.CTkLabel(f, text=val or "—",
                         font=("Segoe UI", 11),
                         text_color=T().texto).pack(side="left")

        ctk.CTkFrame(self.panel, height=1, fg_color=T().borde,
                     corner_radius=0).pack(fill="x", padx=20, pady=12)

        btns = ctk.CTkFrame(self.panel, fg_color="transparent")
        btns.pack(fill="x", padx=20)
        ctk.CTkButton(
            btns, text="⚙  Editar datos",
            fg_color=T().accent, hover_color=T().accent_hover,
            text_color="#ffffff",
            height=36, corner_radius=T().r_btn,
            font=("Segoe UI", 11, "bold"),
            command=lambda: self._form_editar(mid)
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btns, text="✏  Editar XML",
            fg_color=T().surface2, hover_color=T().borde,
            text_color=T().texto,
            border_width=1, border_color=T().borde,
            height=36, corner_radius=T().r_btn,
            font=("Segoe UI", 11),
            command=lambda: self._editar_xml(datos.get("firmware_xml", ""))
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btns, text="Eliminar",
            fg_color=T().rojo_soft, hover_color=T().rojo,
            text_color=T().rojo,
            border_width=1, border_color=T().rojo,
            height=36, corner_radius=T().r_btn,
            font=("Segoe UI", 11),
            command=lambda: self._eliminar(mid)
        ).pack(side="left")

    # ──────────────────────────────────────────────────────────
    #  EDITOR XML
    # ──────────────────────────────────────────────────────────
    def _editar_xml(self, ruta: str):
        if not ruta or not os.path.exists(ruta):
            messagebox.showwarning("Editor XML", f"Archivo no encontrado:\n{ruta}")
            return
        v = ctk.CTkToplevel(self)
        v.title(f"Editor — {os.path.basename(ruta)}")
        v.geometry("720x520")
        v.configure(fg_color=T().surface)
        v.grab_set()

        txt = ctk.CTkTextbox(v, font=("Consolas", 11),
                             fg_color=T().surface2,
                             text_color=T().verde,
                             border_width=1, border_color=T().borde,
                             corner_radius=T().r_chip)
        txt.pack(fill="both", expand=True, padx=12, pady=12)
        with open(ruta, "r", encoding="utf-8", errors="replace") as f:
            txt.insert("end", f.read())

        def _save():
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(txt.get("1.0", "end"))
            messagebox.showinfo("Guardado", "XML guardado correctamente.")
            v.destroy()

        btn_frame = ctk.CTkFrame(v, fg_color="transparent")
        btn_frame.pack(pady=(0, 10))
        ctk.CTkButton(btn_frame, text="💾  Guardar",
                      fg_color=T().verde, text_color="#ffffff",
                      height=36, corner_radius=T().r_btn,
                      command=_save).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancelar",
                      fg_color=T().surface2, text_color=T().texto_muted,
                      height=36, corner_radius=T().r_btn,
                      command=v.destroy).pack(side="left", padx=5)

    # ──────────────────────────────────────────────────────────
    #  ELIMINAR MODELO
    # ──────────────────────────────────────────────────────────
    def _eliminar(self, mid: str):
        if messagebox.askyesno("Eliminar", f"¿Eliminar el modelo '{mid}'?"):
            datos = modelos_manager.obtener(mid)
            if datos:
                for path in [datos.get("firmware_xml"), datos.get("imagen")]:
                    if path and os.path.exists(path):
                        try:
                            os.remove(path)
                        except Exception:
                            pass
            modelos_manager.eliminar_modelo(mid)
            self.app.modelos = modelos_manager.cargar()
            self._cargar_lista()
            for w in self.panel.winfo_children():
                w.destroy()

    # ──────────────────────────────────────────────────────────
    #  FORMULARIOS (NUEVO / EDITAR)
    # ──────────────────────────────────────────────────────────
    def _form_nuevo(self):
        self._abrir_formulario(modo="nuevo")

    def _form_editar(self, mid: str):
        datos = modelos_manager.obtener(mid)
        if not datos:
            messagebox.showerror("Error", f"No se encontró el modelo '{mid}'.")
            return
        self._abrir_formulario(modo="editar", modelo_id=mid, datos_existentes=datos)

    def _abrir_formulario(self, modo: str, modelo_id: str = None,
                          datos_existentes: dict = None):
        """
        Construye el formulario de alta o edición de un modelo.
        """
        datos_existentes = datos_existentes or {}

        v = ctk.CTkToplevel(self)
        v.title("Agregar nuevo modelo" if modo == "nuevo" else f"Editar modelo — {modelo_id}")
        v.geometry("660x700")  # Un poco más alto para los nuevos campos
        v.configure(fg_color=T().surface)
        v.resizable(True, True) 
        v.grab_set()

        scroll = ctk.CTkScrollableFrame(v, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=6)  # pady reducido

        entradas = {}
        self.entradas = entradas

        # ── Dropdown de fabricante ────────────────────────────
        ctk.CTkLabel(scroll, text="Fabricante *",
                     font=("Segoe UI", 9, "bold"),
                     text_color=T().texto_muted).pack(anchor="w", pady=(6, 0))

        fabricantes = sorted(set([
            info["nombre"] for info in onu_database.FABRICANTES_DB.values()
        ]))

        self.combo_fabricante = ctk.CTkComboBox(
            scroll,
            values=fabricantes,
            fg_color=T().surface2,
            border_color=T().borde,
            button_color=T().accent,
            dropdown_fg_color=T().surface2,
            text_color=T().texto,
            command=self._autocompletar_campos
        )
        self.combo_fabricante.pack(fill="x", pady=(0, 10))
        fabricante_actual = datos_existentes.get("fabricante", "")
        self.combo_fabricante.set(
            fabricante_actual if fabricante_actual in fabricantes
            else "Selecciona un fabricante")

        # ── Campo ID (bloqueado en edición) ──────────────────
        ctk.CTkLabel(scroll, text="ID único (ej: VSOL-V2802) *",
                     font=("Segoe UI", 9, "bold"),
                     text_color=T().texto_muted).pack(anchor="w", pady=(6, 0))
        entry_id = ctk.CTkEntry(
            scroll, placeholder_text="ID único (ej: VSOL-V2802)",
            fg_color=T().surface2,
            border_color=T().borde,
            text_color=T().texto)
        entry_id.pack(fill="x")
        if modo == "editar":
            entry_id.insert(0, modelo_id)
            entry_id.configure(state="disabled")
            ctk.CTkLabel(scroll, text="El ID no se puede modificar.",
                         font=("Segoe UI", 8), text_color=T().texto_dim
                         ).pack(anchor="w", pady=(2, 0))

        # ── Campos básicos ─────────────────────────────────────
        campos_basicos = [
            ("nombre_display",   "Nombre para mostrar (ej: VSOL V2802RGW)", True),
            ("ip_fabrica",       "IP de fábrica (ej: 192.168.1.1)", True),
            ("ip_configurada",   "IP final tras configurar (ej: 192.168.100.1)", True),
            ("usuario_fabrica",  "Usuario de fábrica (ej: admin)", True),
            ("clave_fabrica",    "Clave de fábrica (ej: admin)", True),
            ("usuario_final",    "Usuario final (ej: admin)", True),
            ("clave_final",      "Clave final (ej: clave123)", True),
        ]
        for key, placeholder, obligatorio in campos_basicos:
            label_text = key.replace("_", " ").title()
            if obligatorio:
                label_text += " *"
            ctk.CTkLabel(scroll, text=label_text,
                         font=("Segoe UI", 9, "bold"),
                         text_color=T().texto_muted).pack(anchor="w", pady=(6, 0))
            e = ctk.CTkEntry(scroll, placeholder_text=placeholder,
                             fg_color=T().surface2,
                             border_color=T().borde,
                             text_color=T().texto)
            e.pack(fill="x")
            if datos_existentes.get(key, "") != "":
                e.insert(0, str(datos_existentes.get(key, "")))
            entradas[key] = e

        # ── Campos técnicos (con ayuda visual) ────────────────
        # Campo de upload
        ctk.CTkLabel(scroll, text="Campo de upload *",
                     font=("Segoe UI", 9, "bold"),
                     text_color=T().texto_muted).pack(anchor="w", pady=(6, 0))
        entry_campo_upload = ctk.CTkEntry(
            scroll,
            placeholder_text="Nombre del campo del archivo (ej: config, binary, file)",
            fg_color=T().surface2,
            border_color=T().borde,
            text_color=T().texto)
        entry_campo_upload.pack(fill="x")
        if datos_existentes.get("campo_upload", "") != "":
            entry_campo_upload.insert(0, datos_existentes.get("campo_upload", "config"))
        entradas["campo_upload"] = entry_campo_upload
        self.entry_campo_upload = entry_campo_upload
        ctk.CTkLabel(scroll, text="💡 Se autocompleta al elegir fabricante, pero puedes cambiarlo.",
                     font=("Segoe UI", 8), text_color=T().texto_dim).pack(anchor="w", pady=(0, 4))

        # Ruta de upload
        ctk.CTkLabel(scroll, text="Ruta de upload (opcional)",
                     font=("Segoe UI", 9, "bold"),
                     text_color=T().texto_muted).pack(anchor="w", pady=(6, 0))
        entry_ruta_upload = ctk.CTkEntry(
            scroll,
            placeholder_text="URL de subida (ej: /boaform/formSaveConfig)",
            fg_color=T().surface2,
            border_color=T().borde,
            text_color=T().texto)
        entry_ruta_upload.pack(fill="x")
        if datos_existentes.get("ruta_upload", "") != "":
            entry_ruta_upload.insert(0, datos_existentes.get("ruta_upload", "/"))
        entradas["ruta_upload"] = entry_ruta_upload
        ctk.CTkLabel(scroll, text="💡 Normalmente es / o /cgi-bin/upload. Déjalo vacío para usar /",
                     font=("Segoe UI", 8), text_color=T().texto_dim).pack(anchor="w", pady=(0, 4))

        # Datos extra (NUEVO)
        ctk.CTkLabel(scroll, text="Datos extra (opcional)",
                     font=("Segoe UI", 9, "bold"),
                     text_color=T().texto_muted).pack(anchor="w", pady=(6, 0))
        entry_data_extra = ctk.CTkEntry(
            scroll,
            placeholder_text='Formato: {"submit-url": "/saveconf.asp"}',
            fg_color=T().surface2,
            border_color=T().borde,
            text_color=T().texto)
        entry_data_extra.pack(fill="x")
        # Precargar si existe
        if datos_existentes.get("data_extra"):
            try:
                import json
                entry_data_extra.insert(0, json.dumps(datos_existentes["data_extra"]))
            except:
                pass
        entradas["data_extra"] = entry_data_extra
        ctk.CTkLabel(scroll, text="💡 Ejemplo: {\"submit-url\": \"/saveconf.asp\"}. Solo si la ONU lo requiere.",
                     font=("Segoe UI", 8), text_color=T().texto_dim).pack(anchor="w", pady=(0, 4))

        # Tiempo de reinicio
        ctk.CTkLabel(scroll, text="Tiempo de reinicio (segundos) *",
                     font=("Segoe UI", 9, "bold"),
                     text_color=T().texto_muted).pack(anchor="w", pady=(6, 0))
        entry_tiempo = ctk.CTkEntry(
            scroll,
            placeholder_text="Ej: 60, 90, 120",
            fg_color=T().surface2,
            border_color=T().borde,
            text_color=T().texto)
        entry_tiempo.pack(fill="x")
        if datos_existentes.get("tiempo_reinicio", "") != "":
            entry_tiempo.insert(0, str(datos_existentes.get("tiempo_reinicio", 60)))
        entradas["tiempo_reinicio"] = entry_tiempo
        self.entry_tiempo_reinicio = entry_tiempo

        # Notas
        ctk.CTkLabel(scroll, text="Notas (opcional)",
                     font=("Segoe UI", 9, "bold"),
                     text_color=T().texto_muted).pack(anchor="w", pady=(6, 0))
        entry_notas = ctk.CTkEntry(
            scroll,
            placeholder_text="Información adicional",
            fg_color=T().surface2,
            border_color=T().borde,
            text_color=T().texto)
        entry_notas.pack(fill="x")
        if datos_existentes.get("notas", "") != "":
            entry_notas.insert(0, datos_existentes.get("notas", ""))
        entradas["notas"] = entry_notas

        # ── Selección de archivos ─────────────────────────────
        xml_var = ctk.StringVar()
        if modo == "editar" and datos_existentes.get("firmware_xml"):
            xml_var.set(datos_existentes["firmware_xml"])
        ctk.CTkLabel(scroll, text="",
                     font=("Segoe UI", 9),
                     text_color=T().texto_muted,
                     textvariable=xml_var).pack(anchor="w", pady=(4, 0))
        ctk.CTkButton(scroll, text="📂  Seleccionar XML *" if modo == "nuevo" else "📂  Cambiar XML (opcional)",
                      fg_color=T().surface2, text_color=T().texto_muted,
                      border_width=1, border_color=T().borde,
                      height=32, corner_radius=T().r_btn,
                      command=lambda: self._seleccionar_archivo(xml_var, [("XML", "*.xml")])
                      ).pack(fill="x", pady=(4, 8))

        img_var = ctk.StringVar()
        if modo == "editar" and datos_existentes.get("imagen"):
            img_var.set(datos_existentes["imagen"])
        ctk.CTkLabel(scroll, text="",
                     font=("Segoe UI", 9),
                     text_color=T().texto_muted,
                     textvariable=img_var).pack(anchor="w", pady=(4, 0))
        ctk.CTkButton(scroll, text="🖼  Seleccionar imagen (opcional)",
                      fg_color=T().surface2, text_color=T().texto_muted,
                      border_width=1, border_color=T().borde,
                      height=32, corner_radius=T().r_btn,
                      command=lambda: self._seleccionar_archivo(img_var, [("Imágenes", "*.png *.jpg *.jpeg")])
                      ).pack(fill="x", pady=(4, 8))

        # ── Previsualización de imagen ────────────────────────
        lbl_img_preview = ctk.CTkLabel(scroll, text="", width=100, height=70)
        lbl_img_preview.pack(pady=(4, 8))

        def actualizar_preview(*args):
            ruta = img_var.get()
            if ruta and os.path.exists(ruta):
                try:
                    raw = Image.open(ruta)
                    raw.thumbnail((90, 66), Image.LANCZOS)
                    img = ctk.CTkImage(light_image=raw, dark_image=raw, size=(90, 66))
                    lbl_img_preview.configure(image=img, text="")
                    lbl_img_preview._img_ref = img
                except Exception:
                    lbl_img_preview.configure(image=None, text="⚠️ Imagen no válida")
            else:
                lbl_img_preview.configure(image=None, text="")
        img_var.trace_add("write", actualizar_preview)
        actualizar_preview()

        # ── Botón Guardar ──────────────────────────────────────
        def _guardar():
            # Recoger datos
            if modo == "nuevo":
                mid = entry_id.get().strip()
                if not mid:
                    messagebox.showerror("Error", "El ID del modelo es obligatorio.")
                    return
            else:
                mid = modelo_id

            datos = {}
            for key in entradas:
                if key == "data_extra":
                    valor = entradas[key].get().strip()
                    if valor:
                        try:
                            import json
                            datos[key] = json.loads(valor)
                        except:
                            messagebox.showerror("Error", "Formato de 'Datos extra' inválido. Usa JSON válido.")
                            return
                    else:
                        datos[key] = {}
                else:
                    datos[key] = entradas[key].get().strip()

            datos["fabricante"] = self.combo_fabricante.get()

            # Validar campos obligatorios
            obligatorios = ["ip_fabrica", "usuario_fabrica", "clave_fabrica",
                            "ip_configurada", "usuario_final", "clave_final",
                            "campo_upload", "tiempo_reinicio"]
            faltantes = [k for k in obligatorios if not datos.get(k)]
            if faltantes:
                nombres = {k: k.replace("_", " ").title() for k in faltantes}
                msg = "Campos obligatorios faltantes:\n• " + "\n• ".join(nombres.values())
                messagebox.showerror("Error", msg)
                return

            # Validar XML
            xml_path = xml_var.get()
            if modo == "nuevo":
                if not xml_path or not os.path.exists(xml_path):
                    messagebox.showerror("Error", "Debes seleccionar un archivo XML válido.")
                    return
            else:
                if xml_path and not os.path.exists(xml_path):
                    messagebox.showerror("Error", "La ruta de XML seleccionada no es válida.")
                    return

            # Validar tiempo de reinicio
            try:
                tiempo = int(datos["tiempo_reinicio"])
                if tiempo < 10:
                    messagebox.showerror("Error", "El tiempo de reinicio debe ser al menos 10 segundos.")
                    return
                datos["tiempo_reinicio"] = tiempo
            except ValueError:
                messagebox.showerror("Error", "El tiempo de reinicio debe ser un número entero.")
                return

            # Guardar
            if modo == "nuevo":
                ok = modelos_manager.agregar_modelo(
                    mid, datos, img_var.get(), xml_path)
            else:
                # Fusionar datos existentes
                datos_completos = dict(datos_existentes)
                datos_completos.update(datos)
                ruta_xml_nueva = xml_path if xml_path and xml_path != datos_existentes.get("firmware_xml") else None
                ruta_img_nueva = img_var.get() if img_var.get() and img_var.get() != datos_existentes.get("imagen") else None
                ok = modelos_manager.actualizar_modelo(
                    mid, datos_completos,
                    ruta_xml_src=ruta_xml_nueva,
                    ruta_imagen_src=ruta_img_nueva)

            if ok:
                self.app.modelos = modelos_manager.cargar()
                self._cargar_lista()
                if modo == "nuevo" or ok:
                    self._ver_detalle(mid) if modo == "editar" else None
                v.destroy()
                messagebox.showinfo("Guardado", f"Modelo '{mid}' {'actualizado' if modo == 'editar' else 'agregado'} correctamente.")
            else:
                messagebox.showerror("Error", f"No se pudo {'actualizar' if modo == 'editar' else 'agregar'} el modelo. Revisa la consola.")

        ctk.CTkButton(v, text="💾  Guardar modelo" if modo == "nuevo" else "💾  Guardar cambios",
                      fg_color=T().verde, text_color="#ffffff",
                      height=44, corner_radius=T().r_btn,
                      font=("Segoe UI", 13, "bold"),
                      command=_guardar).pack(pady=10)

    # ──────────────────────────────────────────────────────────
    #  AUTOCOMPLETADO
    # ──────────────────────────────────────────────────────────
    def _autocompletar_campos(self, fabricante_seleccionado):
        for prefijo, info in onu_database.FABRICANTES_DB.items():
            if info["nombre"] == fabricante_seleccionado:
                if hasattr(self, 'entry_campo_upload'):
                    self.entry_campo_upload.delete(0, "end")
                    self.entry_campo_upload.insert(0, info.get("campo_upload", "config"))
                if hasattr(self, 'entry_tiempo_reinicio'):
                    self.entry_tiempo_reinicio.delete(0, "end")
                    self.entry_tiempo_reinicio.insert(0, str(info.get("tiempo_reinicio", 60)))
                break

    # ──────────────────────────────────────────────────────────
    #  UTILIDAD
    # ──────────────────────────────────────────────────────────
    def _seleccionar_archivo(self, var, filetypes):
        ruta = filedialog.askopenfilename(title="Seleccionar archivo",
                                          filetypes=filetypes)
        if ruta:
            var.set(ruta)