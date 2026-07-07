# ============================================================
# notificaciones.py — Notificaciones de escritorio
# Usa winotify en Windows. Fallback a print en otros SO.
# ============================================================
import platform
import threading


def _notificar_windows(titulo: str, mensaje: str, tipo: str = "info"):
    """Muestra notificación de escritorio tipo Toast en Windows."""
    try:
        from winotify import Notification, audio
        toast = Notification(
            app_id="DigiConfig Pro",
            title=titulo,
            msg=mensaje,
            duration="short",
            icon=""
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
    except Exception as e:
        print(f"[NOTIF] {titulo}: {mensaje} (sin GUI: {e})")


def notificar(titulo: str, mensaje: str, tipo: str = "info"):
    """Lanza una notificación en un hilo separado para no bloquear la UI."""
    if platform.system() == "Windows":
        t = threading.Thread(
            target=_notificar_windows,
            args=(titulo, mensaje, tipo),
            daemon=True
        )
        t.start()
    else:
        # En Linux/Mac solo imprime (para desarrollo)
        iconos = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}
        print(f"{iconos.get(tipo, 'ℹ️')} {titulo}: {mensaje}")


# ── Atajos semánticos (actualizados) ─────────────────────
def onu_detectada(nombre_display: str, mac: str):
    notificar(
        "🔌 ONU Detectada",
        f"{nombre_display}\nMAC: {mac}",
        "info"
    )


def instalacion_exitosa(nombre_display: str, ip_final: str, clave_final: str = "digicable19"):
    """
    Notifica que la instalación fue exitosa.
    Ahora incluye la clave final para que el técnico sepa cómo acceder.
    """
    notificar(
        "✅ Configuración Exitosa",
        f"{nombre_display} lista\nIP: {ip_final}\nClave: {clave_final}",
        "success"
    )


def error_instalacion(motivo: str):
    notificar(
        "❌ Error de Instalación",
        motivo,
        "error"
    )


def onu_desconectada():
    notificar(
        "🔌 ONU Desconectada",
        "El equipo fue removido de la red local.",
        "info"
    )


def mostrar_mensaje(texto: str, tipo: str = "info", notificar_gui: bool = True):
    """
    Muestra un mensaje. Si notificar_gui es True, envía notificación de escritorio.
    En .exe es útil porque no hay consola visible.
    """
    if notificar_gui and platform.system() == "Windows":
        # Usar notificar para mostrar en ventana emergente
        titulo = {
            "info": "ℹ️ Información",
            "success": "✅ Éxito",
            "error": "❌ Error",
            "warning": "⚠️ Advertencia",
        }.get(tipo, "ℹ️ Información")
        notificar(titulo, texto, tipo)
    else:
        # Fallback a consola
        iconos = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}
        print(f"{iconos.get(tipo, 'ℹ️')} {texto}")