import flet as ft
from components.theme import ThemeColors, create_badge
from utils.navigation import navigate_to

def create_pos_header(
    page: ft.Page,
    title: str,
    subtitle: str = "Front-of-House POS Terminal",
    icon: str = ft.Icons.POINT_OF_SALE,
    back_route: str = None,
    action_controls: list = None
) -> ft.Container:
    """
    Standardized Top Header for Full-Screen POS / Table Map screens.
    """
    user_name = page.session.store.get("user_name") or "พนักงาน"
    user_role = page.session.store.get("user_role") or "STAFF"
    
    left_controls = []
    if back_route:
        left_controls.append(
            ft.IconButton(
                ft.Icons.ARROW_BACK_ROUNDED,
                icon_color=ThemeColors.TEXT_WHITE,
                tooltip="ย้อนกลับ",
                on_click=lambda e: navigate_to(page, back_route)
            )
        )
    
    left_controls.extend([
        ft.Container(
            width=36,
            height=36,
            bgcolor=ThemeColors.AMBER_GOLD,
            border_radius=8,
            alignment=ft.Alignment(0, 0),
            content=ft.Icon(icon, size=20, color=ThemeColors.BG_DARK)
        ),
        ft.Column(
            spacing=0,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_WHITE),
                ft.Text(subtitle, size=11, color=ThemeColors.TEXT_LIGHT)
            ]
        )
    ])
    
    right_controls = list(action_controls or [])
    
    # Add Admin Switcher if authorized
    if user_role in ["OWNER", "MANAGER"]:
        right_controls.append(
            ft.ElevatedButton(
                "แดชบอร์ดแอดมิน",
                icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                style=ft.ButtonStyle(
                    bgcolor=ThemeColors.BG_SIDEBAR_ACTIVE,
                    color=ThemeColors.AMBER_GOLD,
                    shape=ft.RoundedRectangleBorder(radius=6),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8)
                ),
                on_click=lambda e: navigate_to(page, "/admin")
            )
        )
    
    # Role Badge & User Info
    right_controls.extend([
        create_badge(f"👤 {user_name} ({user_role})", ThemeColors.BG_SIDEBAR_ACTIVE, ThemeColors.TEXT_WHITE),
        ft.IconButton(
            icon=ft.Icons.LOGOUT_ROUNDED,
            icon_color=ThemeColors.CRIMSON,
            tooltip="ออกจากระบบ",
            on_click=lambda e: _logout(page)
        )
    ])
    
    return ft.Container(
        height=62,
        bgcolor=ThemeColors.BG_DARK,
        padding=ft.Padding.symmetric(horizontal=20, vertical=10),
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=6, color="#00000033", offset=ft.Offset(0, 2)),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(spacing=12, controls=left_controls),
                ft.Row(spacing=10, controls=right_controls)
            ]
        )
    )

def _logout(page: ft.Page):
    page.session.store.clear()
    navigate_to(page, "/login")
