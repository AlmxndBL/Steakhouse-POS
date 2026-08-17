import flet as ft
from database.connection import SessionLocal
from services.menu_service import MenuService
from utils.navigation import navigate_to

class AdminMenuView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        user_name = page.session.store.get("user_name") or "ผู้ดูแลระบบ"

        # Theme Colors
        primary_color = ft.Colors.BLUE_900
        bg_color = ft.Colors.BLUE_GREY_50
        card_bg = ft.Colors.WHITE

        # Header Navigation
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
                            ft.Text("🥩 จัดการเมนูอาหาร, ราคา & ต้นทุน BOM (Menu & Cost Management)", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]
                    ),
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.ElevatedButton(
                                "+ เพิ่มหมวดหมู่",
                                icon=ft.Icons.CATEGORY,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                                on_click=self._open_add_category_dialog
                            ),
                            ft.ElevatedButton(
                                "+ เพิ่มเมนูอาหาร",
                                icon=ft.Icons.RESTAURANT_MENU,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                                on_click=self._open_add_menu_dialog
                            )
                        ]
                    )
                ]
            )
        )

        # Menu Data Table with Food Cost %
        self.menu_table = ft.DataTable(
            heading_row_color=ft.Colors.GREY_100,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
            data_row_color={"hovered": ft.Colors.BLUE_50},
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

        content_body = ft.Container(
            expand=True,
            padding=30,
            content=ft.Card(
                elevation=2,
                shape=ft.RoundedRectangleBorder(radius=12),
                content=ft.Container(
                    bgcolor=card_bg,
                    padding=25,
                    expand=True,
                    content=ft.Column(
                        expand=True,
                        spacing=15,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("รายการอาหารและโครงสร้างต้นทุนวัตถุดิบทั้งหมด", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                                    ft.Text("💡 คลิกไอคอน ✏️ เพื่อแก้ไขราคา/ชื่อ หรือ 👁️ เพื่อเปิด/ปิดการขาย", size=13, color=ft.Colors.GREY_600)
                                ]
                            ),
                            ft.Container(expand=True, content=ft.ListView([self.menu_table], expand=True))
                        ]
                    )
                )
            )
        )

        super().__init__(
            route="/admin/menus",
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[nav_header, content_body]
                )
            ],
            bgcolor=bg_color,
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
                status_color = ft.Colors.GREEN_700 if item.is_active else ft.Colors.RED_700
                status_bg = ft.Colors.GREEN_50 if item.is_active else ft.Colors.RED_50
                status_text = "เปิดขาย" if item.is_active else "ปิดขายชั่วคราว"
                item_id = item.id
                cat_name = item.category.name if item.category else "-"
                
                bom_cost = MenuService.get_item_bom_cost(db, item.id)
                price_val = float(item.price)
                cost_pct = (bom_cost / price_val * 100.0) if price_val > 0 else 0.0
                cost_pct_color = ft.Colors.GREEN_700 if cost_pct <= 35 else (ft.Colors.AMBER_800 if cost_pct <= 50 else ft.Colors.RED_700)

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item.code, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(item.name, weight=ft.FontWeight.W_500)),
                        ft.DataCell(ft.Text(cat_name)),
                        ft.DataCell(ft.Text(f"{price_val:,.2f} ฿", weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_900)),
                        ft.DataCell(ft.Text(f"{bom_cost:,.2f} ฿" if bom_cost > 0 else "-", color=ft.Colors.GREY_700)),
                        ft.DataCell(
                            ft.Text(f"{cost_pct:.1f}%" if bom_cost > 0 else "-", weight=ft.FontWeight.BOLD, color=cost_pct_color)
                        ),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(status_text, size=12, color=status_color, weight=ft.FontWeight.BOLD),
                                bgcolor=status_bg,
                                padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                                border_radius=12
                            )
                        ),
                        ft.DataCell(
                            ft.Row(
                                spacing=5,
                                controls=[
                                    ft.IconButton(
                                        ft.Icons.EDIT, 
                                        icon_color=ft.Colors.BLUE_700, 
                                        tooltip="แก้ไขเมนู", 
                                        on_click=lambda e, mid=item_id: self._open_edit_menu_dialog(mid)
                                    ),
                                    ft.IconButton(
                                        ft.Icons.VISIBILITY_OFF if item.is_active else ft.Icons.VISIBILITY,
                                        icon_color=ft.Colors.ORANGE_800 if item.is_active else ft.Colors.GREEN_700,
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

                if not code_input.value or not code_input.value.strip():
                    code_input.error_text = "กรุณากรอกรหัสเมนู (เช่น STK001)"
                    has_error = True
                else:
                    code_input.error_text = None

                if not name_input.value or not name_input.value.strip():
                    name_input.error_text = "กรุณากรอกชื่อเมนูอาหาร"
                    has_error = True
                else:
                    name_input.error_text = None

                raw_price = (price_input.value or "").strip()
                if not raw_price:
                    price_input.error_text = "กรุณากรอกราคาขาย"
                    has_error = True
                else:
                    try:
                        price = float(raw_price)
                        if price < 0:
                            price_input.error_text = "ราคาต้องไม่ติดลบ"
                            has_error = True
                        else:
                            price_input.error_text = None
                    except ValueError:
                        price_input.error_text = "กรุณากรอกราคาเป็นตัวเลขเท่านั้น (เช่น 250 หรือ 199.50)"
                        has_error = True

                if has_error:
                    self._update_ui()
                    return

                db_inner = SessionLocal()
                try:
                    price = float(raw_price)
                    selected_cat_id = int(cat_dropdown.value) if cat_dropdown.value else categories[0].id
                    MenuService.create_menu_item(
                        db_inner,
                        category_id=selected_cat_id,
                        code=code_input.value.strip(),
                        name=name_input.value.strip(),
                        price=price,
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
                    content=ft.Column([cat_dropdown, code_input, name_input, price_input, desc_input], spacing=12, tight=True)
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    ft.ElevatedButton("บันทึกเมนู", style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE), on_click=submit)
                ]
            )
            self._open_dialog(dialog)
        finally:
            db.close()

    def _open_edit_menu_dialog(self, item_id: int):
        db = SessionLocal()
        try:
            item = MenuService.get_menu_item_by_id(db, item_id)
            if not item:
                self._show_info_dialog("ข้อผิดพลาด", f"ไม่พบเมนูอาหาร ID {item_id}")
                return

            categories = MenuService.get_categories(db)
            cat_options = [ft.dropdown.Option(str(c.id), c.name) for c in categories]
            cat_dropdown = ft.Dropdown(label="หมวดหมู่อาหาร", options=cat_options, value=str(item.category_id), width=380)
            name_input = ft.TextField(label="ชื่อเมนูอาหาร", value=item.name, width=380)
            price_input = ft.TextField(label="ราคาขาย (บาท)", value=str(float(item.price)), width=380)
            desc_input = ft.TextField(label="คำอธิบาย", value=item.description or "", multiline=True, min_lines=2, width=380)
            active_switch = ft.Switch(label="เปิดขายเมนูนี้", value=item.is_active)

            def submit(e_sub):
                has_error = False

                if not name_input.value or not name_input.value.strip():
                    name_input.error_text = "กรุณากรอกชื่อเมนูอาหาร"
                    has_error = True
                else:
                    name_input.error_text = None

                raw_price = (price_input.value or "").strip()
                if not raw_price:
                    price_input.error_text = "กรุณากรอกราคาขาย"
                    has_error = True
                else:
                    try:
                        price = float(raw_price)
                        if price < 0:
                            price_input.error_text = "ราคาต้องไม่ติดลบ"
                            has_error = True
                        else:
                            price_input.error_text = None
                    except ValueError:
                        price_input.error_text = "กรุณากรอกราคาเป็นตัวเลขเท่านั้น (เช่น 250 หรือ 199.50)"
                        has_error = True

                if has_error:
                    self._update_ui()
                    return

                db_inner = SessionLocal()
                try:
                    price = float(raw_price)
                    selected_cat_id = int(cat_dropdown.value) if cat_dropdown.value else item.category_id
                    MenuService.update_menu_item(
                        db_inner,
                        item_id=item_id,
                        name=name_input.value.strip(),
                        price=price,
                        category_id=selected_cat_id,
                        description=desc_input.value.strip() if desc_input.value else None,
                        is_active=active_switch.value
                    )
                    self._close_dialog(dialog)
                    self._load_menu_data()
                except Exception as err:
                    price_input.error_text = f"เกิดข้อผิดพลาด: {err}"
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text(f"แก้ไขเมนู [{item.code}]", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column([cat_dropdown, name_input, price_input, desc_input, active_switch], spacing=12, tight=True)
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    ft.ElevatedButton("บันทึกการแก้ไข", style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE), on_click=submit)
                ]
            )
            self._open_dialog(dialog)
        finally:
            db.close()

    def _open_add_category_dialog(self, e):
        cat_name_input = ft.TextField(label="ชื่อหมวดหมู่ (เช่น สเต๊กเนื้อ, เครื่องดื่ม)", width=380)
        sort_input = ft.TextField(label="ลำดับการแสดงผล (ตัวเลข เช่น 1, 2)", value="1", width=380)

        def submit(e_sub):
            has_error = False

            if not cat_name_input.value or not cat_name_input.value.strip():
                cat_name_input.error_text = "กรุณากรอกชื่อหมวดหมู่"
                has_error = True
            else:
                cat_name_input.error_text = None

            raw_sort = (sort_input.value or "").strip()
            if not raw_sort:
                sort_input.error_text = "กรุณากรอกลำดับ"
                has_error = True
            else:
                try:
                    sort_val = int(raw_sort)
                    sort_input.error_text = None
                except ValueError:
                    sort_input.error_text = "กรุณากรอกเป็นตัวเลขจำนวนเต็มเท่านั้น"
                    has_error = True

            if has_error:
                self._update_ui()
                return

            db = SessionLocal()
            try:
                MenuService.create_category(
                    db,
                    name=cat_name_input.value.strip(),
                    sort_order=int(raw_sort)
                )
                self._close_dialog(dialog)
                self._load_menu_data()
            except Exception as err:
                cat_name_input.error_text = str(err)
                self._update_ui()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            title=ft.Text("เพิ่มหมวดหมู่อาหารใหม่", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=400,
                content=ft.Column([cat_name_input, sort_input], spacing=12, tight=True)
            ),
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("บันทึกหมวดหมู่", style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE), on_click=submit)
            ]
        )
        self._open_dialog(dialog)

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
