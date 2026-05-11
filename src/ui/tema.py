# ============================================================
# tema.py — Paleta Digicable · Modo Oscuro + Claro
# ============================================================

class TemaOscuro:
    # Fondos
    bg           = "#0a0d14"
    surface      = "#111827"
    surface2     = "#1c2537"
    sidebar      = "#060911"
    topbar       = "#111827"

    # Acento principal (naranja en oscuro)
    accent       = "#F57C00"
    accent_hover = "#FF9800"
    accent_soft  = "#2a1800"

    # Acento secundario (azul en oscuro)
    accent2      = "#1E88E5"
    accent2_hover= "#42A5F5"

    # Semáforo
    verde        = "#16a34a"
    verde_soft   = "#052010"
    rojo         = "#dc2626"
    rojo_soft    = "#200505"
    amarillo     = "#d97706"

    # Texto
    texto        = "#f1f5f9"
    texto_muted  = "#8da0b5"
    texto_dim    = "#4a5568"

    # Bordes
    borde        = "#1e2d45"
    borde2       = "#2a3d55"

    # Nav activo
    nav_active_bg    = "#F57C00"
    nav_active_text  = "#ffffff"
    nav_hover_bg     = "#1a2233"

    # Logo a usar
    logo_path    = "assets/digicable_naranja.png"

    # Fuentes
    font_title   = ("Segoe UI", 16, "bold")
    font_sub     = ("Segoe UI", 13, "bold")
    font_normal  = ("Segoe UI", 12)
    font_sm      = ("Segoe UI", 10)
    font_xs      = ("Segoe UI", 9)
    font_mono    = ("Consolas", 11)
    font_big     = ("Segoe UI", 22, "bold")

    # Radios
    r_card  = 16
    r_btn   = 12
    r_chip  = 8
    r_pill  = 100

    # LED
    led_on  = "#22c55e"
    led_off = "#4a5568"


class TemaClaro:
    # Fondos
    bg           = "#f0f4f8"
    surface      = "#ffffff"
    surface2     = "#f7f9fc"
    sidebar      = "#1a2540"
    topbar       = "#ffffff"

    # Acento principal (azul en claro)
    accent       = "#1565C0"
    accent_hover = "#1E88E5"
    accent_soft  = "#e3eeff"

    # Acento secundario (naranja en claro)
    accent2      = "#F57C00"
    accent2_hover= "#FF9800"

    # Semáforo
    verde        = "#16a34a"
    verde_soft   = "#dcfce7"
    rojo         = "#dc2626"
    rojo_soft    = "#fee2e2"
    amarillo     = "#d97706"

    # Texto
    texto        = "#0d1b2a"
    texto_muted  = "#5a6a7e"
    texto_dim    = "#94a3b8"

    # Bordes
    borde        = "#dde3ec"
    borde2       = "#c8d0dc"

    # Nav activo
    nav_active_bg    = "#1565C0"
    nav_active_text  = "#ffffff"
    nav_hover_bg     = "rgba(255,255,255,0.08)"

    # Logo a usar
    logo_path    = "assets/digicable_azul.png"

    # Fuentes (idéntico al oscuro)
    font_title   = ("Segoe UI", 16, "bold")
    font_sub     = ("Segoe UI", 13, "bold")
    font_normal  = ("Segoe UI", 12)
    font_sm      = ("Segoe UI", 10)
    font_xs      = ("Segoe UI", 9)
    font_mono    = ("Consolas", 11)
    font_big     = ("Segoe UI", 22, "bold")

    # Radios
    r_card  = 16
    r_btn   = 12
    r_chip  = 8
    r_pill  = 100

    # LED
    led_on  = "#16a34a"
    led_off = "#94a3b8"


# Tema activo por defecto
Tema = TemaOscuro
