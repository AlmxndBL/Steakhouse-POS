import flet as ft
from database.connection import SessionLocal
from database.models import OrderType
from services.order_service import OrderService
from components.table_card import TableCard
from utils.navigation import navigate_to

class TableMapView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        user_name = page.session.store.get("user_name") or "ผู้ใช้งาน"
        user_role = page.session.store.get("user_role") or "STAFF"

        # App Bar / Header Navigation
        nav_header = ft.Container(
            padding=ft.Padding.symmetric(horizontal=25, vertical=15),
            bgcolor=ft.Colors.BLUE_900,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=15,
                        controls=[
                            ft.Icon(ft.Icons.TABLE_RESTAURANT, color=ft.Colors.WHITE, size=30),
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("STEAKHOUSE POS", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    ft.Text("ผังโต๊ะอาหาร (Table Map)", size=12, color=ft.Colors.BLUE_200)
                                ]
                            )
                        ]
                    ),
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.ElevatedButton("ผังโต๊ะ", icon=ft.Icons.GRID_VIEW, style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)),
                            ft.ElevatedButton("ออเดอร์ Takeaway", icon=ft.Icons.SHOPPING_BAG, on_click=self._handle_takeaway, style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE)),
                            ft.ElevatedButton("คลังวัตถุดิบ & BOM", icon=ft.Icons.INVENTORY, on_click=lambda e: navigate_to(self.page_ref, "/stock"), style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)),
                            ft.ElevatedButton("รายงานยอดขาย", icon=ft.Icons.BAR_CHART, on_click=lambda e: navigate_to(self.page_ref, "/reports"), style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)),
                        ]
                    ),
                    ft.Row(
                        spacing=15,
                        controls=[
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                spacing=2,
                                controls=[
                                    ft.Text(user_name, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    ft.Text(f"สิทธิ์: {user_role}", size=11, color=ft.Colors.BLUE_200)
                                ]
                            ),
                            ft.IconButton(ft.Icons.LOGOUT, tooltip="ออกจากระบบ", icon_color=ft.Colors.RED_300, on_click=self._handle_logout)
                        ]
                    )
                ]
            )
        )

        # Load Tables Grid
        self.grid = ft.GridView(
            expand=True,
            runs_count=4,
            max_extent=220,
            child_aspect_ratio=1.3,
            spacing=20,
            run_spacing=20,
            padding=25
        )
        self._load_tables()

        super().__init__(
            route="/tables",
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        nav_header,
                        ft.Container(
                            expand=True,
                            bgcolor=ft.Colors.BLUE_GREY_50,
                            content=self.grid
                        )
                    ]
                )
            ],
            padding=0,
            spacing=0
        )

    def _load_tables(self):
        db = SessionLocal()
        try:
            tables = OrderService.get_tables(db)
            self.grid.controls.clear()
            for t in tables:
                card = TableCard(table=t, on_click=self._on_table_click)
                self.grid.controls.append(card)
        finally:
            db.close()

    def _on_table_click(self, table):
        db = SessionLocal()
        user_id = self.page_ref.session.store.get("user_id") or 1
        try:
            order = OrderService.create_or_get_open_order(
                db, table_id=table.id, order_type=OrderType.DINE_IN, customer_name=f"โต๊ะ {table.table_number}", user_id=user_id
            )
            self.page_ref.session.store.set("active_order_id", order.id)
            navigate_to(self.page_ref, "/pos")
        finally:
            db.close()

    def _handle_takeaway(self, e):
        db = SessionLocal()
        user_id = self.page_ref.session.store.get("user_id") or 1
        try:
            order = OrderService.create_or_get_open_order(
                db, table_id=None, order_type=OrderType.TAKEAWAY, customer_name="ลูกค้า Takeaway", user_id=user_id
            )
            self.page_ref.session.store.set("active_order_id", order.id)
            navigate_to(self.page_ref, "/pos")
        finally:
            db.close()

    def _handle_logout(self, e):
        self.page_ref.session.store.clear()
        navigate_to(self.page_ref, "/login")
