# ============================================================
# historial.py — Registro de todas las ONUs configuradas
# Guarda en JSON y permite exportar a CSV/Excel
# ============================================================
import json
import os
import csv
from datetime import datetime

RUTA_BASE  = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
RUTA_LOG   = os.path.join(RUTA_BASE, "instalaciones.json")


def _asegurar_archivo():
    os.makedirs(RUTA_BASE, exist_ok=True)
    if not os.path.exists(RUTA_LOG):
        with open(RUTA_LOG, "w", encoding="utf-8") as f:
            json.dump([], f)


def guardar_registro(modelo_id: str, nombre_display: str,
                     mac: str, gpon_sn: str, ip_final: str,
                     xml_usado: str, exito: bool,
                     tecnico: str = "Técnico", tiempo_seg: float = 0.0):
    """Agrega un registro al historial de instalaciones."""
    _asegurar_archivo()
    registro = {
        "fecha":         datetime.now().strftime("%Y-%m-%d"),
        "hora":          datetime.now().strftime("%H:%M:%S"),
        "modelo_id":     modelo_id,
        "nombre_display":nombre_display,
        "mac":           mac,
        "gpon_sn":       gpon_sn,
        "ip_configurada":ip_final,
        "xml_usado":     os.path.basename(xml_usado),
        "resultado":     "✅ Éxito" if exito else "❌ Error",
        "tecnico":       tecnico,
        "tiempo_seg":    round(tiempo_seg, 1),
    }
    try:
        with open(RUTA_LOG, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(registro)
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[HISTORIAL] Error al guardar: {e}")
    return registro


def cargar_todos() -> list:
    """Retorna lista completa de registros (más reciente primero)."""
    _asegurar_archivo()
    try:
        with open(RUTA_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
            return list(reversed(data))
    except Exception:
        return []


def cargar_hoy() -> list:
    """Solo registros del día de hoy."""
    hoy = datetime.now().strftime("%Y-%m-%d")
    return [r for r in cargar_todos() if r.get("fecha") == hoy]


def estadisticas() -> dict:
    """Calcula estadísticas generales del historial."""
    todos = cargar_todos()
    if not todos:
        return {"total": 0, "exitosas": 0, "errores": 0, "hoy": 0,
                "modelos": {}, "tasa_exito": 0}

    exitosas = sum(1 for r in todos if "Éxito" in r.get("resultado",""))
    errores  = len(todos) - exitosas
    hoy_n    = len(cargar_hoy())

    modelos = {}
    for r in todos:
        m = r.get("nombre_display","?")
        modelos[m] = modelos.get(m, 0) + 1

    return {
        "total":       len(todos),
        "exitosas":    exitosas,
        "errores":     errores,
        "hoy":         hoy_n,
        "modelos":     modelos,
        "tasa_exito":  int(exitosas / len(todos) * 100) if todos else 0,
    }


def mac_ya_configurada(mac: str) -> bool:
    """Verifica si una MAC ya tiene registro previo."""
    mac_clean = mac.upper().replace(":", "").replace("-", "")
    for r in cargar_todos():
        mac_r = r.get("mac","").upper().replace(":", "").replace("-","")
        if mac_clean == mac_r:
            return True
    return False


def exportar_csv(ruta_destino: str) -> bool:
    """Exporta el historial a un archivo CSV."""
    try:
        todos = cargar_todos()
        if not todos:
            return False
        with open(ruta_destino, "w", newline="", encoding="utf-8-sig") as f:
            campos = ["fecha","hora","nombre_display","mac","gpon_sn",
                      "ip_configurada","xml_usado","resultado","tecnico","tiempo_seg"]
            writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(todos)
        return True
    except Exception as e:
        print(f"[HISTORIAL] Error CSV: {e}")
        return False


def limpiar_historial():
    """Borra todos los registros (con confirmación desde la UI)."""
    try:
        with open(RUTA_LOG, "w", encoding="utf-8") as f:
            json.dump([], f)
        return True
    except Exception:
        return False
