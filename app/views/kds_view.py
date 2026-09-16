import json
import logging
import threading
from datetime import datetime, timezone
import flet as ft
from database.connection import SessionLocal
from database.models import Order, OrderItem, OrderItemStatus
from services.order_service import OrderService
from components.pos_header import create_pos_header
from components.theme import ThemeColors, create_card, create_badge, create_button
from utils.navigation import navigate_to

class KdsView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        user_role = page.session.store.get("user_role") or "KITCHEN"

        header_actions = [
            ft.IconButton(
                ft.Icons.REFRESH_ROUNDED,
                icon_color=ThemeColors.TEXT_WHITE,
                tooltip="รีเฟรชออเดอร์",
                on_click=lambda e: self._load_data()
            )
        ]

        back_route = "/tables" if user_role in ["OWNER", "MANAGER"] else None

        pos_header = create_pos_header(
            page=page,
            title="จอคิวครัว (Kitchen Display System - KDS)",
            subtitle="ระบบจัดการคิวอาหารสดแบบ Real-time สำหรับเชฟและพนักงานครัว",
            icon=ft.Icons.KITCHEN_ROUNDED,
            back_route=back_route,
            action_controls=header_actions
        )

        self.pending_col = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
        self.cooking_col = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

        board = ft.Row(
            expand=True,
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                # Pending Column
                ft.Container(
                    expand=True,
                    bgcolor=ThemeColors.SURFACE_WHITE,
                    border_radius=12,
                    border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
                    padding=16,
                    content=ft.Column([
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row([
                                    ft.Container(width=10, height=10, bgcolor=ThemeColors.CRIMSON, border_radius=5),
                                    ft.Text("รอดำเนินการ (PENDING)", size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.CRIMSON_DARK)
                                ]),
                                ft.Text("ออเดอร์ใหม่", size=12, color=ThemeColors.TEXT_MUTED)
                            ]
                        ),
                        ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                        self.pending_col
                    ], expand=True, spacing=10)
                ),
                # Cooking Column
                ft.Container(
                    expand=True,
                    bgcolor=ThemeColors.SURFACE_WHITE,
                    border_radius=12,
                    border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
                    padding=16,
                    content=ft.Column([
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row([
                                    ft.Container(width=10, height=10, bgcolor=ThemeColors.AMBER_DARK, border_radius=5),
                                    ft.Text("กำลังปรุง (COOKING)", size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.AMBER_DARK)
                                ]),
                                ft.Text("อยู่ระหว่างจัดเตรียม", size=12, color=ThemeColors.TEXT_MUTED)
                            ]
                        ),
                        ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                        self.cooking_col
                    ], expand=True, spacing=10)
                )
            ]
        )

        super().__init__(
            route="/kds",
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        pos_header,
                        ft.Container(expand=True, padding=20, bgcolor=ThemeColors.BG_PAGE, content=board)
                    ]
                )
            ],
            padding=0,
            spacing=0
        )

        # Real-time PubSub Channel
        if hasattr(self.page_ref, "pubsub") and self.page_ref.pubsub:
            try:
                self.page_ref.pubsub.subscribe_topic("kds_orders_channel", self._handle_pubsub_order)
            except RuntimeError as err:
                logging.debug("KDS pubsub subscription skipped: %s", err)

        self._auto_refresh()

    def _handle_pubsub_order(self, topic, message):
        try:
            self._load_data()
        except Exception:
            self._show_load_error("ไม่สามารถโหลดคิวครัวได้ กรุณากดรีเฟรชอีกครั้ง")

    def _auto_refresh(self):
        self._refresh_timer = threading.Timer(5.0, self._auto_refresh)
        self._refresh_timer.daemon = True
        self._refresh_timer.start()
        try:
            self._load_data()
        except RuntimeError as err:
            logging.debug("KDS refresh skipped: %s", err)

    def _load_data(self):
        db = SessionLocal()
        try:
            pending_items = db.query(OrderItem).filter(
                OrderItem.item_status == OrderItemStatus.PENDING,
                OrderItem.sent_to_kitchen_at.isnot(None)
            ).join(Order).order_by(Order.created_at.asc(), OrderItem.id.asc()).all()
            cooking_items = db.query(OrderItem).filter(
                OrderItem.item_status == OrderItemStatus.COOKING,
                OrderItem.sent_to_kitchen_at.isnot(None)
            ).join(Order).order_by(Order.created_at.asc(), OrderItem.id.asc()).all()

            self.pending_col.controls.clear()
            for item in pending_items:
                self.pending_col.controls.append(self._create_card(item))

            self.cooking_col.controls.clear()
            for item in cooking_items:
                self.cooking_col.controls.append(self._create_card(item))

            try:
                self.update()
            except RuntimeError:
                self._show_load_error("ไม่สามารถอัปเดตหน้าจอคิวครัวได้")
        finally:
            db.close()

    def _show_load_error(self, message: str):
        """Expose a safe UI error without leaking database details."""
        if hasattr(self, "error_text"):
            self.error_text.value = message
            self.error_text.visible = True
            return
        self.error_text = ft.Text(message, color=ThemeColors.CRIMSON, visible=True)
        if hasattr(self, "pending_col"):
            self.pending_col.controls.insert(0, self.error_text)

    def _create_card(self, item: OrderItem):
        opt_str = ""
        if item.options_json:
            try:
                opts = json.loads(item.options_json)
                opt_str = f" • {opts.get('doneness', '')}, {opts.get('sauce', '')}"
            except (TypeError, ValueError, json.JSONDecodeError) as err:
                logging.debug("KDS options display skipped: %s", err)

        table_name = item.order.customer_name if item.order else "Unknown"
        time_str = item.order.created_at.strftime("%H:%M น.") if (item.order and item.order.created_at) else ""
        elapsed_text = ""
        elapsed_color = ThemeColors.TEXT_MUTED
        if item.order and item.order.created_at:
            created_at = item.order.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            elapsed_minutes = max(0, int((datetime.now(timezone.utc) - created_at).total_seconds() // 60))
            elapsed_text = f"ใช้เวลาแล้ว {elapsed_minutes} นาที"
            if elapsed_minutes >= 20:
                elapsed_color = ThemeColors.CRIMSON
                elapsed_text += " • เกิน SLA"
            elif elapsed_minutes >= 10:
                elapsed_color = ThemeColors.AMBER_DARK

        if item.item_status == OrderItemStatus.PENDING:
            btn = create_button(
                "เริ่มปรุง (Cook)",
                icon=ft.Icons.PLAY_ARROW_ROUNDED,
                bg_color=ThemeColors.AMBER_DARK,
                height=36,
                on_click=lambda e, i=item.id: self._update_status(i, OrderItemStatus.COOKING)
            )
            border_c = ThemeColors.CRIMSON
        else:
            btn = create_button(
                "เสร็จพร้อมเสิร์ฟ (Served)",
                icon=ft.Icons.CHECK_ROUNDED,
                bg_color=ThemeColors.EMERALD,
                height=36,
                on_click=lambda e, i=item.id: self._update_status(i, OrderItemStatus.SERVED)
            )
            border_c = ThemeColors.AMBER_DARK

        card_content = ft.Container(
            padding=14,
            bgcolor=ThemeColors.SURFACE_WHITE,
            border=ft.Border.all(1.5, border_c),
            border_radius=10,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(f"{item.menu_item.name} x{item.quantity}", size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN),
                            create_badge(table_name, f"{ThemeColors.INDIGO}18", ThemeColors.INDIGO)
                        ]
                    ),
                    ft.Text(f"ตัวเลือก:{opt_str}" if opt_str else "ตัวเลือก: สแตนดาร์ด", size=12, color=ThemeColors.AMBER_DARK if opt_str else ThemeColors.TEXT_MUTED, weight=ft.FontWeight.W_500),
                    ft.Text(elapsed_text, size=11, color=elapsed_color, weight=ft.FontWeight.BOLD if elapsed_color != ThemeColors.TEXT_MUTED else ft.FontWeight.NORMAL),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row([
                                ft.Icon(ft.Icons.ACCESS_TIME_ROUNDED, size=14, color=ThemeColors.TEXT_MUTED),
                                ft.Text(time_str, size=11, color=ThemeColors.TEXT_MUTED)
                            ], spacing=4),
                            btn
                        ]
                    )
                ]
            )
        )
        return card_content

    def _update_status(self, item_id: int, new_status):
        db = SessionLocal()
        try:
            OrderService.update_item_status(
                db,
                item_id,
                new_status,
                user_id=self.page_ref.session.store.get("user_id") or 1,
            )
            self._load_data()
        finally:
            db.close()
