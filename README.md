================================================================================
                    DIGICONFIG PRO – MANUAL DE USUARIO
                          Versión 1.0 (Junio 2026)
              Desarrollado para: Digicable | Soporte Técnico
================================================================================

ÍNDICE
-------
1.  INTRODUCCIÓN
2.  REQUISITOS DEL SISTEMA
3.  INSTALACIÓN Y PRIMER INICIO
4.  CONFIGURACIÓN DE GOOGLE SHEETS (PASO A PASO)
5.  FLUJO DE TRABAJO DEL TÉCNICO
6.  ADAPTACIÓN A OTROS MODELOS DE ONU (GUÍA TÉCNICA)
7.  MEJORAS FUTURAS Y EXTENSIONES
8.  SOLUCIÓN DE PROBLEMAS COMUNES
9.  CONTACTO Y SOPORTE


================================================================================
1. INTRODUCCIÓN
================================================================================
DigiConfig Pro es una herramienta de escritorio diseñada para automatizar el
aprovisionamiento de ONUs (Unidades de Red Óptica) y la gestión de inventario en
redes de telecomunicaciones.

1.1 ¿Qué hace DigiConfig Pro?
    - Provisionamiento automático: Inyecta archivos de configuración XML en
      ONUs de múltiples fabricantes (Huawei, ZTE, FiberHome, BT-PON, VSOL, etc.)
      a través de HTTP.
    - Detección inteligente: Escanea la red local y reconoce equipos conectados
      por su contenido HTML (sin necesidad de SN si no está visible).
    - Escáner de códigos: Registra inventario en tiempo real sincronizando con
      Google Sheets (QR / Código de barras).
    - Gestor de modelos: Permite registrar nuevos modelos con sus propias
      credenciales, parámetros de subida y archivos XML.
    - Historial completo: Guarda cada instalación con fecha, MAC, SN, resultado
      y tiempo de ejecución.

1.2 Estructura del Programa (Pantallas)
    - Dashboard: Muestra la ONU detectada y KPIs de instalaciones.
    - Configurar ONU: Seleccionar modelo y ejecutar la instalación.
    - Modelos XML: Crear, editar o eliminar modelos de ONU.
    - Historial: Consultar y exportar registros de instalaciones.
    - Escanear ONU: Leer códigos de barras / QR y enviarlos a Google Sheets.
    - Guía de Usuario: Manual interactivo incluido dentro de la app.


================================================================================
2. REQUISITOS DEL SISTEMA
================================================================================
- Sistema operativo: Windows 10/11 (64 bits).
- Python: 3.11 o superior (recomendado desde python.org).
- Cámara: Webcam USB o integrada (para escaneo).
- Conexión a Internet: Para sincronizar con Google Sheets.
- Permisos de administrador: Para instalar dependencias y configurar la red.

2.1 Dependencias (pip)
Instala todas las librerías necesarias con:
    pip install -r requirements.txt

El archivo requirements.txt incluye:
    customtkinter     -> Interfaz gráfica moderna.
    opencv-python     -> Captura de cámara.
    pyzbar            -> Decodificación de códigos de barras.
    gspread           -> Conexión con Google Sheets API.
    google-auth       -> Autenticación con Google Cloud.
    beautifulsoup4    -> Parsing de HTML.
    lxml              -> Parser de HTML/XML.
    Pillow            -> Manejo de imágenes.
    requests          -> Peticiones HTTP.


================================================================================
3. INSTALACIÓN Y PRIMER INICIO
================================================================================
3.1 Obtener el código
    - Descarga el proyecto "DigiConfig_Pro" en tu PC.
    - Asegúrate de mantener la estructura de carpetas:

    DigiConfig_Pro/
    ├── main.py
    ├── modelos.json
    ├── configs/
    │   ├── firmwares/      -> Archivos XML de configuración
    │   └── imagenes/       -> Imágenes de los modelos
    ├── assets/             -> Logos e iconos
    └── src/                -> Código fuente
        ├── core/           -> Lógica principal (detector, instalador, etc.)
        ├── ui/             -> Pantallas de la interfaz
        └── utils/          -> Utilidades (config_manager, notificaciones)

3.2 Ejecutar el programa
    1. Abre una terminal en la raíz del proyecto.
    2. Instala las dependencias:
        pip install -r requirements.txt
    3. Ejecuta:
        python main.py
    4. La ventana principal de DigiConfig Pro se abrirá.

3.3 Compilar a ejecutable (.exe)
    Para distribuir sin necesidad de Python, usa auto-py-to-exe:
    1. Instalar: pip install auto-py-to-exe
    2. Ejecutar: python -m auto_py_to_exe
    3. Configurar:
        - Script Location: main.py.
        - One File: "One Directory" (más estable para OpenCV y pyzbar).
        - Window Based: Desmarcar (primera prueba con consola visible).
        - Additional Files: Añadir las carpetas: src, assets, configs.
        - Advanced -> --hidden-import:
            customtkinter, PIL, cv2, pyzbar, gspread, google, bs4, lxml
        - Advanced -> --collect-all:
            cv2 pyzbar PIL bs4 lxml gspread google customtkinter
        - Advanced -> --name: DigiConfig_PRO
    4. Haz clic en "Convert .py to .exe".
    5. El ejecutable estará en output/DigiConfig_PRO/.


================================================================================
4. CONFIGURACIÓN DE GOOGLE SHEETS (PASO A PASO)
================================================================================
Sigue estos pasos UNA SOLA VEZ para vincular el escáner de inventario con
Google Sheets.

PASO 1 – Crear la "Identidad Digital" en Google Cloud Console
-------------------------------------------------------------
1. Entra en console.cloud.google.com.
2. Crea un nuevo proyecto (ej. "DigiConfig-Escaneo").
3. Habilita las APIs: "Google Sheets API" y "Google Drive API" (botón Enable).
4. Ve a APIs & Services > Credentials.
5. Haz clic en + CREATE CREDENTIALS > Service Account.
6. Ponle nombre (ej. "escanner-bot"), haz clic en Create y Done.

PASO 2 – Descargar la "Llave" (Archivo JSON)
---------------------------------------------
1. En la misma pantalla, haz clic en el lápiz de la cuenta de servicio.
2. Ve a la pestaña KEYS.
3. Haz clic en ADD KEY > Create new key.
4. Selecciona JSON y haz clic en Create.
5. ¡IMPORTANTE! Se descargará un archivo .json. Cópialo y pégalo dentro de la
   carpeta de tu proyecto (DigiConfig_Pro/).

PASO 3 – El Paso "Maestro" (Compartir el acceso)
-------------------------------------------------
1. Abre el archivo .json con el Bloc de Notas.
2. Busca la línea "client_email". Copia el correo (ej.
   escanner-bot@digiconfig-xxxx.iam.gserviceaccount.com).
3. Abre tu Google Sheet (el que creaste) y haz clic en "Compartir".
4. Pega el correo, asegúrate de que esté en modo "Editor" y dale a Enviar.

PASO 4 – Vincular el ID en el Programa
---------------------------------------
1. Mira la URL de tu Google Sheet. Ejemplo:
   docs.google.com/spreadsheets/d/1zA2bB3cC4dD5eE/edit
   -> ID = "1zA2bB3cC4dD5eE".
2. En DigiConfig Pro, ve a Escaneo -> Ajustes (⚙️).
3. Pega el ID en "Google Sheet ID" y selecciona el archivo JSON.

PASO 5 – La Prueba de Fuego
----------------------------
1. Ve a la pantalla de Escaneo.
2. Escribe un membrete (ej. PRUEBA_INICIAL).
3. Inicia la cámara y escanea cualquier código.
4. Si dice "Sincronizado" y aparece en el Sheet, ¡está listo!


================================================================================
5. FLUJO DE TRABAJO DEL TÉCNICO
================================================================================
5.1 Dashboard – Detección de ONU
    - Conecta la ONU a tu PC mediante cable Ethernet.
    - Espera a que el programa muestre el LED verde y "ONU DETECTADA".
    - Si no se detecta, usa el botón "Buscar ONU manualmente".

5.2 Registrar un modelo nuevo
    - Ve a "Modelos XML" -> "+ Nuevo".
    - Llena los campos obligatorios:
        - ID único (ej. BT-191XR).
        - Nombre para mostrar.
        - Fabricante.
        - IP de fábrica (ej. 192.168.1.1).
        - IP configurada (ej. 192.168.100.1).
        - Usuario fábrica y Clave fábrica.
        - Usuario final y Clave final.
        - Campo de upload (nombre del campo de archivo en el HTML).
        - Tiempo de reinicio (segundos).
        - Archivo XML.
    - Guarda el modelo.

5.3 Configurar una ONU
    - En Dashboard, haz clic en "Configurar ONU".
    - Verifica que el modelo y el XML sean los correctos.
    - Haz clic en "Iniciar instalación".
    - La barra de progreso muestra:
        10% -> Verificando XML.
        25% -> Login exitoso.
        50% -> XML subido correctamente.
        85% -> Esperando reinicio.
        100% -> Verificación exitosa en IP final.

5.4 Escaneo de inventario
    - Ve a "Escanear ONU".
    - Haz clic en "Iniciar escáner".
    - Apunta la cámara al código de barras/QR.
    - Si el equipo tiene MAC y SN separados, el buffer espera 5 segundos para
      combinarlos.
    - Los datos se envían automáticamente a Google Sheets.

5.5 Consultar el historial
    - Ve a "Historial" para ver instalaciones.
    - Filtra por modelo, resultado, o busca por MAC / SN.
    - Exporta a CSV para Excel.


================================================================================
6. ADAPTACIÓN A OTROS MODELOS DE ONU (GUÍA TÉCNICA)
================================================================================
DigiConfig Pro es flexible. Para agregar un nuevo modelo, necesitas obtener
4 piezas de información de su interfaz web.

6.1 ¿Cómo saber si un modelo es compatible?
    + Tiene interfaz web por HTTP (puerto 80).
    + Permite iniciar sesión con credenciales fijas (user/pass).
    + Ofrece una opción de "Restore Configuration" o "Upload".
    - NO debe tener CAPTCHA en el login (si lo tiene, NO se puede automatizar).

6.2 Inspeccionar el formulario de login
    1. Conecta la ONU y pon tu PC en la misma subred (ej. 192.168.1.x).
    2. Abre http://[IP]/ en el navegador.
    3. Haz clic derecho -> Inspeccionar.
    4. Busca el <form> y anota:
        - action (URL de envío).
        - name de los campos de usuario y contraseña.
        - Campos ocultos (hidden).

6.3 Encontrar el formulario de subida
    1. Logueado, busca "Management" -> "Configuration" -> "Upload".
    2. Inspecciona el formulario:
        - action (URL de subida, ej. /boaform/formSaveConfig).
        - name del campo de archivo (input type="file"). Este es el
          "campo_upload".
        - Campos ocultos (ej. submit-url). Se añaden en "campos_extra_upload".

6.4 Tabla de referencia por fabricante
+--------------+---------------------+-----------------------------------+---------------+
| FABRICANTE   | CAMPO DE UPLOAD     | RUTA DE UPLOAD                    | OBSERVACIONES |
+--------------+---------------------+-----------------------------------+---------------+
| Huawei       | config              | /html/ssw/en/config/config_save.. | Sin CAPTCHA   |
| ZTE          | config / uploadfile | /cgi-bin/uploadfile               | Verificar     |
| FiberHome    | config              | /cgi-bin/upload                   | Sin CAPTCHA   |
| VSOL         | file                | /cgi-bin/uploadfile               | Tarda ~90s    |
| BT-PON       | binary              | /boaform/formSaveConfig           | Necesita      |
|              |                     |                                   | submit-url    |
+--------------+---------------------+-----------------------------------+---------------+
NOTA: Si el modelo requiere campos ocultos, agrégalos en modelos.json:
    "campos_extra_upload": {"submit-url": "/saveconf.asp"}


================================================================================
7. MEJORAS FUTURAS Y EXTENSIONES
================================================================================
7.1 Agregar soporte para más modelos
    - Añadir fabricantes a onu_database.py con prefijos SN y parámetros.
    - Implementar autenticación por token CSRF o extracción de challenge.
    - Soporte para TFTP como alternativa a HTTP.

7.2 Mejoras en la interfaz
    - Modo oscuro/claro automático.
    - Multilenguaje (Español/Inglés).
    - Vista previa del XML antes de subir.

7.3 Mejoras en el escáner
    - Sincronización bidireccional con Google Sheets.
    - Registro offline: guardar escaneos sin conexión y sincronizar después.

7.4 Mejoras en el instalador
    - Resolución de CAPTCHA mediante OCR (Tesseract) – complejo.
    - Verificación de configuración más robusta (parámetros de red).

7.5 Automatización de pruebas
    - Pruebas unitarias para detector, instalador y sheets_manager.
    - Simulación de ONUs para pruebas sin hardware.


================================================================================
8. SOLUCIÓN DE PROBLEMAS COMUNES
================================================================================
8.1 La ONU no se detecta en el Dashboard
    - Verifica el cable Ethernet y los LEDs (LINK/ACT encendido).
    - Asegura que tu PC esté en la misma subred (ej. 192.168.1.x).
    - Desactiva el WiFi para evitar conflictos de ruta.
    - Usa el botón "Buscar ONU manualmente".

8.2 El login falla en la instalación
    - Revisa que las credenciales de fábrica sean correctas.
    - Si la ONU tiene CAPTCHA, la automatización NO es posible.
    - Revisa la consola de logs (códigos HTTP y respuestas).

8.3 La subida del XML falla
    - Confirma que "campo_upload" coincida con el name del input en el HTML.
    - Confirma que "ruta_upload" coincida con el action del formulario.
    - Si requiere campos ocultos, agrégalos en "campos_extra_upload".
    - Verifica que el XML no esté vacío.

8.4 El modelo no se guarda después de cerrar el programa
    - Verifica permisos de escritura en la carpeta del proyecto.
    - El archivo modelos.json se guarda en configs/modelos.json para evitar
      problemas de permisos en el .exe.

8.5 Errores de importación al compilar el .exe
    - Asegúrate de incluir la carpeta pyzbar en "Additional Files" (contiene
      las DLLs necesarias).
    - Incluye todos los --hidden-import y --collect-all (ver sección 3.3).


================================================================================
9. CONTACTO Y SOPORTE
================================================================================
Para reportar problemas, sugerir mejoras o solicitar asistencia:
    - Correo electrónico: soporte@digicable.com (ejemplo).
    - Repositorio del proyecto: (incluir enlace si es público).

================================================================================
10. LICENCIA Y AGRADECIMIENTOS
================================================================================
DigiConfig Pro es un proyecto interno de Digicable, desarrollado por el equipo
de soporte técnico. Agradecimientos especiales a los ingenieros que han
contribuido con pruebas y retroalimentación.

================================================================================
                        FIN DEL DOCUMENTO
                Gracias por usar DigiConfig Pro. 
================================================================================