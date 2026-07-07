# ============================================================
# parser_onu.py - Extracción de MAC y SN con alta precisión
# DigiConfig Pro v2.0 - Optimizado y corregido
# ============================================================

import re
from .onu_database import identificar_fabricante, FABRICANTES_DB

def parsear_codigo(texto: str) -> dict:
    """
    Analiza el texto escaneado y extrae MAC y Serial Number (SN).
    Soporta:
      - Etiquetas literales "MAC:", "GPON SN:", "EPON SN:", "SERIAL:", "SN:"
      - MAC en formato hexadecimal de 12 caracteres, con o sin separadores ':' o '-'
      - SN con prefijos conocidos (almacenados en FABRICANTES_DB)
    Retorna dict con claves: mac, serial, tipo_lectura, fabricante, tecnologia
    """
    texto_original = texto.strip()
    resultado = {
        "mac": None,
        "serial": None,
        "tipo_lectura": "ninguno",
        "fabricante": None,
        "tecnologia": "GPON",          # valor por defecto
        "texto_restante": texto_original
    }

    # --- 1. Extracción de MAC (con o sin etiqueta) ---
    # Patrón para MAC con etiqueta "MAC:" (permite separadores)
    mac_with_label = re.search(
        r'MAC:\s*([0-9A-F]{2}[:-]?){5}[0-9A-F]{2}',
        texto_original,
        re.IGNORECASE
    )
    if mac_with_label:
        raw_mac = mac_with_label.group(0)
        # Limpiar separadores y dejar solo 12 hex
        mac_clean = re.sub(r'MAC:\s*|[:-]', '', raw_mac, flags=re.IGNORECASE).upper()
        resultado["mac"] = mac_clean
        resultado["tipo_lectura"] = "mac"
        # Eliminar esta parte del texto para no interferir en búsqueda de SN
        texto_restante = re.sub(r'MAC:\s*[0-9A-F]{2}[:-]?[0-9A-F]{2}[:-]?[0-9A-F]{2}[:-]?[0-9A-F]{2}[:-]?[0-9A-F]{2}[:-]?[0-9A-F]{2}', '', texto_original, flags=re.IGNORECASE)
        resultado["texto_restante"] = texto_restante.strip()
    else:
        # Sin etiqueta: buscar 12 hex consecutivos o con separadores como palabra completa
        mac_plain = re.search(r'\b([0-9A-F]{12})\b', texto_original, re.IGNORECASE)
        if not mac_plain:
            mac_plain = re.search(r'\b(?:[0-9A-F]{2}[:-]){5}[0-9A-F]{2}\b', texto_original, re.IGNORECASE)
        if mac_plain:
            raw_mac = mac_plain.group(0)
            mac_clean = re.sub(r'[:-]', '', raw_mac).upper()
            resultado["mac"] = mac_clean
            resultado["tipo_lectura"] = "mac"
            # También lo eliminamos del texto restante
            texto_restante = re.sub(r'\b(?:[0-9A-F]{2}[:-]?){5}[0-9A-F]{2}\b', '', texto_original, flags=re.IGNORECASE)
            resultado["texto_restante"] = texto_restante.strip()

    # --- 2. Extracción de SN por etiquetas conocidas ---
    sn_patterns = [
        r'GPON\s+SN:\s*([A-Z0-9]+)',      # "GPON SN: ZTEGC2B3A4"
        r'EPON\s+SN:\s*([A-Z0-9]+)',      # "EPON SN: ADC2001AABBCC"
        r'S/N:\s*([A-Z0-9]+)',             # "S/N: HWTC12345678"
        r'SERIAL:\s*([A-Z0-9]+)',          # "SERIAL: ADCTEST123456"
        r'SN:\s*([A-Z0-9]+)',              # "SN: BTPTDD92556B"
    ]
    for pattern in sn_patterns:
        sn_match = re.search(pattern, resultado["texto_restante"], re.IGNORECASE)
        if sn_match:
            resultado["serial"] = sn_match.group(1).upper()
            if resultado["tipo_lectura"] == "mac":
                resultado["tipo_lectura"] = "ambos"
            else:
                resultado["tipo_lectura"] = "serial"
            # Actualizar texto restante eliminando la etiqueta encontrada
            resultado["texto_restante"] = re.sub(pattern, '', resultado["texto_restante"], flags=re.IGNORECASE).strip()
            break

    # --- 3. Si aún no hay SN, buscar cualquier token que empiece con prefijo conocido ---
    if not resultado["serial"]:
        # Primero intentar con los prefijos de la base de datos
        # Ordenamos los prefijos de mayor a menor longitud para evitar falsos positivos
        prefijos_ordenados = sorted(FABRICANTES_DB.keys(), key=len, reverse=True)
        for prefijo in prefijos_ordenados:
            # Buscar el prefijo seguido de caracteres alfanuméricos (longitud mínima 4)
            patron_prefijo = rf'\b{re.escape(prefijo)}[A-Z0-9]{{4,}}\b'
            match = re.search(patron_prefijo, resultado["texto_restante"], re.IGNORECASE)
            if match:
                resultado["serial"] = match.group(0).upper()
                if resultado["tipo_lectura"] == "mac":
                    resultado["tipo_lectura"] = "ambos"
                else:
                    resultado["tipo_lectura"] = "serial"
                break

    # --- 4. Último recurso: si el texto completo parece un SN (largo ≥ 8 y alfanumérico) ---
    if not resultado["serial"] and len(texto_original) >= 8 and texto_original.isalnum():
        resultado["serial"] = texto_original.upper()
        if resultado["tipo_lectura"] == "ninguno":
            resultado["tipo_lectura"] = "serial"

    # --- 5. Identificar fabricante a partir del SN ---
    if resultado["serial"]:
        info = identificar_fabricante(resultado["serial"])
        if info:
            resultado["fabricante"] = info["nombre"]
            resultado["tecnologia"] = info["tecnologia"]

    return resultado
