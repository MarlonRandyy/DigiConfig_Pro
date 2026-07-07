# ============================================================
# pantalla_guia.py - Manual interactivo de DigiConfig Pro
# DigiConfig Pro v2.0 - Guía profesional para el usuario final
# ============================================================

import customtkinter as ctk

class PantallaGuia(ctk.CTkScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._configurar_estilos()
        self._construir_ui()

    def _configurar_estilos(self):
        # Detectar modo oscuro/claro desde la app
        modo_oscuro = self.app._modo_oscuro if hasattr(self.app, '_modo_oscuro') else True
        self.color_bg_card = "#1e293b" if modo_oscuro else "#f8fafc"
        self.color_borde = "#334155" if modo_oscuro else "#e2e8f0"
        self.color_acento = "#3b82f6"
        self.color_exito = "#10b981"
        self.color_advertencia = "#f59e0b"
        self.color_texto = "white" if modo_oscuro else "black"
        self.font_h1 = ("Segoe UI", 28, "bold")
        self.font_h2 = ("Segoe UI", 20, "bold")
        self.font_h3 = ("Segoe UI", 16, "bold")
        self.font_body = ("Segoe UI", 13)
        self.font_code = ("Consolas", 12)

    def _construir_ui(self):
        # --- Encabezado principal ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 10))
        ctk.CTkLabel(header, text="📘 DigiConfig Pro - Manual del Usuario", font=self.font_h1, text_color=self.color_acento).pack(anchor="w")
        ctk.CTkLabel(header, text="Aprovisionamiento inteligente y gestión de inventario en la nube", font=self.font_body, text_color="#94a3b8").pack(anchor="w")

        # --- Secciones ---
        self._seccion_que_es()
        self._seccion_funcionalidades()
        self._seccion_instalacion()
        self._seccion_conexion_google()
        self._seccion_escaneo()
        self._seccion_configurar_onu()      # <--- NUEVA SECCIÓN DETALLADA
        self._seccion_solucion_problemas()

        # Footer
        ctk.CTkLabel(self, text="© Digicable - Soporte Técnico | Versión 2.0", font=("Segoe UI", 10), text_color="gray").pack(pady=30)

    # ------------------------------------------------------------------
    #  SECCIONES INFORMATIVAS
    # ------------------------------------------------------------------
    def _seccion_que_es(self):
        card = self._crear_tarjeta("🚀 ¿Qué es DigiConfig Pro?", self.color_acento)
        texto = (
            "DigiConfig Pro es una herramienta de escritorio diseñada para técnicos de campo que necesitan:\n\n"
            "• **Configurar ONUs automáticamente** (Huawei, ZTE, FiberHome, BT-PON, V-SOL, etc.)\n"
            "• **Registrar inventario** escaneando códigos de barras o QR, sincronizando al instante con Google Sheets.\n"
            "• **Trabajar con cualquier hoja de cálculo existente** (sin afectar las 110+ hojas que ya tienes).\n"
            "• **Operar sin conexión** y sincronizar después (opcional).\n\n"
            "El software es portable, no requiere instalación compleja y funciona con cualquier cámara USB o integrada."
        )
        ctk.CTkLabel(card, text=texto, font=self.font_body, justify="left", wraplength=750).pack(anchor="w", padx=20, pady=10)

    def _seccion_funcionalidades(self):
        card = self._crear_tarjeta("⚙️ Funcionalidades principales", self.color_exito)
        funcs = [
            ("📷 Escáner inteligente", "Detecta códigos CODE128, QR y DataMatrix. Extrae automáticamente MAC y Serial Number de etiquetas únicas o dobles."),
            ("☁️ Sincronización con Google Sheets", "Envía los datos a una hoja de cálculo en la nube. Soporta celdas de inicio personalizables (B2, A1, etc.) y límite de registros por hoja."),
            ("🔄 Buffer de dos etiquetas", "Para equipos V-SOL o ZTE que tienen MAC y SN separados, el programa los combina automáticamente."),
            ("📊 Gestión de lotes", "Crea nuevas hojas automáticamente al alcanzar el límite configurado (100, 200 o el valor que elijas)."),
            ("🔧 Configuración persistente", "Guarda el ID del Sheet, la celda de inicio, el índice de cámara y el límite de lote. La conexión se mantiene activa."),
            ("📝 Edición manual", "Si un código se lee mal, puedes editar el dato directamente en la tabla antes de enviarlo a la nube.")
        ]
        for titulo, desc in funcs:
            f = ctk.CTkFrame(card, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=8)
            ctk.CTkLabel(f, text=titulo, font=self.font_h3, text_color=self.color_exito).pack(anchor="w")
            ctk.CTkLabel(f, text=desc, font=self.font_body, wraplength=700, justify="left").pack(anchor="w", padx=10)

    def _seccion_instalacion(self):
        card = self._crear_tarjeta("💻 Instalación y dependencias", self.color_advertencia)
        instruccion = (
            "1. Asegúrate de tener Python 3.11 o superior instalado.\n"
            "2. Abre una terminal en la carpeta del proyecto (DigiConfig_Pro).\n"
            "3. Ejecuta el siguiente comando para instalar todas las librerías necesarias:\n"
        )
        ctk.CTkLabel(card, text=instruccion, font=self.font_body, justify="left").pack(anchor="w", padx=20, pady=(10, 5))
        # Cuadro de código
        code_frame = ctk.CTkFrame(card, fg_color="#0f172a", corner_radius=8)
        code_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(code_frame, text="pip install -r requirements.txt", font=self.font_code, text_color="#60a5fa").pack(pady=8)
        ctk.CTkLabel(card, text="4. Una vez instalado, ejecuta el programa con: python main.py", font=self.font_body).pack(anchor="w", padx=20, pady=(5, 10))

    def _seccion_conexion_google(self):
        card = self._crear_tarjeta("☁️ Conexión a Google Sheets (Paso a paso)", self.color_acento)
        ctk.CTkLabel(card, text="Sigue estos pasos exactamente para que DigiConfig Pro pueda escribir en tu hoja de cálculo.", 
                     font=self.font_body, wraplength=720).pack(anchor="w", padx=20, pady=(10, 5))

        self._agregar_paso(card, "1. Crear proyecto en Google Cloud Console", 
                           "• Ve a console.cloud.google.com, crea un nuevo proyecto (ej. 'DigiConfig-Escaneo').\n"
                           "• Habilita las APIs: Google Sheets API y Google Drive API (botón 'Enable').\n"
                           "• Ve a 'Credentials' → '+ CREATE CREDENTIALS' → 'Service Account'.\n"
                           "• Dale un nombre (ej. 'escanner-bot') y haz clic en 'Create and Continue' → 'Done'.")

        self._agregar_paso(card, "2. Descargar la llave JSON", 
                           "• En 'Credentials', haz clic en el lápiz de la cuenta de servicio recién creada.\n"
                           "• Ve a la pestaña 'KEYS' → 'ADD KEY' → 'Create new key' → 'JSON'.\n"
                           "• Se descargará un archivo .json. **Copia ese archivo dentro de la carpeta 'DigiConfig_Pro'**.")

        self._agregar_paso(card, "3. El paso crítico: compartir la hoja", 
                           "• Abre el archivo .json con el bloc de notas y busca la línea 'client_email'.\n"
                           "• Copia el correo electrónico (ej. escanner-bot@...iam.gserviceaccount.com).\n"
                           "• Abre tu Google Sheet (el que quieras usar) → botón 'Compartir'.\n"
                           "• Pega el correo, asigna rol 'Editor' y envía la invitación.")

        self._agregar_paso(card, "4. Obtener y pegar el ID de la hoja", 
                           "• En tu navegador, mira la URL de tu Google Sheet.\n"
                           "• El ID es el código largo entre '/d/' y '/edit'.\n"
                           "• Ejemplo: docs.google.com/spreadsheets/d/1zA2bB3cC4dD5eE/edit → ID = '1zA2bB3cC4dD5eE'.\n"
                           "• En DigiConfig Pro, ve a la pantalla de Escaneo → 'AJUSTES' → pega el ID en el campo correspondiente.")

        self._agregar_paso(card, "5. Verificar la conexión", 
                           "• Haz clic en 'APLICAR Y CONECTAR'. El estado cambiará a 'Conectado'.\n"
                           "• Escribe un membrete de prueba (ej. PRUEBA_INICIAL), inicia la cámara y escanea cualquier código.\n"
                           "• Revisa tu Google Sheet: debe aparecer una nueva fila con los datos.\n"
                           "¡Listo! Tu inventario ahora se sincroniza automáticamente.")

    def _seccion_escaneo(self):
        card = self._crear_tarjeta("📷 Uso del escáner y provisionamiento", self.color_exito)
        texto = (
            "**Escaneo de ONUs:**\n"
            "• Conecta tu cámara (integrada o USB) y haz clic en 'INICIAR ESCÁNER'.\n"
            "• Acerca el código de barras o QR de la ONU al objetivo. El programa detectará automáticamente la MAC y el SN.\n"
            "• Si el equipo tiene MAC y SN en etiquetas separadas (ej. V-SOL), el sistema las combinará en un buffer de 5 segundos.\n\n"
            "**Consejos para el escaneo:**\n"
            "• Si un código no se lee, limpia el lente de la cámara o mejora la iluminación.\n"
            "• Puedes editar manualmente cualquier dato en la tabla de resultados antes de enviarlo a la nube.\n\n"
            "📌 **Para la configuración automática de ONUs, consulta la sección específica a continuación.**"
        )
        ctk.CTkLabel(card, text=texto, font=self.font_body, justify="left", wraplength=750).pack(anchor="w", padx=20, pady=10)

    # ────────────────────────────────────────────────────────────────
    #  NUEVA SECCIÓN: CONFIGURAR ONU (DETALLADA)
    # ────────────────────────────────────────────────────────────────
    def _seccion_configurar_onu(self):
        card = self._crear_tarjeta("🛠️ Configuración automática de ONUs (Paso a paso)", self.color_acento)
        
        intro = (
            "Esta sección te guía en el proceso de **configuración automática de una ONU** mediante la subida de un archivo XML de configuración corporativa.\n\n"
            "El programa se encarga de:\n"
            "• **Conectarse a la ONU** usando sus credenciales de fábrica.\n"
            "• **Subir el archivo XML** correspondiente al modelo.\n"
            "• **Esperar el reinicio** de la ONU (tiempo configurable).\n"
            "• **Verificar que la ONU** haya tomado la nueva configuración (IP, usuario y clave final).\n\n"
            "Para que el proceso sea exitoso, necesitas tener registrado previamente el modelo de ONU en la pantalla **Modelos XML**.\n"
        )
        ctk.CTkLabel(card, text=intro, font=self.font_body, wraplength=750, justify="left").pack(anchor="w", padx=20, pady=10)

        # ---- Pasos detallados ----
        self._agregar_paso(card, "Paso 1: Conectar la ONU físicamente",
                           "• Conecta la ONU a la corriente eléctrica.\n"
                           "• Conecta un cable Ethernet desde tu PC al puerto LAN de la ONU.\n"
                           "• Espera aproximadamente 2 minutos a que la ONU arranque completamente.\n"
                           "• Verifica que el LED de enlace (LINK/ACT) esté encendido o parpadeando.")

        self._agregar_paso(card, "Paso 2: Detectar la ONU en el Dashboard",
                           "• Abre DigiConfig Pro y ve a la pantalla **Dashboard**.\n"
                           "• La ONU debería aparecer automáticamente con el LED verde y el mensaje 'ONU DETECTADA'.\n"
                           "• Si no aparece, haz clic en el botón **'Buscar ONU manualmente'**.\n"
                           "• Si aún no aparece, revisa la conexión de red y la IP de tu PC (debe estar en la misma subred que la ONU).")

        self._agregar_paso(card, "Paso 3: Seleccionar el modelo en Configurar ONU",
                           "• Ve a la pantalla **Configurar ONU** (desde el menú lateral o usando el botón del Dashboard).\n"
                           "• En el desplegable **Modelo**, selecciona el modelo que has registrado previamente (ej. 'BT-191XR').\n"
                           "• Verifica que la información mostrada (fabricante, campo de upload, ruta de upload, tiempo de reinicio) sea correcta.\n"
                           "• Si el archivo XML no aparece, usa el botón **'Examinar...'** para seleccionarlo manualmente.")

        self._agregar_paso(card, "Paso 4: Ejecutar la instalación",
                           "• Haz clic en el botón **'▶ Iniciar instalación'**.\n"
                           "• Aparecerá un cuadro de confirmación con los datos de la ONU (MAC, IP de fábrica, IP final).\n"
                           "• Confirma la instalación y el proceso comenzará.\n"
                           "• La barra de progreso avanzará y verás en la consola los pasos:\n"
                           "  - Verificación del XML\n"
                           "  - Login en la ONU\n"
                           "  - Subida del archivo\n"
                           "  - Espera de reinicio\n"
                           "  - Verificación final")

        self._agregar_paso(card, "Paso 5: Verificar la instalación",
                           "• Si todo es correcto, verás un mensaje de **'✅ Instalación completada exitosamente'**.\n"
                           "• También recibirás una notificación en pantalla con la IP final y la clave de acceso.\n"
                           "• Puedes verificar en tu navegador accediendo a la nueva IP (ej. http://192.168.100.1) con las credenciales finales.\n"
                           "• El registro quedará guardado en el **Historial** para futuras consultas.")

        # ---- Parámetros importantes ----
        ctk.CTkLabel(card, text="⚙️ Parámetros clave que debes conocer", font=self.font_h3, text_color=self.color_advertencia).pack(anchor="w", padx=20, pady=(15, 5))
        
        param_texto = (
            "Para que la instalación funcione con cada modelo, es necesario que al registrar el modelo en **Modelos XML** indiques correctamente estos valores:\n\n"
            "• **Campo de upload**: es el nombre del campo de archivo en el formulario de la ONU (ej. 'config', 'binary', 'file').\n"
            "• **Ruta de upload**: es la URL donde se envía el formulario (ej. '/cgi-bin/upload' o '/boaform/formSaveConfig').\n"
            "• **Datos extra**: campos ocultos adicionales que la ONU exige (ej. '{\"submit-url\": \"/saveconf.asp\"}').\n\n"
            "💡 **¿Cómo obtener estos valores?**\n"
            "• Abre la interfaz web de la ONU en tu navegador (ej. http://192.168.1.1).\n"
            "• Busca la sección de 'Restore Configuration' o 'Upload'.\n"
            "• Inspecciona el formulario (F12) y anota el atributo **action** del <form> y el **name** del <input type='file'>.\n"
            "• Revisa si hay campos ocultos (<input type='hidden'>) que también deben ser enviados.\n\n"
            "Con esos datos, registra el modelo correctamente y la instalación funcionará sin problemas."
        )
        ctk.CTkLabel(card, text=param_texto, font=self.font_body, wraplength=750, justify="left").pack(anchor="w", padx=20, pady=10)

        # ---- Errores comunes y soluciones ----
        ctk.CTkLabel(card, text="❌ Errores comunes en la configuración y cómo solucionarlos", font=self.font_h3, text_color=self.color_advertencia).pack(anchor="w", padx=20, pady=(15, 5))
        
        errores = [
            ("Login fallido", 
             "• Verifica que las credenciales de fábrica (usuario/clave) en el modelo sean correctas.\n"
             "• Asegúrate de que la IP de fábrica sea la correcta.\n"
             "• Si la ONU tiene CAPTCHA, la instalación automática no es posible (usa la interfaz web manualmente)."),
            ("Subida del XML falla", 
             "• Comprueba que el **Campo de upload** y la **Ruta de upload** sean los correctos para ese modelo.\n"
             "• Revisa si la ONU requiere campos ocultos adicionales (Datos extra) y agrégalos al modelo.\n"
             "• El archivo XML debe ser válido y no estar vacío."),
            ("Verificación final falla", 
             "• La IP final configurada no está en la misma subred que tu PC. Asegúrate de que tu PC tenga una IP en esa subred.\n"
             "• El tiempo de reinicio puede ser insuficiente; auméntalo en el modelo registrado.\n"
             "• La ONU puede no haber terminado de reiniciar; espera más tiempo y vuelve a intentar."),
            ("La ONU no se detecta en el Dashboard", 
             "• Revisa el cable Ethernet y la conexión física.\n"
             "• Desactiva el WiFi para evitar conflictos de ruta.\n"
             "• Asegúrate de que la IP de tu PC esté en la misma subred que la ONU (ej. 192.168.1.x).\n"
             "• Si la ONU usa otra IP de fábrica (ej. 192.168.0.1), actualiza el modelo con esa IP."),
            ("El modelo registrado desaparece al reiniciar el programa", 
             "• Esto ocurre si el archivo 'modelos.json' no se puede guardar (permisos).\n"
             "• Asegúrate de que la carpeta del programa tenga permisos de escritura.\n"
             "• En la nueva versión, los modelos se guardan en 'configs/modelos.json' (carpeta con permisos).")
        ]
        for err, sol in errores:
            f = ctk.CTkFrame(card, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=8)
            ctk.CTkLabel(f, text=f"• {err}", font=self.font_h3, text_color=self.color_advertencia).pack(anchor="w")
            ctk.CTkLabel(f, text=sol, font=self.font_body, wraplength=700, justify="left").pack(anchor="w", padx=15)

    # ------------------------------------------------------------------
    #  SOLUCIÓN DE PROBLEMAS COMUNES (GENERAL)
    # ------------------------------------------------------------------
    def _seccion_solucion_problemas(self):
        card = self._crear_tarjeta("⚠️ Solución de problemas generales", self.color_advertencia)
        problemas = [
            ("La cámara no se abre", "Cierra otras aplicaciones (Teams, Zoom, Cámara de Windows). Reinicia el programa. Si persiste, cambia el índice de cámara en Ajustes."),
            ("Error 403 al conectar a Sheets", "No compartiste la hoja con el correo del JSON. Revisa el paso 3 de la conexión a Google Sheets."),
            ("El escáner no lee códigos", "Verifica que la etiqueta esté bien iluminada y que el código no esté dañado. Prueba con otro tipo de código (QR vs CODE128)."),
            ("Se escribe en la hoja incorrecta", "Asegúrate de que la celda de inicio (ej. B2) sea la correcta. Si usas muchas hojas, el programa trabaja sobre la última hoja del libro."),
            ("El programa se congela", "Actualiza las librerías: pip install --upgrade opencv-python pyzbar customtkinter. También reduce la resolución en la configuración de cámara.")
        ]
        for titulo, sol in problemas:
            f = ctk.CTkFrame(card, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=8)
            ctk.CTkLabel(f, text=f"• {titulo}", font=self.font_h3, text_color=self.color_advertencia).pack(anchor="w")
            ctk.CTkLabel(f, text=sol, font=self.font_body, wraplength=700, justify="left").pack(anchor="w", padx=15)

    # ------------------------------------------------------------------
    #  MÉTODOS AUXILIARES DE UI
    # ------------------------------------------------------------------
    def _crear_tarjeta(self, titulo, color):
        frame = ctk.CTkFrame(self, fg_color=self.color_bg_card, border_width=1, border_color=self.color_borde, corner_radius=15)
        frame.pack(fill="x", padx=40, pady=12)
        lbl = ctk.CTkLabel(frame, text=titulo, font=self.font_h2, text_color=color)
        lbl.pack(anchor="w", padx=20, pady=(15, 5))
        return frame

    def _agregar_paso(self, parent, titulo, contenido):
        step_frame = ctk.CTkFrame(parent, fg_color="transparent")
        step_frame.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(step_frame, text=titulo, font=self.font_h3, text_color=self.color_acento).pack(anchor="w")
        ctk.CTkLabel(step_frame, text=contenido, font=self.font_body, wraplength=700, justify="left").pack(anchor="w", padx=10)