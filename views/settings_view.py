import flet as ft
from database.connection import SessionLocal
from database.models import MenuItem, Table
from services.menu_service import MenuService
from services.table_service import TableService
from utils.navigation import navigate_to

class SettingsView(ft.View):
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
                            ft.Text("ตั้งค่าระบบหลังบ้าน (Back-office Settings)", size=22, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE)
                        ]
                    ),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=15, vertical=8),
                        bgcolor=ft.Colors.BLUE_800,
                        border_radius=20,
                        content=ft.Text(f"ผู้ดูแล: {user_name}", size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)
                    )
                ]
            )
        )

        # Tab 1: Menu Management Table
        self.menu_table = ft.DataTable(
            heading_row_color=ft.Colors.GREY_100,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
            data_row_color={"hovered": ft.Colors.BLUE_50},
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text("รหัส")),
                ft.DataColumn(ft.Text("ชื่อเมนู")),
                ft.DataColumn(ft.Text("หมวดหมู่")),
                ft.DataColumn(ft.Text("ราคา (บาท)")),
                ft.DataColumn(ft.Text("สถานะการขาย")),
                ft.DataColumn(ft.Text("จัดการ")),
            ],
            rows=[]
        )

        # Tab 2: Table Management Table
        self.table_table = ft.DataTable(
            heading_row_color=ft.Colors.GREY_100,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
            data_row_color={"hovered": ft.Colors.BLUE_50},
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text("หมายเลขโต๊ะ")),
                ft.DataColumn(ft.Text("โซนที่นั่ง")),
                ft.DataColumn(ft.Text("จำนวนที่นั่ง")),
                ft.DataColumn(ft.Text("สถานะโต๊ะ")),
                ft.DataColumn(ft.Text("จัดการ")),
            ],
            rows=[]
        )

        # Containers
        self.menu_container = ft.Container(
            expand=True,
            visible=True,
            content=ft.Column(
                expand=True,
                spacing=15,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        spacing=10,
                        controls=[
                            ft.ElevatedButton("+ เพิ่มหมวดหมู่", icon=ft.Icons.CATEGORY, style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE), on_click=self._open_add_category_dialog),
                            ft.ElevatedButton("+ เพิ่มเมนูอาหาร", icon=ft.Icons.RESTAURANT_MENU, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE), on_click=self._open_add_menu_dialog)
                        ]
                    ),
                    ft.Container(expand=True, content=ft.ListView([self.menu_table], expand=True))
                ]
            )
        )

        self.table_container = ft.Container(
            expand=True,
            visible=False,
            content=ft.Column(
                expand=True,
                spacing=15,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        controls=[
                            ft.ElevatedButton("+ เพิ่มโต๊ะใหม่", icon=ft.Icons.TABLE_RESTAURANT, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE), on_click=self._open_add_table_dialog)
                        ]
                    ),
                    ft.Container(expand=True, content=ft.ListView([self.table_table], expand=True))
                ]
            )
        )

        # Segmented Tabs
        self.btn_tab_menu = ft.ElevatedButton("จัดการเมนูอาหาร & หมวดหมู่", style=self._get_active_tab_style(), on_click=self._show_menu_tab)
        self.btn_tab_table = ft.ElevatedButton("จัดการผังโต๊ะอาหาร", style=self._get_inactive_tab_style(), on_click=self._show_table_tab)

        toggle_bar = ft.Container(
            padding=ft.Padding.only(left=30, top=20, right=30, bottom=10),
            content=ft.Row([self.btn_tab_menu, self.btn_tab_table], spacing=10)
        )

        content_body = ft.Container(
            expand=True,
            padding=30,
            content=ft.Card(
                elevation=2,
                shadow_color=ft.Colors.BLACK26,
                shape=ft.RoundedRectangleBorder(radius=12),
                content=ft.Container(
                    bgcolor=card_bg,
                    padding=25,
                    expand=True,
                    content=ft.Stack([self.menu_container, self.table_container], expand=True)
                )
            )
        )

        super().__init__(
            route="/settings",
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[nav_header, toggle_bar, content_body]
                )
            ],
            bgcolor=bg_color,
            padding=0,
            spacing=0
        )

        self._load_menu_data()
        self._load_table_data()

    def _get_active_tab_style(self):
        return ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_900,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=20),
            elevation=2
        )

    def _get_inactive_tab_style(self):
        return ft.ButtonStyle(
            bgcolor=ft.Colors.WHITE,
            color=ft.Colors.GREY_700,
            shape=ft.RoundedRectangleBorder(radius=20),
            elevation=0
        )

    def _show_menu_tab(self, e):
        self.menu_container.visible = True
        self.table_container.visible = False
        self.btn_tab_menu.style = self._get_active_tab_style()
        self.btn_tab_table.style = self._get_inactive_tab_style()
        self._update_ui()

    def _show_table_tab(self, e):
        self.menu_container.visible = False
        self.table_container.visible = True
        self.btn_tab_menu.style = self._get_inactive_tab_style()
        self.btn_tab_table.style = self._get_active_tab_style()
        self._update_ui()

    # --- Menu Management ---
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

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item.code, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(item.name)),
                        ft.DataCell(ft.Text(cat_name)),
                        ft.DataCell(ft.Text(f"{item.price:,.2f} ฿", weight=ft.FontWeight.W_600, color=ft.Colors.GREEN_700)),
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
                                        tooltip="แก้ไข", 
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
                self._show_info_dialog("กรุณาเพิ่มหมวดหมู่อาหารก่อน", "ยังไม่มีหมวดหมู่อาหารในระบบ กรุณากดปุ่ม '+ เพิ่มหมวดหมู่' ก่อนสร้างเมนู")
                return

            cat_dropdown = ft.Dropdown(
                label="หมวดหมู่อาหาร",
                width=380,
                options=[ft.dropdown.Option(str(c.id), c.name) for c in categories],
                value=str(categories[0].id)
            )
            code_input = ft.TextField(label="รหัสเมนู (เช่น STK009)", width=380)
            name_input = ft.TextField(label="ชื่อเมนูอาหาร", width=380)
            price_input = ft.TextField(label="ราคาขาย (บาท)", width=380, keyboard_type=ft.KeyboardType.NUMBER)
            desc_input = ft.TextField(label="คำอธิบายสั้นๆ (ถ้ามี)", width=380, multiline=True, min_lines=2)

            def submit(e_sub):
                has_error = False
                
                if not code_input.value or not code_input.value.strip():
                    code_input.error_text = "กรุณากรอกรหัสเมนู (เช่น STK009)"
                    has_error = True
                else:
                    code_input.error_text = None

                if not name_input.value or not name_input.value.strip():
                    name_input.error_text = "กรุณากรอกชื่อเมนูอาหาร"
                    has_error = True
                else:
                    name_input.error_text = None

                price = 0.0
                if not price_input.value or not price_input.value.strip():
                    price_input.error_text = "กรุณากรอกราคาขาย"
                    has_error = True
                else:
                    try:
                        price = float(price_input.value.strip())
                        if price <= 0:
                            price_input.error_text = "ราคาต้องมากกว่า 0 บาท"
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
                    MenuService.create_menu_item(
                        db_inner,
                        category_id=int(cat_dropdown.value),
                        code=code_input.value.strip().upper(),
                        name=name_input.value.strip(),
                        price=price,
                        description=desc_input.value.strip() if desc_input.value else None
                    )
                    self._close_dialog(dialog)
                    self._load_menu_data()
                except Exception as err:
                    code_input.error_text = f"ไม่สามารถสร้างเมนูได้: {str(err)}"
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
            item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
            if not item:
                return

            categories = MenuService.get_categories(db)
            cat_dropdown = ft.Dropdown(
                label="หมวดหมู่อาหาร",
                width=380,
                options=[ft.dropdown.Option(str(c.id), c.name) for c in categories],
                value=str(item.category_id)
            )
            name_input = ft.TextField(label="ชื่อเมนูอาหาร", value=item.name, width=380)
            price_input = ft.TextField(label="ราคาขาย (บาท)", value=str(item.price), width=380, keyboard_type=ft.KeyboardType.NUMBER)
            desc_input = ft.TextField(label="คำอธิบาย (ถ้ามี)", value=item.description or "", width=380, multiline=True, min_lines=2)
            is_active_val = item.is_active

            def submit(e_sub):
                has_error = False

                if not name_input.value or not name_input.value.strip():
                    name_input.error_text = "กรุณากรอกชื่อเมนูอาหาร"
                    has_error = True
                else:
                    name_input.error_text = None

                price = 0.0
                if not price_input.value or not price_input.value.strip():
                    price_input.error_text = "กรุณากรอกราคาขาย"
                    has_error = True
                else:
                    try:
                        price = float(price_input.value.strip())
                        if price <= 0:
                            price_input.error_text = "ราคาต้องมากกว่า 0 บาท"
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
                    MenuService.update_menu_item(
                        db_inner,
                        item_id=item_id,
                        name=name_input.value.strip(),
                        price=price,
                        category_id=int(cat_dropdown.value),
                        description=desc_input.value.strip() if desc_input.value else None,
                        is_active=is_active_val
                    )
                    self._close_dialog(dialog)
                    self._load_menu_data()
                except Exception as err:
                    name_input.error_text = f"เกิดข้อผิดพลาด: {str(err)}"
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text(f"แก้ไขเมนู [{item.code}]", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column([cat_dropdown, name_input, price_input, desc_input], spacing=12, tight=True)
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
        cat_name_input = ft.TextField(label="ชื่อหมวดหมู่ใหม่", width=380)
        sort_input = ft.TextField(label="ลำดับการแสดงผล (Sort Order)", value="0", width=380, keyboard_type=ft.KeyboardType.NUMBER)

        def submit(e_sub):
            has_error = False
            if not cat_name_input.value or not cat_name_input.value.strip():
                cat_name_input.error_text = "กรุณากรอกชื่อหมวดหมู่"
                has_error = True
            else:
                cat_name_input.error_text = None

            sort_order = 0
            if sort_input.value and sort_input.value.strip():
                try:
                    sort_order = int(sort_input.value.strip())
                    sort_input.error_text = None
                except ValueError:
                    sort_input.error_text = "กรุณากรอกลำดับเป็นตัวเลขจำนวนเต็ม"
                    has_error = True

            if has_error:
                self._update_ui()
                return

            db = SessionLocal()
            try:
                MenuService.create_category(db, name=cat_name_input.value.strip(), sort_order=sort_order)
                self._close_dialog(dialog)
                self._load_menu_data()
            except Exception as err:
                cat_name_input.error_text = f"เกิดข้อผิดพลาด: {str(err)}"
                self._update_ui()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            title=ft.Text("เพิ่มหมวดหมู่ใหม่", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=400,
                content=ft.Column([cat_name_input, sort_input], spacing=12, tight=True)
            ),
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("บันทึก", style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE), on_click=submit)
            ]
        )
        self._open_dialog(dialog)

    # --- Table Management ---
    def _load_table_data(self):
        db = SessionLocal()
        try:
            tables = TableService.get_tables(db)
            self.table_table.rows.clear()
            for t in tables:
                status_str = getattr(t.status, "value", str(t.status))
                status_label = "ว่าง" if status_str == "VACANT" else ("มีลูกค้า" if status_str == "OCCUPIED" else "รอเก็บ")
                status_color = ft.Colors.GREEN_700 if status_str == "VACANT" else (ft.Colors.AMBER_800 if status_str == "OCCUPIED" else ft.Colors.BLUE_700)
                table_id = t.id

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(t.table_number, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(t.zone)),
                        ft.DataCell(ft.Text(f"{t.capacity} ที่นั่ง")),
                        ft.DataCell(ft.Text(status_label, color=status_color, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(
                            ft.Row(
                                spacing=5,
                                controls=[
                                    ft.IconButton(
                                        ft.Icons.EDIT, 
                                        icon_color=ft.Colors.BLUE_700, 
                                        tooltip="แก้ไขโต๊ะ", 
                                        on_click=lambda e, tid=table_id: self._open_edit_table_dialog(tid)
                                    ),
                                    ft.IconButton(
                                        ft.Icons.DELETE, 
                                        icon_color=ft.Colors.RED_600, 
                                        tooltip="ลบโต๊ะ", 
                                        on_click=lambda e, tid=table_id: self._delete_table(tid)
                                    )
                                ]
                            )
                        )
                    ]
                )
                self.table_table.rows.append(row)
            self._update_ui()
        finally:
            db.close()

    def _delete_table(self, table_id: int):
        db = SessionLocal()
        try:
            TableService.delete_table(db, table_id)
            self._load_table_data()
        except Exception as err:
            self._show_info_dialog("ไม่สามารถลบโต๊ะได้", str(err))
        finally:
            db.close()

    def _open_add_table_dialog(self, e):
        num_input = ft.TextField(label="หมายเลขโต๊ะ (เช่น T09, VIP2)", width=380)
        cap_input = ft.TextField(label="จำนวนที่นั่ง (คน)", value="4", width=380, keyboard_type=ft.KeyboardType.NUMBER)
        zone_dropdown = ft.Dropdown(
            label="โซนที่นั่ง",
            width=380,
            options=[
                ft.dropdown.Option("Indoor"),
                ft.dropdown.Option("Terrace"),
                ft.dropdown.Option("VIP Room"),
                ft.dropdown.Option("Outdoor")
            ],
            value="Indoor"
        )

        def submit(e_sub):
            has_error = False
            if not num_input.value or not num_input.value.strip():
                num_input.error_text = "กรุณากรอกหมายเลขโต๊ะ (เช่น T09)"
                has_error = True
            else:
                num_input.error_text = None

            cap = 4
            if not cap_input.value or not cap_input.value.strip():
                cap_input.error_text = "กรุณากรอกจำนวนที่นั่ง"
                has_error = True
            else:
                try:
                    cap = int(cap_input.value.strip())
                    if cap <= 0:
                        cap_input.error_text = "จำนวนที่นั่งต้องมากกว่า 0"
                        has_error = True
                    else:
                        cap_input.error_text = None
                except ValueError:
                    cap_input.error_text = "กรุณากรอกจำนวนที่นั่งเป็นตัวเลขจำนวนเต็ม"
                    has_error = True

            if has_error:
                self._update_ui()
                return

            db = SessionLocal()
            try:
                TableService.create_table(db, table_number=num_input.value.strip().upper(), capacity=cap, zone=zone_dropdown.value)
                self._close_dialog(dialog)
                self._load_table_data()
            except Exception as err:
                num_input.error_text = f"เกิดข้อผิดพลาด: {str(err)}"
                self._update_ui()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            title=ft.Text("เพิ่มโต๊ะใหม่", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=400,
                content=ft.Column([num_input, cap_input, zone_dropdown], spacing=12, tight=True)
            ),
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("บันทึกโต๊ะ", style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE), on_click=submit)
            ]
        )
        self._open_dialog(dialog)

    def _open_edit_table_dialog(self, table_id: int):
        db = SessionLocal()
        try:
            table = db.query(Table).filter(Table.id == table_id).first()
            if not table:
                return

            num_input = ft.TextField(label="หมายเลขโต๊ะ", value=table.table_number, width=380)
            cap_input = ft.TextField(label="จำนวนที่นั่ง (คน)", value=str(table.capacity), width=380, keyboard_type=ft.KeyboardType.NUMBER)
            zone_dropdown = ft.Dropdown(
                label="โซนที่นั่ง",
                width=380,
                options=[
                    ft.dropdown.Option("Indoor"),
                    ft.dropdown.Option("Terrace"),
                    ft.dropdown.Option("VIP Room"),
                    ft.dropdown.Option("Outdoor")
                ],
                value=table.zone
            )

            def submit(e_sub):
                has_error = False
                if not num_input.value or not num_input.value.strip():
                    num_input.error_text = "กรุณากรอกหมายเลขโต๊ะ"
                    has_error = True
                else:
                    num_input.error_text = None

                cap = 4
                if not cap_input.value or not cap_input.value.strip():
                    cap_input.error_text = "กรุณากรอกจำนวนที่นั่ง"
                    has_error = True
                else:
                    try:
                        cap = int(cap_input.value.strip())
                        if cap <= 0:
                            cap_input.error_text = "จำนวนที่นั่งต้องมากกว่า 0"
                            has_error = True
                        else:
                            cap_input.error_text = None
                    except ValueError:
                        cap_input.error_text = "กรุณากรอกจำนวนที่นั่งเป็นตัวเลขจำนวนเต็ม"
                        has_error = True

                if has_error:
                    self._update_ui()
                    return

                db_inner = SessionLocal()
                try:
                    TableService.update_table(db_inner, table_id=table_id, table_number=num_input.value.strip().upper(), capacity=cap, zone=zone_dropdown.value)
                    self._close_dialog(dialog)
                    self._load_table_data()
                except Exception as err:
                    num_input.error_text = f"เกิดข้อผิดพลาด: {str(err)}"
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text(f"แก้ไขโต๊ะ [{table.table_number}]", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column([num_input, cap_input, zone_dropdown], spacing=12, tight=True)
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    ft.ElevatedButton("บันทึกการแก้ไข", style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE), on_click=submit)
                ]
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
