# ============================================================
# onu_database.py - Base de datos de fabricantes de ONUs
# DigiConfig Pro v2.1 (con campos para autocompletado)
# ============================================================

"""
Contiene los prefijos de Serial Number (SN) y reglas de validación
para la mayoría de fabricantes de ONUs del mercado.
Además incluye los valores por defecto para campo_upload y tiempo_reinicio
según el fabricante.
"""

# Mapeo de prefijos a nombre de fabricante y tipo de PON
FABRICANTES_DB = {
    # Huawei (GPON)
    "HWTC": {
        "nombre": "Huawei",
        "tecnologia": "GPON",
        "longitud_sn": 10,
        "campo_upload": "config",
        "tiempo_reinicio": 60,
    },
    "HWGC": {
        "nombre": "Huawei",
        "tecnologia": "GPON",
        "longitud_sn": 10,
        "campo_upload": "config",
        "tiempo_reinicio": 60,
    },
    "HWGA": {
        "nombre": "Huawei",
        "tecnologia": "GPON",
        "longitud_sn": 10,
        "campo_upload": "config",
        "tiempo_reinicio": 60,
    },
    
    # ZTE (GPON)
    "ZTEG": {
        "nombre": "ZTE",
        "tecnologia": "GPON",
        "longitud_sn": 10,
        "campo_upload": "config",
        "tiempo_reinicio": 70,
    },
    
    # FiberHome (GPON/EPON)
    "FHTT": {
        "nombre": "FiberHome",
        "tecnologia": "GPON",
        "longitud_sn": 12,
        "campo_upload": "config",
        "tiempo_reinicio": 60,
    },
    
    # Nokia / Alcatel-Lucent (GPON)
    "ALCL": {
        "nombre": "Nokia",
        "tecnologia": "GPON",
        "longitud_sn": 12,
        "campo_upload": "config",
        "tiempo_reinicio": 60,
    },
    "ALCT": {
        "nombre": "Nokia",
        "tecnologia": "GPON",
        "longitud_sn": 12,
        "campo_upload": "config",
        "tiempo_reinicio": 60,
    },
    
    # BT-PON (GPON)
    "BTPT": {
        "nombre": "BT-PON",
        "tecnologia": "GPON",
        "longitud_sn": 12,
        "campo_upload": "binary",
        "tiempo_reinicio": 60,
    },
    
    # V-SOL (GPON) - USAN "file" como campo de upload
    "VSOL2026": {
        "nombre": "V-SOL",
        "tecnologia": "GPON",
        "longitud_sn": 14,
        "campo_upload": "file",
        "tiempo_reinicio": 90,
    },
    "VSOL2025": {
        "nombre": "V-SOL",
        "tecnologia": "GPON",
        "longitud_sn": 14,
        "campo_upload": "file",
        "tiempo_reinicio": 90,
    },
    "VSOL2024": {
        "nombre": "V-SOL",
        "tecnologia": "GPON",
        "longitud_sn": 14,
        "campo_upload": "file",
        "tiempo_reinicio": 90,
    },
    
    # ADC (EPON) - Generalmente usan "file"
    "ADC2001": {
        "nombre": "ADC",
        "tecnologia": "EPON",
        "longitud_sn": 14,
        "campo_upload": "file",
        "tiempo_reinicio": 60,
    },
    "ADC3001": {
        "nombre": "ADC",
        "tecnologia": "EPON",
        "longitud_sn": 14,
        "campo_upload": "file",
        "tiempo_reinicio": 60,
    },
    "ADC4001": {
        "nombre": "ADC",
        "tecnologia": "EPON",
        "longitud_sn": 14,
        "campo_upload": "file",
        "tiempo_reinicio": 60,
    },
    
    # Sercomm (GPON)
    "SCOM": {
        "nombre": "Sercomm",
        "tecnologia": "GPON",
        "longitud_sn": 12,
        "campo_upload": "config",
        "tiempo_reinicio": 60,
    },
    
    # Genexis (GPON) - Generalmente usan "file"
    "GNXS": {
        "nombre": "Genexis",
        "tecnologia": "GPON",
        "longitud_sn": 12,
        "campo_upload": "file",
        "tiempo_reinicio": 60,
    },
    
    # Ubiquiti (GPON)
    "UBNT": {
        "nombre": "Ubiquiti",
        "tecnologia": "GPON",
        "longitud_sn": 12,
        "campo_upload": "config",
        "tiempo_reinicio": 60,
    },
    
    # Calix (GPON)
    "CXNK": {
        "nombre": "Calix",
        "tecnologia": "GPON",
        "longitud_sn": 12,
        "campo_upload": "config",
        "tiempo_reinicio": 60,
    },
    
    # Dasan (GPON)
    "DSAN": {
        "nombre": "Dasan",
        "tecnologia": "GPON",
        "longitud_sn": 12,
        "campo_upload": "config",
        "tiempo_reinicio": 60,
    },
}

def identificar_fabricante(serial: str) -> dict:
    """
    Identifica el fabricante y tecnología a partir del SN.
    Retorna dict con 'nombre', 'tecnologia', 'prefijo_encontrado',
    'campo_upload' y 'tiempo_reinicio'.
    Si no se encuentra, retorna None.
    """
    if not serial:
        return None
    
    for prefijo, info in FABRICANTES_DB.items():
        if serial.startswith(prefijo):
            return {
                "nombre": info["nombre"],
                "tecnologia": info["tecnologia"],
                "prefijo": prefijo,
                "longitud_esperada": info.get("longitud_sn"),
                "campo_upload": info.get("campo_upload", "config"),
                "tiempo_reinicio": info.get("tiempo_reinicio", 60),
            }
    return None

def obtener_fabricantes_unicos() -> list:
    """Retorna una lista con los nombres de fabricantes únicos (ordenados)."""
    nombres = sorted({info["nombre"] for info in FABRICANTES_DB.values()})
    return nombres

def obtener_parametros_por_fabricante(nombre_fabricante: str) -> dict:
    """
    Retorna los parámetros (campo_upload, tiempo_reinicio) del primer prefijo
    que coincida con el nombre del fabricante.
    """
    for prefijo, info in FABRICANTES_DB.items():
        if info["nombre"] == nombre_fabricante:
            return {
                "campo_upload": info.get("campo_upload", "config"),
                "tiempo_reinicio": info.get("tiempo_reinicio", 60),
            }
    return {"campo_upload": "config", "tiempo_reinicio": 60}