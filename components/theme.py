import flet as ft

class ThemeColors:
    # Surfaces & Backgrounds
    BG_DARK = "#0F172A"       # Slate 900 (Main Dark Surface / Sidebar)
    BG_SIDEBAR = "#1E293B"    # Slate 800 (Sidebar Background)
    BG_SIDEBAR_ACTIVE = "#334155" # Slate 700 (Active Sidebar Item)
    BG_PAGE = "#F1F5F9"       # Slate 100 (Clean Light Content Background)
    SURFACE_WHITE = "#FFFFFF" # Pure White Card Background
    SURFACE_HOVER = "#F8FAFC" # Slate 50
    
    # Borders & Dividers
    BORDER_LIGHT = "#E2E8F0"  # Slate 200
    BORDER_DARK = "#334155"   # Slate 700
    
    # Typography
    TEXT_MAIN = "#0F172A"     # Slate 900
    TEXT_MUTED = "#64748B"    # Slate 500
    TEXT_LIGHT = "#94A3B8"    # Slate 400
    TEXT_WHITE = "#FFFFFF"    # Pure White
    
    # Steakhouse Accent Colors
    AMBER_GOLD = "#F59E0B"    # Warm Amber 500
    AMBER_DARK = "#D97706"    # Amber 600
    CRIMSON = "#EF4444"       # Red 500
    CRIMSON_DARK = "#DC2626"  # Red 600
    EMERALD = "#10B981"       # Emerald 500 (Success / Active)
    SAPPHIRE = "#2563EB"      # Blue 600 (Primary Action)
    INDIGO = "#6366F1"        # Indigo 500 (Admin / Special)
    PURPLE = "#8B5CF6"        # Violet 500 (Reserved)
    
    # Status Tones
    STATUS_AVAILABLE = "#10B981" # Green
    STATUS_OCCUPIED = "#F59E0B"  # Amber
    STATUS_BILLED = "#2563EB"    # Blue
    STATUS_RESERVED = "#8B5CF6"  # Purple
    STATUS_CANCELLED = "#EF4444" # Red


def create_card(
    content: ft.Control, 
    padding: int = 20, 
    border_radius: int = 12, 
    elevation: bool = True,
    on_click = None,
    ink: bool = False
) -> ft.Container:
    """Standardized white card container with subtle shadow and optional full-surface click handler."""
    return ft.Container(
        content=content,
        bgcolor=ThemeColors.SURFACE_WHITE,
        border_radius=border_radius,
        padding=padding,
        ink=ink,
        on_click=on_click,
        border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=8,
            color="#0000000D",
            offset=ft.Offset(0, 2)
        ) if elevation else None
    )


def create_badge(text: str, bg_color: str, text_color: str = ThemeColors.TEXT_WHITE, icon: str = None) -> ft.Container:
    """Standardized pill badge."""
    row_controls = []
    if icon:
        row_controls.append(ft.Icon(icon, size=14, color=text_color))
    row_controls.append(ft.Text(text, size=12, weight=ft.FontWeight.W_600, color=text_color))
    
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        bgcolor=bg_color,
        border_radius=16,
        content=ft.Row(
            spacing=4,
            tight=True,
            controls=row_controls
        )
    )


def create_button(
    text: str,
    icon: str = None,
    on_click = None,
    bg_color: str = ThemeColors.BG_DARK,
    text_color: str = ThemeColors.TEXT_WHITE,
    height: int = 40,
    width: int = None
) -> ft.ElevatedButton:
    """Standardized high-contrast action button."""
    return ft.ElevatedButton(
        text,
        icon=icon,
        on_click=on_click,
        height=height,
        width=width,
        style=ft.ButtonStyle(
            bgcolor=bg_color,
            color=text_color,
            elevation=0,
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.Padding.symmetric(horizontal=16, vertical=8)
        )
    )
