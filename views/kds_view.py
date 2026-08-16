import flet as ft
import threading
from database.connection import SessionLocal
from database.models import OrderItem, OrderItemStatus
from utils.navigation import navigate_to

class KdsView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        
        nav_header = ft.Container(
            padding=ft.Padding.symmetric(horizontal=25, vertical=15),
            bgcolor=ft.Colors.ORANGE_900,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=15,
                        controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, on_click=lambda e: navigate_to(self.page_ref, "/tables")),
                            ft.Text("Kitchen Display System (KDS)", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]
                    ),
                    ft.IconButton(ft.Icons.REFRESH, icon_color=ft.Colors.WHITE, on_click=lambda e: self._load_data())
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
        
        self._auto_refresh()
        
    def _auto_refresh(self):
        self._refresh_timer = threading.Timer(15.0, self._auto_refresh)
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
        
        # Action Button
        if item.item_status == OrderItemStatus.PENDING:
            btn = ft.ElevatedButton("เริ่มทำ", style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_500, color=ft.Colors.WHITE), on_click=lambda e, i=item.id: self._update_status(i, OrderItemStatus.COOKING))
        else:
            btn = ft.ElevatedButton("เสร็จแล้ว", style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE), on_click=lambda e, i=item.id: self._update_status(i, OrderItemStatus.SERVED))
            
        return ft.Card(
            elevation=2,
            content=ft.Container(
                padding=12,
                content=ft.Column([
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                        ft.Text(f"{item.menu_item.name} x{item.quantity}", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(table_name, size=14, color=ft.Colors.BLUE_900, weight=ft.FontWeight.BOLD)
                    ]),
                    ft.Text(f"ตัวเลือก:{opt_str}" if opt_str else "ตัวเลือก: -", size=12, color=ft.Colors.GREY_700),
                    btn
                ])
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
