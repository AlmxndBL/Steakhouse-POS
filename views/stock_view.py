import flet as ft
from datetime import datetime
from database.connection import SessionLocal
from database.models import Ingredient, StockLot
from services.bom_engine import BOMEngine
from utils.navigation import navigate_to

class StockView(ft.View):
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
                            ft.Text("บริหารคลังวัตถุดิบ & ตัดสต๊อก BOM", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]
                    ),
                    ft.ElevatedButton(
                        "บันทึกตัดของเสีย (Wastage)",
                        icon=ft.Icons.DELETE_SWEEP,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE),
                        on_click=self._open_wastage_dialog
                    )
                ]
            )
        )

        # Tables
        self.inventory_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("รหัสวัตถุดิบ", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("ชื่อวัตถุดิบ", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("สต๊อกปัจจุบัน", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("ขั้นต่ำแจ้งเตือน", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("ต้นทุนเฉลี่ย/หน่วย", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("สถานะสต๊อก", weight=ft.FontWeight.BOLD)),
            ],
            rows=[]
        )

        self.lots_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("วัตถุดิบ", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("เลข Lot/Batch", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("คงเหลือ", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("วันหมดอายุ (FEFO Priority)", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("สถานะ Lot", weight=ft.FontWeight.BOLD)),
            ],
            rows=[]
        )

        self.inv_container = ft.Container(content=ft.ListView([self.inventory_table], expand=True), expand=True, visible=True)
        self.lots_container = ft.Container(content=ft.ListView([self.lots_table], expand=True), expand=True, visible=False)

        # Toggle Buttons
        self.btn_inv = ft.ElevatedButton("สรุปคลังวัตถุดิบปัจจุบัน", icon=ft.Icons.INVENTORY_2, style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE), on_click=self._show_inv)
        self.btn_lots = ft.ElevatedButton("รายละเอียด Lot / Batch (FIFO/FEFO)", icon=ft.Icons.VIEW_LIST, style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE), on_click=self._show_lots)

        toggle_bar = ft.Container(
            padding=ft.Padding.symmetric(horizontal=25, vertical=15),
            content=ft.Row([self.btn_inv, self.btn_lots], spacing=15)
        )

        content_body = ft.Container(
            expand=True,
            padding=ft.Padding.symmetric(horizontal=25),
            content=ft.Stack([self.inv_container, self.lots_container], expand=True)
        )

        super().__init__(
            route="/stock",
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[nav_header, toggle_bar, ft.Container(expand=True, content=content_body, bgcolor=ft.Colors.BLUE_GREY_50)]
                )
            ],
            padding=0,
            spacing=0
        )

        self._load_inventory_data()

    def _show_inv(self, e):
        self.inv_container.visible = True
        self.lots_container.visible = False
        self.btn_inv.style.bgcolor = ft.Colors.BLUE_700
        self.btn_lots.style.bgcolor = ft.Colors.BLUE_GREY_700
        try:
            self.page_ref.update()
        except Exception:
            pass

    def _show_lots(self, e):
        self.inv_container.visible = False
        self.lots_container.visible = True
        self.btn_inv.style.bgcolor = ft.Colors.BLUE_GREY_700
        self.btn_lots.style.bgcolor = ft.Colors.BLUE_700
        try:
            self.page_ref.update()
        except Exception:
            pass

    def _load_inventory_data(self):
        db = SessionLocal()
        try:
            status_list = BOMEngine.get_inventory_status(db)
            self.inventory_table.rows.clear()
            for item in status_list:
                status_color = ft.Colors.GREEN_700
                status_bg = ft.Colors.GREEN_100
                status_label = "ปกติ (Normal)"

                if item["status"] == "OUT_OF_STOCK":
                    status_color = ft.Colors.RED_700
                    status_bg = ft.Colors.RED_100
                    status_label = "สินค้าหมด!"
                elif item["status"] == "LOW_STOCK":
                    status_color = ft.Colors.AMBER_900
                    status_bg = ft.Colors.AMBER_100
                    status_label = "ใกล้หมด! (Low Stock)"

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item["code"], weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(item["name"])),
                        ft.DataCell(ft.Text(f"{item['current_stock']:,.1f} {item['unit']}", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(f"{item['min_stock_alert']:,.1f} {item['unit']}")),
                        ft.DataCell(ft.Text(f"{item['cost_per_unit']:,.2f} ฿")),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(status_label, size=11, color=status_color, weight=ft.FontWeight.BOLD),
                                bgcolor=status_bg,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                border_radius=6
                            )
                        )
                    ]
                )
                self.inventory_table.rows.append(row)

            # Load Active Lots
            lots = db.query(StockLot).filter(StockLot.remaining_quantity > 0, StockLot.is_depleted == False).order_by(StockLot.expiry_date.asc()).all()
            self.lots_table.rows.clear()
            for lot in lots:
                exp_str = lot.expiry_date.strftime("%Y-%m-%d") if lot.expiry_date else "-"
                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(lot.ingredient.name)),
                        ft.DataCell(ft.Text(lot.lot_number, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(f"{lot.remaining_quantity:,.1f} {lot.ingredient.unit}")),
                        ft.DataCell(ft.Text(exp_str, color=ft.Colors.RED_700 if lot.expiry_date else ft.Colors.BLACK)),
                        ft.DataCell(ft.Text("พร้อมใช้งาน", color=ft.Colors.GREEN_700))
                    ]
                )
                self.lots_table.rows.append(row)

            try:
                self.update()
            except Exception:
                pass
        finally:
            db.close()

    def _open_wastage_dialog(self, e):
        db = SessionLocal()
        try:
            ingredients = db.query(Ingredient).filter(Ingredient.is_active == True).all()
            ing_dropdown = ft.Dropdown(
                label="เลือกวัตถุดิบที่เสีย/ตัดทิ้ง",
                width=350,
                options=[ft.dropdown.Option(str(ing.id), f"{ing.name} ({ing.unit})") for ing in ingredients]
            )
            qty_input = ft.TextField(label="จำนวนวัตถุดิบที่เสีย", width=350, keyboard_type=ft.KeyboardType.NUMBER)
            reason_input = ft.TextField(label="เหตุผล (เช่น เนื้อมีกลิ่นเสีย, ทำหล่น)", width=350)

            def submit_wastage(e_sub):
                if not ing_dropdown.value or not qty_input.value:
                    return
                user_id = self.page_ref.session.store.get("user_id") or 1
                ing_id = int(ing_dropdown.value)
                qty = float(qty_input.value)
                reason = reason_input.value or "ตัดของเสีย"

                db_inner = SessionLocal()
                try:
                    BOMEngine.record_wastage(db_inner, ing_id, qty, reason, user_id)
                    dialog.open = False
                    try:
                        self.page_ref.update()
                    except Exception:
                        pass
                    self._load_inventory_data()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text("บันทึกตัดของเสีย (Record Wastage)"),
                content=ft.Column([ing_dropdown, qty_input, reason_input], height=220),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    ft.ElevatedButton("บันทึกตัดสต๊อก", style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE), on_click=submit_wastage)
                ]
            )
            self.page_ref.dialog = dialog
            dialog.open = True
            try:
                self.page_ref.update()
            except Exception:
                pass
        finally:
            db.close()

    def _close_dialog(self, dialog):
        dialog.open = False
        try:
            self.page_ref.update()
        except Exception:
            pass
