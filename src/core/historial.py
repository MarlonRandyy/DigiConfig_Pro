# ============================================================
# historial.py — Registro de todas las ONUs configuradas
# Guarda en JSON y permite exportar a CSV/Excel
# ============================================================
import json
import os
import csv
import sys
from datetime import datetime

# ─── Rutas (usando BASE_DIR para portabilidad) ──────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUTA_BASE = os.path.join(BASE_DIR, "logs")
RUTA_LOG = os.path.join(RUTA_BASE, "instalaciones.json")


def _asegurar_archivo():
    """Crea el directorio y el archivo JSON si no existen."""
    try:
        os.makedirs(RUTA_BASE, exist_ok=True)
        if not os.path.exists(RUTA_LOG):
            with open(RUTA_LOG, "w", encoding="utf-8") as f:
                json.dump([], f)
    except Exception as e:
        print(f"[HISTORIAL] Error al crear archivo: {e}")


def guardar_registro(modelo_id: str, nombre_display: str,
                     mac: str, gpon_sn: str, ip_final: str,
                     xml_usado: str, exito: bool,
                     tecnico: str = "Técnico", tiempo_seg: float = 0.0) -> dict | None:
    """
    Agrega un registro al historial de instalaciones.
    Retorna el registro guardado o None en caso de error.
    """
    _asegurar_archivo()

    # Validar datos mínimos
    if not mac or not modelo_id:
        print("[HISTORIAL] Error: MAC y Modelo ID son obligatorios.")
        return None

    registro = {
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M:%S"),
        "modelo_id": modelo_id,
        "nombre_display": nombre_display or "Desconocido",
        "mac": mac.upper().replace(":", "").replace("-", ""),
        "gpon_sn": gpon_sn or "No disponible",
        "ip_configurada": ip_final or "N/A",
        "xml_usado": os.path.basename(xml_usado) if xml_usado else "N/A",
        "resultado": "✅ Éxito" if exito else "❌ Error",
        "tecnico": tecnico or "Técnico",
        "tiempo_seg": round(tiempo_seg, 1),
    }

    try:
        with open(RUTA_LOG, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(registro)
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.truncate()
        return registro
    except json.JSONDecodeError as e:
        print(f"[HISTORIAL] Error: JSON corrupto. {e}")
        # Intentar reparar: crear archivo nuevo
        try:
            with open(RUTA_LOG, "w", encoding="utf-8") as f:
                json.dump([registro], f, indent=2, ensure_ascii=False)
            return registro
        except Exception:
            return None
    except Exception as e:
        print(f"[HISTORIAL] Error al guardar: {e}")
        return None


def cargar_todos() -> list:
    """Retorna lista completa de registros (más reciente primero)."""
    _asegurar_archivo()
    try:
        with open(RUTA_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
            return list(reversed(data)) if isinstance(data, list) else []
    except json.JSONDecodeError as e:
        print(f"[HISTORIAL] Error al leer JSON: {e}")
        return []
    except Exception as e:
        print(f"[HISTORIAL] Error al cargar: {e}")
        return []


def cargar_hoy() -> list:
    """Solo registros del día de hoy."""
    hoy = datetime.now().strftime("%Y-%m-%d")
    return [r for r in cargar_todos() if r.get("fecha") == hoy]


def estadisticas() -> dict:
    """Calcula estadísticas generales del historial."""
    todos = cargar_todos()
    if not todos:
        return {
            "total": 0,
            "exitosas": 0,
            "errores": 0,
            "hoy": 0,
            "modelos": {},
            "tasa_exito": 0
        }

    exitosas = sum(1 for r in todos if "Éxito" in r.get("resultado", ""))
    errores = len(todos) - exitosas
    hoy_n = len(cargar_hoy())

    modelos = {}
    for r in todos:
        m = r.get("nombre_display", "?")
        modelos[m] = modelos.get(m, 0) + 1

    return {
        "total": len(todos),
        "exitosas": exitosas,
        "errores": errores,
        "hoy": hoy_n,
        "modelos": modelos,
        "tasa_exito": int((exitosas / len(todos)) * 100) if todos else 0,
    }


def mac_ya_configurada(mac: str) -> bool:
    """Verifica si una MAC ya tiene registro previo en el historial."""
    if not mac:
        return False
    mac_clean = mac.upper().replace(":", "").replace("-", "")
    for r in cargar_todos():
        mac_r = r.get("mac", "").upper().replace(":", "").replace("-", "")
        if mac_clean == mac_r:
            return True
    return False


def exportar_csv(ruta_destino: str) -> bool:
    """Exporta el historial a un archivo CSV (UTF-8 con BOM para Excel)."""
    try:
        todos = cargar_todos()
        if not todos:
            print("[HISTORIAL] No hay datos para exportar.")
            return False

        # Asegurar directorio de destino
        os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)

        campos = [
            "fecha", "hora", "nombre_display", "mac", "gpon_sn",
            "ip_configurada", "xml_usado", "resultado", "tecnico", "tiempo_seg"
        ]

        with open(ruta_destino, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(todos)

        print(f"[HISTORIAL] Exportado a: {ruta_destino}")
        return True
    except Exception as e:
        print(f"[HISTORIAL] Error exportando CSV: {e}")
        return False


def limpiar_historial() -> bool:
    """Borra todos los registros del historial (con confirmación desde la UI)."""
    try:
        _asegurar_archivo()
        with open(RUTA_LOG, "w", encoding="utf-8") as f:
            json.dump([], f)
        return True
    except Exception as e:
        print(f"[HISTORIAL] Error al limpiar: {e}")
        return False


def obtener_registros_por_modelo(modelo_id: str) -> list:
    """Filtra registros por ID de modelo."""
    todos = cargar_todos()
    return [r for r in todos if r.get("modelo_id") == modelo_id]


def obtener_ultimo_registro_por_mac(mac: str) -> dict | None:
    """Retorna el último registro de una MAC específica."""
    if not mac:
        return None
    mac_clean = mac.upper().replace(":", "").replace("-", "")
    for r in cargar_todos():
        mac_r = r.get("mac", "").upper().replace(":", "").replace("-", "")
        if mac_clean == mac_r:
            return r
    return None