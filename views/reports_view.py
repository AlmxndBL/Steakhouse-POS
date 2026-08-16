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
                            ft.Text("📊 รายงานยอดขาย & กราฟวิเคราะห์การเงิน (Visual Analytics Dashboard)", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
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
        self.btn_today = ft.ElevatedButton("🔘 วันนี้ (Today)", style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_900, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)), on_click=lambda e: self._change_period("today"))
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

        # Chart 1: 7-Day Daily Trend Bar Chart
        self.bar_chart = ft.BarChart(
            bar_groups=[],
            border=ft.border.all(1, ft.Colors.GREY_300),
            left_axis=ft.ChartAxis(
                labels_size=40,
                title=ft.Text("ยอดขาย (บาท)", size=11, color=ft.Colors.GREY_600)
            ),
            bottom_axis=ft.ChartAxis(
                labels_size=32,
            ),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.Colors.GREY_200, width=1, dash_pattern=[3, 3]
            ),
            tooltip_bgcolor=ft.Colors.BLUE_GREY_900,
            max_y=1000,
            interactive=True,
            expand=True
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
                                ft.Text("แท่งกราฟแสดงยอดขายแต่ละวัน", size=12, color=ft.Colors.GREY_600)
                            ]
                        ),
                        ft.Container(
                            height=220,
                            padding=ft.Padding.only(top=10, right=15),
                            content=self.bar_chart
                        )
                    ]
                )
            )
        )

        # Chart 2: Category Share Pie Chart
        self.category_pie_chart = ft.PieChart(
            sections=[],
            sections_space=3,
            center_space_radius=40,
            expand=True
        )
        self.category_legend_col = ft.Column(spacing=8, alignment=ft.MainAxisAlignment.CENTER)

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
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(width=160, height=160, content=self.category_pie_chart),
                                ft.Container(content=self.category_legend_col)
                            ]
                        )
                    ]
                )
            )
        )

        # Chart 3: Payment Split Pie Chart
        self.payment_pie_chart = ft.PieChart(
            sections=[],
            sections_space=3,
            center_space_radius=35,
            expand=True
        )
        self.payment_legend_col = ft.Column(spacing=8, alignment=ft.MainAxisAlignment.CENTER)

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
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(width=160, height=160, content=self.payment_pie_chart),
                                ft.Container(content=self.payment_legend_col)
                            ]
                        )
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

            # 2. Update 7-Day Bar Chart
            daily_data = report.get("daily_trend", [])
            max_sales = max([d["sales"] for d in daily_data] + [1000])
            self.bar_chart.max_y = max_sales * 1.25

            bar_groups = []
            bottom_labels = []
            for idx, d in enumerate(daily_data):
                bar_groups.append(
                    ft.BarChartGroup(
                        x=idx,
                        bar_rods=[
                            ft.BarChartRod(
                                from_y=0,
                                to_y=d["sales"],
                                width=24,
                                color=ft.Colors.BLUE_700,
                                border_radius=ft.border_radius.only(top_left=6, top_right=6),
                                tooltip=f"{d['day_name']} ({d['date']}): {d['sales']:,.2f} ฿ ({d['bills']} บิล)"
                            )
                        ]
                    )
                )
                bottom_labels.append(
                    ft.ChartAxisLabel(
                        value=idx,
                        label=ft.Container(padding=ft.Padding.only(top=5), content=ft.Text(d["date"], size=10, weight=ft.FontWeight.W_500))
                    )
                )

            self.bar_chart.bar_groups = bar_groups
            self.bar_chart.bottom_axis.labels = bottom_labels

            # 3. Update Category Pie Chart
            palette = [ft.Colors.RED_600, ft.Colors.ORANGE_600, ft.Colors.BLUE_600, ft.Colors.GREEN_600, ft.Colors.PURPLE_600]
            cat_data = report.get("category_breakdown", [])
            cat_sections = []
            cat_legends = []

            if cat_data:
                for idx, c in enumerate(cat_data):
                    color = palette[idx % len(palette)]
                    cat_sections.append(
                        ft.PieChartSection(
                            value=max(1.0, c["pct"]),
                            title=f"{c['pct']:.0f}%",
                            title_style=ft.TextStyle(size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                            color=color,
                            radius=35
                        )
                    )
                    cat_legends.append(
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Container(width=12, height=12, bgcolor=color, border_radius=3),
                                ft.Text(f"{c['name']}: {c['revenue']:,.0f}฿ ({c['pct']:.1f}%)", size=12, weight=ft.FontWeight.W_500)
                            ]
                        )
                    )
            else:
                cat_sections.append(ft.PieChartSection(value=100, title="0%", color=ft.Colors.GREY_400, radius=35))
                cat_legends.append(ft.Text("ยังไม่มีข้อมูลยอดขายหมวดหมู่", size=12, color=ft.Colors.GREY_600))

            self.category_pie_chart.sections = cat_sections
            self.category_legend_col.controls = cat_legends

            # 4. Update Payment Split Pie Chart
            cash_val = report["cash_sales"]
            qr_val = report["qr_sales"]
            tot = cash_val + qr_val

            pay_sections = []
            pay_legends = []
            if tot > 0:
                c_pct = (cash_val / tot) * 100.0
                q_pct = (qr_val / tot) * 100.0
                if cash_val > 0:
                    pay_sections.append(
                        ft.PieChartSection(value=c_pct, title=f"{c_pct:.0f}%", title_style=ft.TextStyle(size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD), color=ft.Colors.GREEN_600, radius=35)
                    )
                if qr_val > 0:
                    pay_sections.append(
                        ft.PieChartSection(value=q_pct, title=f"{q_pct:.0f}%", title_style=ft.TextStyle(size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD), color=ft.Colors.BLUE_600, radius=35)
                    )
                pay_legends.append(ft.Row([ft.Container(width=12, height=12, bgcolor=ft.Colors.GREEN_600, border_radius=3), ft.Text(f"เงินสด (Cash): {cash_val:,.2f}฿ ({c_pct:.1f}%)", size=12)]))
                pay_legends.append(ft.Row([ft.Container(width=12, height=12, bgcolor=ft.Colors.BLUE_600, border_radius=3), ft.Text(f"QR PromptPay: {qr_val:,.2f}฿ ({q_pct:.1f}%)", size=12)]))
            else:
                pay_sections.append(ft.PieChartSection(value=100, title="0%", color=ft.Colors.GREY_400, radius=35))
                pay_legends.append(ft.Text("ยังไม่มีข้อมูลการชำระเงิน", size=12, color=ft.Colors.GREY_600))

            self.payment_pie_chart.sections = pay_sections
            self.payment_legend_col.controls = pay_legends

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

            b64_img = ReceiptService.generate_ereceipt_image_base64(payload)
            modal = EReceiptModal(self.page_ref, payload, b64_img)
            modal.show()
        finally:
            db.close()

    def _handle_export_csv(self, e):
        db = SessionLocal()
        try:
            csv_content = ReportService.generate_sales_csv(db, period=self.current_period)
            
            dialog = ft.AlertDialog(
                title=ft.Text("ส่งออกข้อมูลรายงานสำเร็จ (CSV Export)", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=450,
                    content=ft.Column(
                        spacing=10,
                        tight=True,
                        controls=[
                            ft.Text("ข้อมูลยอดขายและต้นทุนถูกแปลงเป็น CSV เรียบร้อยแล้ว:"),
                            ft.Container(
                                bgcolor=ft.Colors.GREY_100,
                                padding=12,
                                border_radius=8,
                                content=ft.Text(csv_content[:300] + "\n...", size=11, font_family="monospace")
                            )
                        ]
                    )
                ),
                actions=[
                    ft.ElevatedButton("ปิด", on_click=lambda e: self._close_dialog(dialog))
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
