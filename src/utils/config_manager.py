import json
import os
import shutil

# ─── CONFIGURACIÓN DE RUTAS ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_DIR = os.path.join(BASE_DIR, "configs")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")
CREDS_DIR = os.path.join(BASE_DIR, "src", "core", "secure_creds")
CREDS_FILE = os.path.join(CREDS_DIR, "credentials.json")

def asegurar_directorios():
    """Crea las carpetas necesarias si no existen."""
    for directorio in [CONFIG_DIR, CREDS_DIR]:
        if not os.path.exists(directorio):
            os.makedirs(directorio, exist_ok=True)

def leer_dato(clave, default=None):
    """
    Lee un dato del archivo de configuración. 
    Si la clave no existe, devuelve el valor por defecto configurado.
    """
    asegurar_directorios()
    
    # Valores por defecto globales para la nueva visión
    defaults_proyecto = {
        "celda_inicio": "B2",
        "limite_lote": 100,
        "google_sheet_id": ""
    }
    
    if not os.path.exists(CONFIG_FILE):
        return defaults_proyecto.get(clave, default)
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Prioridad: 1. Archivo JSON, 2. Defaults del proyecto, 3. Default del argumento
            return data.get(clave, defaults_proyecto.get(clave, default))
    except Exception:
        return defaults_proyecto.get(clave, default)

def guardar_dato(clave, valor):
    """Guarda un dato asegurando limpieza (ej. coordenadas en mayúsculas)."""
    asegurar_directorios()
    
    # Limpieza específica para coordenadas de celda
    if clave == "celda_inicio" and isinstance(valor, str):
        valor = valor.upper().strip()

    data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}
    
    data[clave] = valor
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    return True

def importar_credenciales(ruta_origen):
    """Copia el archivo JSON de credenciales a la carpeta segura."""
    asegurar_directorios()
    try:
        if not os.path.exists(ruta_origen):
            return False, "El archivo de origen no existe."
            
        shutil.copy2(ruta_origen, CREDS_FILE)
        return True, "Credenciales vinculadas con éxito."
    except Exception as e:
        return False, f"Error crítico al importar: {str(e)}"