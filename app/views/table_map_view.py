import flet as ft
import logging
from database.connection import SessionLocal
from database.models import OrderType, OrderItem
from services.order_service import OrderService
from services.table_service import TableService
from components.table_card import TableCard
from components.pos_header import create_pos_header
from components.theme import ThemeColors, create_button, create_badge
from utils.navigation import navigate_to

class TableMapView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        self.selected_zone = "ALL"

        user_role = page.session.store.get("user_role") or "STAFF"

        # Action Buttons in Header
        header_actions = [
            create_button(
                "ออเดอร์ Takeaway",
                icon=ft.Icons.SHOPPING_BAG_ROUNDED,
                bg_color=ThemeColors.AMBER_DARK,
                on_click=self._handle_takeaway
            )
        ]
        if user_role in ["OWNER", "MANAGER", "KITCHEN"]:
            header_actions.append(
                create_button(
                    "จอครัว (KDS)",
                    icon=ft.Icons.KITCHEN_ROUNDED,
                    bg_color=ThemeColors.CRIMSON,
                    on_click=lambda e: navigate_to(self.page_ref, "/kds")
                )
            )

        pos_header = create_pos_header(
            page=page,
            title="ผังโต๊ะอาหารหน้าร้าน (Table Map)",
            subtitle="เลือกโต๊ะเพื่อเปิดบิล / รับออเดอร์ หรือสั่งอาหารกลับบ้าน",
            icon=ft.Icons.TABLE_RESTAURANT_ROUNDED,
            action_controls=header_actions
        )

        # Zone Filter Tabs
        self.zone_buttons = []
        zones = [
            ("ALL", "ทั้งหมด (All Zones)"),
            ("Indoor", "ห้องแอร์ (Indoor)"),
            ("Terrace", "ระเบียง (Terrace)"),
            ("VIP Room", "ห้องวีไอพี (VIP Room)"),
            ("Outdoor", "กลางแจ้ง (Outdoor)"),
        ]

        zone_row_controls = []
        for z_code, z_label in zones:
            btn = ft.ElevatedButton(
                z_label,
                style=self._get_zone_btn_style(z_code == "ALL"),
                on_click=lambda e, zc=z_code: self._filter_zone(zc)
            )
            self.zone_buttons.append((z_code, btn))
            zone_row_controls.append(btn)

        zone_bar = ft.Container(
            padding=ft.Padding.symmetric(horizontal=24, vertical=14),
            bgcolor=ThemeColors.SURFACE_WHITE,
            border=ft.Border(bottom=ft.BorderSide(1, ThemeColors.BORDER_LIGHT)),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(spacing=8, controls=zone_row_controls),
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.Row([ft.Container(width=10, height=10, bgcolor=ThemeColors.EMERALD, border_radius=5), ft.Text("ว่าง", size=12, color=ThemeColors.TEXT_MUTED)]),
                            ft.Row([ft.Container(width=10, height=10, bgcolor=ThemeColors.AMBER_DARK, border_radius=5), ft.Text("มีลูกค้า", size=12, color=ThemeColors.TEXT_MUTED)]),
                            ft.Row([ft.Container(width=10, height=10, bgcolor=ThemeColors.SAPPHIRE, border_radius=5), ft.Text("รอทำความสะอาด", size=12, color=ThemeColors.TEXT_MUTED)]),
                        ]
                    )
                ]
            )
        )

        # Load Tables Grid
        self.grid = ft.GridView(
            expand=True,
            runs_count=4,
            max_extent=240,
            child_aspect_ratio=1.35,
            spacing=16,
            run_spacing=16,
            padding=24
        )
        super().__init__(
            route="/tables",
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        pos_header,
                        zone_bar,
                        ft.Container(
                            expand=True,
                            bgcolor=ThemeColors.BG_PAGE,
                            content=self.grid
                        )
                    ]
                )
            ],
            padding=0,
            spacing=0
        )
        self._load_tables()

    def _get_zone_btn_style(self, is_active: bool):
        if is_active:
            return ft.ButtonStyle(
                bgcolor=ThemeColors.BG_DARK,
                color=ThemeColors.TEXT_WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation=0,
                padding=ft.Padding.symmetric(horizontal=14, vertical=8)
            )
        return ft.ButtonStyle(
            bgcolor=ThemeColors.SURFACE_HOVER,
            color=ThemeColors.TEXT_MUTED,
            shape=ft.RoundedRectangleBorder(radius=8),
            side=ft.BorderSide(1, ThemeColors.BORDER_LIGHT),
            elevation=0,
            padding=ft.Padding.symmetric(horizontal=14, vertical=8)
        )

    def _filter_zone(self, zone_code: str):
        self.selected_zone = zone_code
        for zc, btn in self.zone_buttons:
            btn.style = self._get_zone_btn_style(zc == zone_code)
        self._load_tables()

    def _load_tables(self):
        db = SessionLocal()
        try:
            tables = TableService.get_tables(db)
            self.grid.controls.clear()
            for t in tables:
                if self.selected_zone != "ALL" and (t.zone or "Indoor") != self.selected_zone:
                    continue
                card = TableCard(table=t, on_click=self._on_table_click, on_manage=self._open_table_operations)
                self.grid.controls.append(card)
            self._update_ui()
        finally:
            db.close()

    def _on_table_click(self, table):
        db = SessionLocal()
        user_id = self.page_ref.session.store.get("user_id")
        if user_id is None:
            navigate_to(self.page_ref, "/login")
            return
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
        user_id = self.page_ref.session.store.get("user_id")
        if user_id is None:
            navigate_to(self.page_ref, "/login")
            return
        try:
            order = OrderService.create_or_get_open_order(
                db, table_id=None, order_type=OrderType.TAKEAWAY, customer_name="ลูกค้า Takeaway", user_id=user_id
            )
            self.page_ref.session.store.set("active_order_id", order.id)
            navigate_to(self.page_ref, "/pos")
        finally:
            db.close()

    def _open_table_operations(self, table):
        order = getattr(table, "current_order", None)
        if not order:
            return
        lookup_db = SessionLocal()
        try:
            targets = [candidate for candidate in TableService.get_tables(lookup_db) if candidate.id != table.id and candidate.status == "VACANT"]
        finally:
            lookup_db.close()
        target_dropdown = ft.Dropdown(
            label="โต๊ะปลายทาง (โอน/รวม)",
            options=[ft.DropdownOption(key=str(candidate.id), text=candidate.table_number) for candidate in targets],
        )
        item_dropdown = ft.Dropdown(
            label="รายการที่จะแยก",
            options=[ft.DropdownOption(key=str(item.id), text=f"{item.menu_item.name} x{item.quantity}") for item in order.items],
        )
        quantity_input = ft.TextField(label="จำนวนที่แยก", value="1", keyboard_type=ft.KeyboardType.NUMBER)
        operation = ft.Dropdown(
            label="การทำงาน",
            value="TRANSFER",
            options=[
                ft.DropdownOption(key="TRANSFER", text="ย้ายโต๊ะ"),
                ft.DropdownOption(key="MERGE", text="รวมบิลเข้ากับโต๊ะปลายทาง"),
                ft.DropdownOption(key="SPLIT", text="แยกรายการเป็นบิลใหม่"),
            ],
        )
        form = ft.Column([operation, target_dropdown, item_dropdown, quantity_input], tight=True, spacing=8)

        def refresh_fields(e):
            is_split = operation.value == "SPLIT"
            target_dropdown.visible = not is_split
            item_dropdown.visible = is_split
            quantity_input.visible = is_split
            dialog.update()

        operation.on_change = refresh_fields

        def submit(e):
            db = SessionLocal()
            try:
                user_id = self.page_ref.session.store.get("user_id")
                if operation.value == "TRANSFER":
                    if not target_dropdown.value:
                        raise ValueError("กรุณาเลือกโต๊ะปลายทาง")
                    TableService.transfer_order(db, order.id, int(target_dropdown.value), user_id)
                elif operation.value == "MERGE":
                    if not target_dropdown.value:
                        raise ValueError("กรุณาเลือกโต๊ะปลายทาง")
                    target = db.query(type(table)).filter(type(table).id == int(target_dropdown.value)).first()
                    if not target or not target.current_order_id:
                        raise ValueError("โต๊ะปลายทางยังไม่มีออเดอร์สำหรับรวมบิล")
                    TableService.merge_orders(db, target.current_order_id, order.id, user_id)
                else:
                    if not item_dropdown.value:
                        raise ValueError("กรุณาเลือกรายการที่จะแยก")
                    OrderService.split_item_to_new_order(db, order.id, int(item_dropdown.value), int(quantity_input.value or "0"), user_id)
                self._close_dialog(dialog)
                self._load_tables()
            except (ValueError, PermissionError) as err:
                self._show_message(str(err))
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"จัดการบิล • {table.table_number}"),
            content=form,
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                create_button("ยืนยัน", bg_color=ThemeColors.EMERALD, on_click=submit),
            ],
        )
        self.page_ref.dialog = dialog
        dialog.open = True
        self.page_ref.update()

    def _close_dialog(self, dialog):
        dialog.open = False
        self.page_ref.update()

    def _show_message(self, message):
        self.page_ref.snack_bar = ft.SnackBar(ft.Text(message), open=True)
        self.page_ref.update()

    def _update_ui(self):
        try:
            self.update()
        except RuntimeError as err:
            logging.debug("Table map view update skipped: %s", err)
        try:
            self.page_ref.update()
        except RuntimeError as err:
            logging.debug("Table map page update skipped: %s", err)
