import flet as ft
from database.connection import SessionLocal
from database.models import TableStatus
from services.table_service import TableService
from utils.navigation import navigate_to

class AdminTableView(ft.View):
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
                            ft.Text("🪑 จัดการผังโต๊ะอาหาร & โซน (Table Management)", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]
                    ),
                    ft.ElevatedButton(
                        "+ เพิ่มโต๊ะใหม่",
                        icon=ft.Icons.TABLE_RESTAURANT,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=self._open_add_table_dialog
                    )
                ]
            )
        )

        # Table Data Table
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
                                    ft.Text("ผังโต๊ะทั้งหมดในร้านอาหาร", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                                    ft.Text("คลิกไอคอน ✏️ เพื่อแก้ไขจำนวนที่นั่ง/โซน หรือ 🗑️ เพื่อลบโต๊ะ", size=13, color=ft.Colors.GREY_600)
                                ]
                            ),
                            ft.Container(expand=True, content=ft.ListView([self.table_table], expand=True))
                        ]
                    )
                )
            )
        )

        super().__init__(
            route="/admin/tables",
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

        self._load_table_data()

    def _load_table_data(self):
        db = SessionLocal()
        try:
            tables = TableService.get_tables(db)
            self.table_table.rows.clear()
            for t in tables:
                status_color = ft.Colors.GREEN_700 if t.status == TableStatus.VACANT else ft.Colors.ORANGE_800
                status_bg = ft.Colors.GREEN_50 if t.status == TableStatus.VACANT else ft.Colors.ORANGE_50
                status_text = "โต๊ะว่าง" if t.status == TableStatus.VACANT else "มีลูกค้า"
                table_id = t.id

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(t.table_number, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(t.zone)),
                        ft.DataCell(ft.Text(f"{t.capacity} ที่นั่ง", weight=ft.FontWeight.W_500)),
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
                                        tooltip="แก้ไขโต๊ะ", 
                                        on_click=lambda e, tid=table_id: self._open_edit_table_dialog(tid)
                                    ),
                                    ft.IconButton(
                                        ft.Icons.DELETE_OUTLINE, 
                                        icon_color=ft.Colors.RED_700, 
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

            if not num_input.value or not num_input.value.strip():
                num_input.error_text = "กรุณากรอกหมายเลขโต๊ะ (เช่น T01 หรือ VIP1)"
                has_error = True
            else:
                num_input.error_text = None

            raw_cap = (cap_input.value or "").strip()
            if not raw_cap:
                cap_input.error_text = "กรุณากรอกจำนวนที่นั่ง"
                has_error = True
            else:
                try:
                    cap = int(raw_cap)
                    if cap <= 0:
                        cap_input.error_text = "จำนวนที่นั่งต้องมากกว่า 0"
                        has_error = True
                    else:
                        cap_input.error_text = None
                except ValueError:
                    cap_input.error_text = "กรุณากรอกจำนวนที่นั่งเป็นตัวเลขจำนวนเต็มเท่านั้น (เช่น 2 หรือ 4)"
                    has_error = True

            if has_error:
                self._update_ui()
                return

            db = SessionLocal()
            try:
                cap = int(raw_cap)
                TableService.create_table(
                    db,
                    table_number=num_input.value.strip(),
                    capacity=cap,
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
                ft.ElevatedButton("บันทึกโต๊ะ", style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE), on_click=submit)
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

                if not num_input.value or not num_input.value.strip():
                    num_input.error_text = "กรุณากรอกหมายเลขโต๊ะ"
                    has_error = True
                else:
                    num_input.error_text = None

                raw_cap = (cap_input.value or "").strip()
                if not raw_cap:
                    cap_input.error_text = "กรุณากรอกจำนวนที่นั่ง"
                    has_error = True
                else:
                    try:
                        cap = int(raw_cap)
                        if cap <= 0:
                            cap_input.error_text = "จำนวนที่นั่งต้องมากกว่า 0"
                            has_error = True
                        else:
                            cap_input.error_text = None
                    except ValueError:
                        cap_input.error_text = "กรุณากรอกจำนวนที่นั่งเป็นตัวเลขจำนวนเต็มเท่านั้น (เช่น 2 หรือ 4)"
                        has_error = True

                if has_error:
                    self._update_ui()
                    return

                db_inner = SessionLocal()
                try:
                    cap = int(raw_cap)
                    TableService.update_table(
                        db_inner,
                        table_id=table_id,
                        table_number=num_input.value.strip(),
                        capacity=cap,
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
                title=ft.Text(f"แก้ไขโต๊ะ [{table.table_number}]", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=400,
                    content=ft.Column([num_input, zone_dropdown, cap_input], spacing=12, tight=True)
                ),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                    ft.ElevatedButton("บันทึกการแก้ไข", style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE), on_click=submit)
                ]
            )
            self._open_dialog(dialog)
        finally:
            db.close()

    def _confirm_delete_table(self, table_id: int):
        def delete(e_del):
            db = SessionLocal()
            try:
                success = TableService.delete_table(db, table_id)
                self._close_dialog(dialog)
                if success:
                    self._load_table_data()
                else:
                    self._show_info_dialog("ไม่สามารถลบได้", "ไม่พบโต๊ะ หรือมีออเดอร์ค้างอยู่ที่โต๊ะนี้")
            except Exception as err:
                self._show_info_dialog("เกิดข้อผิดพลาด", str(err))
            finally:
                db.close()

        dialog = ft.AlertDialog(
            title=ft.Text("ยืนยันการลบโต๊ะ", weight=ft.FontWeight.BOLD),
            content=ft.Text("คุณแน่ใจหรือไม่ว่าต้องการลบโต๊ะนี้ออกจากระบบ?"),
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("ยืนยันลบ", style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE), on_click=delete)
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
