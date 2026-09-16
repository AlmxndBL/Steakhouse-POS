import flet as ft
import logging
from datetime import datetime, date
from database.connection import SessionLocal
from database.models import Ingredient, StockLot
from services.bom_engine import BOMEngine
from components.theme import ThemeColors, create_card, create_badge, create_button
from components.admin_shell import AdminShell
from utils.validators import Validator
from utils.dialogs import open_dialog, close_dialog

class StockView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page

        # Proactive Alert Banner for Low Stock and Expiring Lots
        self.alert_banner_container = ft.Container(visible=False, padding=ft.Padding.only(bottom=16))
        self.task_summary = ft.Row(spacing=12, wrap=True)

        # Tables
        self.inventory_table = ft.DataTable(
            heading_row_color=ThemeColors.SURFACE_HOVER,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN, size=13),
            data_row_color={"hovered": f"{ThemeColors.SAPPHIRE}11"},
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text("รหัส")),
                ft.DataColumn(ft.Text("ชื่อวัตถุดิบ")),
                ft.DataColumn(ft.Text("สต๊อกปัจจุบัน")),
                ft.DataColumn(ft.Text("จุดสั่งซื้อ (Min)")),
                ft.DataColumn(ft.Text("ต้นทุนเฉลี่ย/หน่วย")),
                ft.DataColumn(ft.Text("สถานะสต๊อก")),
            ],
            rows=[]
        )

        self.lots_table = ft.DataTable(
            heading_row_color=ThemeColors.SURFACE_HOVER,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN, size=13),
            data_row_color={"hovered": f"{ThemeColors.SAPPHIRE}11"},
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text("วัตถุดิบ")),
                ft.DataColumn(ft.Text("เลข Lot/Batch")),
                ft.DataColumn(ft.Text("คงเหลือ")),
                ft.DataColumn(ft.Text("วันหมดอายุ")),
                ft.DataColumn(ft.Text("สถานะ Lot")),
            ],
            rows=[]
        )

        self.inv_container = ft.Container(content=ft.ListView([self.inventory_table], expand=True), expand=True, visible=True)
        self.lots_container = ft.Container(content=ft.ListView([self.lots_table], expand=True), expand=True, visible=False)

        # Toggle Buttons (Segmented Control Style)
        self.btn_inv = ft.ElevatedButton("📦 ภาพรวมคลังสินค้า", style=self._get_active_tab_style(), on_click=self._show_inv)
        self.btn_lots = ft.ElevatedButton("🏷️ รายละเอียดราย Lot (FIFO)", style=self._get_inactive_tab_style(), on_click=self._show_lots)

        toggle_bar = ft.Container(
            padding=ft.Padding.only(bottom=16),
            content=ft.Row([self.btn_inv, self.btn_lots], spacing=10)
        )

        header_actions = [
            create_button(
                "ตรวจนับสต็อกจริง",
                icon=ft.Icons.FACT_CHECK_ROUNDED,
                bg_color=ThemeColors.AMBER_DARK,
                on_click=self._open_stock_take_dialog
            ),
            create_button(
                "ตัดของเสีย",
                icon=ft.Icons.DELETE_SWEEP_ROUNDED,
                bg_color=ThemeColors.CRIMSON,
                on_click=self._open_wastage_dialog
            ),
            create_button(
                "+ รับวัตถุดิบเข้าคลัง",
                icon=ft.Icons.ADD_SHOPPING_CART_ROUNDED,
                bg_color=ThemeColors.EMERALD,
                on_click=self._open_receive_dialog
            )
        ]

        self.tab_content_area = ft.Container(
            expand=True,
            content=self.inv_container
        )

        main_card = create_card(
            ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    self.task_summary,
                    self.alert_banner_container,
                    toggle_bar,
                    self.tab_content_area
                ]
            ),
            padding=20
        )

        shell = AdminShell(
            page=page,
            current_route="/admin/stock",
            title="คลังสินค้า & สต็อกวัตถุดิบ (Inventory & FIFO BOM)",
            subtitle="ระบบควบคุมสต็อกวัตถุดิบ, ล็อต FIFO, การตรวจนับสต็อกจริง และการตัดของเสีย",
            content_control=main_card,
            header_actions=header_actions
        )

        super().__init__(
            route="/admin/stock",
            controls=[shell],
            padding=0,
            spacing=0
        )

        self._load_inventory_data()

    def _get_active_tab_style(self):
        return ft.ButtonStyle(
            bgcolor=ThemeColors.BG_DARK, 
            color=ThemeColors.TEXT_WHITE,
            shape=ft.RoundedRectangleBorder(radius=8),
            elevation=0,
            padding=ft.Padding.symmetric(horizontal=16, vertical=10)
        )

    def _get_inactive_tab_style(self):
        return ft.ButtonStyle(
            bgcolor=ThemeColors.SURFACE_HOVER, 
            color=ThemeColors.TEXT_MUTED,
            shape=ft.RoundedRectangleBorder(radius=8),
            elevation=0,
            side=ft.BorderSide(1, ThemeColors.BORDER_LIGHT),
            padding=ft.Padding.symmetric(horizontal=16, vertical=10)
        )

    def _show_inv(self, e):
        self.tab_content_area.content = self.inv_container
        self.btn_inv.style = self._get_active_tab_style()
        self.btn_lots.style = self._get_inactive_tab_style()
        self._update_ui()

    def _show_lots(self, e):
        self.tab_content_area.content = self.lots_container
        self.btn_inv.style = self._get_inactive_tab_style()
        self.btn_lots.style = self._get_active_tab_style()
        self._update_ui()

    def _load_inventory_data(self):
        db = SessionLocal()
        try:
            task_center = BOMEngine.get_inventory_task_center(db, expiring_days=7)
            status_list = BOMEngine.get_inventory_status(db)
            expiring_lots = task_center["expiring_lots"]

            # 1. Build Alert Banner
            low_stock_items = [i for i in status_list if i["status"] in ["LOW_STOCK", "OUT_OF_STOCK"]]
            self.task_summary.controls = [
                create_badge(f"งานสต็อกต่ำ {task_center['counts']['low_stock']}", f"{ThemeColors.CRIMSON}18", ThemeColors.CRIMSON_DARK, ft.Icons.WARNING_AMBER_ROUNDED),
                create_badge(f"ล็อตใกล้หมดอายุ {task_center['counts']['expiring_lots']}", f"{ThemeColors.AMBER_GOLD}22", ThemeColors.AMBER_DARK, ft.Icons.EVENT_BUSY_ROUNDED),
                create_badge(f"งานค้าง {task_center['counts']['pending_actions']}", f"{ThemeColors.SAPPHIRE}18", ThemeColors.SAPPHIRE, ft.Icons.TASK_ALT_ROUNDED),
            ]
            alerts = []
            if low_stock_items:
                low_names = ", ".join([f"{i['name']} ({i['current_stock']:.1f} {i['unit']})" for i in low_stock_items])
                alerts.append(
                    ft.Container(
                        bgcolor=f"{ThemeColors.CRIMSON}15",
                        border=ft.Border.all(1, f"{ThemeColors.CRIMSON}44"),
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                        content=ft.Row([
                            ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ThemeColors.CRIMSON, size=22),
                            ft.Text(f"แจ้งเตือนสินค้าใกล้หมด/หมดสต๊อก ({len(low_stock_items)} รายการ): {low_names}", color=ThemeColors.CRIMSON_DARK, weight=ft.FontWeight.W_600, size=12, expand=True),
                            ft.TextButton("ดูรายการ", on_click=self._show_inventory)
                        ])
                    )
                )

            if expiring_lots:
                exp_names = ", ".join([f"{l['ingredient_name']} (Lot: {l['lot_number']}, เหลือ {l['days_left']} วัน)" for l in expiring_lots])
                alerts.append(
                    ft.Container(
                        bgcolor=f"{ThemeColors.AMBER_GOLD}15",
                        border=ft.Border.all(1, f"{ThemeColors.AMBER_GOLD}44"),
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                        content=ft.Row([
                            ft.Icon(ft.Icons.TIMER_ROUNDED, color=ThemeColors.AMBER_DARK, size=22),
                            ft.Text(f"แจ้งเตือนวัตถุดิบใกล้หมดอายุภายใน 7 วัน ({len(expiring_lots)} รายการ): {exp_names}", color=ThemeColors.AMBER_DARK, weight=ft.FontWeight.W_600, size=12, expand=True),
                            ft.TextButton("ดูล็อต", on_click=self._show_lots)
                        ])
                    )
                )

            if alerts:
                self.alert_banner_container.content = ft.Column(alerts, spacing=8)
                self.alert_banner_container.visible = True
            else:
                self.alert_banner_container.visible = False

            # 2. Populate Inventory Table
            self.inventory_table.rows.clear()
            for item in status_list:
                status_color = ThemeColors.EMERALD
                status_bg = f"{ThemeColors.EMERALD}18"
                status_label = "ปกติ"

                if item["status"] == "OUT_OF_STOCK":
                    status_color = ThemeColors.CRIMSON
                    status_bg = f"{ThemeColors.CRIMSON}18"
                    status_label = "สินค้าหมด"
                elif item["status"] == "LOW_STOCK":
                    status_color = ThemeColors.AMBER_DARK
                    status_bg = f"{ThemeColors.AMBER_DARK}18"
                    status_label = "ใกล้หมด"

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item["code"], weight=ft.FontWeight.W_500, color=ThemeColors.TEXT_MUTED)),
                        ft.DataCell(ft.Text(item["name"], weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN)),
                        ft.DataCell(ft.Text(f"{item['current_stock']:,.1f} {item['unit']}", weight=ft.FontWeight.BOLD, color=status_color)),
                        ft.DataCell(ft.Text(f"{item['min_stock_alert']:,.1f} {item['unit']}", color=ThemeColors.TEXT_MUTED)),
                        ft.DataCell(ft.Text(f"{item['cost_per_unit']:,.2f} ฿", color=ThemeColors.TEXT_MAIN)),
                        ft.DataCell(
                            create_badge(status_label, status_bg, status_color)
                        )
                    ]
                )
                self.inventory_table.rows.append(row)

            # 3. Populate FIFO Lots Table
            self.lots_table.rows.clear()
            lots = db.query(StockLot).join(Ingredient).filter(StockLot.remaining_quantity > 0).order_by(StockLot.ingredient_id, StockLot.received_date.asc()).all()
            for l in lots:
                exp_str = l.expiry_date.strftime("%Y-%m-%d") if l.expiry_date else "-"
                is_expired = l.expiry_date and l.expiry_date < date.today()
                
                lot_color = ThemeColors.CRIMSON if is_expired else ThemeColors.SAPPHIRE
                lot_bg = f"{ThemeColors.CRIMSON}18" if is_expired else f"{ThemeColors.SAPPHIRE}18"
                lot_label = "หมดอายุแล้ว" if is_expired else "พร้อมใช้ (FIFO Active)"

                l_row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(l.ingredient.name if l.ingredient else "-", weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN)),
                        ft.DataCell(create_badge(l.lot_number, f"{ThemeColors.INDIGO}18", ThemeColors.INDIGO)),
                        ft.DataCell(ft.Text(f"{float(l.remaining_quantity):,.1f} / {float(l.initial_quantity):,.1f} {l.ingredient.unit if l.ingredient else ''}", weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN)),
                        ft.DataCell(ft.Text(exp_str, color=ThemeColors.CRIMSON if is_expired else ThemeColors.TEXT_MUTED)),
                        ft.DataCell(
                            create_badge(lot_label, lot_bg, lot_color)
                        )
                    ]
                )
                self.lots_table.rows.append(l_row)

            self._update_ui()
        finally:
            db.close()

    def _open_receive_dialog(self, e):
        db = SessionLocal()
        try:
            ingredients = db.query(Ingredient).all()
            if not ingredients:
                return

            ing_options = [ft.dropdown.Option(str(i.id), f"{i.name} ({i.unit})") for i in ingredients]
            ing_dropdown = ft.Dropdown(label="เลือกวัตถุดิบ", options=ing_options, value=str(ingredients[0].id), width=380)
            lot_input = ft.TextField(label="เลขที่ Lot/Batch (เช่น LOT-20260825-01)", width=380)
            qty_input = ft.TextField(label="จำนวนที่รับเข้า (ตามหน่วย)", width=380)
            cost_input = ft.TextField(label="ราคาต้นทุนต่อหน่วย (บาท)", width=380)
            exp_input = ft.TextField(label="วันหมดอายุ (YYYY-MM-DD)", hint_text="เช่น 2026-12-31", width=380)

            def submit_receive(e_sub):
                has_error = False

                q_res = Validator.validate_price(qty_input.value, min_val=0.001, max_val=1000000.0, field_name="จำนวนรับเข้า")
                if not q_res.is_valid:
                    qty_input.error_text = q_res.error
                    has_error = True
                else:
                    qty_input.error_text = None

                c_res = Validator.validate_price(cost_input.value, min_val=0.0, max_val=1000000.0, field_name="ต้นทุนต่อหน่วย")
                if not c_res.is_valid:
                    cost_input.error_text = c_res.error
                    has_error = True
                else:
                    cost_input.error_text = None

                d_res = Validator.validate_date(exp_input.value, required=False, field_name="วันหมดอายุ")
                if not d_res.is_valid:
                    exp_input.error_text = d_res.error
                    has_error = True
                else:
                    exp_input.error_text = None

                if has_error:
                    self._update_ui()
                    return

                db_inner = SessionLocal()
                try:
                    selected_ing_id = int(ing_dropdown.value)
                    lot_num = lot_input.value.strip() if lot_input.value else f"LOT-{datetime.now().strftime('%Y%m%d%H%M')}"
                    exp_date = d_res.value
                    
                    BOMEngine.receive_stock(
                        db_inner,
                        ingredient_id=selected_ing_id,
                        lot_number=lot_num,
                        quantity=q_res.value,
                        unit_cost=c_res.value,
                        expiry_date=exp_date,
                        user_id=self.page_ref.session.store.get("user_id")
                    )
                    self._close_dialog(dialog)
                    self._load_inventory_data()
                except Exception as err:
                    qty_input.error_text = f"เกิดข้อผิดพลาด: {err}"
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text("รับวัตถุดิบเข้าคลัง (Purchase Inbound)", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column(
                        tight=True,
                        spacing=12,
                        controls=[ing_dropdown, lot_input, qty_input, cost_input, exp_input]
                    )
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    create_button("บันทึกรับเข้า", bg_color=ThemeColors.EMERALD, on_click=submit_receive)
                ]
            )
            self._show_dialog(dialog)
        finally:
            db.close()

    def _open_stock_take_dialog(self, e):
        db = SessionLocal()
        try:
            ingredients = db.query(Ingredient).all()
            if not ingredients:
                return

            ing_options = [ft.dropdown.Option(str(i.id), f"{i.name} (สต๊อกปัจจุบัน: {float(i.current_stock):.1f} {i.unit})") for i in ingredients]
            ing_dropdown = ft.Dropdown(label="เลือกวัตถุดิบที่ต้องการนับจริง", options=ing_options, value=str(ingredients[0].id), width=380)
            actual_qty_input = ft.TextField(label="จำนวนสต๊อกที่นับได้จริง (Physical Count)", width=380)
            reason_input = ft.TextField(label="เหตุผลการปรับปรุงยอด (เช่น ปรับสต๊อกปลายเดือน)", value="ตรวจนับสต๊อกจริงปลายรอบ", width=380)

            def submit_stock_take(e_sub):
                q_res = Validator.validate_price(actual_qty_input.value, min_val=0.0, max_val=1000000.0, field_name="จำนวนนับจริง")
                if not q_res.is_valid:
                    actual_qty_input.error_text = q_res.error
                    self._update_ui()
                    return

                db_inner = SessionLocal()
                try:
                    selected_ing_id = int(ing_dropdown.value)
                    user_id = self.page_ref.session.store.get("user_id")
                    
                    BOMEngine.adjust_stock(
                        db_inner,
                        ingredient_id=selected_ing_id,
                        actual_quantity=q_res.value,
                        reason=reason_input.value or "Physical Stock Take",
                        user_id=user_id
                    )
                    self._close_dialog(dialog)
                    self._load_inventory_data()
                except Exception as err:
                    actual_qty_input.error_text = f"เกิดข้อผิดพลาด: {err}"
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text("ตรวจนับสต๊อกจริง (Stock Take Adjustment)", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column(
                        tight=True,
                        spacing=12,
                        controls=[ing_dropdown, actual_qty_input, reason_input]
                    )
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    create_button("ปรับปรุงยอดสต๊อก", bg_color=ThemeColors.AMBER_DARK, on_click=submit_stock_take)
                ]
            )
            self._show_dialog(dialog)
        finally:
            db.close()

    def _open_wastage_dialog(self, e):
        db = SessionLocal()
        try:
            ingredients = db.query(Ingredient).all()
            if not ingredients:
                return

            ing_options = [ft.dropdown.Option(str(i.id), f"{i.name} (คงเหลือ: {float(i.current_stock):.1f} {i.unit})") for i in ingredients]
            ing_dropdown = ft.Dropdown(label="เลือกวัตถุดิบที่เสียหาย/ทิ้ง", options=ing_options, value=str(ingredients[0].id), width=380)
            qty_input = ft.TextField(label="จำนวนที่ตัดของเสีย (ตามหน่วย)", width=380)
            reason_input = ft.TextField(label="สาเหตุของเสีย (เช่น หมดอายุ, ทำตกพื้น, เสียคุณภาพ)", width=380)

            def submit_waste(e_sub):
                q_res = Validator.validate_price(qty_input.value, min_val=0.001, max_val=1000000.0, field_name="จำนวนของเสีย")
                if not q_res.is_valid:
                    qty_input.error_text = q_res.error
                    self._update_ui()
                    return

                db_inner = SessionLocal()
                try:
                    selected_ing_id = int(ing_dropdown.value)
                    user_id = self.page_ref.session.store.get("user_id")
                    
                    BOMEngine.record_wastage(
                        db_inner,
                        ingredient_id=selected_ing_id,
                        quantity=q_res.value,
                        reason=reason_input.value or "ตัดของเสีย",
                        user_id=user_id
                    )
                    self._close_dialog(dialog)
                    self._load_inventory_data()
                except Exception as err:
                    qty_input.error_text = f"เกิดข้อผิดพลาด: {err}"
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text("บันทึกตัดของเสีย (Record Wastage)", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column(
                        tight=True,
                        spacing=12,
                        controls=[ing_dropdown, qty_input, reason_input]
                    )
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    create_button("บันทึกตัดทิ้ง", bg_color=ThemeColors.CRIMSON, on_click=submit_waste)
                ]
            )
            self._show_dialog(dialog)
        finally:
            db.close()

    def _show_dialog(self, dialog: ft.AlertDialog):
        open_dialog(self.page_ref, dialog)

    def _close_dialog(self, dialog: ft.AlertDialog = None):
        close_dialog(self.page_ref, dialog)
        self._update_ui()

    def _update_ui(self):
        try:
            self.update()
        except RuntimeError as err:
            logging.debug("Stock view update skipped: %s", err)
        try:
            self.page_ref.update()
        except RuntimeError as err:
            logging.debug("Stock page update skipped: %s", err)
