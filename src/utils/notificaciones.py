# ============================================================
# notificaciones.py — Notificaciones de escritorio
# Usa winotify en Windows. Fallback a print en otros SO.
# ============================================================
import platform
import threading


def _notificar_windows(titulo: str, mensaje: str, icono: str = "info"):
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


def notificar(titulo: str, mensaje: str, icono: str = "info"):
    """Lanza una notificación en un hilo separado para no bloquear la UI."""
    if platform.system() == "Windows":
        t = threading.Thread(
            target=_notificar_windows,
            args=(titulo, mensaje, icono),
            daemon=True
        )
        t.start()
    else:
        # En Linux/Mac solo imprime (para desarrollo)
        print(f"[{icono.upper()}] {titulo}: {mensaje}")


# ── Atajos semánticos ─────────────────────────────────────
def onu_detectada(nombre_display: str, mac: str):
    notificar(
        "🔌 ONU Detectada",
        f"{nombre_display}\nMAC: {mac}",
        "info"
    )

def instalacion_exitosa(nombre_display: str, ip_final: str):
    notificar(
        "✅ Configuración Exitosa",
        f"{nombre_display} lista\nIP: {ip_final} | Clave: digicable19",
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

def mostrar_mensaje(texto: str, tipo: str = "info"):
    """
    Muestra un mensaje simple en consola o notificación.
    Se usa como fallback para pantallas que no requieren Toast.
    """
    iconos = {
        "info": "ℹ️",
        "exito": "✅",
        "error": "❌",
        "warning": "⚠️"
    }
    icono = iconos.get(tipo, "ℹ️")
    print(f"{icono} {texto}")
