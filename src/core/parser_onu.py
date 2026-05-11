import re

def parsear_codigo(texto):
    """
    Analiza el texto escaneado para extraer MAC, Serial y detectar el tipo de PON.
    Es capaz de separar datos pegados o identificar prefijos comunes.
    """
    # Limpiamos espacios innecesarios pero mantenemos el texto original para el análisis
    texto_limpio = texto.strip()
    datos = {
        "mac": None, 
        "serial": None,
        "pon": "GPON"  # Valor por defecto, se puede mejorar con detección
    }

    # 1. EXTRACCIÓN DE MAC (Busca 12 caracteres hex con o sin separadores)
    # Soporta: AA:BB:CC:DD:EE:FF, AA-BB-CC-DD-EE-FF o AABBCCDDEEFF
    mac_pattern = r'(([0-9A-F]{2}[:-]){5}([0-9A-F]{2})|([0-9A-F]{12}))'
    mac_match = re.search(mac_pattern, texto_limpio, re.IGNORECASE)
    
    if mac_match:
        # Extraemos y normalizamos (sin puntos ni guiones)
        mac_raw = mac_match.group(0)
        datos["mac"] = re.sub(r'[:-]', '', mac_raw).upper()
        # Removemos la MAC del texto para que no interfiera con la búsqueda del Serial
        texto_restante = texto_limpio.replace(mac_raw, "")
    else:
        texto_restante = texto_limpio

    # 2. EXTRACCIÓN DE SERIAL (S/N o SN)
    # Buscamos patrones típicos de fabricantes (Huawei, ZTE, Nokia, etc.)
    # Suelen empezar con 4 letras y seguir con 8 caracteres hex o números
    sn_patterns = [
        r'(?:SN|S/N)[:\s]*([A-Z0-9]{12,16})', # Formato largo estándar
        r'([A-Z]{4}[0-9A-F]{8})',            # Formato típico Huawei/ZTE (4 letras + 8 hex)
    ]
    
    for pattern in sn_patterns:
        sn_match = re.search(pattern, texto_restante, re.IGNORECASE)
        if sn_match:
            # Si el patrón tiene grupos, tomamos el primero (el código), si no, el grupo 0
            datos["serial"] = sn_match.group(1).upper() if sn_match.groups() else sn_match.group(0).upper()
            break

    # 3. LÓGICA DE RESPALDO (Failsafe)
    # Si no encontró nada específico pero hay texto largo, intentamos deducir
    if not datos["mac"] and not datos["serial"]:
        if len(texto_limpio) >= 12:
            # Si parece una MAC (solo hex y 12 char)
            if re.match(r'^[0-9A-F]{12}$', texto_limpio, re.IGNORECASE):
                datos["mac"] = texto_limpio.upper()
            else:
                datos["serial"] = texto_limpio.upper()

    # 4. DETECCIÓN DE PON (Opcional - Mejora profesional)
    # Si el serial empieza por 'ZTEG' o 'HWTC' podemos predecir el tipo
    if datos["serial"]:
        if datos["serial"].startswith("ZTEG"): datos["pon"] = "GPON (ZTE)"
        elif datos["serial"].startswith("HWTC"): datos["pon"] = "GPON (HW)"

    return datos