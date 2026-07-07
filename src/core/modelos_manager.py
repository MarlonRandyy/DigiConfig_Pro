# ============================================================
# modelos_manager.py — Gestión de la base de datos de modelos
# CRUD completo con validaciones, copia de archivos y limpieza
# ============================================================
import json
import os
import shutil

# ─── Rutas ─────────────────────────────────────────────────────
# Calculamos la raíz del proyecto (subimos 3 niveles desde src/core)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# NUEVA RUTA: Ahora se guarda dentro de la carpeta configs/ (que es más segura)
RUTA_JSON = os.path.join(BASE_DIR, "configs", "modelos.json")
RUTA_IMAGENES = os.path.join(BASE_DIR, "configs", "imagenes")
RUTA_FIRMWARES = os.path.join(BASE_DIR, "configs", "firmwares")

# ─── Campos obligatorios para que un modelo sea válido ──────
CAMPOS_OBLIGATORIOS = [
    "ip_fabrica",
    "usuario_fabrica",
    "clave_fabrica",
    "ip_configurada",
    "usuario_final",
    "clave_final",
    "campo_upload",
    "tiempo_reinicio",
    # NOTA: "ruta_upload" no es obligatorio porque se puede dejar vacío
    # y el instalador usará "/" por defecto.
]


# ──────────────────────────────────────────────────────────────
#  FUNCIONES DE CARGA / GUARDADO (con logs de depuración)
# ──────────────────────────────────────────────────────────────
def cargar() -> dict:
    """Carga y retorna todo el dict de modelos."""
    try:
        with open(RUTA_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Si no existe, devolvemos dict vacío (es normal la primera vez)
        return {}
    except Exception as e:
        print(f"[MODELOS] Error al cargar {RUTA_JSON}: {e}")
        return {}


def guardar(modelos: dict):
    """
    Sobrescribe modelos.json con el dict actualizado.
    Ahora fuerza la creación de la carpeta configs/ si no existe.
    """
    try:
        # Asegurar que el directorio configs/ existe
        os.makedirs(os.path.dirname(RUTA_JSON), exist_ok=True)
        with open(RUTA_JSON, "w", encoding="utf-8") as f:
            json.dump(modelos, f, indent=4, ensure_ascii=False)
        print(f"[MODELOS] ✅ Datos guardados correctamente en: {RUTA_JSON}")
    except Exception as e:
        print(f"[MODELOS] ❌ ERROR CRÍTICO al guardar {RUTA_JSON}: {e}")
        # Relanzamos la excepción para que el usuario vea el error en la UI/consola
        raise


# ──────────────────────────────────────────────────────────────
#  VALIDACIÓN DE MODELO (sin cambios, pero mantenemos)
# ──────────────────────────────────────────────────────────────
def validar_modelo(datos: dict) -> tuple[bool, str]:
    """
    Verifica que el diccionario tenga todos los campos obligatorios
    y que el tiempo de reinicio sea un número entero positivo.
    Retorna (valido, mensaje_error).
    """
    faltantes = [campo for campo in CAMPOS_OBLIGATORIOS if not datos.get(campo)]
    if faltantes:
        return False, f"Campos obligatorios faltantes: {', '.join(faltantes)}"

    # Validar tiempo de reinicio (debe ser entero > 0)
    try:
        tiempo = int(datos["tiempo_reinicio"])
        if tiempo < 10:
            return False, "El tiempo de reinicio debe ser al menos 10 segundos."
        datos["tiempo_reinicio"] = tiempo  # lo normalizamos a entero
    except (ValueError, TypeError):
        return False, "El tiempo de reinicio debe ser un número entero."

    return True, "OK"


# ──────────────────────────────────────────────────────────────
#  CRUD DE MODELOS (con optimización de caché)
# ──────────────────────────────────────────────────────────────
# Cache en memoria para no leer el JSON cada vez
_cache_modelos = None


def _obtener_cache() -> dict:
    """Lee el JSON solo si el caché está vacío (optimización de rendimiento)."""
    global _cache_modelos
    if _cache_modelos is None:
        _cache_modelos = cargar()
    return _cache_modelos


def _invalidar_cache():
    """Invalida el caché después de guardar cambios."""
    global _cache_modelos
    _cache_modelos = None


def agregar_modelo(modelo_id: str, datos: dict,
                   ruta_imagen_src: str = None,
                   ruta_xml_src: str = None) -> bool:
    """
    Agrega un nuevo modelo. Copia imagen y XML a las carpetas del proyecto.
    Retorna True si se guardó correctamente.
    """
    # 1. Validar ID
    if not modelo_id or not modelo_id.strip():
        print("[MODELOS] Error: ID de modelo vacío")
        return False

    modelo_id = modelo_id.strip()

    # 2. Validar que no exista ya
    modelos = _obtener_cache()
    if modelo_id in modelos:
        print(f"[MODELOS] Error: El ID '{modelo_id}' ya existe")
        return False

    # 3. Validar campos obligatorios
    valido, msg = validar_modelo(datos)
    if not valido:
        print(f"[MODELOS] Error de validación: {msg}")
        return False

    # 4. Limpiar el diccionario (eliminar claves vacías)
    datos = {k: v for k, v in datos.items() if v is not None and v != ""}

    # 5. Copiar archivos (con rollback en caso de error)
    archivos_copiados = []

    try:
        # 5a. Copiar imagen
        if ruta_imagen_src and os.path.exists(ruta_imagen_src):
            ext = os.path.splitext(ruta_imagen_src)[1]
            if not ext:
                ext = ".png"
            nombre_img = f"{modelo_id.lower()}{ext}"
            destino_img = os.path.join(RUTA_IMAGENES, nombre_img)
            os.makedirs(RUTA_IMAGENES, exist_ok=True)
            shutil.copy2(ruta_imagen_src, destino_img)
            datos["imagen"] = f"configs/imagenes/{nombre_img}"
            archivos_copiados.append(destino_img)

        # 5b. Copiar XML
        if ruta_xml_src and os.path.exists(ruta_xml_src):
            nombre_xml = f"{modelo_id.lower()}.xml"
            destino_xml = os.path.join(RUTA_FIRMWARES, nombre_xml)
            os.makedirs(RUTA_FIRMWARES, exist_ok=True)
            shutil.copy2(ruta_xml_src, destino_xml)
            datos["firmware_xml"] = f"configs/firmwares/{nombre_xml}"
            archivos_copiados.append(destino_xml)
        else:
            # XML es obligatorio
            raise ValueError("No se proporcionó un archivo XML válido.")

        # 6. Guardar en JSON (actualizar caché y disco)
        modelos[modelo_id] = datos
        guardar(modelos)
        _invalidar_cache()  # Forzar recarga en futuras lecturas
        return True

    except Exception as e:
        print(f"[MODELOS] Error al agregar modelo '{modelo_id}': {e}")
        # Rollback: eliminar archivos ya copiados
        for archivo in archivos_copiados:
            try:
                if os.path.exists(archivo):
                    os.remove(archivo)
            except Exception:
                pass
        return False


def actualizar_modelo(modelo_id: str, datos_nuevos: dict,
                      ruta_imagen_src: str = None,
                      ruta_xml_src: str = None) -> bool:
    """
    Actualiza un modelo existente.

    IMPORTANTE: datos_nuevos debe contener el diccionario COMPLETO del
    modelo (no solo los campos que cambiaron), ya que validar_modelo()
    exige la presencia de todos los CAMPOS_OBLIGATORIOS. La pantalla
    que llama a esta función es responsable de fusionar los datos
    existentes con los cambios antes de invocarla.

    Si se proporciona ruta_imagen_src y/o ruta_xml_src, se copian los
    nuevos archivos (reemplazando los anteriores) con el mismo
    mecanismo de rollback que agregar_modelo().
    """
    try:
        modelos = _obtener_cache()
        if modelo_id not in modelos:
            print(f"[MODELOS] Error: el modelo '{modelo_id}' no existe")
            return False

        datos_nuevos = dict(datos_nuevos)  # copia defensiva

        # Validar que el diccionario completo cumpla los campos obligatorios
        valido, msg = validar_modelo(datos_nuevos)
        if not valido:
            print(f"[MODELOS] Error de validación en actualización: {msg}")
            return False

        # Limpiar claves vacías, igual que en agregar_modelo
        datos_nuevos = {k: v for k, v in datos_nuevos.items() if v is not None and v != ""}

        archivos_copiados = []
        archivos_a_borrar_si_exito = []

        try:
            # Reemplazar imagen si se proporcionó una nueva
            if ruta_imagen_src and os.path.exists(ruta_imagen_src):
                ext = os.path.splitext(ruta_imagen_src)[1] or ".png"
                nombre_img = f"{modelo_id.lower()}{ext}"
                destino_img = os.path.join(RUTA_IMAGENES, nombre_img)
                os.makedirs(RUTA_IMAGENES, exist_ok=True)

                imagen_anterior = modelos[modelo_id].get("imagen")
                shutil.copy2(ruta_imagen_src, destino_img)
                datos_nuevos["imagen"] = f"configs/imagenes/{nombre_img}"
                archivos_copiados.append(destino_img)
                if imagen_anterior and imagen_anterior != datos_nuevos["imagen"]:
                    ruta_anterior_abs = (imagen_anterior if os.path.isabs(imagen_anterior)
                                         else os.path.join(BASE_DIR, imagen_anterior))
                    archivos_a_borrar_si_exito.append(ruta_anterior_abs)

            # Reemplazar XML si se proporcionó uno nuevo
            if ruta_xml_src and os.path.exists(ruta_xml_src):
                nombre_xml = f"{modelo_id.lower()}.xml"
                destino_xml = os.path.join(RUTA_FIRMWARES, nombre_xml)
                os.makedirs(RUTA_FIRMWARES, exist_ok=True)

                xml_anterior = modelos[modelo_id].get("firmware_xml")
                shutil.copy2(ruta_xml_src, destino_xml)
                datos_nuevos["firmware_xml"] = f"configs/firmwares/{nombre_xml}"
                archivos_copiados.append(destino_xml)
                if xml_anterior and xml_anterior != datos_nuevos["firmware_xml"]:
                    ruta_anterior_abs = (xml_anterior if os.path.isabs(xml_anterior)
                                         else os.path.join(BASE_DIR, xml_anterior))
                    archivos_a_borrar_si_exito.append(ruta_anterior_abs)

            # Aplicar la actualización al diccionario en memoria y guardar
            modelos[modelo_id].update(datos_nuevos)
            guardar(modelos)
            _invalidar_cache()  # Forzar recarga

            # Limpiar archivos viejos solo después de guardar con éxito
            for ruta_vieja in archivos_a_borrar_si_exito:
                try:
                    if os.path.exists(ruta_vieja):
                        os.remove(ruta_vieja)
                except Exception:
                    pass

            return True

        except Exception as e:
            print(f"[MODELOS] Error al actualizar archivos de '{modelo_id}': {e}")
            # Rollback: eliminar archivos nuevos ya copiados
            for archivo in archivos_copiados:
                try:
                    if os.path.exists(archivo):
                        os.remove(archivo)
                except Exception:
                    pass
            return False

    except Exception as e:
        print(f"[MODELOS] Error al actualizar '{modelo_id}': {e}")
        return False


def eliminar_modelo(modelo_id: str) -> bool:
    """
    Elimina un modelo del JSON y borra sus archivos asociados (imagen y XML).
    """
    try:
        modelos = _obtener_cache()
        if modelo_id not in modelos:
            return False

        datos = modelos[modelo_id]

        # Borrar archivos físicos
        for campo in ["imagen", "firmware_xml"]:
            ruta = datos.get(campo)
            if ruta:
                if not os.path.isabs(ruta):
                    ruta = os.path.join(BASE_DIR, ruta)
                if os.path.exists(ruta):
                    try:
                        os.remove(ruta)
                        print(f"[MODELOS] Archivo eliminado: {ruta}")
                    except Exception as e:
                        print(f"[MODELOS] No se pudo eliminar {ruta}: {e}")

        # Eliminar del JSON
        del modelos[modelo_id]
        guardar(modelos)
        _invalidar_cache()
        return True

    except Exception as e:
        print(f"[MODELOS] Error al eliminar '{modelo_id}': {e}")
        return False


def obtener(modelo_id: str) -> dict | None:
    """Retorna el dict de un modelo específico o None."""
    modelos = _obtener_cache()
    return modelos.get(modelo_id)


def listar_ids() -> list:
    """Lista de IDs de todos los modelos registrados."""
    modelos = _obtener_cache()
    return list(modelos.keys())


def obtener_campos_obligatorios() -> list:
    """Retorna la lista de campos obligatorios (para la UI)."""
    return CAMPOS_OBLIGATORIOS.copy()