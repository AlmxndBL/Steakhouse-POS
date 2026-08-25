import flet as ft
from database.connection import SessionLocal
from database.models import Order
from services.report_service import ReportService
from components.ereceipt_modal import EReceiptModal
from components.theme import ThemeColors, create_card, create_badge, create_button
from components.admin_shell import AdminShell
from utils.dialogs import open_dialog, close_dialog

class ReportsView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        self.current_period = "today"

        # 4 Key Financial KPI Cards
        self.kpi_net_sales = ft.Text("0.00 ฿", size=22, weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD)
        self.kpi_payment_split = ft.Text("เงินสด: 0 | QR: 0", size=13, color=ThemeColors.TEXT_MAIN, weight=ft.FontWeight.W_600)
        self.kpi_bill_stats = ft.Text("0 บิล (เฉลี่ย 0.00 ฿)", size=16, weight=ft.FontWeight.BOLD, color=ThemeColors.SAPPHIRE)
        self.kpi_food_cost = ft.Text("0.0 % (กำไร 0.00 ฿)", size=16, weight=ft.FontWeight.BOLD, color=ThemeColors.PURPLE)

        # Date Filter Bar Buttons
        self.btn_today = ft.ElevatedButton(
            "วันนี้ (Today)",
            style=self._get_period_btn_style(True),
            on_click=lambda e: self._change_period("today")
        )
        self.btn_7days = ft.ElevatedButton(
            "7 วันล่าสุด (7 Days)",
            style=self._get_period_btn_style(False),
            on_click=lambda e: self._change_period("7days")
        )
        self.btn_month = ft.ElevatedButton(
            "เดือนนี้ (This Month)",
            style=self._get_period_btn_style(False),
            on_click=lambda e: self._change_period("month")
        )
        self.btn_all = ft.ElevatedButton(
            "ทั้งหมด (All Time)",
            style=self._get_period_btn_style(False),
            on_click=lambda e: self._change_period("all")
        )

        filter_bar = ft.Container(
            padding=ft.Padding.only(bottom=16),
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Text("ช่วงเวลา:", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN),
                    self.btn_today,
                    self.btn_7days,
                    self.btn_month,
                    self.btn_all
                ]
            )
        )

        kpi_row = ft.ResponsiveRow(
            spacing=16,
            run_spacing=16,
            controls=[
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    content=self._build_card("ยอดขายสุทธิ (Net Revenue)", self.kpi_net_sales, ft.Icons.ATTACH_MONEY, ThemeColors.EMERALD)
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    content=self._build_card("ช่องทางชำระเงิน (Payment)", self.kpi_payment_split, ft.Icons.PAYMENTS, ThemeColors.SAPPHIRE)
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    content=self._build_card("จำนวนบิล & ยอดเฉลี่ย", self.kpi_bill_stats, ft.Icons.RECEIPT_LONG, ThemeColors.INDIGO)
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    content=self._build_card("Food Cost % & กำไรขั้นต้น", self.kpi_food_cost, ft.Icons.PIE_CHART, ThemeColors.PURPLE)
                ),
            ]
        )

        # Visual Chart 1: 7-Day Trend Container Bar Chart
        self.trend_bars_row = ft.Row(
            spacing=16,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            vertical_alignment=ft.CrossAxisAlignment.END
        )

        self.chart_trend_card = create_card(
            ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.SHOW_CHART_ROUNDED, color=ThemeColors.SAPPHIRE, size=20),
                                    ft.Text("แนวโน้มยอดขาย 7 วันล่าสุด (7-Day Sales Trend)", size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN)
                                ]
                            ),
                            ft.Text("กราฟแท่งเปรียบเทียบยอดขายรายวัน", size=11, color=ThemeColors.TEXT_MUTED)
                        ]
                    ),
                    ft.Container(
                        height=180,
                        padding=ft.Padding.symmetric(vertical=10),
                        content=self.trend_bars_row
                    )
                ]
            ),
            padding=18
        )

        # Visual Chart 2: Category Share Visual Progress Bars
        self.category_bars_col = ft.Column(spacing=10)
        self.chart_category_card = create_card(
            ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.PIE_CHART_OUTLINE_ROUNDED, color=ThemeColors.INDIGO, size=20),
                            ft.Text("สัดส่วนยอดขายตามหมวดหมู่ (Category Share)", size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN)
                        ]
                    ),
                    self.category_bars_col
                ]
            ),
            padding=18
        )

        # Visual Chart 3: Payment Split Comparison Card
        self.payment_bars_col = ft.Column(spacing=10)
        self.chart_payment_card = create_card(
            ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.DONUT_LARGE_ROUNDED, color=ThemeColors.EMERALD, size=20),
                            ft.Text("สัดส่วนช่องทางชำระเงิน (Payment Split)", size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN)
                        ]
                    ),
                    self.payment_bars_col
                ]
            ),
            padding=18
        )

        # Deep-Dive Tables
        self.top_sellers_table = ft.DataTable(
            heading_row_color=ThemeColors.SURFACE_HOVER,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN, size=12),
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

        charts_row = ft.ResponsiveRow(
            spacing=16,
            run_spacing=16,
            controls=[
                ft.Container(col={"sm": 12, "md": 12}, content=self.chart_trend_card),
                ft.Container(col={"sm": 12, "md": 6}, content=self.chart_category_card),
                ft.Container(col={"sm": 12, "md": 6}, content=self.chart_payment_card),
            ]
        )

        analytics_row = ft.ResponsiveRow(
            spacing=16,
            run_spacing=16,
            controls=[
                ft.Container(
                    col={"sm": 12, "md": 7},
                    content=create_card(
                        ft.Column(
                            spacing=12,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Icon(ft.Icons.LEADERBOARD_ROUNDED, color=ThemeColors.AMBER_DARK, size=20),
                                        ft.Text("5 อันดับเมนูขายดีที่สุด (Top 5 Best Sellers)", size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN)
                                    ]
                                ),
                                self.top_sellers_table
                            ]
                        ),
                        padding=18
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 5},
                    content=create_card(
                        ft.Column(
                            spacing=12,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED, color=ThemeColors.PURPLE, size=20),
                                        ft.Text("สรุปต้นทุน & ของเสีย (Cost Analysis)", size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN)
                                    ]
                                ),
                                self.cost_breakdown_col
                            ]
                        ),
                        padding=18
                    )
                )
            ]
        )

        # Order Transaction History Table
        self.orders_table = ft.DataTable(
            heading_row_color=ThemeColors.SURFACE_HOVER,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN, size=12),
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

        history_card = create_card(
            ft.Column(
                spacing=14,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.RECEIPT_LONG_ROUNDED, color=ThemeColors.SAPPHIRE, size=20),
                            ft.Text("ประวัติรายการขายทั้งหมด (Transaction History)", size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN)
                        ]
                    ),
                    ft.Container(content=ft.ListView([self.orders_table], expand=False))
                ]
            ),
            padding=18
        )

        header_actions = [
            create_button(
                "ส่งออกข้อมูล (Export CSV)",
                icon=ft.Icons.DOWNLOAD_ROUNDED,
                bg_color=ThemeColors.EMERALD,
                on_click=self._handle_export_csv
            )
        ]

        body_content = ft.ListView(
            spacing=16,
            controls=[
                filter_bar,
                kpi_row,
                charts_row,
                analytics_row,
                history_card
            ]
        )

        shell = AdminShell(
            page=page,
            current_route="/admin/reports",
            title="รายงานยอดขาย & วิเคราะห์การเงิน (Sales Analytics)",
            subtitle="สรุปรายได้, สัดส่วนยอดขาย, อัตราส่วนต้นทุนอาหาร Food Cost % และประวัติการสั่งซื้อ",
            content_control=body_content,
            header_actions=header_actions
        )

        super().__init__(
            route="/admin/reports",
            controls=[shell],
            padding=0,
            spacing=0
        )

        self._load_reports_data()

    def _get_period_btn_style(self, is_active: bool):
        if is_active:
            return ft.ButtonStyle(
                bgcolor=ThemeColors.BG_DARK,
                color=ThemeColors.TEXT_WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation=0,
                padding=ft.Padding.symmetric(horizontal=14, vertical=8)
            )
        return ft.ButtonStyle(
            bgcolor=ThemeColors.SURFACE_WHITE,
            color=ThemeColors.TEXT_MUTED,
            shape=ft.RoundedRectangleBorder(radius=8),
            side=ft.BorderSide(1, ThemeColors.BORDER_LIGHT),
            elevation=0,
            padding=ft.Padding.symmetric(horizontal=14, vertical=8)
        )

    def _build_card(self, title, val_control, icon, color):
        card_content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(title, size=12, color=ThemeColors.TEXT_MUTED, weight=ft.FontWeight.W_500),
                        val_control
                    ]
                ),
                ft.Container(
                    width=38,
                    height=38,
                    bgcolor=f"{color}18",
                    border_radius=8,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(icon, color=color, size=22)
                )
            ]
        )
        return create_card(card_content, padding=16)

    def _change_period(self, period: str):
        self.current_period = period
        buttons = [("today", self.btn_today), ("7days", self.btn_7days), ("month", self.btn_month), ("all", self.btn_all)]
        for p, btn in buttons:
            btn.style = self._get_period_btn_style(p == period)
        self._load_reports_data()

    def _load_reports_data(self):
        db = SessionLocal()
        try:
            report = ReportService.get_sales_report(db, period=self.current_period)

            self.kpi_net_sales.value = f"{report['total_net']:,.2f} ฿"
            self.kpi_payment_split.value = f"เงินสด: {report['cash_sales']:,.2f} ฿\nQR: {report['qr_sales']:,.2f} ฿"
            self.kpi_bill_stats.value = f"{report['bill_count']} บิล (เฉลี่ย {report['avg_bill']:,.2f} ฿)"
            self.kpi_food_cost.value = f"{report['food_cost_pct']:.1f}% (กำไร {report['gross_profit']:,.2f} ฿)"

            daily_data = report.get("daily_trend", [])
            max_sales = max([d["sales"] for d in daily_data] + [1000.0])
            self.trend_bars_row.controls.clear()

            for d in daily_data:
                height_ratio = min(1.0, max(0.08, d["sales"] / max_sales))
                bar_height = height_ratio * 120.0
                bar_color = ThemeColors.SAPPHIRE if d["sales"] > 0 else ThemeColors.BORDER_LIGHT

                self.trend_bars_row.controls.append(
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                        controls=[
                            ft.Text(f"{d['sales']:,.0f}฿" if d["sales"] > 0 else "0฿", size=10, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN),
                            ft.Container(
                                width=32,
                                height=bar_height,
                                bgcolor=bar_color,
                                border_radius=ft.BorderRadius(top_left=6, top_right=6, bottom_left=0, bottom_right=0),
                                tooltip=f"{d['day_name']} ({d['date']}): {d['sales']:,.2f} ฿ ({d['bills']} บิล)"
                            ),
                            ft.Text(d["day_label"], size=11, color=ThemeColors.TEXT_MUTED, weight=ft.FontWeight.W_500)
                        ]
                    )
                )

            palette = [ThemeColors.CRIMSON, ThemeColors.AMBER_DARK, ThemeColors.SAPPHIRE, ThemeColors.EMERALD, ThemeColors.PURPLE]
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
                                            ft.Container(width=8, height=8, bgcolor=color, border_radius=2),
                                            ft.Text(c["name"], size=12, weight=ft.FontWeight.W_500, color=ThemeColors.TEXT_MAIN)
                                        ]),
                                        ft.Text(f"{c['revenue']:,.2f} ฿ ({c['pct']:.1f}%)", size=11, weight=ft.FontWeight.BOLD, color=color)
                                    ]
                                ),
                                ft.ProgressBar(value=progress_val, color=color, bgcolor=ThemeColors.BORDER_LIGHT, height=6)
                            ]
                        )
                    )
            else:
                self.category_bars_col.controls.append(ft.Text("ยังไม่มีข้อมูลยอดขายหมวดหมู่", size=12, color=ThemeColors.TEXT_MUTED))

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
                                        ft.Icon(ft.Icons.PAYMENTS_ROUNDED, size=15, color=ThemeColors.EMERALD),
                                        ft.Text("เงินสด (Cash)", size=12, weight=ft.FontWeight.W_500, color=ThemeColors.TEXT_MAIN)
                                    ]),
                                    ft.Text(f"{cash_val:,.2f} ฿ ({c_pct:.1f}%)", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD)
                                ]
                            ),
                            ft.ProgressBar(value=c_pct / 100.0, color=ThemeColors.EMERALD, bgcolor=ThemeColors.BORDER_LIGHT, height=6)
                        ]
                    ),
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Row([
                                        ft.Icon(ft.Icons.QR_CODE_2_ROUNDED, size=15, color=ThemeColors.SAPPHIRE),
                                        ft.Text("QR PromptPay", size=12, weight=ft.FontWeight.W_500, color=ThemeColors.TEXT_MAIN)
                                    ]),
                                    ft.Text(f"{qr_val:,.2f} ฿ ({q_pct:.1f}%)", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.SAPPHIRE)
                                ]
                            ),
                            ft.ProgressBar(value=q_pct / 100.0, color=ThemeColors.SAPPHIRE, bgcolor=ThemeColors.BORDER_LIGHT, height=6)
                        ]
                    )
                ])
            else:
                self.payment_bars_col.controls.append(ft.Text("ยังไม่มีข้อมูลการชำระเงิน", size=12, color=ThemeColors.TEXT_MUTED))

            self.top_sellers_table.rows.clear()
            if report["top_sellers"]:
                for idx, item in enumerate(report["top_sellers"], 1):
                    self.top_sellers_table.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(f"#{idx}", weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MUTED)),
                                ft.DataCell(ft.Text(item["name"], weight=ft.FontWeight.W_500, color=ThemeColors.TEXT_MAIN)),
                                ft.DataCell(create_badge(item["category"], f"{ThemeColors.INDIGO}18", ThemeColors.INDIGO)),
                                ft.DataCell(ft.Text(f"{item['qty']} จาน", weight=ft.FontWeight.BOLD, color=ThemeColors.SAPPHIRE)),
                                ft.DataCell(ft.Text(f"{item['revenue']:,.2f} ฿", weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD)),
                            ]
                        )
                    )
            else:
                self.top_sellers_table.rows.append(
                    ft.DataRow(cells=[ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("ยังไม่มีข้อมูลการขาย")), ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("-"))])
                )

            self.cost_breakdown_col.controls = [
                self._build_cost_item("ต้นทุนวัตถุดิบ (COGS):", f"{report['total_food_cost']:,.2f} ฿", ThemeColors.TEXT_MAIN),
                self._build_cost_item("มูลค่าของเสีย (Wastage):", f"{report['total_wastage_cost']:,.2f} ฿", ThemeColors.CRIMSON),
                ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                self._build_cost_item("กำไรขั้นต้น (Gross Profit):", f"{report['gross_profit']:,.2f} ฿", ThemeColors.EMERALD, is_bold=True),
                self._build_cost_item("อัตรากำไร (Margin %):", f"{report['gross_margin_pct']:.1f} %", ThemeColors.INDIGO, is_bold=True),
            ]

            self.orders_table.rows.clear()
            for o in report["orders"][:20]:
                staff_name = o.user.name if o.user else "-"
                tbl = f"โต๊ะ {o.table.table_number}" if o.table else (o.customer_name or "Takeaway")
                dt_str = o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else "-"
                order_id = o.id

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(o.order_number, weight=ft.FontWeight.BOLD, color=ThemeColors.SAPPHIRE)),
                        ft.DataCell(ft.Text(dt_str, size=11, color=ThemeColors.TEXT_MUTED)),
                        ft.DataCell(create_badge(o.order_type.value if hasattr(o.order_type, "value") else str(o.order_type), f"{ThemeColors.INDIGO}18", ThemeColors.INDIGO)),
                        ft.DataCell(ft.Text(tbl, weight=ft.FontWeight.W_500, color=ThemeColors.TEXT_MAIN)),
                        ft.DataCell(ft.Text(staff_name, size=12, color=ThemeColors.TEXT_MUTED)),
                        ft.DataCell(create_badge(o.payment_method or "-", f"{ThemeColors.EMERALD}18", ThemeColors.EMERALD)),
                        ft.DataCell(ft.Text(f"{float(o.discount_amount):,.2f} ฿", color=ThemeColors.AMBER_DARK)),
                        ft.DataCell(ft.Text(f"{float(o.net_amount):,.2f} ฿", weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD)),
                        ft.DataCell(
                            ft.IconButton(
                                ft.Icons.RECEIPT_ROUNDED,
                                icon_color=ThemeColors.SAPPHIRE,
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
                ft.Text(label, size=13, color=ThemeColors.TEXT_MUTED, weight=ft.FontWeight.BOLD if is_bold else ft.FontWeight.NORMAL),
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
            
            exports_dir = os.path.join(os.getcwd(), "exports")
            os.makedirs(exports_dir, exist_ok=True)
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sales_report_{self.current_period}_{timestamp_str}.csv"
            filepath = os.path.join(exports_dir, filename)
            
            with open(filepath, "w", encoding="utf-8-sig") as f:
                f.write(csv_content)

            download_url = f"/{filename}"

            btn_copy = ft.OutlinedButton(
                "คัดลอกข้อมูล (Copy)",
                icon=ft.Icons.CONTENT_COPY_ROUNDED
            )

            def copy_to_clipboard(e_copy):
                try:
                    self.page_ref.clipboard = csv_content
                except Exception:
                    pass
                btn_copy.text = "คัดลอกสำเร็จแล้ว!"
                btn_copy.icon = ft.Icons.CHECK_ROUNDED
                try:
                    btn_copy.update()
                except Exception:
                    pass

                try:
                    self.page_ref.snack_bar = ft.SnackBar(
                        content=ft.Text("คัดลอกข้อมูล CSV สำเร็จ! นำไปวางใน Excel หรือ Google Sheets ได้ทันที", color=ThemeColors.TEXT_WHITE),
                        bgcolor=ThemeColors.EMERALD,
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
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ThemeColors.EMERALD, size=24),
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
                                bgcolor=f"{ThemeColors.SAPPHIRE}15",
                                padding=10,
                                border_radius=8,
                                content=ft.Row([
                                    ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, color=ThemeColors.SAPPHIRE, size=18),
                                    ft.Text(f"บันทึกไฟล์ไว้ที่: exports/{filename}", size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.SAPPHIRE)
                                ])
                            ),
                            ft.Text("ข้อมูล CSV (สามารถเลือกคลุมดำและคัดลอกได้โดยตรง):", size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MUTED),
                            ft.TextField(
                                value=csv_content,
                                multiline=True,
                                min_lines=5,
                                max_lines=7,
                                read_only=True,
                                text_size=11,
                                bgcolor=ThemeColors.SURFACE_HOVER,
                                border_color=ThemeColors.BORDER_LIGHT
                            )
                        ]
                    )
                ),
                actions=[
                    btn_copy,
                    create_button("ดาวน์โหลดไฟล์ (Download)", icon=ft.Icons.DOWNLOAD_ROUNDED, bg_color=ThemeColors.EMERALD, on_click=trigger_download),
                    ft.TextButton("ปิด", on_click=lambda e: self._close_dialog(dialog))
                ]
            )
            self._open_dialog(dialog)
        finally:
            db.close()

    def _open_dialog(self, dialog: ft.AlertDialog):
        open_dialog(self.page_ref, dialog)

    def _close_dialog(self, dialog: ft.AlertDialog = None):
        close_dialog(self.page_ref, dialog)
        self._update_ui()

    def _update_ui(self):
        try:
            self.update()
        except Exception:
            pass
        try:
            self.page_ref.update()
        except Exception:
            pass
