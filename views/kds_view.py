import flet as ft
import threading
from database.connection import SessionLocal
from database.models import OrderItem, OrderItemStatus
from utils.navigation import navigate_to

class KdsView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        
        user_role = page.session.store.get("user_role") or "KITCHEN"
        
        left_controls = []
        if user_role in ["OWNER", "MANAGER"]:
            left_controls.append(
                ft.IconButton(
                    ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.WHITE,
                    tooltip="กลับหน้าผังโต๊ะ",
                    on_click=lambda e: navigate_to(self.page_ref, "/tables")
                )
            )
        else:
            left_controls.append(ft.Icon(ft.Icons.KITCHEN, color=ft.Colors.WHITE, size=28))
            
        left_controls.append(
            ft.Column(
                spacing=2,
                controls=[
                    ft.Text("Kitchen Display System (KDS)", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("ระบบจัดการคิวอาหารในครัว (สำหรับเชฟและพนักงานครัว)", size=12, color=ft.Colors.ORANGE_200)
                ]
            )
        )

        nav_header = ft.Container(
            padding=ft.Padding.symmetric(horizontal=25, vertical=15),
            bgcolor=ft.Colors.ORANGE_900,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(spacing=15, controls=left_controls),
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.IconButton(ft.Icons.REFRESH, tooltip="รีเฟรชออเดอร์", icon_color=ft.Colors.WHITE, on_click=lambda e: self._load_data()),
                            ft.IconButton(ft.Icons.LOGOUT, tooltip="ออกจากระบบ", icon_color=ft.Colors.RED_300, on_click=self._handle_logout)
                        ]
                    )
                ]
            )
        )
        
        self.pending_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        self.cooking_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        
        board = ft.Row(
            expand=True,
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                # Pending Column
                ft.Container(
                    expand=True,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=12,
                    padding=15,
                    content=ft.Column([
                        ft.Text("รอดำเนินการ (PENDING)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                        ft.Divider(),
                        self.pending_col
                    ])
                ),
                # Cooking Column
                ft.Container(
                    expand=True,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=12,
                    padding=15,
                    content=ft.Column([
                        ft.Text("กำลังทำ (COOKING)", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700),
                        ft.Divider(),
                        self.cooking_col
                    ])
                )
            ]
        )
        
        super().__init__(
            route="/kds",
            controls=[
                ft.Column(expand=True, spacing=0, controls=[nav_header, ft.Container(expand=True, padding=20, content=board)])
            ],
            padding=0,
            spacing=0
        )
        
        # Subscribe to Real-time PubSub Channel
        if hasattr(self.page_ref, "pubsub") and self.page_ref.pubsub:
            try:
                self.page_ref.pubsub.subscribe_topic("kds_orders_channel", self._handle_pubsub_order)
            except Exception:
                pass

        self._auto_refresh()
        
    def _handle_pubsub_order(self, topic, message):
        try:
            self._load_data()
        except Exception:
            pass

    def _auto_refresh(self):
        self._refresh_timer = threading.Timer(5.0, self._auto_refresh)
        self._refresh_timer.daemon = True
        self._refresh_timer.start()
        try:
            self._load_data()
        except Exception:
            pass

    def _load_data(self):
        db = SessionLocal()
        try:
            pending_items = db.query(OrderItem).filter(OrderItem.item_status == OrderItemStatus.PENDING).all()
            cooking_items = db.query(OrderItem).filter(OrderItem.item_status == OrderItemStatus.COOKING).all()
            
            self.pending_col.controls.clear()
            for item in pending_items:
                self.pending_col.controls.append(self._create_card(item))
                
            self.cooking_col.controls.clear()
            for item in cooking_items:
                self.cooking_col.controls.append(self._create_card(item))
                
            try:
                self.update()
            except:
                pass
        finally:
            db.close()
            
    def _create_card(self, item: OrderItem):
        opt_str = ""
        if item.options_json:
            import json
            try:
                opts = json.loads(item.options_json)
                opt_str = f" ({opts.get('doneness', '')}, {opts.get('sauce', '')})"
            except:
                pass
                
        table_name = item.order.customer_name if item.order else "Unknown"
        time_str = item.order.created_at.strftime("%H:%M น.") if (item.order and item.order.created_at) else ""
        
        # Action Button
        if item.item_status == OrderItemStatus.PENDING:
            btn = ft.ElevatedButton("เริ่มทำ (Cook)", icon=ft.Icons.PLAY_ARROW, style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_500, color=ft.Colors.WHITE), on_click=lambda e, i=item.id: self._update_status(i, OrderItemStatus.COOKING))
        else:
            btn = ft.ElevatedButton("เสร็จแล้ว (Served)", icon=ft.Icons.CHECK, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE), on_click=lambda e, i=item.id: self._update_status(i, OrderItemStatus.SERVED))
            
        return ft.Card(
            elevation=2,
            content=ft.Container(
                padding=14,
                content=ft.Column([
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                        ft.Text(f"{item.menu_item.name} x{item.quantity}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                        ft.Container(
                            content=ft.Text(table_name, size=13, color=ft.Colors.BLUE_900, weight=ft.FontWeight.BOLD),
                            bgcolor=ft.Colors.BLUE_50,
                            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                            border_radius=6
                        )
                    ]),
                    ft.Text(f"ตัวเลือก: {opt_str}" if opt_str else "ตัวเลือก: ไม่มี", size=12, color=ft.Colors.GREY_700),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(f"{time_str}" if time_str else "", size=11, color=ft.Colors.GREY_500),
                            btn
                        ]
                    )
                ], spacing=8)
            )
        )
        
    def _update_status(self, item_id: int, new_status):
        db = SessionLocal()
        try:
            item = db.query(OrderItem).filter(OrderItem.id == item_id).first()
            if item:
                item.item_status = new_status
                db.commit()
            self._load_data()
        finally:
            db.close()

    def _handle_logout(self, e):
        self.page_ref.session.store.clear()
        navigate_to(self.page_ref, "/login")

