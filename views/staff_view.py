import flet as ft
from database.connection import SessionLocal
from database.models import User, UserRole
from services.staff_service import StaffService
from utils.navigation import navigate_to
from utils.validators import Validator

class StaffView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        user_name = page.session.store.get("user_name") or "ผู้บริหาร"

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
                        spacing=12,
                        controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, on_click=lambda e: navigate_to(self.page_ref, "/admin")),
                            ft.Text("ระบบจัดการพนักงาน (Staff Management)", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]
                    ),
                    ft.ElevatedButton(
                        "+ เพิ่มพนักงานใหม่",
                        icon=ft.Icons.PERSON_ADD,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN_600,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.Padding.symmetric(horizontal=16, vertical=10)
                        ),
                        on_click=self._open_add_staff_dialog
                    )
                ]
            )
        )

        # Staff Table
        self.staff_table = ft.DataTable(
            heading_row_color=ft.Colors.GREY_100,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
            data_row_color={"hovered": ft.Colors.BLUE_50},
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("ชื่อผู้ใช้ (Username)")),
                ft.DataColumn(ft.Text("ชื่อ-นามสกุล")),
                ft.DataColumn(ft.Text("ตำแหน่ง (Role)")),
                ft.DataColumn(ft.Text("เบอร์โทร")),
                ft.DataColumn(ft.Text("สถานะ")),
                ft.DataColumn(ft.Text("จัดการ")),
            ],
            rows=[]
        )

        body_content = ft.Container(
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
                                    ft.Text("รายชื่อพนักงานทั้งหมดในระบบ", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                                    ft.Text("คลิกไอคอนดินสอ เพื่อแก้ไขข้อมูล หรือไอคอนกุญแจ เพื่อรีเซ็ตรหัสผ่าน", size=13, color=ft.Colors.GREY_600)
                                ]
                            ),
                            ft.Container(expand=True, content=ft.ListView([self.staff_table], expand=True))
                        ]
                    )
                )
            )
        )

        super().__init__(
            route="/admin/staff",
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[nav_header, body_content]
                )
            ],
            bgcolor=bg_color,
            padding=0,
            spacing=0
        )

        self._load_staff_data()

    def _load_staff_data(self):
        db = SessionLocal()
        try:
            staff_list = StaffService.get_all_staff(db, active_only=False)
            self.staff_table.rows.clear()
            for s in staff_list:
                status_color = ft.Colors.GREEN_700 if s.is_active else ft.Colors.RED_700
                status_bg = ft.Colors.GREEN_50 if s.is_active else ft.Colors.RED_50
                status_text = "ปฏิบัติงาน" if s.is_active else "ปิดใช้งาน"
                role_val = s.role.value if hasattr(s.role, "value") else str(s.role)
                user_id = s.id

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(s.id), weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(s.username, color=ft.Colors.BLUE_900, weight=ft.FontWeight.W_600)),
                        ft.DataCell(ft.Text(s.name, weight=ft.FontWeight.W_500)),
                        ft.DataCell(
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                                bgcolor=ft.Colors.BLUE_GREY_100,
                                border_radius=12,
                                content=ft.Text(role_val, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)
                            )
                        ),
                        ft.DataCell(ft.Text(s.phone or "-")),
                        ft.DataCell(
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                                bgcolor=status_bg,
                                border_radius=12,
                                content=ft.Text(status_text, size=12, color=status_color, weight=ft.FontWeight.BOLD)
                            )
                        ),
                        ft.DataCell(
                            ft.Row(
                                spacing=4,
                                controls=[
                                    ft.IconButton(
                                        ft.Icons.EDIT, 
                                        icon_color=ft.Colors.BLUE_700, 
                                        tooltip="แก้ไขข้อมูล", 
                                        on_click=lambda e, uid=user_id: self._open_edit_staff_dialog(uid)
                                    ),
                                    ft.IconButton(
                                        ft.Icons.PASSWORD, 
                                        icon_color=ft.Colors.AMBER_800, 
                                        tooltip="รีเซ็ตรหัสผ่าน", 
                                        on_click=lambda e, uid=user_id: self._open_reset_password_dialog(uid)
                                    ),
                                    ft.IconButton(
                                        ft.Icons.TOGGLE_ON if s.is_active else ft.Icons.TOGGLE_OFF,
                                        icon_color=ft.Colors.GREEN_700 if s.is_active else ft.Colors.GREY_400,
                                        tooltip="เปิด/ปิดการใช้งาน",
                                        on_click=lambda e, uid=user_id: self._toggle_staff_status(uid)
                                    )
                                ]
                            )
                        )
                    ]
                )
                self.staff_table.rows.append(row)
            self._update_ui()
        finally:
            db.close()

    def _toggle_staff_status(self, user_id: int):
        db = SessionLocal()
        try:
            StaffService.toggle_active_status(db, user_id)
            self._load_staff_data()
        except Exception as err:
            self._show_info_dialog("เกิดข้อผิดพลาด", str(err))
        finally:
            db.close()

    def _open_add_staff_dialog(self, e):
        username_input = ft.TextField(label="ชื่อผู้ใช้ (Username เช่น somchai01)", width=380)
        name_input = ft.TextField(label="ชื่อ-นามสกุล (แสดงในบิล)", width=380)
        password_input = ft.TextField(label="รหัสผ่าน (อย่างน้อย 4 ตัวอักษร)", password=True, can_reveal_password=True, width=380)
        phone_input = ft.TextField(label="เบอร์โทรศัพท์ (ถ้ามี)", width=380)
        role_dropdown = ft.Dropdown(
            label="ตำแหน่ง (Role)",
            width=380,
            options=[
                ft.dropdown.Option(UserRole.WAITER.value, "พนักงานเสิร์ฟ (WAITER)"),
                ft.dropdown.Option(UserRole.CASHIER.value, "แคชเชียร์ (CASHIER)"),
                ft.dropdown.Option(UserRole.KITCHEN.value, "พนักงานครัว (KITCHEN)"),
                ft.dropdown.Option(UserRole.MANAGER.value, "ผู้จัดการ (MANAGER)"),
                ft.dropdown.Option(UserRole.OWNER.value, "เจ้าของร้าน (OWNER)"),
            ],
            value=UserRole.WAITER.value
        )

        def submit(e_sub):
            has_error = False

            u_res = Validator.validate_username(username_input.value)
            if not u_res.is_valid:
                username_input.error_text = u_res.error
                has_error = True
            else:
                username_input.error_text = None

            n_res = Validator.validate_required_text(name_input.value, field_name="ชื่อ-นามสกุล", min_len=2, max_len=100)
            if not n_res.is_valid:
                name_input.error_text = n_res.error
                has_error = True
            else:
                name_input.error_text = None

            p_res = Validator.validate_password(password_input.value, min_len=4)
            if not p_res.is_valid:
                password_input.error_text = p_res.error
                has_error = True
            else:
                password_input.error_text = None

            ph_res = Validator.validate_phone(phone_input.value, required=False)
            if not ph_res.is_valid:
                phone_input.error_text = ph_res.error
                has_error = True
            else:
                phone_input.error_text = None

            if has_error:
                self._update_ui()
                return

            db = SessionLocal()
            try:
                selected_role = UserRole(role_dropdown.value)
                StaffService.create_staff(
                    db,
                    username=u_res.value,
                    name=n_res.value,
                    password=password_input.value.strip(),
                    role=selected_role,
                    phone=ph_res.value
                )
                self._close_dialog(dialog)
                self._load_staff_data()
            except Exception as err:
                username_input.error_text = str(err)
                self._update_ui()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            title=ft.Text("เพิ่มพนักงานใหม่", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=400,
                content=ft.Column([username_input, name_input, password_input, role_dropdown, phone_input], spacing=12, tight=True)
            ),
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("บันทึกพนักงาน", style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE), on_click=submit)
            ]
        )
        self._open_dialog(dialog)

    def _open_edit_staff_dialog(self, user_id: int):
        db = SessionLocal()
        try:
            user = StaffService.get_staff_by_id(db, user_id)
            if not user:
                return

            name_input = ft.TextField(label="ชื่อ-นามสกุล", value=user.name, width=380)
            phone_input = ft.TextField(label="เบอร์โทรศัพท์", value=user.phone or "", width=380)
            role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
            role_dropdown = ft.Dropdown(
                label="ตำแหน่ง (Role)",
                width=380,
                options=[
                    ft.dropdown.Option(UserRole.WAITER.value, "พนักงานเสิร์ฟ (WAITER)"),
                    ft.dropdown.Option(UserRole.CASHIER.value, "แคชเชียร์ (CASHIER)"),
                    ft.dropdown.Option(UserRole.KITCHEN.value, "พนักงานครัว (KITCHEN)"),
                    ft.dropdown.Option(UserRole.MANAGER.value, "ผู้จัดการ (MANAGER)"),
                    ft.dropdown.Option(UserRole.OWNER.value, "เจ้าของร้าน (OWNER)"),
                ],
                value=role_val
            )

            def submit(e_sub):
                has_error = False

                n_res = Validator.validate_required_text(name_input.value, field_name="ชื่อ-นามสกุล", min_len=2, max_len=100)
                if not n_res.is_valid:
                    name_input.error_text = n_res.error
                    has_error = True
                else:
                    name_input.error_text = None

                ph_res = Validator.validate_phone(phone_input.value, required=False)
                if not ph_res.is_valid:
                    phone_input.error_text = ph_res.error
                    has_error = True
                else:
                    phone_input.error_text = None

                if has_error:
                    self._update_ui()
                    return

                db_inner = SessionLocal()
                try:
                    selected_role = UserRole(role_dropdown.value)
                    StaffService.update_staff(
                        db_inner,
                        user_id=user_id,
                        name=n_res.value,
                        role=selected_role,
                        phone=ph_res.value,
                        is_active=user.is_active
                    )
                    self._close_dialog(dialog)
                    self._load_staff_data()
                except Exception as err:
                    name_input.error_text = str(err)
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text(f"แก้ไขพนักงาน [{user.username}]", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column([name_input, role_dropdown, phone_input], spacing=12, tight=True)
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    ft.ElevatedButton("บันทึกการแก้ไข", style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE), on_click=submit)
                ]
            )
            self._open_dialog(dialog)
        finally:
            db.close()

    def _open_reset_password_dialog(self, user_id: int):
        db = SessionLocal()
        try:
            user = StaffService.get_staff_by_id(db, user_id)
            if not user:
                return

            new_pw_input = ft.TextField(label="รหัสผ่านใหม่ (อย่างน้อย 4 ตัวอักษร)", password=True, can_reveal_password=True, width=380)

            def submit(e_sub):
                p_res = Validator.validate_password(new_pw_input.value, min_len=4)
                if not p_res.is_valid:
                    new_pw_input.error_text = p_res.error
                    self._update_ui()
                    return

                db_inner = SessionLocal()
                try:
                    StaffService.reset_password(db_inner, user_id, new_pw_input.value.strip())
                    self._close_dialog(dialog)
                    self._show_info_dialog("สำเร็จ", f"รีเซ็ตรหัสผ่านของ {user.username} เรียบร้อยแล้ว")
                except Exception as err:
                    new_pw_input.error_text = str(err)
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text(f"รีเซ็ตรหัสผ่าน [{user.username}]", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column([new_pw_input], spacing=12, tight=True)
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    ft.ElevatedButton("ยืนยันเปลี่ยนรหัส", style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_800, color=ft.Colors.WHITE), on_click=submit)
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
