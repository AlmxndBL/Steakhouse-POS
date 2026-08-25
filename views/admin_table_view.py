import flet as ft
from database.connection import SessionLocal
from database.models import TableStatus
from services.table_service import TableService
from components.theme import ThemeColors, create_card, create_badge, create_button
from components.admin_shell import AdminShell
from utils.validators import Validator
from utils.dialogs import open_dialog, close_dialog

class AdminTableView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page

        # Table Data Table
        self.table_table = ft.DataTable(
            heading_row_color=ThemeColors.SURFACE_HOVER,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN, size=13),
            data_row_color={"hovered": f"{ThemeColors.SAPPHIRE}11"},
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

        header_actions = [
            create_button(
                "+ เพิ่มโต๊ะใหม่",
                icon=ft.Icons.ADD_ROUNDED,
                bg_color=ThemeColors.EMERALD,
                on_click=self._open_add_table_dialog
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
                                    ft.Text("ผังโต๊ะทั้งหมดในร้านอาหาร", size=16, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN),
                                    ft.Text("คลิกไอคอนดินสอ เพื่อแก้ไขจำนวนที่นั่ง/โซน หรือไอคอนถังขยะ เพื่อลบโต๊ะ", size=12, color=ThemeColors.TEXT_MUTED)
                                ]
                            ),
                            ft.ElevatedButton(
                                "รีเฟรชผังโต๊ะ",
                                icon=ft.Icons.REFRESH_ROUNDED,
                                style=ft.ButtonStyle(
                                    bgcolor=ThemeColors.SURFACE_WHITE,
                                    color=ThemeColors.TEXT_MAIN,
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    side=ft.BorderSide(1, ThemeColors.BORDER_LIGHT)
                                ),
                                on_click=lambda e: self._load_table_data()
                            )
                        ]
                    ),
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    ft.Container(expand=True, content=ft.ListView([self.table_table], expand=True))
                ]
            ),
            padding=20
        )

        shell = AdminShell(
            page=page,
            current_route="/admin/tables",
            title="ผังโต๊ะ & โซนที่นั่ง (Table & Floor Plan)",
            subtitle="จัดสรรผังโต๊ะอาหาร กำหนดจำนวนที่นั่ง และจัดการโซน Indoor / Terrace / VIP",
            content_control=table_card,
            header_actions=header_actions
        )

        super().__init__(
            route="/admin/tables",
            controls=[shell],
            padding=0,
            spacing=0
        )

        self._load_table_data()

    def _load_table_data(self):
        db = SessionLocal()
        try:
            tables = TableService.get_tables(db)
            self.table_table.rows.clear()
            for t in tables:
                status_color = ThemeColors.EMERALD if t.status == TableStatus.VACANT else ThemeColors.AMBER_DARK
                status_bg = f"{ThemeColors.EMERALD}18" if t.status == TableStatus.VACANT else f"{ThemeColors.AMBER_DARK}18"
                status_text = "โต๊ะว่าง" if t.status == TableStatus.VACANT else "มีลูกค้า"
                table_id = t.id

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(t.table_number, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN)),
                        ft.DataCell(create_badge(t.zone or "Indoor", f"{ThemeColors.SAPPHIRE}18", ThemeColors.SAPPHIRE)),
                        ft.DataCell(ft.Text(f"{t.capacity} ที่นั่ง", weight=ft.FontWeight.W_500, color=ThemeColors.TEXT_MAIN)),
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
                                        tooltip="แก้ไขโต๊ะ", 
                                        on_click=lambda e, tid=table_id: self._open_edit_table_dialog(tid)
                                    ),
                                    ft.IconButton(
                                        ft.Icons.DELETE_OUTLINE_ROUNDED, 
                                        icon_color=ThemeColors.CRIMSON, 
                                        tooltip="ลบโต๊ะ", 
                                        on_click=lambda e, tid=table_id: self._confirm_delete_table(tid)
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

    def _open_add_table_dialog(self, e):
        num_input = ft.TextField(label="หมายเลขโต๊ะ (เช่น T01, VIP1)", width=380)
        zone_dropdown = ft.Dropdown(
            label="โซนที่นั่ง",
            width=380,
            options=[
                ft.dropdown.Option("Indoor", "โซนห้องแอร์ (Indoor)"),
                ft.dropdown.Option("Terrace", "โซนระเบียง (Terrace)"),
                ft.dropdown.Option("VIP Room", "ห้องวีไอพี (VIP Room)"),
                ft.dropdown.Option("Outdoor", "โซนกลางแจ้ง (Outdoor)")
            ],
            value="Indoor"
        )
        cap_input = ft.TextField(label="จำนวนที่นั่ง (เช่น 2, 4, 8)", value="4", width=380)

        def submit(e_sub):
            has_error = False

            t_res = Validator.validate_table_number(num_input.value)
            if not t_res.is_valid:
                num_input.error_text = t_res.error
                has_error = True
            else:
                num_input.error_text = None

            c_res = Validator.validate_integer(cap_input.value, field_name="จำนวนที่นั่ง", min_val=1, max_val=50)
            if not c_res.is_valid:
                cap_input.error_text = c_res.error
                has_error = True
            else:
                cap_input.error_text = None

            if has_error:
                self._update_ui()
                return

            db = SessionLocal()
            try:
                TableService.create_table(
                    db,
                    table_number=t_res.value,
                    capacity=c_res.value,
                    zone=zone_dropdown.value or "Indoor"
                )
                self._close_dialog(dialog)
                self._load_table_data()
            except Exception as err:
                num_input.error_text = f"เกิดข้อผิดพลาด: {err}"
                self._update_ui()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            title=ft.Text("เพิ่มโต๊ะอาหารใหม่", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=400,
                content=ft.Column([num_input, zone_dropdown, cap_input], spacing=12, tight=True)
            ),
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                create_button("บันทึกโต๊ะ", bg_color=ThemeColors.EMERALD, on_click=submit)
            ]
        )
        self._open_dialog(dialog)

    def _open_edit_table_dialog(self, table_id: int):
        db = SessionLocal()
        try:
            table = TableService.get_table_by_id(db, table_id)
            if not table:
                self._show_info_dialog("ข้อผิดพลาด", f"ไม่พบข้อมูลโต๊ะ ID {table_id}")
                return

            num_input = ft.TextField(label="หมายเลขโต๊ะ", value=table.table_number, width=380)
            zone_dropdown = ft.Dropdown(
                label="โซนที่นั่ง",
                width=380,
                options=[
                    ft.dropdown.Option("Indoor", "โซนห้องแอร์ (Indoor)"),
                    ft.dropdown.Option("Terrace", "โซนระเบียง (Terrace)"),
                    ft.dropdown.Option("VIP Room", "ห้องวีไอพี (VIP Room)"),
                    ft.dropdown.Option("Outdoor", "โซนกลางแจ้ง (Outdoor)")
                ],
                value=table.zone or "Indoor"
            )
            cap_input = ft.TextField(label="จำนวนที่นั่ง", value=str(table.capacity), width=380)

            def submit(e_sub):
                has_error = False

                t_res = Validator.validate_table_number(num_input.value)
                if not t_res.is_valid:
                    num_input.error_text = t_res.error
                    has_error = True
                else:
                    num_input.error_text = None

                c_res = Validator.validate_integer(cap_input.value, field_name="จำนวนที่นั่ง", min_val=1, max_val=50)
                if not c_res.is_valid:
                    cap_input.error_text = c_res.error
                    has_error = True
                else:
                    cap_input.error_text = None

                if has_error:
                    self._update_ui()
                    return

                db_inner = SessionLocal()
                try:
                    TableService.update_table(
                        db_inner,
                        table_id=table.id,
                        table_number=t_res.value,
                        capacity=c_res.value,
                        zone=zone_dropdown.value or "Indoor"
                    )
                    self._close_dialog(dialog)
                    self._load_table_data()
                except Exception as err:
                    num_input.error_text = f"เกิดข้อผิดพลาด: {err}"
                    self._update_ui()
                finally:
                    db_inner.close()

            dialog = ft.AlertDialog(
                title=ft.Text(f"แก้ไขโต๊ะ: {table.table_number}", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column([num_input, zone_dropdown, cap_input], spacing=12, tight=True)
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    create_button("บันทึกการแก้ไข", bg_color=ThemeColors.SAPPHIRE, on_click=submit)
                ]
            )
            self._open_dialog(dialog)
        finally:
            db.close()

    def _confirm_delete_table(self, table_id: int):
        def delete(e):
            db = SessionLocal()
            try:
                success = TableService.delete_table(db, table_id)
                self._close_dialog(dialog)
                if not success:
                    self._show_info_dialog("ไม่สามารถลบได้", "โต๊ะนี้มีลูกค้ากำลังใช้งานหรือมีออเดอร์ค้างอยู่")
                else:
                    self._load_table_data()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            title=ft.Text("ยืนยันการลบโต๊ะ", weight=ft.FontWeight.BOLD),
            content=ft.Text("คุณแน่ใจหรือไม่ว่าต้องการลบโต๊ะนี้ออกจากระบบ?"),
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                create_button("ยืนยันลบ", bg_color=ThemeColors.CRIMSON, on_click=delete)
            ]
        )
        self._open_dialog(dialog)

    def _show_info_dialog(self, title: str, msg: str):
        dialog = ft.AlertDialog(
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Text(msg),
            actions=[ft.TextButton("ตกลง", on_click=lambda e: self._close_dialog(dialog))]
        )
        self._open_dialog(dialog)

    def _open_dialog(self, dialog: ft.AlertDialog):
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
