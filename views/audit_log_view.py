import json
import flet as ft
from datetime import datetime
from database.connection import SessionLocal
from database.models import AuditLog, User
from components.theme import ThemeColors, create_card, create_badge, create_button
from components.admin_shell import AdminShell
from utils.dialogs import open_dialog, close_dialog

class AuditLogView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page

        # Filter Bar Controls
        self.filter_dropdown = ft.Dropdown(
            label="กรองประเภทการกระทำ",
            width=240,
            value="ALL",
            options=[
                ft.dropdown.Option("ALL", "ทั้งหมด (All Actions)"),
                ft.dropdown.Option("STOCK", "คลังและรับวัตถุดิบ (Stock)"),
                ft.dropdown.Option("WASTAGE", "ของเสีย (Wastage)"),
                ft.dropdown.Option("ADJUSTMENT", "นับสต๊อกจริง (Adjustment)"),
                ft.dropdown.Option("AUTH", "เข้าสู่ระบบ (Auth)"),
                ft.dropdown.Option("STAFF", "จัดการพนักงาน (Staff)"),
            ],
            on_select=lambda e: self._load_logs()
        )

        self.search_input = ft.TextField(
            label="ค้นหาชื่อผู้ใช้ / รายละเอียด...",
            width=300,
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            on_change=lambda e: self._load_logs()
        )

        filter_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row([self.filter_dropdown, self.search_input], spacing=12),
                create_button(
                    "รีเฟรชประวัติ",
                    icon=ft.Icons.REFRESH_ROUNDED,
                    bg_color=ThemeColors.BG_DARK,
                    on_click=lambda e: self._load_logs()
                )
            ]
        )

        # Audit Logs Table
        self.logs_table = ft.DataTable(
            heading_row_color=ThemeColors.SURFACE_HOVER,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN, size=13),
            data_row_color={"hovered": f"{ThemeColors.SAPPHIRE}11"},
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text("วันที่ / เวลา")),
                ft.DataColumn(ft.Text("ผู้ดำเนินการ")),
                ft.DataColumn(ft.Text("การกระทำ (Action)")),
                ft.DataColumn(ft.Text("เป้าหมาย")),
                ft.DataColumn(ft.Text("รายละเอียดย่อ")),
                ft.DataColumn(ft.Text("ดูข้อมูลเต็ม")),
            ],
            rows=[]
        )

        table_card = create_card(
            ft.Column(
                expand=True,
                spacing=16,
                controls=[
                    filter_row,
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    ft.Container(expand=True, content=ft.ListView([self.logs_table], expand=True))
                ]
            ),
            padding=20
        )

        shell = AdminShell(
            page=page,
            current_route="/admin/audit",
            title="บันทึกประวัติระบบ (Audit Logs & Security Trail)",
            subtitle="ตรวจสอบประวัติการทำรายการย้อนหลัง กิจกรรมคลังสินค้า และการเข้าสู่ระบบเพื่อความโปร่งใส",
            content_control=table_card
        )

        super().__init__(
            route="/admin/audit",
            controls=[shell],
            padding=0,
            spacing=0
        )

        self._load_logs()

    def _load_logs(self):
        db = SessionLocal()
        try:
            query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
            
            selected_action = self.filter_dropdown.value
            if selected_action and selected_action != "ALL":
                query = query.filter(AuditLog.action.ilike(f"%{selected_action}%"))

            search_text = (self.search_input.value or "").strip().lower()
            logs = query.limit(100).all()

            self.logs_table.rows.clear()
            for log in logs:
                user_display = log.user.name if log.user else ("System" if not log.user_id else f"User #{log.user_id}")
                dt_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "-"
                
                details_val = log.details_json or ""
                details_short = (details_val[:45] + "...") if len(details_val) > 45 else (details_val or "-")
                target_display = f"{log.target_type} #{log.target_id}" if (log.target_type and log.target_id) else (log.target_type or "-")

                if search_text:
                    match_user = search_text in user_display.lower()
                    match_action = search_text in (log.action or "").lower()
                    match_details = search_text in details_val.lower()
                    if not (match_user or match_action or match_details):
                        continue

                action_color = ThemeColors.SAPPHIRE
                action_str = (log.action or "").upper()
                if "STOCK" in action_str:
                    action_color = ThemeColors.EMERALD
                elif "WASTE" in action_str:
                    action_color = ThemeColors.CRIMSON
                elif "ADJUST" in action_str:
                    action_color = ThemeColors.AMBER_DARK
                elif "AUTH" in action_str or "LOGIN" in action_str:
                    action_color = ThemeColors.INDIGO
                elif "STAFF" in action_str:
                    action_color = ThemeColors.PURPLE

                log_id = log.id
                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(dt_str, size=12, color=ThemeColors.TEXT_MUTED)),
                        ft.DataCell(ft.Text(user_display, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN)),
                        ft.DataCell(create_badge(log.action or "-", f"{action_color}18", action_color)),
                        ft.DataCell(ft.Text(target_display, color=ThemeColors.TEXT_MUTED)),
                        ft.DataCell(ft.Text(details_short, size=12, color=ThemeColors.TEXT_MAIN)),
                        ft.DataCell(
                            ft.IconButton(
                                ft.Icons.VISIBILITY_ROUNDED,
                                icon_color=ThemeColors.SAPPHIRE,
                                tooltip="ดูรายละเอียดทั้งหมด",
                                on_click=lambda e, lid=log_id: self._show_log_details(lid)
                            )
                        )
                    ]
                )
                self.logs_table.rows.append(row)

            self._update_ui()
        finally:
            db.close()

    def _show_log_details(self, log_id: int):
        db = SessionLocal()
        try:
            log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
            if not log:
                return

            user_display = log.user.name if log.user else ("System" if not log.user_id else f"User #{log.user_id}")
            dt_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "-"
            target_display = f"{log.target_type} #{log.target_id}" if (log.target_type and log.target_id) else (log.target_type or "-")

            json_details_str = log.details_json or "ไม่มีรายละเอียดเพิ่มเติม"
            try:
                parsed_json = json.loads(json_details_str)
                json_details_str = json.dumps(parsed_json, indent=2, ensure_ascii=False)
            except Exception:
                pass

            dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.SHIELD_ROUNDED, color=ThemeColors.SAPPHIRE, size=24),
                    ft.Text(f"รายละเอียด Log #{log.id} - {log.action}", weight=ft.FontWeight.BOLD, size=16)
                ]),
                content=ft.Container(
                    width=480,
                    content=ft.Column(
                        tight=True,
                        spacing=12,
                        controls=[
                            ft.Row([
                                ft.Text("วันและเวลา:", weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(dt_str, size=13)
                            ]),
                            ft.Row([
                                ft.Text("ผู้ดำเนินการ:", weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(user_display, size=13, color=ThemeColors.SAPPHIRE, weight=ft.FontWeight.BOLD)
                            ]),
                            ft.Row([
                                ft.Text("เป้าหมาย (Target):", weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(target_display, size=13)
                            ]),
                            ft.Text("ข้อมูลที่บันทึก (Payload / Details):", weight=ft.FontWeight.BOLD, size=13),
                            ft.TextField(
                                value=json_details_str,
                                multiline=True,
                                min_lines=5,
                                max_lines=8,
                                read_only=True,
                                text_size=12,
                                bgcolor=ThemeColors.SURFACE_HOVER,
                                border_color=ThemeColors.BORDER_LIGHT
                            )
                        ]
                    )
                ),
                actions=[
                    ft.TextButton("ปิด", on_click=lambda e: self._close_dialog(dialog))
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
        except Exception:
            pass
        try:
            self.page_ref.update()
        except Exception:
            pass
