import flet as ft
from database.connection import SessionLocal
from services.menu_service import MenuService
from components.theme import ThemeColors, create_card, create_badge, create_button
from components.admin_shell import AdminShell
from utils.validators import Validator
from utils.dialogs import open_dialog, close_dialog

class AdminMenuView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page

        # Menu Data Table with Food Cost %
        self.menu_table = ft.DataTable(
            heading_row_color=ThemeColors.SURFACE_HOVER,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN, size=13),
            data_row_color={"hovered": f"{ThemeColors.SAPPHIRE}11"},
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text("รหัสเมนู")),
                ft.DataColumn(ft.Text("ชื่อเมนูอาหาร")),
                ft.DataColumn(ft.Text("หมวดหมู่")),
                ft.DataColumn(ft.Text("ราคาขาย")),
                ft.DataColumn(ft.Text("ต้นทุน BOM")),
                ft.DataColumn(ft.Text("Food Cost %")),
                ft.DataColumn(ft.Text("สถานะการขาย")),
                ft.DataColumn(ft.Text("จัดการ")),
            ],
            rows=[]
        )

        header_actions = [
            create_button(
                "+ เพิ่มหมวดหมู่",
                icon=ft.Icons.CATEGORY_ROUNDED,
                bg_color=ThemeColors.BG_SIDEBAR,
                on_click=self._open_add_category_dialog
            ),
            create_button(
                "+ เพิ่มเมนูอาหาร",
                icon=ft.Icons.ADD_ROUNDED,
                bg_color=ThemeColors.EMERALD,
                on_click=self._open_add_menu_dialog
            )
        ]

        table_card = create_card(
            ft.Column(
                expand=True,
                spacing=16,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("รายการอาหารและโครงสร้างต้นทุนวัตถุดิบทั้งหมด", size=16, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN),
                                    ft.Text("คลิกไอคอนดินสอ เพื่อแก้ไขราคา/ชื่อ หรือไอคอนดวงตา เพื่อเปิด/ปิดการขาย", size=12, color=ThemeColors.TEXT_MUTED)
                                ]
                            ),
                            ft.ElevatedButton(
                                "รีเฟรชตาราง",
                                icon=ft.Icons.REFRESH_ROUNDED,
                                style=ft.ButtonStyle(
                                    bgcolor=ThemeColors.SURFACE_WHITE,
                                    color=ThemeColors.TEXT_MAIN,
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    side=ft.BorderSide(1, ThemeColors.BORDER_LIGHT)
                                ),
                                on_click=lambda e: self._load_menu_data()
                            )
                        ]
                    ),
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    ft.Container(expand=True, content=ft.ListView([self.menu_table], expand=True))
                ]
            ),
            padding=20
        )

        shell = AdminShell(
            page=page,
            current_route="/admin/menus",
            title="จัดการเมนูอาหาร & หมวดหมู่ (Menu & Pricing)",
            subtitle="กำหนดราคาขาย คำนวณอัตราส่วนต้นทุนอาหาร (Food Cost %) และจัดการรายการเมนู",
            content_control=table_card,
            header_actions=header_actions
        )

        super().__init__(
            route="/admin/menus",
            controls=[shell],
            padding=0,
            spacing=0
        )

        self._load_menu_data()

    def _load_menu_data(self):
        db = SessionLocal()
        try:
            items = MenuService.get_menu_items(db, active_only=False)
            self.menu_table.rows.clear()
            for item in items:
                status_color = ThemeColors.EMERALD if item.is_active else ThemeColors.CRIMSON
                status_bg = f"{ThemeColors.EMERALD}18" if item.is_active else f"{ThemeColors.CRIMSON}18"
                status_text = "เปิดขาย" if item.is_active else "ปิดขายชั่วคราว"
                item_id = item.id
                cat_name = item.category.name if item.category else "-"
                
                bom_cost = MenuService.get_item_bom_cost(db, item.id)
                price_val = float(item.price)
                cost_pct = (bom_cost / price_val * 100.0) if price_val > 0 else 0.0
                cost_pct_color = ThemeColors.EMERALD if cost_pct <= 35 else (ThemeColors.AMBER_DARK if cost_pct <= 50 else ThemeColors.CRIMSON)

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item.code, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN)),
                        ft.DataCell(ft.Text(item.name, weight=ft.FontWeight.W_500, color=ThemeColors.TEXT_MAIN)),
                        ft.DataCell(create_badge(cat_name, f"{ThemeColors.INDIGO}18", ThemeColors.INDIGO)),
                        ft.DataCell(ft.Text(f"{price_val:,.2f} ฿", weight=ft.FontWeight.BOLD, color=ThemeColors.SAPPHIRE)),
                        ft.DataCell(ft.Text(f"{bom_cost:,.2f} ฿" if bom_cost > 0 else "-", color=ThemeColors.TEXT_MUTED)),
                        ft.DataCell(
                            ft.Text(f"{cost_pct:.1f}%" if bom_cost > 0 else "-", weight=ft.FontWeight.BOLD, color=cost_pct_color)
                        ),
                        ft.DataCell(
                            create_badge(status_text, status_bg, status_color)
                        ),
                        ft.DataCell(
                            ft.Row(
                                spacing=4,
                                controls=[
                                    ft.IconButton(
                                        ft.Icons.EDIT_ROUNDED, 
                                        icon_color=ThemeColors.SAPPHIRE, 
                                        tooltip="แก้ไขเมนู", 
                                        on_click=lambda e, mid=item_id: self._open_edit_menu_dialog(mid)
                                    ),
                                    ft.IconButton(
                                        ft.Icons.VISIBILITY_OFF_ROUNDED if item.is_active else ft.Icons.VISIBILITY_ROUNDED,
                                        icon_color=ThemeColors.AMBER_DARK if item.is_active else ThemeColors.EMERALD,
                                        tooltip="เปิด/ปิดการขาย",
                                        on_click=lambda e, mid=item_id: self._toggle_menu_status(mid)
                                    )
                                ]
                            )
                        )
                    ]
                )
                self.menu_table.rows.append(row)
            self._update_ui()
        finally:
            db.close()

    def _toggle_menu_status(self, item_id: int):
        db = SessionLocal()
        try:
            MenuService.toggle_menu_item_status(db, item_id)
            self._load_menu_data()
        finally:
            db.close()

    def _open_add_menu_dialog(self, e):
        db = SessionLocal()
        try:
            categories = MenuService.get_categories(db)
            if not categories:
                self._show_info_dialog("แจ้งเตือน", "กรุณาเพิ่มหมวดหมู่อาหารก่อนเพิ่มเมนู")
                return

            cat_options = [ft.dropdown.Option(str(c.id), c.name) for c in categories]
            cat_dropdown = ft.Dropdown(label="หมวดหมู่อาหาร", options=cat_options, value=str(categories[0].id), width=380)
            code_input = ft.TextField(label="รหัสเมนู (เช่น STK001)", width=380)
            name_input = ft.TextField(label="ชื่อเมนูอาหาร", width=380)
            price_input = ft.TextField(label="ราคาขาย (บาท)", width=380)
            desc_input = ft.TextField(label="คำอธิบายสั้นๆ (ถ้ามี)", multiline=True, min_lines=2, width=380)

            def submit(e_sub):
                has_error = False

                c_res = Validator.validate_menu_code(code_input.value)
                if not c_res.is_valid:
                    code_input.error_text = c_res.error
                    has_error = True
                else:
                    code_input.error_text = None

                n_res = Validator.validate_required_text(name_input.value, field_name="ชื่อเมนูอาหาร", min_len=2, max_len=100)
                if not n_res.is_valid:
                    name_input.error_text = n_res.error
                    has_error = True
                else:
                    name_input.error_text = None

                p_res = Validator.validate_price(price_input.value, min_val=0.01, max_val=100000.0, field_name="ราคาขาย")
                if not p_res.is_valid:
                    price_input.error_text = p_res.error
                    has_error = True
                else:
                    price_input.error_text = None

                if has_error:
                    self._update_ui()
                    return

                db_inner = SessionLocal()
                try:
                    selected_cat_id = int(cat_dropdown.value) if cat_dropdown.value else categories[0].id
                    MenuService.create_menu_item(
                        db_inner,
                        category_id=selected_cat_id,
                        code=c_res.value,
                        name=n_res.value,
                        price=p_res.value,
                        description=desc_input.value.strip() if desc_input.value else None
                    )
                    self._close_dialog(dialog)
                    self._load_menu_data()
                except Exception as err:
                    code_input.error_text = f"เกิดข้อผิดพลาด: {err}"
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text("เพิ่มเมนูอาหารใหม่", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column(
                        tight=True,
                        spacing=12,
                        controls=[cat_dropdown, code_input, name_input, price_input, desc_input]
                    )
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    create_button("บันทึกเมนู", bg_color=ThemeColors.EMERALD, on_click=submit)
                ]
            )
            self._show_dialog(dialog)
        finally:
            db.close()

    def _open_edit_menu_dialog(self, item_id: int):
        db = SessionLocal()
        try:
            item = MenuService.get_menu_item_by_id(db, item_id)
            if not item:
                return

            categories = MenuService.get_categories(db)
            cat_options = [ft.dropdown.Option(str(c.id), c.name) for c in categories]
            cat_dropdown = ft.Dropdown(label="หมวดหมู่อาหาร", options=cat_options, value=str(item.category_id), width=380)
            name_input = ft.TextField(label="ชื่อเมนูอาหาร", value=item.name, width=380)
            price_input = ft.TextField(label="ราคาขาย (บาท)", value=f"{float(item.price):.2f}", width=380)
            desc_input = ft.TextField(label="คำอธิบาย", value=item.description or "", multiline=True, min_lines=2, width=380)
            is_active_switch = ft.Switch(label="เปิดจำหน่ายเมนูนี้", value=item.is_active)

            def submit_edit(e_sub):
                has_error = False

                n_res = Validator.validate_required_text(name_input.value, field_name="ชื่อเมนูอาหาร", min_len=2, max_len=100)
                if not n_res.is_valid:
                    name_input.error_text = n_res.error
                    has_error = True
                else:
                    name_input.error_text = None

                p_res = Validator.validate_price(price_input.value, min_val=0.01, max_val=100000.0, field_name="ราคาขาย")
                if not p_res.is_valid:
                    price_input.error_text = p_res.error
                    has_error = True
                else:
                    price_input.error_text = None

                if has_error:
                    self._update_ui()
                    return

                db_inner = SessionLocal()
                try:
                    selected_cat_id = int(cat_dropdown.value) if cat_dropdown.value else item.category_id
                    MenuService.update_menu_item(
                        db_inner,
                        item_id=item.id,
                        name=n_res.value,
                        price=p_res.value,
                        category_id=selected_cat_id,
                        description=desc_input.value.strip() if desc_input.value else None,
                        is_active=is_active_switch.value
                    )
                    self._close_dialog(dialog)
                    self._load_menu_data()
                except Exception as err:
                    name_input.error_text = f"เกิดข้อผิดพลาด: {err}"
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text(f"แก้ไขเมนู: {item.code}", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column(
                        tight=True,
                        spacing=12,
                        controls=[cat_dropdown, name_input, price_input, desc_input, is_active_switch]
                    )
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    create_button("บันทึกการแก้ไข", bg_color=ThemeColors.SAPPHIRE, on_click=submit_edit)
                ]
            )
            self._show_dialog(dialog)
        finally:
            db.close()

    def _open_add_category_dialog(self, e):
        name_input = ft.TextField(label="ชื่อหมวดหมู่ (เช่น สเต๊กเนื้อ, สลัด, เครื่องดื่ม)", width=380)

        def submit_cat(e_sub):
            n_res = Validator.validate_required_text(name_input.value, field_name="ชื่อหมวดหมู่", min_len=2, max_len=50)
            if not n_res.is_valid:
                name_input.error_text = n_res.error
                self._update_ui()
                return

            db = SessionLocal()
            try:
                MenuService.create_category(db, name=n_res.value)
                self._close_dialog(dialog)
                self._load_menu_data()
            except Exception as err:
                name_input.error_text = f"เกิดข้อผิดพลาด: {err}"
                self._update_ui()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            title=ft.Text("เพิ่มหมวดหมู่อาหารใหม่", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=400,
                content=ft.Column(tight=True, spacing=10, controls=[name_input])
            ),
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                create_button("บันทึกหมวดหมู่", bg_color=ThemeColors.EMERALD, on_click=submit_cat)
            ]
        )
        self._show_dialog(dialog)

    def _show_info_dialog(self, title: str, msg: str):
        dialog = ft.AlertDialog(
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Text(msg),
            actions=[ft.TextButton("ตกลง", on_click=lambda e: self._close_dialog(dialog))]
        )
        self._show_dialog(dialog)

    def _show_dialog(self, dialog: ft.AlertDialog):
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
