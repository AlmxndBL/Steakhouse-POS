import json
import logging
import flet as ft
from datetime import datetime, date, timezone
from database.connection import SessionLocal
from database.models import AuditLog, Order, OrderStatus, Table, TableStatus
from services.bom_engine import BOMEngine
from services.shift_service import ShiftService
from components.theme import ThemeColors, create_card, create_badge, create_button
from components.admin_shell import AdminShell
from utils.navigation import navigate_to

class AdminDashboardView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        user_name = page.session.store.get("user_name") or "ผู้บริหาร"
        user_role = page.session.store.get("user_role") or "OWNER"

        # KPI Metrics Values
        self.shift_text = ft.Text("ยังไม่มีข้อมูลกะ", size=13, color=ThemeColors.TEXT_MUTED)
        self.kpi_sales_text = ft.Text("0.00 ฿", size=26, weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD)
        self.kpi_bills_text = ft.Text("0 บิล", size=26, weight=ft.FontWeight.BOLD, color=ThemeColors.SAPPHIRE)
        self.kpi_tables_text = ft.Text("0 / 0 โต๊ะ", size=26, weight=ft.FontWeight.BOLD, color=ThemeColors.AMBER_DARK)
        self.kpi_low_stock_text = ft.Text("0 รายการ", size=26, weight=ft.FontWeight.BOLD, color=ThemeColors.CRIMSON)

        # KPI Cards Deck
        kpi_cards = ft.ResponsiveRow(
            spacing=16,
            run_spacing=16,
            controls=[
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    content=self._build_kpi_card(
                        icon=ft.Icons.PAYMENTS_ROUNDED,
                        icon_color=ThemeColors.EMERALD,
                        title="ยอดขายรวมทั้งหมด",
                        subtitle="บิลชำระเงินสำเร็จ",
                        value_control=self.kpi_sales_text,
                        badge_text="Real-time",
                        badge_color=ThemeColors.EMERALD
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    content=self._build_kpi_card(
                        icon=ft.Icons.RECEIPT_LONG_ROUNDED,
                        icon_color=ThemeColors.SAPPHIRE,
                        title="จำนวนบิลที่ปิดยอด",
                        subtitle="คำสั่งซื้อสำเร็จ",
                        value_control=self.kpi_bills_text,
                        badge_text="Completed",
                        badge_color=ThemeColors.SAPPHIRE
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    content=self._build_kpi_card(
                        icon=ft.Icons.TABLE_RESTAURANT_ROUNDED,
                        icon_color=ThemeColors.AMBER_DARK,
                        title="โต๊ะที่มีลูกค้า (Occupied)",
                        subtitle="สถานะโต๊ะหน้าร้าน",
                        value_control=self.kpi_tables_text,
                        badge_text="Live Dine-in",
                        badge_color=ThemeColors.AMBER_GOLD
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 3},
                    content=self._build_kpi_card(
                        icon=ft.Icons.WARNING_AMBER_ROUNDED,
                        icon_color=ThemeColors.CRIMSON,
                        title="วัตถุดิบใกล้หมดสต็อก",
                        subtitle="ต่ำกว่า Reorder Point",
                        value_control=self.kpi_low_stock_text,
                        badge_text="Low Alert",
                        badge_color=ThemeColors.CRIMSON
                    )
                ),
            ]
        )

        # Quick Modules Grid
        modules_grid = ft.ResponsiveRow(
            spacing=16,
            run_spacing=16,
            controls=[
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 4},
                    content=self._build_module_card(
                        title="เมนูอาหาร & หมวดหมู่",
                        desc="จัดการรายการสเต๊ก เครื่องเคียง ราคาขาย และเปิด/ปิดการจำหน่าย",
                        icon=ft.Icons.RESTAURANT_MENU_ROUNDED,
                        icon_color=ThemeColors.AMBER_DARK,
                        route="/admin/menus"
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 4},
                    content=self._build_module_card(
                        title="ผังโต๊ะอาหาร & โซน",
                        desc="เพิ่ม/แก้ไขผังโต๊ะ กำหนดจำนวนที่นั่ง และจัดสรรโซน Indoor / VIP",
                        icon=ft.Icons.TABLE_RESTAURANT_ROUNDED,
                        icon_color=ThemeColors.SAPPHIRE,
                        route="/admin/tables"
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 4},
                    content=self._build_module_card(
                        title="คลังสินค้า & สต็อกวัตถุดิบ",
                        desc="รับวัตถุดิบเข้าคลัง, ตรวจนับสต็อกจริง, ตัดของเสีย และสูตรตัดสต็อก BOM",
                        icon=ft.Icons.INVENTORY_2_ROUNDED,
                        icon_color=ThemeColors.EMERALD,
                        route="/admin/stock"
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 4},
                    content=self._build_module_card(
                        title="รายงานยอดขาย & การเงิน",
                        desc="วิเคราะห์รายได้, สรุปอันดับเมนูขายดี และส่งออกข้อมูลเป็น CSV",
                        icon=ft.Icons.BAR_CHART_ROUNDED,
                        icon_color=ThemeColors.INDIGO,
                        route="/admin/reports"
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 4},
                    content=self._build_module_card(
                        title="จัดการพนักงาน & สิทธิ์",
                        desc="เพิ่มพนักงานใหม่, รีเซ็ตรหัสผ่าน และกำหนดบทบาท 5 ระดับ",
                        icon=ft.Icons.PEOPLE_ALT_ROUNDED,
                        icon_color="#0D9488",
                        route="/admin/staff"
                    )
                ),
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 4},
                    content=self._build_module_card(
                        title="บันทึกประวัติ (Audit Logs)",
                        desc="ตรวจสอบประวัติการทำรายการย้อนหลังเพื่อความโปร่งใสและปลอดภัย",
                        icon=ft.Icons.SECURITY_ROUNDED,
                        icon_color=ThemeColors.PURPLE,
                        route="/admin/audit"
                    )
                ),
            ]
        )

        # Dashboard Scrollable Body
        dashboard_content = ft.ListView(
            spacing=20,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("ดัชนีชี้วัดหลักประจำร้าน (Executive KPI Metrics)", size=16, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN),
                        ft.ElevatedButton(
                            "รีเฟรชข้อมูล",
                            icon=ft.Icons.REFRESH_ROUNDED,
                            style=ft.ButtonStyle(
                                bgcolor=ThemeColors.SURFACE_WHITE,
                                color=ThemeColors.TEXT_MAIN,
                                shape=ft.RoundedRectangleBorder(radius=8),
                                side=ft.BorderSide(1, ThemeColors.BORDER_LIGHT)
                            ),
                            on_click=lambda e: self._load_kpi_data()
                        )
                    ]
                ),
                kpi_cards,
                create_card(ft.Row([
                    ft.Icon(ft.Icons.WORK_HISTORY_ROUNDED, color=ThemeColors.SAPPHIRE),
                    ft.Column([ft.Text("สถานะกะล่าสุด", weight=ft.FontWeight.BOLD), self.shift_text], spacing=2),
                    ft.Row([
                        ft.TextButton("เปิดกะ", on_click=self._open_shift_dialog),
                        ft.TextButton("ปิดกะ", on_click=self._close_shift_dialog),
                        ft.TextButton("ดู Audit", on_click=lambda e: navigate_to(self.page_ref, "/admin/audit")),
                    ]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=14),
                ft.Container(height=10),
                ft.Text("ระบบการจัดการและบริการส่วนกลาง", size=16, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN),
                modules_grid
            ]
        )

        shell = AdminShell(
            page=page,
            current_route="/admin",
            title="แดชบอร์ดภาพรวม (Dashboard)",
            subtitle="ศูนย์ควบคุมและสรุปสถานะการทำงานของร้านสเต๊ก",
            content_control=dashboard_content
        )

        super().__init__(
            route="/admin",
            controls=[shell],
            padding=0,
            spacing=0
        )

        self._load_kpi_data()

    def _build_kpi_card(self, icon, icon_color, title, subtitle, value_control, badge_text, badge_color):
        card_content = ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Container(
                            width=42,
                            height=42,
                            bgcolor=f"{icon_color}18",
                            border_radius=10,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(icon, color=icon_color, size=24)
                        ),
                        create_badge(badge_text, f"{badge_color}22", badge_color)
                    ]
                ),
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text(title, size=13, color=ThemeColors.TEXT_MUTED, weight=ft.FontWeight.W_500),
                        value_control,
                        ft.Text(subtitle, size=11, color=ThemeColors.TEXT_LIGHT)
                    ]
                )
            ]
        )
        return create_card(card_content, padding=18)

    def _open_shift_dialog(self, e):
        opening = ft.TextField(label="เงินทอนเริ่มต้น", value="0", keyboard_type=ft.KeyboardType.NUMBER)
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("เปิดกะ"),
            content=opening,
            actions=[ft.TextButton("ยกเลิก", on_click=lambda _: self._close_dialog(dialog)), create_button("ยืนยัน", bg_color=ThemeColors.EMERALD, on_click=lambda _: self._submit_shift_start(dialog, opening))],
        )
        self._show_dialog(dialog)

    def _submit_shift_start(self, dialog, opening):
        db = SessionLocal()
        try:
            ShiftService.start_shift(db, self.page_ref.session.store.get("user_id"), float(opening.value or 0))
            self._close_dialog(dialog)
            self._load_kpi_data()
        except (ValueError, TypeError) as err:
            self._show_message(str(err))
        finally:
            db.close()

    def _close_shift_dialog(self, e):
        actual = ft.TextField(label="เงินสดจริงตอนปิดกะ", value="0", keyboard_type=ft.KeyboardType.NUMBER)
        reason = ft.TextField(label="หมายเหตุ (ถ้ามี)", multiline=True)
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("ปิดกะและกระทบยอด"),
            content=ft.Column([actual, reason], tight=True),
            actions=[ft.TextButton("ยกเลิก", on_click=lambda _: self._close_dialog(dialog)), create_button("ยืนยัน", bg_color=ThemeColors.EMERALD, on_click=lambda _: self._submit_shift_end(dialog, actual, reason))],
        )
        self._show_dialog(dialog)

    def _submit_shift_end(self, dialog, actual, reason):
        db = SessionLocal()
        try:
            result = ShiftService.close_shift(db, self.page_ref.session.store.get("user_id"), float(actual.value or 0), reason.value or "")
            self._close_dialog(dialog)
            self.shift_text.value = f"ปิดกะแล้ว • Expected {result['expected_cash']:,.2f} ฿ • Variance {result['variance']:,.2f} ฿"
            self._update_ui()
        except (ValueError, TypeError) as err:
            self._show_message(str(err))
        finally:
            db.close()

    def _show_dialog(self, dialog):
        self.page_ref.dialog = dialog
        dialog.open = True
        self.page_ref.update()

    def _close_dialog(self, dialog):
        dialog.open = False
        self.page_ref.update()

    def _show_message(self, message):
        self.page_ref.snack_bar = ft.SnackBar(ft.Text(message), open=True)
        self.page_ref.update()

    def _build_module_card(self, title, desc, icon, icon_color, route):
        card_content = ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Container(
                            width=40,
                            height=40,
                            bgcolor=f"{icon_color}18",
                            border_radius=8,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(icon, color=icon_color, size=22)
                        ),
                        ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=14, color=ThemeColors.TEXT_LIGHT)
                    ]
                ),
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN),
                        ft.Text(desc, size=12, color=ThemeColors.TEXT_MUTED, max_lines=2)
                    ]
                )
            ]
        )
        return create_card(card_content, padding=18, on_click=lambda e: navigate_to(self.page_ref, route), ink=True)

    def _load_kpi_data(self):
        db = SessionLocal()
        try:
            paid_orders = db.query(Order).filter(Order.status == OrderStatus.PAID).all()
            total_sales = sum(float(o.net_amount) for o in paid_orders)
            self.kpi_sales_text.value = f"{total_sales:,.2f} ฿"
            self.kpi_bills_text.value = f"{len(paid_orders)} บิล"

            total_tables = db.query(Table).count()
            occupied_tables = db.query(Table).filter(Table.status == TableStatus.OCCUPIED).count()
            self.kpi_tables_text.value = f"{occupied_tables} / {total_tables} โต๊ะ"

            inventory = BOMEngine.get_inventory_status(db)
            low_stock_count = sum(1 for item in inventory if item["status"] in ["LOW_STOCK", "OUT_OF_STOCK"])
            self.kpi_low_stock_text.value = f"{low_stock_count} รายการ"

            latest_shift = db.query(AuditLog).filter(AuditLog.action.in_(["SHIFT_START", "SHIFT_END"])).order_by(AuditLog.timestamp.desc()).first()
            if latest_shift:
                data = json.loads(latest_shift.details_json or "{}")
                if latest_shift.action == "SHIFT_END":
                    self.shift_text.value = f"ปิดกะแล้ว • Expected {data.get('expected_cash', 0):,.2f} ฿ • Variance {data.get('variance', 0):,.2f} ฿"
                else:
                    self.shift_text.value = f"เปิดกะแล้ว • เงินทอนเริ่มต้น {data.get('opening_float', 0):,.2f} ฿"

            self._update_ui()
        finally:
            db.close()

    def _update_ui(self):
        try:
            self.update()
        except RuntimeError as err:
            logging.debug("Admin dashboard view update skipped: %s", err)
        try:
            self.page_ref.update()
        except RuntimeError as err:
            logging.debug("Admin dashboard page update skipped: %s", err)
