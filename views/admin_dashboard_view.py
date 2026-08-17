import flet as ft
from datetime import datetime, date, timezone
from database.connection import SessionLocal
from database.models import Order, OrderStatus, Table, TableStatus
from services.bom_engine import BOMEngine
from utils.navigation import navigate_to

class AdminDashboardView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        user_name = page.session.store.get("user_name") or "ผู้บริหาร"
        user_role = page.session.store.get("user_role") or "OWNER"

        # Theme Colors
        primary_color = ft.Colors.BLUE_900
        bg_color = ft.Colors.BLUE_GREY_50
        card_bg = ft.Colors.WHITE

        # Header Navigation
        nav_header = ft.Container(
            padding=ft.Padding.symmetric(horizontal=30, vertical=16),
            bgcolor=primary_color,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.BLACK12),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.Icon(ft.Icons.DASHBOARD_ROUNDED, color=ft.Colors.WHITE, size=28),
                            ft.Text("ระบบจัดการผู้บริหาร (Executive Dashboard)", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]
                    ),
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=14, vertical=6),
                                bgcolor=ft.Colors.BLUE_800,
                                border_radius=20,
                                content=ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=ft.Colors.AMBER_400, size=18),
                                        ft.Text(f"{user_name} ({user_role})", size=13, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)
                                    ]
                                )
                            ),
                            ft.ElevatedButton(
                                "🚪 ออกจากระบบ",
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.RED_700,
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    padding=ft.Padding.symmetric(horizontal=12, vertical=8)
                                ),
                                on_click=self._handle_logout
                            )
                        ]
                    )
                ]
            )
        )

        # KPI Metrics Cards
        self.kpi_sales_text = ft.Text("0.00 ฿", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
        self.kpi_bills_text = ft.Text("0 บิล", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)
        self.kpi_tables_text = ft.Text("0 / 0 โต๊ะ", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_800)
        self.kpi_low_stock_text = ft.Text("0 รายการ", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)

        kpi_cards = ft.ResponsiveRow(
            spacing=16,
            run_spacing=16,
            controls=[
                ft.Container(
                    col={"sm": 6, "md": 3},
                    content=self._build_kpi_card(
                        icon=ft.Icons.ATTACH_MONEY,
                        icon_color=ft.Colors.GREEN_700,
                        title="ยอดขายวันนี้",
                        value_control=self.kpi_sales_text,
                        bg_color=ft.Colors.GREEN_50
                    )
                ),
                ft.Container(
                    col={"sm": 6, "md": 3},
                    content=self._build_kpi_card(
                        icon=ft.Icons.RECEIPT_LONG,
                        icon_color=ft.Colors.BLUE_900,
                        title="บิลที่ชำระแล้ว",
                        value_control=self.kpi_bills_text,
                        bg_color=ft.Colors.BLUE_50
                    )
                ),
                ft.Container(
                    col={"sm": 6, "md": 3},
                    content=self._build_kpi_card(
                        icon=ft.Icons.TABLE_RESTAURANT,
                        icon_color=ft.Colors.AMBER_800,
                        title="โต๊ะที่มีลูกค้า",
                        value_control=self.kpi_tables_text,
                        bg_color=ft.Colors.AMBER_50
                    )
                ),
                ft.Container(
                    col={"sm": 6, "md": 3},
                    content=self._build_kpi_card(
                        icon=ft.Icons.WARNING_AMBER_ROUNDED,
                        icon_color=ft.Colors.RED_700,
                        title="ของใกล้หมดสต๊อก",
                        value_control=self.kpi_low_stock_text,
                        bg_color=ft.Colors.RED_50
                    )
                ),
            ]
        )

        # Action Navigation Grid
        actions_grid = ft.ResponsiveRow(
            spacing=20,
            run_spacing=20,
            controls=[
                ft.Container(
                    col={"sm": 12, "md": 4},
                    content=self._build_action_card(
                        title="👥 จัดการพนักงาน",
                        desc="เพิ่มพนักงานใหม่ กำหนดรหัสผ่าน และสิทธิ์เข้าใช้งาน",
                        icon=ft.Icons.BADGE,
                        icon_color=ft.Colors.INDIGO_700,
                        btn_label="จัดการพนักงาน",
                        on_click=lambda e: navigate_to(self.page_ref, "/admin/staff")
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 4},
                    content=self._build_action_card(
                        title="🥩 จัดการเมนูอาหาร",
                        desc="เพิ่มเมนูอาหาร ปรับราคาขาย เปิด/ปิดการขาย และหมวดหมู่",
                        icon=ft.Icons.RESTAURANT_MENU,
                        icon_color=ft.Colors.ORANGE_800,
                        btn_label="จัดการเมนูอาหาร",
                        on_click=lambda e: navigate_to(self.page_ref, "/admin/menus")
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 4},
                    content=self._build_action_card(
                        title="🪑 จัดการผังโต๊ะอาหาร",
                        desc="เพิ่ม/ลบโต๊ะ กำหนดจำนวนที่นั่ง และจัดโซนร้านอาหาร",
                        icon=ft.Icons.TABLE_RESTAURANT,
                        icon_color=ft.Colors.BLUE_GREY_800,
                        btn_label="จัดการผังโต๊ะ",
                        on_click=lambda e: navigate_to(self.page_ref, "/admin/tables")
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 4},
                    content=self._build_action_card(
                        title="📦 คลังวัตถุดิบ & ตัดสต๊อก",
                        desc="รับของเข้าคลัง, ตรวจนับสต๊อกจริง, ตัดของเสีย และสูตร BOM",
                        icon=ft.Icons.INVENTORY_2,
                        icon_color=ft.Colors.GREEN_800,
                        btn_label="จัดการคลังสินค้า",
                        on_click=lambda e: navigate_to(self.page_ref, "/stock")
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 4},
                    content=self._build_action_card(
                        title="📊 รายงานยอดขายและการเงิน",
                        desc="สรุปยอดขาย ประวัติการสั่งซื้อ และคำนวณ Food Cost %",
                        icon=ft.Icons.BAR_CHART,
                        icon_color=ft.Colors.BLUE_800,
                        btn_label="ดูรายงานการเงิน",
                        on_click=lambda e: navigate_to(self.page_ref, "/admin/reports")
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 4},
                    content=self._build_action_card(
                        title="📜 บันทึกประวัติระบบ (Audit Logs)",
                        desc="ตรวจสอบประวัติการทำงานของพนักงาน ใครทำอะไร เมื่อไหร่",
                        icon=ft.Icons.SECURITY,
                        icon_color=ft.Colors.DEEP_PURPLE_800,
                        btn_label="ดู Audit Logs",
                        on_click=lambda e: navigate_to(self.page_ref, "/admin/audit")
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 12},
                    content=self._build_action_card(
                        title="🍽️ สลับเข้าสู่หน้าร้าน (POS Table Map)",
                        desc="เปิดดูผังโต๊ะหน้าร้าน รับออเดอร์ Takeaway และคิดเงินลูกค้า",
                        icon=ft.Icons.POINT_OF_SALE,
                        icon_color=ft.Colors.TEAL_800,
                        btn_label="เปิดหน้าร้าน POS",
                        on_click=lambda e: navigate_to(self.page_ref, "/tables")
                    )
                ),
            ]
        )

        body_content = ft.Container(
            expand=True,
            padding=30,
            content=ft.ListView(
                spacing=25,
                controls=[
                    ft.Text("ภาพรวมและสถิติสำคัญประจำวัน", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                    kpi_cards,
                    ft.Divider(height=10, color=ft.Colors.GREY_300),
                    ft.Text("เมนูระบบบริหารจัดการร้าน", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                    actions_grid
                ]
            )
        )

        super().__init__(
            route="/admin",
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[nav_header, body_content]
                )
            ],
            bgcolor=bg_color,
            padding=0,
            spacing=0
        )

        self._load_kpi_data()

    def _build_kpi_card(self, icon, icon_color, title, value_control, bg_color):
        return ft.Card(
            elevation=1,
            shape=ft.RoundedRectangleBorder(radius=12),
            content=ft.Container(
                bgcolor=ft.Colors.WHITE,
                padding=20,
                border_radius=12,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=4,
                            controls=[
                                ft.Text(title, size=13, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                                value_control
                            ]
                        ),
                        ft.Container(
                            padding=12,
                            bgcolor=bg_color,
                            border_radius=12,
                            content=ft.Icon(icon, color=icon_color, size=28)
                        )
                    ]
                )
            )
        )

    def _build_action_card(self, title, desc, icon, icon_color, btn_label, on_click):
        return ft.Card(
            elevation=2,
            shape=ft.RoundedRectangleBorder(radius=14),
            content=ft.Container(
                bgcolor=ft.Colors.WHITE,
                padding=24,
                border_radius=14,
                ink=True,
                on_click=on_click,
                content=ft.Column(
                    spacing=14,
                    controls=[
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Icon(icon, color=icon_color, size=26),
                                ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)
                            ]
                        ),
                        ft.Text(desc, size=13, color=ft.Colors.GREY_600, max_lines=2),
                        ft.ElevatedButton(
                            btn_label,
                            icon=ft.Icons.ARROW_FORWARD,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.BLUE_GREY_50,
                                color=icon_color,
                                shape=ft.RoundedRectangleBorder(radius=8),
                                padding=ft.Padding.symmetric(vertical=12, horizontal=16)
                            ),
                            on_click=on_click
                        )
                    ]
                )
            )
        )

    def _load_kpi_data(self):
        db = SessionLocal()
        try:
            # 1. Total sales & paid orders
            paid_orders = db.query(Order).filter(Order.status == OrderStatus.PAID).all()
            total_sales = sum(float(o.net_amount) for o in paid_orders)
            self.kpi_sales_text.value = f"{total_sales:,.2f} ฿"
            self.kpi_bills_text.value = f"{len(paid_orders)} บิล"

            # 2. Occupied tables
            total_tables = db.query(Table).count()
            occupied_tables = db.query(Table).filter(Table.status == TableStatus.OCCUPIED).count()
            self.kpi_tables_text.value = f"{occupied_tables} / {total_tables} โต๊ะ"

            # 3. Low stock alert
            inventory = BOMEngine.get_inventory_status(db)
            low_stock_count = sum(1 for item in inventory if item["status"] in ["LOW_STOCK", "OUT_OF_STOCK"])
            self.kpi_low_stock_text.value = f"{low_stock_count} รายการ"

            self._update_ui()
        finally:
            db.close()

    def _handle_logout(self, e):
        self.page_ref.session.store.clear()
        navigate_to(self.page_ref, "/login")

    def _update_ui(self):
        try:
            self.update()
        except Exception:
            pass
        try:
            self.page_ref.update()
        except Exception:
            pass
