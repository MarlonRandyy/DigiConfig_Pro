# DigiConfig Pro 🔧
### Sistema de Aprovisionamiento Inteligente de ONUs — Digicable

---

## 📋 ¿Qué hace este programa?

Automatiza la configuración de equipos ONU (terminales de fibra óptica):

1. **Detecta** automáticamente la ONU cuando se conecta por cable
2. **Identifica** el modelo (BT-PON, VSOL, Huawei, ZTE) por MAC o HTML
3. **Sube** el archivo `.xml` de configuración correcto
4. **Verifica** que la ONU quedó configurada (IP 192.168.100.1 / digicable19)
5. **Registra** todo en el historial con fecha, SN y resultado

---

## 🛠️ PASOS PARA INSTALAR Y EJECUTAR

### Paso 1 — Instalar Python 3.11+
Descargar desde: https://www.python.org/downloads/
✅ Marcar "Add Python to PATH" durante la instalación.

### Paso 2 — Abrir terminal en la carpeta del proyecto
```
cd DigiConfig_Pro
```

### Paso 3 — Instalar dependencias
```bash
pip install -r requirements.txt
```

Esto instala:
| Librería | Para qué sirve |
|---|---|
| `customtkinter` | Interfaz gráfica moderna |
| `requests` | Login y subida de XML a la ONU |
| `beautifulsoup4` | Leer el HTML de la ONU para identificar modelo/MAC |
| `Pillow` | Mostrar imágenes de los modelos |
| `winotify` | Notificaciones de escritorio en Windows |
| `openpyxl` | Exportar historial a Excel |

### Paso 4 — Ejecutar el programa
```bash
python main.py
```

---

## 📁 Estructura del proyecto

```
DigiConfig_Pro/
│
├── main.py                    ← Punto de entrada (ejecutar este)
├── modelos.json               ← Base de datos de modelos ONU
├── requirements.txt           ← Dependencias pip
│
├── configs/
│   ├── firmwares/             ← Poner aquí los archivos .xml de cada ONU
│   │   ├── bt191xr.xml
│   │   ├── vsol.xml
│   │   └── huawei.xml
│   └── imagenes/              ← Fotos PNG/JPG de cada modelo de ONU
│       ├── bt191xr.png
│       ├── vsol.png
│       └── huawei.png
│
├── logs/
│   └── instalaciones.json     ← Historial auto-generado
│
└── src/
    ├── core/
    │   ├── detector.py        ← Detecta ONUs en la red (ping + HTTP)
    │   ├── instalador.py      ← Sube XML, reinicia ONU, verifica
    │   ├── historial.py       ← Guarda/lee el log de instalaciones
    │   └── modelos_manager.py ← CRUD de modelos en modelos.json
    │
    ├── ui/
    │   ├── app.py             ← Ventana principal + navegación
    │   ├── tema.py            ← Colores y fuentes Digicable
    │   ├── pantalla_dashboard.py     ← Detección automática
    │   ├── pantalla_configuracion.py ← Subir XML + progreso
    │   ├── pantalla_modelos.py       ← Gestión de modelos
    │   └── pantalla_historial.py     ← Log + filtros + exportar
    │
    └── utils/
        └── notificaciones.py  ← Notificaciones Windows Toast
```

---

## 📦 Agregar tus archivos XML e imágenes

1. Copiar los `.xml` de Digicable a `configs/firmwares/`
2. Copiar fotos PNG de las ONUs a `configs/imagenes/`
3. Editar `modelos.json` con las rutas correctas **o** usar la pantalla "Modelos XML" del programa

---

## 🔄 Flujo de trabajo del técnico

```
1. Abrir DigiConfig Pro
2. Conectar ONU por cable de red a la PC
3. El programa detecta la ONU automáticamente (notificación Windows)
4. Ir a "Configurar ONU" → el modelo y XML ya están preseleccionados
5. Click "INICIAR INSTALACIÓN"
6. Esperar ~90 segundos (el programa hace todo solo)
7. Ver ✅ "Instalación exitosa" → ONU lista para campo
8. El registro queda guardado en "Historial"
```

---

## ⚙️ Adaptar al modelo específico de ONU

Cada marca de ONU tiene un formulario web diferente. En `modelos.json` configura:

- `ruta_upload` — La URL donde el navegador sube el `.xml`
- `ruta_reset` — La URL del botón "Restore Default"

Para encontrar estas rutas: abre Wireshark o las DevTools del navegador (F12 → Network) mientras subes un XML manualmente, y copia la URL del POST que aparece.

---

## 📤 Convertir a .exe (para distribuir sin Python)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name DigiConfigPro main.py
```
El `.exe` queda en la carpeta `dist/`.

---

## 🐛 Troubleshooting

| Error | Solución |
|---|---|
| `ModuleNotFoundError` | Correr `pip install -r requirements.txt` de nuevo |
| ONU no detectada | Verificar que el cable de red está conectado y que Windows asignó IP en la red 192.168.x.x |
| Fallo de login | La ONU puede usar credenciales diferentes en fábrica. Revisar `usuario_fabrica` y `clave_fabrica` en modelos.json |
| XML no sube | Capturar la ruta correcta de upload con Wireshark para ese modelo específico |
| Winotify error | Solo funciona en Windows 10/11. En desarrollo con Linux/Mac, las notificaciones se muestran en consola |
