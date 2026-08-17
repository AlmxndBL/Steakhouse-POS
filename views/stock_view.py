import flet as ft
from datetime import datetime, date
from database.connection import SessionLocal
from database.models import Ingredient, StockLot
from services.bom_engine import BOMEngine
from utils.navigation import navigate_to

class StockView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        user_name = page.session.store.get("user_name") or "ผู้ใช้งาน"

        # Premium Colors
        bg_color = ft.Colors.BLUE_GREY_50
        card_bg = ft.Colors.WHITE
        primary_color = ft.Colors.BLUE_800
        text_primary = ft.Colors.BLUE_GREY_900

        # Header Nav
        nav_header = ft.Container(
            padding=ft.Padding.symmetric(horizontal=30, vertical=18),
            bgcolor=primary_color,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.BLACK12),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=15,
                        controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, on_click=lambda e: navigate_to(self.page_ref, "/admin")),
                            ft.Text("📦 ระบบคลังวัตถุดิบ & ตรวจนับสต๊อก (Inventory Management)", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]
                    ),
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.ElevatedButton(
                                "⚖️ ตรวจนับสต๊อกจริง",
                                icon=ft.Icons.FACT_CHECK,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.AMBER_800, 
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                ),
                                on_click=self._open_stock_take_dialog
                            ),
                            ft.ElevatedButton(
                                "📥 รับวัตถุดิบเข้าคลัง",
                                icon=ft.Icons.ADD_SHOPPING_CART,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.GREEN_600, 
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                ),
                                on_click=self._open_receive_dialog
                            ),
                            ft.ElevatedButton(
                                "บันทึกตัดของเสีย",
                                icon=ft.Icons.DELETE_SWEEP,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.RED_600, 
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                ),
                                on_click=self._open_wastage_dialog
                            )
                        ]
                    )
                ]
            )
        )

        # 🚨 Proactive Alert Banner for Low Stock and Expiring Lots
        self.alert_banner_container = ft.Container(visible=False, padding=ft.Padding.symmetric(horizontal=30, vertical=10))

        # Tables
        self.inventory_table = ft.DataTable(
            heading_row_color=ft.Colors.GREY_100,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=text_primary),
            data_row_color={"hovered": ft.Colors.BLUE_50},
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
            heading_row_color=ft.Colors.GREY_100,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=text_primary),
            data_row_color={"hovered": ft.Colors.BLUE_50},
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
        self.btn_inv = ft.ElevatedButton("ภาพรวมคลังสินค้า", style=self._get_active_tab_style(), on_click=self._show_inv)
        self.btn_lots = ft.ElevatedButton("รายละเอียดราย Lot (FIFO)", style=self._get_inactive_tab_style(), on_click=self._show_lots)

        toggle_bar = ft.Container(
            padding=ft.Padding.only(left=30, top=10, right=30, bottom=5),
            content=ft.Row([self.btn_inv, self.btn_lots], spacing=10)
        )

        content_body = ft.Container(
            expand=True,
            padding=ft.Padding.only(left=30, right=30, bottom=30, top=10),
            content=ft.Card(
                elevation=2,
                shape=ft.RoundedRectangleBorder(radius=12),
                content=ft.Container(
                    bgcolor=card_bg,
                    padding=20,
                    expand=True,
                    content=ft.Stack([self.inv_container, self.lots_container], expand=True)
                )
            )
        )

        super().__init__(
            route="/stock",
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[nav_header, self.alert_banner_container, toggle_bar, content_body]
                )
            ],
            bgcolor=bg_color,
            padding=0,
            spacing=0
        )

        self._load_inventory_data()

    def _get_active_tab_style(self):
        return ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_900, 
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=8),
            elevation=1
        )

    def _get_inactive_tab_style(self):
        return ft.ButtonStyle(
            bgcolor=ft.Colors.WHITE, 
            color=ft.Colors.BLUE_GREY_800,
            shape=ft.RoundedRectangleBorder(radius=8),
            elevation=0
        )

    def _show_inv(self, e):
        self.inv_container.visible = True
        self.lots_container.visible = False
        self.btn_inv.style = self._get_active_tab_style()
        self.btn_lots.style = self._get_inactive_tab_style()
        self._update_ui()

    def _show_lots(self, e):
        self.inv_container.visible = False
        self.lots_container.visible = True
        self.btn_inv.style = self._get_inactive_tab_style()
        self.btn_lots.style = self._get_active_tab_style()
        self._update_ui()

    def _load_inventory_data(self):
        db = SessionLocal()
        try:
            status_list = BOMEngine.get_inventory_status(db)
            expiring_lots = BOMEngine.get_expiring_soon_lots(db, days=7)

            # 🚨 1. Build Alert Banner
            low_stock_items = [i for i in status_list if i["status"] in ["LOW_STOCK", "OUT_OF_STOCK"]]
            alerts = []
            if low_stock_items:
                low_names = ", ".join([f"{i['name']} ({i['current_stock']:.1f} {i['unit']})" for i in low_stock_items])
                alerts.append(
                    ft.Container(
                        bgcolor=ft.Colors.RED_50,
                        border=ft.Border.all(1, ft.Colors.RED_300),
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=15, vertical=10),
                        content=ft.Row([
                            ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.RED_700, size=22),
                            ft.Text(f"⚠️ แจ้งเตือนสินค้าใกล้หมด/หมดสต๊อก ({len(low_stock_items)} รายการ): {low_names}", color=ft.Colors.RED_900, weight=ft.FontWeight.W_600, size=13)
                        ])
                    )
                )

            if expiring_lots:
                exp_names = ", ".join([f"{l['ingredient_name']} (Lot: {l['lot_number']}, เหลือ {l['days_left']} วัน)" for l in expiring_lots])
                alerts.append(
                    ft.Container(
                        bgcolor=ft.Colors.AMBER_50,
                        border=ft.Border.all(1, ft.Colors.AMBER_300),
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=15, vertical=10),
                        content=ft.Row([
                            ft.Icon(ft.Icons.TIMER, color=ft.Colors.AMBER_800, size=22),
                            ft.Text(f"⏰ แจ้งเตือนวัตถุดิบใกล้หมดอายุภายใน 7 วัน ({len(expiring_lots)} รายการ): {exp_names}", color=ft.Colors.AMBER_900, weight=ft.FontWeight.W_600, size=13)
                        ])
                    )
                )

            if alerts:
                self.alert_banner_container.content = ft.Column(alerts, spacing=6)
                self.alert_banner_container.visible = True
            else:
                self.alert_banner_container.visible = False

            # 2. Populate Inventory Table
            self.inventory_table.rows.clear()
            for item in status_list:
                status_color = ft.Colors.GREEN_700
                status_bg = ft.Colors.GREEN_50
                status_label = "ปกติ"

                if item["status"] == "OUT_OF_STOCK":
                    status_color = ft.Colors.RED_700
                    status_bg = ft.Colors.RED_50
                    status_label = "สินค้าหมด"
                elif item["status"] == "LOW_STOCK":
                    status_color = ft.Colors.ORANGE_800
                    status_bg = ft.Colors.ORANGE_50
                    status_label = "ใกล้หมด"

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item["code"], weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700)),
                        ft.DataCell(ft.Text(item["name"], weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(f"{item['current_stock']:,.1f} {item['unit']}", weight=ft.FontWeight.W_600, color=status_color)),
                        ft.DataCell(ft.Text(f"{item['min_stock_alert']:,.1f} {item['unit']}", color=ft.Colors.GREY_600)),
                        ft.DataCell(ft.Text(f"{item['cost_per_unit']:,.2f} ฿")),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(status_label, size=12, color=status_color, weight=ft.FontWeight.BOLD),
                                bgcolor=status_bg,
                                padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                                border_radius=12
                            )
                        )
                    ]
                )
                self.inventory_table.rows.append(row)

            # 3. Load Active Lots
            lots = db.query(StockLot).filter(StockLot.remaining_quantity > 0, StockLot.is_depleted == False).order_by(StockLot.expiry_date.asc()).all()
            self.lots_table.rows.clear()
            for lot in lots:
                exp_str = lot.expiry_date.strftime("%Y-%m-%d") if lot.expiry_date else "-"
                is_expiring = False
                if lot.expiry_date:
                    days_left = (lot.expiry_date - date.today()).days
                    if days_left <= 7:
                        is_expiring = True

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(lot.ingredient.name if lot.ingredient else "-", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(lot.lot_number, color=ft.Colors.BLUE_700)),
                        ft.DataCell(ft.Text(f"{float(lot.remaining_quantity):,.1f} {lot.ingredient.unit if lot.ingredient else ''}", weight=ft.FontWeight.W_600)),
                        ft.DataCell(ft.Text(exp_str, color=ft.Colors.RED_700 if is_expiring else ft.Colors.BLACK, weight=ft.FontWeight.BOLD if is_expiring else ft.FontWeight.NORMAL)),
                        ft.DataCell(ft.Text("พร้อมใช้งาน", color=ft.Colors.GREEN_700))
                    ]
                )
                self.lots_table.rows.append(row)

            self._update_ui()
        finally:
            db.close()

    def _open_stock_take_dialog(self, e):
        """Physical Stock Take Dialog (ตรวจนับสต๊อกจริงเทียบระบบ)"""
        db = SessionLocal()
        try:
            ingredients = db.query(Ingredient).filter(Ingredient.is_active == True).all()
            if not ingredients:
                self._show_info_dialog("แจ้งเตือน", "ไม่พบรายการวัตถุดิบในระบบ")
                return

            ing_map = {str(ing.id): ing for ing in ingredients}
            
            ing_dropdown = ft.Dropdown(
                label="เลือกวัตถุดิบที่ต้องการตรวจนับ",
                width=400,
                options=[ft.dropdown.Option(str(ing.id), f"{ing.name} ({ing.unit})") for ing in ingredients],
                value=str(ingredients[0].id)
            )
            
            system_stock_text = ft.Text("สต๊อกในระบบปัจจุบัน: ...", size=13, color=ft.Colors.BLUE_GREY_700, weight=ft.FontWeight.BOLD)
            actual_qty_input = ft.TextField(label="จำนวนที่นับได้จริง (Physical Count)", width=400, keyboard_type=ft.KeyboardType.NUMBER)
            variance_text = ft.Text("ผลต่าง (Variance): 0.00", size=13, color=ft.Colors.BLUE_900, weight=ft.FontWeight.BOLD)
            reason_input = ft.TextField(label="หมายเหตุการปรับปรุง (เช่น นับสต๊อกสิ้นเดือน, ตัดเศษ)", value="ตรวจนับสต๊อกจริงประจำงวด", width=400)

            def update_system_stock_info(e_change):
                selected_id = ing_dropdown.value
                if selected_id and selected_id in ing_map:
                    ing = ing_map[selected_id]
                    db_tmp = SessionLocal()
                    try:
                        lots = db_tmp.query(StockLot).filter(StockLot.ingredient_id == ing.id, StockLot.remaining_quantity > 0, StockLot.is_depleted == False).all()
                        current_sys = sum(float(l.remaining_quantity) for l in lots)
                        system_stock_text.value = f"📦 สต๊อกในระบบปัจจุบัน: {current_sys:,.2f} {ing.unit}"
                        
                        try:
                            act_val = float(actual_qty_input.value or 0)
                            diff = act_val - current_sys
                            diff_color = ft.Colors.GREEN_700 if diff >= 0 else ft.Colors.RED_700
                            sign = "+" if diff > 0 else ""
                            variance_text.value = f"📊 ส่วนต่าง: {sign}{diff:,.2f} {ing.unit}"
                            variance_text.color = diff_color
                        except ValueError:
                            variance_text.value = "ส่วนต่าง: -"
                        
                        self._update_ui()
                    finally:
                        db_tmp.close()

            ing_dropdown.on_select = update_system_stock_info
            actual_qty_input.on_change = update_system_stock_info
            update_system_stock_info(None)

            def submit_stock_take(e_sub):
                if not ing_dropdown.value:
                    ing_dropdown.error_text = "กรุณาเลือกวัตถุดิบ"
                    self._update_ui()
                    return

                raw_act = (actual_qty_input.value or "").strip()
                if not raw_act:
                    actual_qty_input.error_text = "กรุณากรอกจำนวนที่นับได้จริง"
                    self._update_ui()
                    return

                try:
                    act_qty = float(raw_act)
                    if act_qty < 0:
                        actual_qty_input.error_text = "จำนวนต้องไม่ติดลบ"
                        self._update_ui()
                        return
                    actual_qty_input.error_text = None
                except ValueError:
                    actual_qty_input.error_text = "กรุณากรอกตัวเลขที่ถูกต้อง"
                    self._update_ui()
                    return

                user_id = self.page_ref.session.store.get("user_id") or 1
                ing_id = int(ing_dropdown.value)
                reason = reason_input.value.strip() if reason_input.value else "ปรับปรุงยอดนับสต๊อกจริง"

                db_inner = SessionLocal()
                try:
                    res = BOMEngine.adjust_stock(db_inner, ing_id, act_qty, reason, user_id)
                    self._close_dialog(dialog)
                    self._load_inventory_data()
                    self._show_info_dialog("บันทึกการนับสต๊อกสำเร็จ", f"ปรับปรุงยอดวัตถุดิบ '{res['ingredient_name']}' เป็น {res['actual_qty']:,.2f} เรียบร้อยแล้ว (ส่วนต่าง: {res['variance']:+,.2f})")
                except Exception as err:
                    actual_qty_input.error_text = str(err)
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text("⚖️ ตรวจนับสต๊อกจริง (Physical Stock Take)", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=420,
                    content=ft.Column(
                        [ing_dropdown, system_stock_text, actual_qty_input, variance_text, reason_input],
                        spacing=14,
                        tight=True
                    )
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    ft.ElevatedButton("บันทึกปรับยอดสต๊อก", style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_800, color=ft.Colors.WHITE), on_click=submit_stock_take)
                ],
                shape=ft.RoundedRectangleBorder(radius=12)
            )
            self._open_dialog(dialog)
        finally:
            db.close()

    def _open_receive_dialog(self, e):
        db = SessionLocal()
        try:
            ingredients = db.query(Ingredient).filter(Ingredient.is_active == True).all()
            
            ing_dropdown = ft.Dropdown(
                label="เลือกวัตถุดิบ",
                width=400,
                options=[ft.dropdown.Option(str(ing.id), f"{ing.name} ({ing.unit})") for ing in ingredients],
                value=str(ingredients[0].id) if ingredients else None,
                border_radius=8
            )
            lot_input = ft.TextField(label="เลข Lot / Batch (เว้นว่างระบบจะสร้างให้อัตโนมัติ)", width=400, border_radius=8)
            qty_input = ft.TextField(label="จำนวนที่รับเข้า", width=400, keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
            cost_input = ft.TextField(label="ต้นทุนต่อหน่วย (Unit Cost)", width=400, keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
            exp_input = ft.TextField(label="วันหมดอายุ (YYYY-MM-DD เช่น 2026-12-31)", width=400, border_radius=8)

            def submit_receive(e_sub):
                has_error = False

                if not ing_dropdown.value:
                    ing_dropdown.error_text = "กรุณาเลือกวัตถุดิบ"
                    has_error = True
                else:
                    ing_dropdown.error_text = None

                qty = 0.0
                if not qty_input.value or not qty_input.value.strip():
                    qty_input.error_text = "กรุณากรอกจำนวนที่รับเข้า"
                    has_error = True
                else:
                    try:
                        qty = float(qty_input.value.strip())
                        if qty <= 0:
                            qty_input.error_text = "จำนวนต้องมากกว่า 0"
                            has_error = True
                        else:
                            qty_input.error_text = None
                    except ValueError:
                        qty_input.error_text = "กรุณากรอกจำนวนเป็นตัวเลข (เช่น 500 หรือ 1000.5)"
                        has_error = True

                cost = 0.0
                if not cost_input.value or not cost_input.value.strip():
                    cost_input.error_text = "กรุณากรอกราคาต้นทุนต่อหน่วย"
                    has_error = True
                else:
                    try:
                        cost = float(cost_input.value.strip())
                        if cost < 0:
                            cost_input.error_text = "ต้นทุนต้องไม่ติดลบ"
                            has_error = True
                        else:
                            cost_input.error_text = None
                    except ValueError:
                        cost_input.error_text = "กรุณากรอกราคาต้นทุนเป็นตัวเลข (เช่น 1.5 หรือ 250)"
                        has_error = True

                exp_date = None
                if exp_input.value and exp_input.value.strip():
                    try:
                        exp_date = datetime.strptime(exp_input.value.strip(), "%Y-%m-%d").date()
                        exp_input.error_text = None
                    except ValueError:
                        exp_input.error_text = "รูปแบบวันที่ไม่ถูกต้อง กรุณาใช้ YYYY-MM-DD (เช่น 2026-12-31)"
                        has_error = True
                else:
                    exp_input.error_text = None

                if has_error:
                    self._update_ui()
                    return
                
                user_id = self.page_ref.session.store.get("user_id") or 1
                ing_id = int(ing_dropdown.value)
                lot_no = lot_input.value.strip() if lot_input.value and lot_input.value.strip() else f"LOT-{datetime.now().strftime('%Y%m%d%H%M')}"

                db_inner = SessionLocal()
                try:
                    BOMEngine.receive_stock(db_inner, ing_id, lot_no, qty, cost, exp_date, user_id)
                    self._close_dialog(dialog)
                    self._load_inventory_data()
                except Exception as err:
                    qty_input.error_text = f"เกิดข้อผิดพลาด: {str(err)}"
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text("📥 รับวัตถุดิบเข้าคลัง (Purchase In)", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column(
                        [ing_dropdown, lot_input, qty_input, cost_input, exp_input],
                        spacing=14,
                        tight=True
                    )
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    ft.ElevatedButton("บันทึกรับเข้า", style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE), on_click=submit_receive)
                ],
                shape=ft.RoundedRectangleBorder(radius=12)
            )
            self._open_dialog(dialog)
        finally:
            db.close()

    def _open_wastage_dialog(self, e):
        db = SessionLocal()
        try:
            ingredients = db.query(Ingredient).filter(Ingredient.is_active == True).all()
            ing_dropdown = ft.Dropdown(
                label="เลือกวัตถุดิบที่เสีย/ตัดทิ้ง",
                width=400,
                options=[ft.dropdown.Option(str(ing.id), f"{ing.name} ({ing.unit})") for ing in ingredients],
                value=str(ingredients[0].id) if ingredients else None,
                border_radius=8
            )
            qty_input = ft.TextField(label="จำนวนที่เสีย", width=400, keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
            reason_input = ft.TextField(label="เหตุผล (เช่น เนื้อมีกลิ่นเสีย, ทำหล่น)", width=400, border_radius=8)

            def submit_wastage(e_sub):
                has_error = False

                if not ing_dropdown.value:
                    ing_dropdown.error_text = "กรุณาเลือกวัตถุดิบ"
                    has_error = True
                else:
                    ing_dropdown.error_text = None

                qty = 0.0
                if not qty_input.value or not qty_input.value.strip():
                    qty_input.error_text = "กรุณากรอกจำนวนที่เสีย"
                    has_error = True
                else:
                    try:
                        qty = float(qty_input.value.strip())
                        if qty <= 0:
                            qty_input.error_text = "จำนวนต้องมากกว่า 0"
                            has_error = True
                        else:
                            qty_input.error_text = None
                    except ValueError:
                        qty_input.error_text = "กรุณากรอกจำนวนเป็นตัวเลข (เช่น 100 หรือ 250.5)"
                        has_error = True

                if not reason_input.value or not reason_input.value.strip():
                    reason_input.error_text = "กรุณาระบุเหตุผลการตัดของเสีย"
                    has_error = True
                else:
                    reason_input.error_text = None

                if has_error:
                    self._update_ui()
                    return

                user_id = self.page_ref.session.store.get("user_id") or 1
                ing_id = int(ing_dropdown.value)
                reason = reason_input.value.strip()

                db_inner = SessionLocal()
                try:
                    BOMEngine.record_wastage(db_inner, ing_id, qty, reason, user_id)
                    self._close_dialog(dialog)
                    self._load_inventory_data()
                except Exception as err:
                    qty_input.error_text = f"เกิดข้อผิดพลาด: {str(err)}"
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text("🗑️ บันทึกตัดของเสีย (Record Wastage)", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column([ing_dropdown, qty_input, reason_input], spacing=14, tight=True)
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    ft.ElevatedButton("ยืนยันตัดสต๊อก", style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE), on_click=submit_wastage)
                ],
                shape=ft.RoundedRectangleBorder(radius=12)
            )
            self._open_dialog(dialog)
        finally:
            db.close()

    def _show_info_dialog(self, title: str, message: str):
        dialog = ft.AlertDialog(
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Text(message),
            actions=[
                ft.ElevatedButton("ตกลง", on_click=lambda e: self._close_dialog(dialog))
            ]
        )
        self._open_dialog(dialog)

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
