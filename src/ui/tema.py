# ============================================================
# tema.py — Paleta Corporativa "Light Mode" Invertida
# ============================================================

class Tema:
    # ─── Fondos (Invertidos: De oscuro a claro) ────────────────
    bg          = "#F8FAFC"      # Blanco muy suave (Fondo general)
    surface     = "#FFFFFF"      # Blanco puro (Cards/Paneles)
    surface2    = "#E2E8F0"      # Gris claro (Separadores/Bordes)
    sidebar     = "#002B7F"      # Azul corporativo profundo (Mantiene la identidad)
    topbar      = "#FFFFFF"      # Blanco para contraste superior

    # ─── Bordes ──────────────────────────────────────────────────
    borde       = "#CBD5E1"      # Gris claro para bordes principales
    borde2      = "#E2E8F0"      # Gris más claro para bordes secundarios

    # ─── Acentos (Azul vibrante sobre fondo claro) ─────────────
    accent      = "#0062FF"      # Azul Digicable (Botones, estados)
    accent_hover= "#0047BA"      # Acción hover (más oscuro)
    accent_soft = "#E0EFFF"      # Fondo suave para elementos seleccionados

    # Secundario (Azul marino oscuro para textos importantes)
    accent2     = "#1E293B"      # Azul oscuro institucional
    accent2_hover = "#0F172A"

    # ─── Semáforo (Ajustado para legibilidad en fondo claro) ───
    verde       = "#16A34A"      # Éxito sólido
    verde_soft  = "#DCFCE7"      # Fondo éxito
    rojo        = "#DC2626"      # Error sólido
    rojo_soft   = "#FEE2E2"      # Fondo error
    amarillo    = "#D97706"      # Alerta (naranja oscuro para que se lea bien)

    # ─── Textos (Invertidos: De blanco a azul marino) ─────────
    texto       = "#1E293B"      # Azul marino profundo (Legible en fondo blanco)
    texto_muted = "#475569"      # Gris profesional (Texto secundario)
    texto_dim   = "#94A3B8"      # Gris tenue (Etiquetas/Placeholders)

    # ─── Navegación activa (Específico para Sidebar) ──────────
    nav_active_bg   = "#FDA219"  # Botón activo blanco sobre sidebar azul
    nav_active_text = "#002B7F"  # Texto azul sobre botón activo blanco
    nav_hover_bg    = "#0035A0"  # Hover más claro sobre sidebar azul
    
    # ─── Logo ─────────────────────────────────────────────────
    # Asegúrate de usar la versión blanca del logo en el sidebar
    logo_path   = "assets/digicable_blanco.png"

    # ─── Fuentes ──────────────────────────────────────────────
    font_title  = ("Segoe UI", 16, "bold")
    font_sub    = ("Segoe UI", 13, "bold")
    font_normal = ("Segoe UI", 12)
    font_sm     = ("Segoe UI", 10)
    font_xs     = ("Segoe UI", 9)
    font_mono   = ("Consolas", 11)
    font_big    = ("Segoe UI", 22, "bold")

    # ─── Radios ───────────────────────────────────────────────
    r_card      = 12
    r_btn       = 8
    r_chip      = 6
    r_pill      = 100

    # ─── LED (Colores de estado) ──────────────────────────────
    led_on      = "#16A34A"      # Verde legible
    led_off     = "#CBD5E1"      # Gris claro (se percibe apagado)