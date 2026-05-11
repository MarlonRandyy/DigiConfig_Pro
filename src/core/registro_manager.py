# ============================================================
# registro_manager.py — Controlador Exclusivo Google Sheets
# ============================================================

import json
import os
import sys

# Importamos solo el gestor de Sheets
try:
    from src.core.sheets_manager import registrar_equipo_sheets
except ImportError as e:
    print(f"[ERROR] No se pudo importar el gestor de Google Sheets: {e}")

# Ruta del archivo de configuración
CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "configs", "config_registro.json"
)

def registrar_equipo(datos: dict) -> bool:
    """
    Registra los datos directamente en Google Sheets.
    Ignora el archivo Excel y el modo híbrido.
    """
    print(f"[REGISTRO] Enviando a Google Sheets: MAC={datos.get('mac')}, SN={datos.get('serial')}")
    
    try:
        # Ejecutamos directamente el registro en la nube
        resultado = registrar_equipo_sheets(datos)
        
        if resultado:
            print("[EXITO] Datos guardados en la nube correctamente.")
        else:
            print("[ERROR] El servidor de Google rechazó el registro.")
            
        return resultado
        
    except Exception as e:
        print(f"[ERROR CRÍTICO] Fallo en la comunicación con Sheets: {e}")
        return False