import flet as ft
from database.connection import SessionLocal
from database.models import User, UserRole
from services.staff_service import StaffService
from components.theme import ThemeColors, create_card, create_badge, create_button
from components.admin_shell import AdminShell
from utils.validators import Validator
from utils.dialogs import open_dialog, close_dialog

class StaffView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page

        # Staff Table
        self.staff_table = ft.DataTable(
            heading_row_color=ThemeColors.SURFACE_HOVER,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN, size=13),
            data_row_color={"hovered": f"{ThemeColors.SAPPHIRE}11"},
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

        header_actions = [
            create_button(
                "+ เพิ่มพนักงานใหม่",
                icon=ft.Icons.PERSON_ADD_ROUNDED,
                bg_color=ThemeColors.EMERALD,
                on_click=self._open_add_staff_dialog
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
                                    ft.Text("รายชื่อพนักงานและสิทธิ์การเข้าใช้งานทั้งหมด", size=16, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN),
                                    ft.Text("คลิกไอคอนดินสอ เพื่อแก้ไขข้อมูล หรือไอคอนกุญแจ เพื่อรีเซ็ตรหัสผ่าน", size=12, color=ThemeColors.TEXT_MUTED)
                                ]
                            ),
                            ft.ElevatedButton(
                                "รีเฟรชรายชื่อ",
                                icon=ft.Icons.REFRESH_ROUNDED,
                                style=ft.ButtonStyle(
                                    bgcolor=ThemeColors.SURFACE_WHITE,
                                    color=ThemeColors.TEXT_MAIN,
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    side=ft.BorderSide(1, ThemeColors.BORDER_LIGHT)
                                ),
                                on_click=lambda e: self._load_staff_data()
                            )
                        ]
                    ),
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    ft.Container(expand=True, content=ft.ListView([self.staff_table], expand=True))
                ]
            ),
            padding=20
        )

        shell = AdminShell(
            page=page,
            current_route="/admin/staff",
            title="จัดการพนักงาน & สิทธิ์ (Staff & RBAC)",
            subtitle="เพิ่มพนักงานใหม่ กำหนดบทบาทสิทธิ์ 5 ระดับ และรีเซ็ตรหัสผ่าน",
            content_control=table_card,
            header_actions=header_actions
        )

        super().__init__(
            route="/admin/staff",
            controls=[shell],
            padding=0,
            spacing=0
        )

        self._load_staff_data()

    def _load_staff_data(self):
        db = SessionLocal()
        try:
            users = StaffService.get_all_staff(db)
            self.staff_table.rows.clear()
            for u in users:
                status_color = ThemeColors.EMERALD if u.is_active else ThemeColors.CRIMSON
                status_bg = f"{ThemeColors.EMERALD}18" if u.is_active else f"{ThemeColors.CRIMSON}18"
                status_text = "กำลังปฏิบัติงาน" if u.is_active else "ปิดใช้งาน"
                user_id = u.id

                role_str = u.role.value if hasattr(u.role, "value") else str(u.role)
                role_color = ThemeColors.INDIGO
                if role_str == "OWNER":
                    role_color = ThemeColors.AMBER_DARK
                elif role_str == "MANAGER":
                    role_color = ThemeColors.PURPLE
                elif role_str == "CASHIER":
                    role_color = ThemeColors.SAPPHIRE
                elif role_str == "KITCHEN":
                    role_color = ThemeColors.CRIMSON
                elif role_str == "WAITER":
                    role_color = ThemeColors.EMERALD

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(u.id), color=ThemeColors.TEXT_MUTED)),
                        ft.DataCell(ft.Text(u.username, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN)),
                        ft.DataCell(ft.Text(u.name, weight=ft.FontWeight.W_500, color=ThemeColors.TEXT_MAIN)),
                        ft.DataCell(create_badge(role_str, f"{role_color}18", role_color)),
                        ft.DataCell(ft.Text(u.phone or "-", color=ThemeColors.TEXT_MUTED)),
                        ft.DataCell(create_badge(status_text, status_bg, status_color)),
                        ft.DataCell(
                            ft.Row(
                                spacing=4,
                                controls=[
                                    ft.IconButton(
                                        ft.Icons.EDIT_ROUNDED, 
                                        icon_color=ThemeColors.SAPPHIRE, 
                                        tooltip="แก้ไขข้อมูล", 
                                        on_click=lambda e, uid=user_id: self._open_edit_staff_dialog(uid)
                                    ),
                                    ft.IconButton(
                                        ft.Icons.KEY_ROUNDED, 
                                        icon_color=ThemeColors.AMBER_DARK, 
                                        tooltip="รีเซ็ตรหัสผ่าน", 
                                        on_click=lambda e, uid=user_id: self._open_reset_password_dialog(uid)
                                    ),
                                ]
                            )
                        )
                    ]
                )
                self.staff_table.rows.append(row)
            self._update_ui()
        finally:
            db.close()

    def _open_add_staff_dialog(self, e):
        username_input = ft.TextField(label="ชื่อผู้ใช้สำหรับเข้าสู่ระบบ (Username)", width=380)
        password_input = ft.TextField(label="รหัสผ่านเริ่มต้น", password=True, can_reveal_password=True, width=380)
        name_input = ft.TextField(label="ชื่อ-นามสกุลพนักงาน", width=380)
        phone_input = ft.TextField(label="เบอร์โทรศัพท์ (ถ้ามี)", width=380)
        role_dropdown = ft.Dropdown(
            label="ตำแหน่ง (Role)",
            width=380,
            options=[
                ft.dropdown.Option("OWNER", "👑 OWNER (เจ้าของร้าน / ผู้บริหารสูงสุด)"),
                ft.dropdown.Option("MANAGER", "👔 MANAGER (ผู้จัดการร้าน)"),
                ft.dropdown.Option("CASHIER", "💵 CASHIER (แคชเชียร์ / คิดเงิน)"),
                ft.dropdown.Option("WAITER", "🍽️ WAITER (พนักงานเสิร์ฟ / รับออเดอร์)"),
                ft.dropdown.Option("KITCHEN", "👨‍🍳 KITCHEN (เชฟ / ประจำครัว)"),
            ],
            value="WAITER"
        )

        def submit(e_sub):
            has_error = False

            u_res = Validator.validate_username(username_input.value)
            if not u_res.is_valid:
                username_input.error_text = u_res.error
                has_error = True
            else:
                username_input.error_text = None

            pw_res = Validator.validate_password(password_input.value)
            if not pw_res.is_valid:
                password_input.error_text = pw_res.error
                has_error = True
            else:
                password_input.error_text = None

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

            db = SessionLocal()
            try:
                selected_role = UserRole[role_dropdown.value]
                StaffService.create_staff(
                    db,
                    username=u_res.value,
                    password=pw_res.value,
                    name=n_res.value,
                    role=selected_role,
                    phone=ph_res.value
                )
                self._close_dialog(dialog)
                self._load_staff_data()
            except ValueError as val_err:
                username_input.error_text = str(val_err)
                self._update_ui()
            except Exception as err:
                username_input.error_text = f"เกิดข้อผิดพลาด: {err}"
                self._update_ui()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            title=ft.Text("เพิ่มพนักงานใหม่", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=400,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[username_input, password_input, name_input, phone_input, role_dropdown]
                )
            ),
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                create_button("บันทึกพนักงาน", bg_color=ThemeColors.EMERALD, on_click=submit)
            ]
        )
        self._show_dialog(dialog)

    def _open_edit_staff_dialog(self, user_id: int):
        db = SessionLocal()
        try:
            user = StaffService.get_staff_by_id(db, user_id)
            if not user:
                return

            name_input = ft.TextField(label="ชื่อ-นามสกุลพนักงาน", value=user.name, width=380)
            phone_input = ft.TextField(label="เบอร์โทรศัพท์", value=user.phone or "", width=380)
            
            cur_role = user.role.value if hasattr(user.role, "value") else str(user.role)
            role_dropdown = ft.Dropdown(
                label="ตำแหน่ง (Role)",
                width=380,
                options=[
                    ft.dropdown.Option("OWNER", "👑 OWNER (เจ้าของร้าน / ผู้บริหารสูงสุด)"),
                    ft.dropdown.Option("MANAGER", "👔 MANAGER (ผู้จัดการร้าน)"),
                    ft.dropdown.Option("CASHIER", "💵 CASHIER (แคชเชียร์ / คิดเงิน)"),
                    ft.dropdown.Option("WAITER", "🍽️ WAITER (พนักงานเสิร์ฟ / รับออเดอร์)"),
                    ft.dropdown.Option("KITCHEN", "👨‍🍳 KITCHEN (เชฟ / ประจำครัว)"),
                ],
                value=cur_role
            )
            is_active_switch = ft.Switch(label="สถานะปฏิบัติงาน (Active)", value=user.is_active)

            def submit_edit(e_sub):
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
                    selected_role = UserRole[role_dropdown.value]
                    StaffService.update_staff(
                        db_inner,
                        user_id=user_id,
                        name=n_res.value,
                        role=selected_role,
                        phone=ph_res.value,
                        is_active=is_active_switch.value
                    )
                    self._close_dialog(dialog)
                    self._load_staff_data()
                except Exception as err:
                    name_input.error_text = f"เกิดข้อผิดพลาด: {err}"
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text(f"แก้ไขข้อมูลพนักงาน: {user.username}", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column(
                        tight=True,
                        spacing=12,
                        controls=[name_input, phone_input, role_dropdown, is_active_switch]
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

    def _open_reset_password_dialog(self, user_id: int):
        new_password_input = ft.TextField(label="รหัสผ่านใหม่", password=True, can_reveal_password=True, width=380)

        def submit_reset(e_sub):
            pw_res = Validator.validate_password(new_password_input.value)
            if not pw_res.is_valid:
                new_password_input.error_text = pw_res.error
                self._update_ui()
                return

            db = SessionLocal()
            try:
                StaffService.reset_password(db, user_id=user_id, new_password=pw_res.value)
                self._close_dialog(dialog)
                self._show_info_dialog("สำเร็จ", "รีเซ็ตรหัสผ่านเรียบร้อยแล้ว")
            except Exception as err:
                new_password_input.error_text = f"เกิดข้อผิดพลาด: {err}"
                self._update_ui()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            title=ft.Text("รีเซ็ตรหัสผ่านพนักงาน", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=400,
                content=ft.Column(tight=True, spacing=10, controls=[new_password_input])
            ),
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                create_button("ยืนยันเปลี่ยนรหัส", bg_color=ThemeColors.AMBER_DARK, on_click=submit_reset)
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
