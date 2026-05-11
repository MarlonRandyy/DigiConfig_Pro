# ============================================================
# modelos_manager.py — Gestión de la base de datos de modelos
# Lee, guarda, agrega y elimina entradas en modelos.json
# ============================================================
import json
import os
import shutil

RUTA_JSON = os.path.join(
    os.path.dirname(__file__), "..", "..", "modelos.json"
)
RUTA_IMAGENES  = os.path.join(
    os.path.dirname(__file__), "..", "..", "configs", "imagenes"
)
RUTA_FIRMWARES = os.path.join(
    os.path.dirname(__file__), "..", "..", "configs", "firmwares"
)


def cargar() -> dict:
    """Carga y retorna todo el dict de modelos."""
    try:
        with open(RUTA_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def guardar(modelos: dict):
    """Sobreescribe modelos.json con el dict actualizado."""
    with open(RUTA_JSON, "w", encoding="utf-8") as f:
        json.dump(modelos, f, indent=4, ensure_ascii=False)


def agregar_modelo(modelo_id: str, datos: dict,
                   ruta_imagen_src: str = None,
                   ruta_xml_src: str = None) -> bool:
    """
    Agrega un nuevo modelo. Copia imagen y XML a las carpetas del proyecto.
    Retorna True si se guardó correctamente.
    """
    try:
        modelos = cargar()
        if modelo_id in modelos:
            return False   # ya existe

        # Copiar imagen si se proporcionó
        if ruta_imagen_src and os.path.exists(ruta_imagen_src):
            ext     = os.path.splitext(ruta_imagen_src)[1]
            destino = os.path.join(RUTA_IMAGENES, f"{modelo_id.lower()}{ext}")
            os.makedirs(RUTA_IMAGENES, exist_ok=True)
            shutil.copy2(ruta_imagen_src, destino)
            datos["imagen"] = f"configs/imagenes/{modelo_id.lower()}{ext}"

        # Copiar XML si se proporcionó
        if ruta_xml_src and os.path.exists(ruta_xml_src):
            destino = os.path.join(RUTA_FIRMWARES, f"{modelo_id.lower()}.xml")
            os.makedirs(RUTA_FIRMWARES, exist_ok=True)
            shutil.copy2(ruta_xml_src, destino)
            datos["firmware_xml"] = f"configs/firmwares/{modelo_id.lower()}.xml"

        modelos[modelo_id] = datos
        guardar(modelos)
        return True
    except Exception as e:
        print(f"[MODELOS] Error al agregar: {e}")
        return False


def actualizar_modelo(modelo_id: str, datos_nuevos: dict) -> bool:
    """Actualiza campos de un modelo existente."""
    try:
        modelos = cargar()
        if modelo_id not in modelos:
            return False
        modelos[modelo_id].update(datos_nuevos)
        guardar(modelos)
        return True
    except Exception:
        return False


def eliminar_modelo(modelo_id: str) -> bool:
    """Elimina un modelo del JSON (no borra los archivos físicos)."""
    try:
        modelos = cargar()
        if modelo_id in modelos:
            del modelos[modelo_id]
            guardar(modelos)
            return True
        return False
    except Exception:
        return False


def obtener(modelo_id: str) -> dict | None:
    """Retorna el dict de un modelo específico o None."""
    return cargar().get(modelo_id)


def listar_ids() -> list:
    """Lista de IDs de todos los modelos registrados."""
    return list(cargar().keys())
