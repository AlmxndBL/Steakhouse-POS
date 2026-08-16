import flet as ft
from database.connection import SessionLocal
from services.report_service import ReportService
from services.receipt_service import ReceiptService
from components.ereceipt_modal import EReceiptModal
from utils.navigation import navigate_to

class ReportsView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        self.current_period = "today"

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
                        spacing=15,
                        controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, on_click=lambda e: navigate_to(self.page_ref, "/admin")),
                            ft.Text("📊 รายงานยอดขาย & วิเคราะห์การเงิน (Visual Analytics Dashboard)", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]
                    ),
                    ft.ElevatedButton(
                        "📥 ส่งออกข้อมูล (Export CSV)",
                        icon=ft.Icons.DOWNLOAD,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN_600,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.Padding.symmetric(horizontal=16, vertical=10)
                        ),
                        on_click=self._handle_export_csv
                    )
                ]
            )
        )

        # Date Filter Bar
        self.btn_today = ft.ElevatedButton(
            "🔘 วันนี้ (Today)",
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_900, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=lambda e: self._change_period("today")
        )
        self.btn_7days = ft.OutlinedButton("7 วันล่าสุด (7 Days)", on_click=lambda e: self._change_period("7days"))
        self.btn_month = ft.OutlinedButton("เดือนนี้ (This Month)", on_click=lambda e: self._change_period("month"))
        self.btn_all = ft.OutlinedButton("ทั้งหมด (All Time)", on_click=lambda e: self._change_period("all"))

        filter_bar = ft.Container(
            padding=ft.Padding.symmetric(horizontal=30, vertical=10),
            bgcolor=ft.Colors.WHITE,
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Text("📅 เลือกช่วงเวลา:", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                    self.btn_today,
                    self.btn_7days,
                    self.btn_month,
                    self.btn_all
                ]
            )
        )

        # 4 Key Financial KPI Cards
        self.kpi_net_sales = ft.Text("0.00 ฿", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
        self.kpi_payment_split = ft.Text("เงินสด: 0 | QR: 0", size=13, color=ft.Colors.BLUE_GREY_800, weight=ft.FontWeight.W_600)
        self.kpi_bill_stats = ft.Text("0 บิล (เฉลี่ย 0.00 ฿)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)
        self.kpi_food_cost = ft.Text("0.0 % (กำไร 0.00 ฿)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_800)

        kpi_row = ft.ResponsiveRow(
            spacing=16,
            run_spacing=16,
            controls=[
                ft.Container(
                    col={"sm": 6, "md": 3},
                    content=self._build_card("ยอดขายสุทธิ (Net Revenue)", self.kpi_net_sales, ft.Icons.ATTACH_MONEY, ft.Colors.GREEN_700, ft.Colors.GREEN_50)
                ),
                ft.Container(
                    col={"sm": 6, "md": 3},
                    content=self._build_card("ช่องทางชำระเงิน (Payment)", self.kpi_payment_split, ft.Icons.PAYMENTS, ft.Colors.BLUE_800, ft.Colors.BLUE_50)
                ),
                ft.Container(
                    col={"sm": 6, "md": 3},
                    content=self._build_card("จำนวนบิล & ยอดเฉลี่ย", self.kpi_bill_stats, ft.Icons.RECEIPT_LONG, ft.Colors.INDIGO_700, ft.Colors.INDIGO_50)
                ),
                ft.Container(
                    col={"sm": 6, "md": 3},
                    content=self._build_card("Food Cost % & กำไรขั้นต้น", self.kpi_food_cost, ft.Icons.PIE_CHART, ft.Colors.PURPLE_700, ft.Colors.PURPLE_50)
                ),
            ]
        )

        # Visual Chart 1: 7-Day Trend Container Bar Chart
        self.trend_bars_row = ft.Row(
            spacing=16,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            vertical_alignment=ft.CrossAxisAlignment.END
        )

        self.chart_trend_card = ft.Card(
            elevation=2,
            shape=ft.RoundedRectangleBorder(radius=12),
            content=ft.Container(
                bgcolor=card_bg,
                padding=20,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Icon(ft.Icons.SHOW_CHART, color=ft.Colors.BLUE_800),
                                        ft.Text("📈 แนวโน้มยอดขาย 7 วันล่าสุด (7-Day Sales Trend)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)
                                    ]
                                ),
                                ft.Text("กราฟแท่งเปรียบเทียบยอดขายรายวัน", size=12, color=ft.Colors.GREY_600)
                            ]
                        ),
                        ft.Container(
                            height=200,
                            padding=ft.Padding.symmetric(vertical=10),
                            content=self.trend_bars_row
                        )
                    ]
                )
            )
        )

        # Visual Chart 2: Category Share Visual Progress Bars
        self.category_bars_col = ft.Column(spacing=12)

        self.chart_category_card = ft.Card(
            elevation=2,
            shape=ft.RoundedRectangleBorder(radius=12),
            content=ft.Container(
                bgcolor=card_bg,
                padding=20,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.PIE_CHART_OUTLINE, color=ft.Colors.INDIGO_700),
                                ft.Text("🥧 สัดส่วนยอดขายตามหมวดหมู่อาหาร (Category Share)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)
                            ]
                        ),
                        self.category_bars_col
                    ]
                )
            )
        )

        # Visual Chart 3: Payment Split Comparison Card
        self.payment_bars_col = ft.Column(spacing=12)

        self.chart_payment_card = ft.Card(
            elevation=2,
            shape=ft.RoundedRectangleBorder(radius=12),
            content=ft.Container(
                bgcolor=card_bg,
                padding=20,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.DONUT_LARGE, color=ft.Colors.TEAL_800),
                                ft.Text("💳 สัดส่วนช่องทางชำระเงิน (Payment Split)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)
                            ]
                        ),
                        self.payment_bars_col
                    ]
                )
            )
        )

        # 2 Deep-Dive Analytic Tables
        self.top_sellers_table = ft.DataTable(
            heading_row_color=ft.Colors.GREY_100,
            columns=[
                ft.DataColumn(ft.Text("#")),
                ft.DataColumn(ft.Text("เมนูอาหาร")),
                ft.DataColumn(ft.Text("หมวดหมู่")),
                ft.DataColumn(ft.Text("จำนวนจาน")),
                ft.DataColumn(ft.Text("ยอดขายรวม")),
            ],
            rows=[]
        )

        self.cost_breakdown_col = ft.Column(spacing=10)

        # Responsive Rows
        charts_row = ft.ResponsiveRow(
            spacing=20,
            run_spacing=20,
            controls=[
                ft.Container(col={"sm": 12, "md": 12}, content=self.chart_trend_card),
                ft.Container(col={"sm": 12, "md": 6}, content=self.chart_category_card),
                ft.Container(col={"sm": 12, "md": 6}, content=self.chart_payment_card),
            ]
        )

        analytics_row = ft.ResponsiveRow(
            spacing=20,
            run_spacing=20,
            controls=[
                ft.Container(
                    col={"sm": 12, "md": 7},
                    content=ft.Card(
                        elevation=2,
                        shape=ft.RoundedRectangleBorder(radius=12),
                        content=ft.Container(
                            bgcolor=card_bg,
                            padding=20,
                            content=ft.Column(
                                spacing=12,
                                controls=[
                                    ft.Row(
                                        spacing=8,
                                        controls=[
                                            ft.Icon(ft.Icons.LEADERBOARD, color=ft.Colors.ORANGE_800),
                                            ft.Text("🥩 5 อันดับเมนูขายดีที่สุด (Top 5 Best Sellers)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)
                                        ]
                                    ),
                                    self.top_sellers_table
                                ]
                            )
                        )
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 5},
                    content=ft.Card(
                        elevation=2,
                        shape=ft.RoundedRectangleBorder(radius=12),
                        content=ft.Container(
                            bgcolor=card_bg,
                            padding=20,
                            content=ft.Column(
                                spacing=12,
                                controls=[
                                    ft.Row(
                                        spacing=8,
                                        controls=[
                                            ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, color=ft.Colors.PURPLE_800),
                                            ft.Text("📉 สรุปต้นทุนวัตถุดิบ & ของเสีย (Cost Analysis)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)
                                        ]
                                    ),
                                    self.cost_breakdown_col
                                ]
                            )
                        )
                    )
                )
            ]
        )

        # Order Transaction History Table
        self.orders_table = ft.DataTable(
            heading_row_color=ft.Colors.GREY_100,
            columns=[
                ft.DataColumn(ft.Text("เลขที่บิล")),
                ft.DataColumn(ft.Text("วันที่/เวลา")),
                ft.DataColumn(ft.Text("ประเภท")),
                ft.DataColumn(ft.Text("โต๊ะ/ลูกค้า")),
                ft.DataColumn(ft.Text("พนักงาน")),
                ft.DataColumn(ft.Text("วิธีชำระ")),
                ft.DataColumn(ft.Text("ส่วนลด")),
                ft.DataColumn(ft.Text("ยอดสุทธิ")),
                ft.DataColumn(ft.Text("ใบเสร็จ")),
            ],
            rows=[]
        )

        history_card = ft.Card(
            elevation=2,
            shape=ft.RoundedRectangleBorder(radius=12),
            content=ft.Container(
                bgcolor=card_bg,
                padding=20,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.BLUE_900),
                                ft.Text("🧾 ประวัติรายการขายทั้งหมด (Transaction History)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)
                            ]
                        ),
                        ft.Container(content=ft.ListView([self.orders_table], expand=False))
                    ]
                )
            )
        )

        body_content = ft.Container(
            expand=True,
            padding=25,
            content=ft.ListView(
                spacing=20,
                controls=[
                    kpi_row,
                    charts_row,
                    analytics_row,
                    history_card
                ]
            )
        )

        super().__init__(
            route="/admin/reports",
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[nav_header, filter_bar, body_content]
                )
            ],
            bgcolor=bg_color,
            padding=0,
            spacing=0
        )

        self._load_reports_data()

    def _build_card(self, title, val_control, icon, icon_color, bg_color):
        return ft.Card(
            elevation=1,
            shape=ft.RoundedRectangleBorder(radius=12),
            content=ft.Container(
                bgcolor=ft.Colors.WHITE,
                padding=18,
                border_radius=12,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=4,
                            controls=[
                                ft.Text(title, size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                                val_control
                            ]
                        ),
                        ft.Container(
                            padding=10,
                            bgcolor=bg_color,
                            border_radius=10,
                            content=ft.Icon(icon, color=icon_color, size=26)
                        )
                    ]
                )
            )
        )

    def _change_period(self, period: str):
        self.current_period = period
        buttons = [("today", self.btn_today), ("7days", self.btn_7days), ("month", self.btn_month), ("all", self.btn_all)]
        for p, btn in buttons:
            if p == period:
                btn.style = ft.ButtonStyle(bgcolor=ft.Colors.BLUE_900, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8))
            else:
                btn.style = ft.ButtonStyle(bgcolor=ft.Colors.WHITE, color=ft.Colors.BLUE_GREY_800, shape=ft.RoundedRectangleBorder(radius=8))
        self._load_reports_data()

    def _load_reports_data(self):
        db = SessionLocal()
        try:
            report = ReportService.get_sales_report(db, period=self.current_period)

            # 1. Update KPI Text
            self.kpi_net_sales.value = f"{report['total_net']:,.2f} ฿"
            self.kpi_payment_split.value = f"💵 เงินสด: {report['cash_sales']:,.2f} ฿\n📱 QR: {report['qr_sales']:,.2f} ฿"
            self.kpi_bill_stats.value = f"{report['bill_count']} บิล (เฉลี่ย {report['avg_bill']:,.2f} ฿)"
            self.kpi_food_cost.value = f"{report['food_cost_pct']:.1f}% (กำไร {report['gross_profit']:,.2f} ฿)"

            # 2. Update 7-Day Trend Visual Bars
            daily_data = report.get("daily_trend", [])
            max_sales = max([d["sales"] for d in daily_data] + [1000.0])
            self.trend_bars_row.controls.clear()

            for d in daily_data:
                height_ratio = min(1.0, max(0.08, d["sales"] / max_sales))
                bar_height = height_ratio * 120.0
                bar_color = ft.Colors.BLUE_700 if d["sales"] > 0 else ft.Colors.GREY_300

                self.trend_bars_row.controls.append(
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                        controls=[
                            ft.Text(f"{d['sales']:,.0f}฿" if d["sales"] > 0 else "0฿", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                            ft.Container(
                                width=32,
                                height=bar_height,
                                bgcolor=bar_color,
                                border_radius=ft.BorderRadius(top_left=6, top_right=6, bottom_left=0, bottom_right=0),
                                tooltip=f"{d['day_name']} ({d['date']}): {d['sales']:,.2f} ฿ ({d['bills']} บิล)"
                            ),
                            ft.Text(d["day_label"], size=11, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_500)
                        ]
                    )
                )

            # 3. Update Category Visual Bars
            palette = [ft.Colors.RED_600, ft.Colors.ORANGE_600, ft.Colors.BLUE_600, ft.Colors.GREEN_600, ft.Colors.PURPLE_600]
            cat_data = report.get("category_breakdown", [])
            self.category_bars_col.controls.clear()

            if cat_data:
                for idx, c in enumerate(cat_data):
                    color = palette[idx % len(palette)]
                    progress_val = min(1.0, max(0.02, c["pct"] / 100.0))
                    self.category_bars_col.controls.append(
                        ft.Column(
                            spacing=4,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Row([
                                            ft.Container(width=10, height=10, bgcolor=color, border_radius=2),
                                            ft.Text(c["name"], size=13, weight=ft.FontWeight.W_500)
                                        ]),
                                        ft.Text(f"{c['revenue']:,.2f} ฿ ({c['pct']:.1f}%)", size=12, weight=ft.FontWeight.BOLD, color=color)
                                    ]
                                ),
                                ft.ProgressBar(value=progress_val, color=color, bgcolor=ft.Colors.GREY_100, height=8)
                            ]
                        )
                    )
            else:
                self.category_bars_col.controls.append(ft.Text("ยังไม่มีข้อมูลยอดขายหมวดหมู่", size=12, color=ft.Colors.GREY_600))

            # 4. Update Payment Split Visual Bars
            cash_val = report["cash_sales"]
            qr_val = report["qr_sales"]
            tot = cash_val + qr_val
            self.payment_bars_col.controls.clear()

            if tot > 0:
                c_pct = (cash_val / tot) * 100.0
                q_pct = (qr_val / tot) * 100.0

                self.payment_bars_col.controls.extend([
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Row([
                                        ft.Icon(ft.Icons.PAYMENTS, size=16, color=ft.Colors.GREEN_700),
                                        ft.Text("เงินสด (Cash)", size=13, weight=ft.FontWeight.W_500)
                                    ]),
                                    ft.Text(f"{cash_val:,.2f} ฿ ({c_pct:.1f}%)", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
                                ]
                            ),
                            ft.ProgressBar(value=c_pct / 100.0, color=ft.Colors.GREEN_600, bgcolor=ft.Colors.GREY_100, height=8)
                        ]
                    ),
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Row([
                                        ft.Icon(ft.Icons.QR_CODE_2, size=16, color=ft.Colors.BLUE_700),
                                        ft.Text("QR PromptPay", size=13, weight=ft.FontWeight.W_500)
                                    ]),
                                    ft.Text(f"{qr_val:,.2f} ฿ ({q_pct:.1f}%)", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)
                                ]
                            ),
                            ft.ProgressBar(value=q_pct / 100.0, color=ft.Colors.BLUE_600, bgcolor=ft.Colors.GREY_100, height=8)
                        ]
                    )
                ])
            else:
                self.payment_bars_col.controls.append(ft.Text("ยังไม่มีข้อมูลการชำระเงิน", size=12, color=ft.Colors.GREY_600))

            # 5. Update Top Sellers Table
            self.top_sellers_table.rows.clear()
            if report["top_sellers"]:
                for idx, item in enumerate(report["top_sellers"], 1):
                    self.top_sellers_table.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(f"#{idx}", weight=ft.FontWeight.BOLD)),
                                ft.DataCell(ft.Text(item["name"], weight=ft.FontWeight.W_500)),
                                ft.DataCell(ft.Text(item["category"])),
                                ft.DataCell(ft.Text(f"{item['qty']} จาน", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)),
                                ft.DataCell(ft.Text(f"{item['revenue']:,.2f} ฿", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)),
                            ]
                        )
                    )
            else:
                self.top_sellers_table.rows.append(
                    ft.DataRow(cells=[ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("ยังไม่มีข้อมูลการขาย")), ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("-"))])
                )

            # 6. Update Cost Breakdown Column
            self.cost_breakdown_col.controls = [
                self._build_cost_item("🥩 ต้นทุนวัตถุดิบ (COGS):", f"{report['total_food_cost']:,.2f} ฿", ft.Colors.BLUE_GREY_900),
                self._build_cost_item("🗑️ มูลค่าของเสีย (Wastage):", f"{report['total_wastage_cost']:,.2f} ฿", ft.Colors.RED_700),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                self._build_cost_item("💰 กำไรขั้นต้น (Gross Profit):", f"{report['gross_profit']:,.2f} ฿", ft.Colors.GREEN_700, is_bold=True),
                self._build_cost_item("📊 อัตรากำไร (Margin %):", f"{report['gross_margin_pct']:.1f} %", ft.Colors.INDIGO_700, is_bold=True),
            ]

            # 7. Update Orders History Table
            self.orders_table.rows.clear()
            for o in report["orders"][:20]: # Show latest 20
                staff_name = o.user.name if o.user else "-"
                tbl = f"โต๊ะ {o.table.table_number}" if o.table else o.customer_name
                dt_str = o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else "-"
                order_id = o.id

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(o.order_number, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)),
                        ft.DataCell(ft.Text(dt_str)),
                        ft.DataCell(ft.Text(o.order_type.value if hasattr(o.order_type, "value") else str(o.order_type))),
                        ft.DataCell(ft.Text(tbl)),
                        ft.DataCell(ft.Text(staff_name)),
                        ft.DataCell(ft.Text(o.payment_method or "-")),
                        ft.DataCell(ft.Text(f"{float(o.discount_amount):,.2f} ฿", color=ft.Colors.AMBER_800)),
                        ft.DataCell(ft.Text(f"{float(o.net_amount):,.2f} ฿", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)),
                        ft.DataCell(
                            ft.IconButton(
                                ft.Icons.RECEIPT,
                                icon_color=ft.Colors.BLUE_700,
                                tooltip="ดู E-Receipt",
                                on_click=lambda e, oid=order_id: self._show_ereceipt_modal(oid)
                            )
                        )
                    ]
                )
                self.orders_table.rows.append(row)

            self._update_ui()
        finally:
            db.close()

    def _build_cost_item(self, label: str, val: str, color, is_bold: bool = False):
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(label, size=13, color=ft.Colors.GREY_700, weight=ft.FontWeight.BOLD if is_bold else ft.FontWeight.NORMAL),
                ft.Text(val, size=14, color=color, weight=ft.FontWeight.BOLD if is_bold else ft.FontWeight.W_600)
            ]
        )

    def _show_ereceipt_modal(self, order_id: int):
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return

            items_payload = []
            for item in order.items:
                m_name = item.menu_item.name if item.menu_item else "อาหาร"
                items_payload.append({
                    "name": m_name,
                    "qty": item.quantity,
                    "price": float(item.price_per_unit),
                    "total": float(item.price_per_unit) * item.quantity
                })

            tbl_name = f"โต๊ะ {order.table.table_number}" if order.table else (order.customer_name or "Takeaway")
            payload = {
                "order_number": order.order_number,
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else "",
                "order_type": order.order_type.value if hasattr(order.order_type, "value") else str(order.order_type),
                "table_or_customer": tbl_name,
                "items": items_payload,
                "subtotal": float(order.subtotal),
                "discount": float(order.discount_amount),
                "net_total": float(order.net_amount),
                "payment_method": order.payment_method or "เงินสด"
            }

            modal = EReceiptModal(order_data=payload, page=self.page_ref)
            self._open_dialog(modal)
        finally:
            db.close()

    def _handle_export_csv(self, e):
        import os
        from datetime import datetime
        
        db = SessionLocal()
        try:
            csv_content = ReportService.generate_sales_csv(db, period=self.current_period)
            
            # 1. Save to exports folder with UTF-8 BOM for Thai Excel support
            exports_dir = os.path.join(os.getcwd(), "exports")
            os.makedirs(exports_dir, exist_ok=True)
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sales_report_{self.current_period}_{timestamp_str}.csv"
            filepath = os.path.join(exports_dir, filename)
            
            with open(filepath, "w", encoding="utf-8-sig") as f:
                f.write(csv_content)

            # Download URL served statically by Flet assets_dir
            download_url = f"/{filename}"

            btn_copy = ft.OutlinedButton(
                "📋 คัดลอกข้อมูล (Copy)",
                icon=ft.Icons.CONTENT_COPY
            )

            def copy_to_clipboard(e_copy):
                try:
                    self.page_ref.clipboard = csv_content
                except Exception:
                    pass
                btn_copy.text = "✅ คัดลอกสำเร็จแล้ว!"
                btn_copy.icon = ft.Icons.CHECK
                try:
                    btn_copy.update()
                except Exception:
                    pass

                try:
                    self.page_ref.snack_bar = ft.SnackBar(
                        content=ft.Text("📋 คัดลอกข้อมูล CSV สำเร็จ! นำไปวางใน Excel หรือ Google Sheets ได้ทันที", color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.GREEN_700,
                        open=True
                    )
                    self.page_ref.update()
                except Exception:
                    pass

            btn_copy.on_click = copy_to_clipboard

            def trigger_download(e_down):
                try:
                    self.page_ref.launch_url(download_url, web_window_name="_blank")
                except Exception:
                    pass

            dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=24),
                    ft.Text("ส่งออกข้อมูลรายงานสำเร็จ (CSV Export)", weight=ft.FontWeight.BOLD, size=16)
                ]),
                content=ft.Container(
                    width=520,
                    content=ft.Column(
                        spacing=12,
                        tight=True,
                        controls=[
                            ft.Text("ไฟล์รายงานยอดขายและต้นทุนถูกบันทึกเรียบร้อยแล้ว รองรับภาษาไทย 100% ใน Excel:", size=13),
                            ft.Container(
                                bgcolor=ft.Colors.BLUE_50,
                                padding=10,
                                border_radius=8,
                                content=ft.Row([
                                    ft.Icon(ft.Icons.FOLDER_OPEN, color=ft.Colors.BLUE_800, size=18),
                                    ft.Text(f"บันทึกไฟล์ไว้ที่: exports/{filename}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)
                                ])
                            ),
                            ft.Text("ข้อมูล CSV (สามารถเลือกคลุมดำและคัดลอกได้โดยตรง):", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                            ft.TextField(
                                value=csv_content,
                                multiline=True,
                                min_lines=5,
                                max_lines=7,
                                read_only=True,
                                text_size=11,
                                bgcolor=ft.Colors.GREY_100,
                                border_color=ft.Colors.GREY_300
                            )
                        ]
                    )
                ),
                actions=[
                    btn_copy,
                    ft.ElevatedButton(
                        "📥 ดาวน์โหลดไฟล์ (Download)",
                        icon=ft.Icons.DOWNLOAD,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                        on_click=trigger_download
                    ),
                    ft.TextButton("ปิด", on_click=lambda e: self._close_dialog(dialog))
                ]
            )
            self._open_dialog(dialog)
        finally:
            db.close()



    def _open_dialog(self, dialog: ft.AlertDialog):
        try:
            if hasattr(self.page_ref, "show_dialog"):
                self.page_ref.show_dialog(dialog)
            elif hasattr(self.page_ref, "open"):
                self.page_ref.open(dialog)
            else:
                self.page_ref.overlay.append(dialog)
                dialog.open = True
                self.page_ref.update()
        except Exception:
            try:
                self.page_ref.overlay.append(dialog)
                dialog.open = True
                self.page_ref.update()
            except Exception:
                pass

    def _close_dialog(self, dialog: ft.AlertDialog = None):
        try:
            if hasattr(self.page_ref, "pop_dialog"):
                self.page_ref.pop_dialog()
            elif hasattr(self.page_ref, "close"):
                self.page_ref.close(dialog)
            elif dialog is not None:
                dialog.open = False
                self.page_ref.update()
        except Exception:
            if dialog is not None:
                dialog.open = False
                try:
                    self.page_ref.update()
                except Exception:
                    pass

    def _update_ui(self):
        try:
            self.update()
        except Exception:
            pass
        try:
            self.page_ref.update()
        except Exception:
            pass
