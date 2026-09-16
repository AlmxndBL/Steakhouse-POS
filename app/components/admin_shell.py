import flet as ft
from components.theme import ThemeColors, create_badge
from utils.navigation import navigate_to

class AdminShell(ft.Container):
    """
    Persistent Left Sidebar Shell for all Admin and Back-office Workspaces.
    Provides instant 1-click navigation between admin modules with breadcrumbs & role status.
    """
    def __init__(
        self,
        page: ft.Page,
        current_route: str,
        title: str,
        subtitle: str = "",
        content_control: ft.Control = None,
        header_actions: list = None
    ):
        self.page_ref = page
        self.current_route = current_route
        
        user_name = page.session.store.get("user_name") or "ผู้บริหาร"
        user_role = page.session.store.get("user_role") or "OWNER"
        self.user_role = user_role.value if hasattr(user_role, "value") else str(user_role)
        
        # Build Navigation Items
        sidebar_items = [
            # Group 1: Overview
            ft.Container(
                padding=ft.Padding.only(left=12, top=16, bottom=6),
                content=ft.Text("ภาพรวม", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_LIGHT)
            ),
            self._build_nav_item("/admin", ft.Icons.DASHBOARD_ROUNDED, "แดชบอร์ดภาพรวม"),
            
            # Group 2: Catalog & Store
            ft.Container(
                padding=ft.Padding.only(left=12, top=16, bottom=6),
                content=ft.Text("จัดการร้านอาหาร", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_LIGHT)
            ),
            self._build_nav_item("/admin/menus", ft.Icons.RESTAURANT_MENU, "เมนูอาหาร & หมวดหมู่"),
            self._build_nav_item("/admin/tables", ft.Icons.TABLE_RESTAURANT, "ผังโต๊ะ & โซนที่นั่ง"),
            
            # Group 3: Inventory
            ft.Container(
                padding=ft.Padding.only(left=12, top=16, bottom=6),
                content=ft.Text("คลังวัตถุดิบ & ต้นทุน", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_LIGHT)
            ),
            self._build_nav_item("/admin/stock", ft.Icons.INVENTORY_2_ROUNDED, "คลังสินค้า & สต็อก"),
            
            # Group 4: Finance
            ft.Container(
                padding=ft.Padding.only(left=12, top=16, bottom=6),
                content=ft.Text("การเงิน & บัญชี", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_LIGHT)
            ),
            self._build_nav_item("/admin/reports", ft.Icons.BAR_CHART_ROUNDED, "รายงานยอดขาย"),
            
            # Group 5: Organization & Security
            ft.Container(
                padding=ft.Padding.only(left=12, top=16, bottom=6),
                content=ft.Text("ระบบ & ความปลอดภัย", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_LIGHT)
            ),
            self._build_nav_item("/admin/staff", ft.Icons.PEOPLE_ALT_ROUNDED, "จัดการพนักงาน & สิทธิ์"),
            self._build_nav_item("/admin/audit", ft.Icons.SECURITY_ROUNDED, "บันทึกประวัติ (Audit Logs)"),
        ]
        
        # Left Sidebar Layout
        sidebar = ft.Container(
            width=260,
            bgcolor=ThemeColors.BG_SIDEBAR,
            padding=ft.Padding.all(16),
            content=ft.Column(
                spacing=4,
                controls=[
                    # Brand Header
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=8, vertical=12),
                        content=ft.Row(
                            spacing=10,
                            controls=[
                                ft.Container(
                                    width=38,
                                    height=38,
                                    bgcolor=ThemeColors.AMBER_GOLD,
                                    border_radius=8,
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Icon(ft.Icons.RESTAURANT_MENU_ROUNDED, size=22, color=ThemeColors.BG_DARK)
                                ),
                                ft.Column(
                                    spacing=0,
                                    controls=[
                                        ft.Text("STEAKHOUSE", size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_WHITE),
                                        ft.Text("Executive Console", size=11, color=ThemeColors.AMBER_GOLD, weight=ft.FontWeight.W_500)
                                    ]
                                )
                            ]
                        )
                    ),
                    ft.Divider(height=1, color=ThemeColors.BORDER_DARK),
                    
                    # Scrollable Nav Items
                    ft.Container(
                        expand=True,
                        content=ft.ListView(
                            spacing=4,
                            controls=sidebar_items
                        )
                    ),
                    
                    # Switch to POS Front Desk
                    ft.Divider(height=1, color=ThemeColors.BORDER_DARK),
                    ft.Container(
                        padding=ft.Padding.symmetric(vertical=8),
                        content=ft.ElevatedButton(
                            "เปิดหน้าร้าน POS",
                            icon=ft.Icons.POINT_OF_SALE,
                            style=ft.ButtonStyle(
                                bgcolor=ThemeColors.AMBER_DARK,
                                color=ThemeColors.TEXT_WHITE,
                                shape=ft.RoundedRectangleBorder(radius=8),
                                padding=ft.Padding.symmetric(horizontal=12, vertical=10)
                            ),
                            width=228,
                            on_click=lambda e: navigate_to(self.page_ref, "/pos")
                        )
                    ),
                    
                    # User Profile Footer
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=10, vertical=10),
                        bgcolor=ThemeColors.BG_SIDEBAR_ACTIVE,
                        border_radius=8,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.CircleAvatar(
                                            bgcolor=ThemeColors.INDIGO,
                                            radius=16,
                                            content=ft.Icon(ft.Icons.PERSON, size=18, color=ThemeColors.TEXT_WHITE)
                                        ),
                                        ft.Column(
                                            spacing=0,
                                            controls=[
                                                ft.Text(user_name, size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_WHITE),
                                                ft.Text(user_role, size=10, color=ThemeColors.TEXT_LIGHT)
                                            ]
                                        )
                                    ]
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.LOGOUT_ROUNDED,
                                    icon_size=18,
                                    icon_color=ThemeColors.CRIMSON,
                                    tooltip="ออกจากระบบ",
                                    on_click=self._handle_logout
                                )
                            ]
                        )
                    )
                ]
            )
        )
        
        # Top Header Bar
        actions_row = header_actions or []
        top_header = ft.Container(
            height=65,
            bgcolor=ThemeColors.SURFACE_WHITE,
            padding=ft.Padding.symmetric(horizontal=24, vertical=12),
            border=ft.Border(bottom=ft.BorderSide(1, ThemeColors.BORDER_LIGHT)),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    # Breadcrumb & Title
                    ft.Column(
                        spacing=0,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Text("ระบบจัดการหลังบ้าน", size=12, color=ThemeColors.TEXT_MUTED),
                                    ft.Text(">", size=12, color=ThemeColors.TEXT_LIGHT),
                                    ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN)
                                ]
                            ),
                            ft.Text(subtitle, size=11, color=ThemeColors.TEXT_MUTED) if subtitle else ft.Container()
                        ]
                    ),
                    # Header Actions & Role Badge
                    ft.Row(
                        spacing=12,
                        controls=[
                            *actions_row,
                            create_badge(f"👑 {user_role}", ThemeColors.BG_DARK, ThemeColors.AMBER_GOLD)
                        ]
                    )
                ]
            )
        )
        
        # Main Work Surface
        main_surface = ft.Container(
            expand=True,
            bgcolor=ThemeColors.BG_PAGE,
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    top_header,
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.all(24),
                        content=content_control or ft.Container()
                    )
                ]
            )
        )
        
        super().__init__(
            expand=True,
            content=ft.Row(
                expand=True,
                spacing=0,
                controls=[sidebar, main_surface]
            )
        )
    
    def _build_nav_item(self, route: str, icon: str, label: str) -> ft.Container:
        is_active = self.current_route == route or (route != "/admin" and self.current_route.startswith(route))
        bg = ThemeColors.BG_SIDEBAR_ACTIVE if is_active else "transparent"
        text_color = ThemeColors.AMBER_GOLD if is_active else ThemeColors.TEXT_WHITE
        icon_color = ThemeColors.AMBER_GOLD if is_active else ThemeColors.TEXT_LIGHT
        weight = ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL
        
        return ft.Container(
            visible=self.user_role in {"OWNER", "MANAGER"},
            border_radius=8,
            bgcolor=bg,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            ink=True,
            on_click=lambda e: navigate_to(self.page_ref, route),
            content=ft.Row(
                spacing=12,
                controls=[
                    ft.Icon(icon, size=18, color=icon_color),
                    ft.Text(label, size=13, color=text_color, weight=weight)
                ]
            )
        )
    
    def _handle_logout(self, e):
        self.page_ref.session.store.clear()
        navigate_to(self.page_ref, "/login")
