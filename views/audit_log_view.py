import json
import flet as ft
from datetime import datetime
from database.connection import SessionLocal
from database.models import AuditLog, User
from utils.navigation import navigate_to

class AuditLogView(ft.View):
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
                            ft.Text("บันทึกประวัติการใช้งานระบบ (Audit Logs & Security Trail)", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]
                    ),
                    ft.ElevatedButton(
                        "รีเฟรชข้อมูล",
                        icon=ft.Icons.REFRESH,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_800, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=lambda e: self._load_logs()
                    )
                ]
            )
        )

        # Filter Bar
        self.filter_dropdown = ft.Dropdown(
            label="กรองประเภทการกระทำ (Action Filter)",
            width=260,
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
            width=320,
            prefix_icon=ft.Icons.SEARCH,
            on_change=lambda e: self._load_logs()
        )

        filter_bar = ft.Container(
            padding=ft.Padding.symmetric(horizontal=30, vertical=12),
            bgcolor=ft.Colors.WHITE,
            content=ft.Row(
                spacing=15,
                controls=[
                    self.filter_dropdown,
                    self.search_input,
                ]
            )
        )

        # Audit Logs Table
        self.logs_table = ft.DataTable(
            heading_row_color=ft.Colors.GREY_100,
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
            data_row_color={"hovered": ft.Colors.BLUE_50},
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
                    content=ft.Column(
                        expand=True,
                        spacing=12,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("ประวัติการกระทำทั้งหมดในระบบ (บันทึกอัตโนมัติ 100%)", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                                    ft.Text("แสดง 50 รายการล่าสุด", size=12, color=ft.Colors.GREY_600)
                                ]
                            ),
                            ft.Container(expand=True, content=ft.ListView([self.logs_table], expand=True))
                        ]
                    )
                )
            )
        )

        super().__init__(
            route="/admin/audit",
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[nav_header, filter_bar, content_body]
                )
            ],
            bgcolor=bg_color,
            padding=0,
            spacing=0
        )

        self._load_logs()

    def _load_logs(self):
        db = SessionLocal()
        try:
            query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
            
            filter_val = self.filter_dropdown.value
            if filter_val and filter_val != "ALL":
                query = query.filter(AuditLog.action.contains(filter_val))

            logs = query.limit(50).all()
            
            search_text = (self.search_input.value or "").strip().lower()
            
            self.logs_table.rows.clear()
            for log in logs:
                u_name = log.user.name if log.user else f"User #{log.user_id}"
                u_role = f"({log.user.role.value})" if log.user and hasattr(log.user.role, "value") else ""
                user_display = f"{u_name} {u_role}"
                dt_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "-"
                action_badge = self._get_action_badge(log.action)
                target_str = f"{log.target_type or '-'} #{log.target_id or ''}".strip()
                
                details_preview = "-"
                raw_json = log.details_json or "{}"
                try:
                    parsed = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
                    if isinstance(parsed, dict):
                        details_preview = ", ".join([f"{k}: {v}" for k, v in list(parsed.items())[:2]])
                    else:
                        details_preview = str(parsed)[:40]
                except Exception:
                    details_preview = str(raw_json)[:40]

                # Filter by search text
                if search_text:
                    match = (
                        search_text in user_display.lower() or
                        search_text in log.action.lower() or
                        search_text in details_preview.lower() or
                        search_text in target_str.lower()
                    )
                    if not match:
                        continue

                log_id = log.id
                raw_payload = log.details_json or ""
                action_name = log.action

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(dt_str, size=12)),
                        ft.DataCell(ft.Text(user_display, weight=ft.FontWeight.W_500)),
                        ft.DataCell(action_badge),
                        ft.DataCell(ft.Text(target_str, color=ft.Colors.GREY_700)),
                        ft.DataCell(ft.Text(details_preview, size=12, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)),
                        ft.DataCell(
                            ft.IconButton(
                                ft.Icons.VISIBILITY,
                                icon_color=ft.Colors.BLUE_700,
                                tooltip="ดูรายละเอียด JSON เต็ม",
                                on_click=lambda e, a=action_name, u=user_display, t=dt_str, p=raw_payload: self._show_detail_modal(a, u, t, p)
                            )
                        )
                    ]
                )
                self.logs_table.rows.append(row)

            if len(self.logs_table.rows) == 0:
                self.logs_table.rows.append(
                    ft.DataRow(cells=[ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("ไม่พบข้อมูลประวัติ")), ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("-")), ft.DataCell(ft.Text("-"))])
                )

            self._update_ui()
        finally:
            db.close()

    def _get_action_badge(self, action: str):
        color = ft.Colors.BLUE_700
        bg = ft.Colors.BLUE_50
        
        if "WASTAGE" in action:
            color = ft.Colors.RED_700
            bg = ft.Colors.RED_50
        elif "RECEIVE" in action or "PURCHASE" in action:
            color = ft.Colors.GREEN_700
            bg = ft.Colors.GREEN_50
        elif "ADJUSTMENT" in action:
            color = ft.Colors.AMBER_800
            bg = ft.Colors.AMBER_50
        elif "OVERDRAFT" in action:
            color = ft.Colors.DEEP_ORANGE_800
            bg = ft.Colors.DEEP_ORANGE_50
        elif "LOGIN" in action:
            color = ft.Colors.PURPLE_800
            bg = ft.Colors.PURPLE_50

        return ft.Container(
            bgcolor=bg,
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_radius=10,
            content=ft.Text(action, size=11, weight=ft.FontWeight.BOLD, color=color)
        )

    def _show_detail_modal(self, action: str, user: str, timestamp: str, raw_json: str):
        formatted_json = raw_json
        try:
            parsed = json.loads(raw_json)
            formatted_json = json.dumps(parsed, indent=2, ensure_ascii=False)
        except Exception:
            pass

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.SECURITY, color=ft.Colors.BLUE_900),
                ft.Text(f"รายละเอียดประวัติ [{action}]", weight=ft.FontWeight.BOLD, size=16)
            ]),
            content=ft.Container(
                width=500,
                content=ft.Column(
                    spacing=10,
                    tight=True,
                    controls=[
                        ft.Text(f"ผู้ดำเนินการ: {user}", weight=ft.FontWeight.W_500, size=13),
                        ft.Text(f"เวลา: {timestamp}", color=ft.Colors.GREY_600, size=12),
                        ft.Divider(height=1),
                        ft.Text("ข้อมูลที่บันทึก (Details Payload):", weight=ft.FontWeight.BOLD, size=12),
                        ft.TextField(
                            value=formatted_json,
                            multiline=True,
                            min_lines=6,
                            max_lines=12,
                            read_only=True,
                            text_size=12,
                            bgcolor=ft.Colors.GREY_100
                        )
                    ]
                )
            ),
            actions=[
                ft.TextButton("ปิด", on_click=lambda e: self._close_dialog(dialog))
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
