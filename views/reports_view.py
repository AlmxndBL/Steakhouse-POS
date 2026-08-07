import flet as ft
from sqlalchemy import func
from database.connection import SessionLocal
from database.models import Order, OrderItem, OrderStatus, MenuItem, RecipeBOM, Ingredient
from utils.navigation import navigate_to

class ReportsView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        user_name = page.session.store.get("user_name") or "ผู้ใช้งาน"

        # Header Nav
        nav_header = ft.Container(
            padding=ft.Padding.symmetric(horizontal=25, vertical=15),
            bgcolor=ft.Colors.BLUE_900,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=15,
                        controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, on_click=lambda e: navigate_to(self.page_ref, "/tables")),
                            ft.Text("รายงานยอดขาย & Food Cost %", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]
                    ),
                    ft.Text(f"สิทธิ์การเข้าถึง: Manager / Owner", size=12, color=ft.Colors.BLUE_200)
                ]
            )
        )

        # Summary Metric Cards
        self.total_sales_card = self._create_metric_card("ยอดขายรวมทั้งหมด", "0.00 ฿", ft.Icons.ATTACH_MONEY, ft.Colors.GREEN_700)
        self.total_orders_card = self._create_metric_card("จำนวนบิลที่ปิดแล้ว", "0 บิล", ft.Icons.RECEIPT_LONG, ft.Colors.BLUE_700)
        self.total_discount_card = self._create_metric_card("ส่วนลดทั้งหมด", "0.00 ฿", ft.Icons.DISCOUNT, ft.Colors.AMBER_800)
        self.avg_food_cost_card = self._create_metric_card("Food Cost % เฉลี่ย", "0.0 %", ft.Icons.PIE_CHART, ft.Colors.PURPLE_700)

        metrics_row = ft.Row(
            spacing=20,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            controls=[
                self.total_sales_card,
                self.total_orders_card,
                self.total_discount_card,
                self.avg_food_cost_card
            ]
        )

        # Sales List Table
        self.sales_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("เลขที่บิล", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("วันที่ / เวลา", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("ประเภทบิล", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("ช่องทางชำระเงิน", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("ส่วนลด", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("ยอดรวมสุทธิ", weight=ft.FontWeight.BOLD)),
            ],
            rows=[]
        )

        super().__init__(
            route="/reports",
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        nav_header,
                        ft.Container(
                            expand=True,
                            padding=25,
                            bgcolor=ft.Colors.BLUE_GREY_50,
                            content=ft.Column(
                                spacing=25,
                                controls=[
                                    metrics_row,
                                    ft.Text("ประวัติรายการชำระเงินบิลหน้าร้าน (Paid Orders)", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                                    ft.Container(
                                        expand=True,
                                        bgcolor=ft.Colors.WHITE,
                                        border_radius=16,
                                        padding=15,
                                        content=ft.ListView([self.sales_table], expand=True)
                                    )
                                ]
                            )
                        )
                    ]
                )
            ],
            padding=0,
            spacing=0
        )

        self._load_reports_data()

    def _create_metric_card(self, title: str, val: str, icon, color):
        return ft.Card(
            elevation=4,
            shape=ft.RoundedRectangleBorder(radius=16),
            content=ft.Container(
                width=240,
                padding=20,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text(title, size=12, color=ft.Colors.GREY_600),
                                ft.Text(val, size=20, weight=ft.FontWeight.BOLD, color=color, key=f"val_{title}")
                            ]
                        ),
                        ft.Icon(icon, size=36, color=color)
                    ]
                )
            )
        )

    def _load_reports_data(self):
        db = SessionLocal()
        try:
            orders = db.query(Order).filter(Order.status == OrderStatus.PAID).order_by(Order.closed_at.desc()).all()
            
            total_net = sum(o.net_amount for o in orders)
            total_count = len(orders)
            total_disc = sum(o.discount_amount for o in orders)

            # Calculate estimated Food Cost %
            menu_items = db.query(MenuItem).filter(MenuItem.is_active == True).all()
            total_cost_ratio = 0.0
            valid_ratio_count = 0
            for item in menu_items:
                dish_cost = 0.0
                for bom in item.recipes:
                    dish_cost += bom.quantity_required * bom.ingredient.cost_per_unit
                if item.price > 0:
                    total_cost_ratio += (dish_cost / item.price) * 100
                    valid_ratio_count += 1

            avg_food_cost = (total_cost_ratio / valid_ratio_count) if valid_ratio_count > 0 else 32.5

            # Update Metrics
            self.total_sales_card.content.content.controls[0].controls[1].value = f"{total_net:,.2f} ฿"
            self.total_orders_card.content.content.controls[0].controls[1].value = f"{total_count} บิล"
            self.total_discount_card.content.content.controls[0].controls[1].value = f"{total_disc:,.2f} ฿"
            self.avg_food_cost_card.content.content.controls[0].controls[1].value = f"{avg_food_cost:.1f} %"

            # Populate Table Rows
            self.sales_table.rows.clear()
            for o in orders:
                closed_str = o.closed_at.strftime("%Y-%m-%d %H:%M") if o.closed_at else "-"
                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(o.order_number, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(closed_str)),
                        ft.DataCell(ft.Text(o.order_type.value)),
                        ft.DataCell(ft.Text(o.payment_method or "เงินสด")),
                        ft.DataCell(ft.Text(f"{o.discount_amount:,.2f} ฿")),
                        ft.DataCell(ft.Text(f"{o.net_amount:,.2f} ฿", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700))
                    ]
                )
                self.sales_table.rows.append(row)

            try:
                self.update()
            except Exception:
                pass
        finally:
            db.close()
