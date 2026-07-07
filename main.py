# ============================================================
# DigiConfig Pro — Main.py 
# Punto de entrada principal de la aplicación.
# Gestiona el entorno de ejecución, la captura de errores,
# la configuración de rutas y el lanzamiento de la interfaz.
# ============================================================

import sys
import os
import traceback
import ctypes
import multiprocessing


# ──────────────────────────────────────────────────────────────
#  FUNCIÓN: get_resource_path
#  Propósito: Obtiene la ruta absoluta de recursos (imágenes,
#  configuraciones, etc.) tanto en modo desarrollo (ejecución
#  desde script) como en modo empaquetado (ejecutable .exe).
#  En el ejecutable, PyInstaller usa sys._MEIPASS para la
#  carpeta temporal de extracción. En modo desarrollo, usa el
#  directorio actual.
# ──────────────────────────────────────────────────────────────
def get_resource_path(relative_path):
    """ Obtiene la ruta absoluta de recursos para modo dev y modo ejecutable """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ──────────────────────────────────────────────────────────────
#  FUNCIÓN: excepthook
#  Propósito: Reemplaza el manejador de excepciones no capturadas
#  para registrar cualquier error crítico en un archivo de log
#  (digiconfig_error.log). Esto facilita la depuración en
#  entornos de producción donde la consola no está disponible.
# ──────────────────────────────────────────────────────────────
def excepthook(exc_type, exc_value, exc_tb):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    with open("digiconfig_error.log", "a", encoding="utf-8") as f:
        f.write(f"\n--- ERROR CRÍTICO {os.linesep} {error_msg}\n")
    # Delegar al manejador original para que el error también se muestre en consola
    sys.__excepthook__(exc_type, exc_value, exc_tb)


# ──────────────────────────────────────────────────────────────
#  CONFIGURACIÓN DE MANEJO DE EXCEPCIONES GLOBAL
# ──────────────────────────────────────────────────────────────
sys.excepthook = excepthook


# ──────────────────────────────────────────────────────────────
#  CONFIGURACIÓN DE DPI PARA WINDOWS
#  Propósito: Hace que la aplicación sea consciente del DPI
#  por monitor, evitando que la interfaz se vea borrosa o
#  escalada incorrectamente en monitores de alta definición
#  (4K, etc.). Solo aplica en Windows.
# ──────────────────────────────────────────────────────────────
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────
#  CONFIGURACIÓN DE DIRECTORIO DE TRABAJO
#  Propósito: Fijar el directorio de trabajo a la raíz del
#  proyecto. Esto asegura que todas las rutas relativas
#  (carpetas assets, configs, etc.) se resuelvan correctamente
#  tanto en desarrollo como en el ejecutable.
# ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
os.chdir(BASE_DIR)


# ──────────────────────────────────────────────────────────────
#  CONFIGURACIÓN DE SYS.PATH
#  Propósito: Agregar la carpeta 'src' al path de Python,
#  permitiendo que los módulos internos (ui.app, core, utils)
#  se importen correctamente, incluso cuando el programa se
#  ejecuta desde un entorno empaquetado.
# ──────────────────────────────────────────────────────────────
SRC_PATH = get_resource_path("src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


# ──────────────────────────────────────────────────────────────
#  PUNTO DE ENTRADA PRINCIPAL
#  Propósito: Inicializa y ejecuta la aplicación.
#  Se utiliza multiprocessing.freeze_support() para garantizar
#  la compatibilidad con PyInstaller cuando se usa multiproceso.
#  Captura excepciones al arrancar la UI y las registra en un
#  archivo de log específico (digiconfig_startup_error.log).
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    multiprocessing.freeze_support() 
    
    try:
        import ui.app
        
        app = ui.app.App()
        app.run()
        
    except Exception as e:
        with open("digiconfig_startup_error.log", "w", encoding="utf-8") as f:
            f.write(f"Fallo al arrancar la UI: {str(e)}\n")
            traceback.print_exc(file=f)
        sys.exit(1)