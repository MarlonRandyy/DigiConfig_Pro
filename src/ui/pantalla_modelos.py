# ============================================================
# pantalla_modelos.py — Gestión modelos XML (nuevo estilo)
# ============================================================
import customtkinter as ctk
import os
from tkinter import filedialog, messagebox

import src.ui.tema as tema_mod
from src.core import modelos_manager


def T(): return tema_mod.Tema


class PantallaModelos(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T().bg, corner_radius=0)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Layout: lista izquierda | detalle derecha
        main = ctk.CTkFrame(self, fg_color=T().bg)
        main.pack(fill="both", expand=True, padx=22, pady=18)

        # ── Lista izquierda ───────────────────────────────────
        left = ctk.CTkFrame(main, fg_color=T().surface,
                             corner_radius=T().r_card,
                             border_width=1, border_color=T().borde,
                             width=260)
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

        # ── Detalle derecha ───────────────────────────────────
        self.panel = ctk.CTkFrame(main, fg_color=T().surface,
                                   corner_radius=T().r_card,
                                   border_width=1, border_color=T().borde)
        self.panel.pack(side="left", fill="both", expand=True)

        self._cargar_lista()

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

    def _ver_detalle(self, mid: str):
        for w in self.panel.winfo_children():
            w.destroy()
        datos = modelos_manager.obtener(mid)
        if not datos:
            return

        # Franja accent
        ctk.CTkFrame(self.panel, height=3,
                     fg_color=T().accent, corner_radius=0).pack(fill="x")

        ctk.CTkLabel(self.panel,
                     text=datos.get("nombre_display", mid),
                     font=("Segoe UI", 16, "bold"),
                     text_color=T().accent).pack(
            anchor="w", padx=20, pady=(16, 4))
        ctk.CTkLabel(self.panel,
                     text=f"ID: {mid}",
                     font=("Consolas", 10),
                     text_color=T().texto_dim).pack(anchor="w", padx=20)

        ctk.CTkFrame(self.panel, height=1, fg_color=T().borde,
                     corner_radius=0).pack(fill="x", padx=20, pady=12)

        campos = [
            ("Fabricante",     datos.get("fabricante","")),
            ("IP de fábrica",  datos.get("ip_fabrica","")),
            ("IP configurada", datos.get("ip_configurada","")),
            ("Usuario fábrica",datos.get("usuario_fabrica","")),
            ("Clave fábrica",  datos.get("clave_fabrica","")),
            ("Usuario final",  datos.get("usuario_final","")),
            ("Clave final",    datos.get("clave_final","")),
            ("XML",            datos.get("firmware_xml","")),
            ("Notas",          datos.get("notas","")),
        ]
        for lbl, val in campos:
            f = ctk.CTkFrame(self.panel, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(f, text=f"{lbl}:",
                         font=("Segoe UI", 10, "bold"),
                         text_color=T().texto_muted,
                         width=130).pack(side="left")
            ctk.CTkLabel(f, text=val or "—",
                         font=("Segoe UI", 11),
                         text_color=T().texto).pack(side="left")

        ctk.CTkFrame(self.panel, height=1, fg_color=T().borde,
                     corner_radius=0).pack(fill="x", padx=20, pady=12)

        btns = ctk.CTkFrame(self.panel, fg_color="transparent")
        btns.pack(fill="x", padx=20)
        ctk.CTkButton(
            btns, text="✏  Editar XML",
            fg_color=T().accent, hover_color=T().accent_hover,
            text_color="#ffffff",
            height=36, corner_radius=T().r_btn,
            font=("Segoe UI", 11, "bold"),
            command=lambda: self._editar_xml(datos.get("firmware_xml",""))
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

    def _editar_xml(self, ruta: str):
        if not ruta or not os.path.exists(ruta):
            messagebox.showwarning("Editor XML",
                                   f"Archivo no encontrado:\n{ruta}")
            return
        v = ctk.CTkToplevel(self)
        v.title(f"Editor — {os.path.basename(ruta)}")
        v.geometry("720x520")
        v.configure(fg_color=T().surface)

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
                f.write(txt.get("1.0","end"))
            messagebox.showinfo("Guardado", "XML guardado correctamente.")
        ctk.CTkButton(v, text="💾  Guardar",
                      fg_color=T().verde, text_color="#ffffff",
                      height=36, corner_radius=T().r_btn,
                      command=_save).pack(pady=(0, 10))

    def _eliminar(self, mid: str):
        if messagebox.askyesno("Eliminar", f"¿Eliminar '{mid}'?"):
            modelos_manager.eliminar_modelo(mid)
            self.app.modelos = modelos_manager.cargar()
            self._cargar_lista()
            for w in self.panel.winfo_children():
                w.destroy()

    def _form_nuevo(self):
        v = ctk.CTkToplevel(self)
        v.title("Agregar modelo")
        v.geometry("520x540")
        v.configure(fg_color=T().surface)
        v.resizable(False, False)

        scroll = ctk.CTkScrollableFrame(v, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=10)

        campos = [
            ("modelo_id",        "ID único, ej: VSOL-V2802"),
            ("nombre_display",   "Nombre para mostrar"),
            ("fabricante",       "Fabricante"),
            ("ip_fabrica",       "IP de fábrica (ej: 192.168.1.1)"),
            ("ip_configurada",   "IP configurada (ej: 192.168.100.1)"),
            ("usuario_fabrica",  "Usuario fábrica"),
            ("clave_fabrica",    "Clave fábrica"),
            ("usuario_final",    "Usuario final"),
            ("clave_final",      "Clave final (ej: digicable19)"),
            ("notas",            "Notas adicionales"),
        ]
        entradas = {}
        for key, ph in campos:
            ctk.CTkLabel(scroll, text=key,
                         font=("Segoe UI", 9, "bold"),
                         text_color=T().texto_muted).pack(
                anchor="w", pady=(6, 0))
            e = ctk.CTkEntry(scroll, placeholder_text=ph,
                             fg_color=T().surface2,
                             border_color=T().borde,
                             text_color=T().texto)
            e.pack(fill="x")
            entradas[key] = e

        xml_var = ctk.StringVar()
        img_var = ctk.StringVar()

        ctk.CTkButton(scroll, text="📂  Seleccionar XML",
                      fg_color=T().surface2, text_color=T().texto_muted,
                      border_width=1, border_color=T().borde,
                      height=32, corner_radius=T().r_btn,
                      command=lambda: xml_var.set(
                          filedialog.askopenfilename(
                              filetypes=[("XML","*.xml")]) or xml_var.get())
                      ).pack(fill="x", pady=(8, 2))
        ctk.CTkButton(scroll, text="🖼  Seleccionar imagen",
                      fg_color=T().surface2, text_color=T().texto_muted,
                      border_width=1, border_color=T().borde,
                      height=32, corner_radius=T().r_btn,
                      command=lambda: img_var.set(
                          filedialog.askopenfilename(
                              filetypes=[("Images","*.png *.jpg *.jpeg")]) or img_var.get())
                      ).pack(fill="x", pady=2)

        def _guardar():
            mid = entradas["modelo_id"].get().strip()
            if not mid:
                messagebox.showerror("Error", "El ID es obligatorio.")
                return
            datos = {k: entradas[k].get().strip()
                     for k in entradas if k != "modelo_id"}
            ok = modelos_manager.agregar_modelo(
                mid, datos, img_var.get(), xml_var.get())
            if ok:
                self.app.modelos = modelos_manager.cargar()
                self._cargar_lista()
                v.destroy()
                messagebox.showinfo("Guardado",
                                    f"Modelo '{mid}' agregado.")
            else:
                messagebox.showerror("Error",
                                     f"El ID '{mid}' ya existe.")

        ctk.CTkButton(v, text="💾  Guardar modelo",
                      fg_color=T().verde, text_color="#ffffff",
                      height=40, corner_radius=T().r_btn,
                      font=("Segoe UI", 12, "bold"),
                      command=_guardar).pack(pady=10)
