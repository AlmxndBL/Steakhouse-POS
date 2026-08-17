import json
import flet as ft
from database.connection import SessionLocal
from database.models import Order, Category, MenuItem, ModifierGroup, OrderStatus
from services.order_service import OrderService
from services.menu_service import MenuService
from components.ereceipt_modal import EReceiptModal
from utils.navigation import navigate_to

class PosMainView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        self.order_id = page.session.store.get("active_order_id")
        user_name = page.session.store.get("user_name") or "พนักงาน"

        self.selected_category_id = None
        self._cached_net_amount = 0.0
        self.cart_items_list = ft.ListView(expand=True, spacing=10, padding=10)
        self.subtotal_text = ft.Text("0.00 THB", size=18, weight=ft.FontWeight.BOLD)
        self.sc_text = ft.Text("0.00 THB", size=14)
        self.vat_text = ft.Text("0.00 THB", size=14)
        self.discount_input = ft.TextField(value="0", label="ส่วนลด (บาท)", width=120, keyboard_type=ft.KeyboardType.NUMBER, on_change=self._on_discount_change)
        self.net_total_text = ft.Text("0.00 THB", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
        self.order_title_text = ft.Text("รายการออเดอร์", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900)
        
        self.payment_dropdown = ft.Dropdown(
            label="ช่องทางชำระเงิน",
            width=200,
            value="เงินสด (CASH)",
            options=[
                ft.dropdown.Option("เงินสด (CASH)"),
                ft.dropdown.Option("สแกน QR พร้อมเพย์"),
                ft.dropdown.Option("บัตรเครดิต/เดบิต")
            ]
        )

        # Premium Theme Colors
        primary_color = ft.Colors.BLUE_800
        bg_color = ft.Colors.BLUE_GREY_50
        card_bg = ft.Colors.WHITE

        # Header Navigation
        nav_header = ft.Container(
            padding=ft.Padding.symmetric(horizontal=30, vertical=15),
            bgcolor=primary_color,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.BLACK12),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=15,
                        controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, on_click=lambda e: navigate_to(self.page_ref, "/tables")),
                            ft.Text("รับออเดอร์ & คิดเงิน (POS Checkout)", size=20, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE)
                        ]
                    ),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=15, vertical=8),
                        bgcolor=ft.Colors.BLUE_900,
                        border_radius=20,
                        content=ft.Text(f"พนักงาน: {user_name}", size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)
                    )
                ]
            )
        )

        # Categories & Menu Grid
        self.category_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=10)
        self.menu_grid = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=220,
            child_aspect_ratio=1.0,
            spacing=20,
            run_spacing=20,
            padding=20
        )

        # Left Column: Menu Items
        left_layout = ft.Column(
            col={"sm": 12, "md": 7, "lg": 8},
            spacing=0,
            controls=[
                ft.Container(
                    content=self.category_row, 
                    padding=ft.Padding.symmetric(horizontal=20, vertical=15),
                    bgcolor=card_bg,
                    border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_200))
                ),
                ft.Container(expand=True, content=self.menu_grid, bgcolor=bg_color)
            ]
        )

        # Right Column: Cart & Payment Sidebar
        right_layout = ft.Container(
            col={"sm": 12, "md": 5, "lg": 4},
            bgcolor=card_bg,
            border=ft.Border(left=ft.BorderSide(1, ft.Colors.GREY_200)),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.Colors.BLACK12),
            padding=25,
            content=ft.Column(
                expand=True,
                spacing=20,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            self.order_title_text,
                            ft.Icon(ft.Icons.SHOPPING_CART, color=ft.Colors.BLUE_GREY_400)
                        ]
                    ),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Container(expand=True, content=self.cart_items_list),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Column(
                        spacing=12,
                        controls=[
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("ราคารวม (Subtotal):", size=14, color=ft.Colors.GREY_700), self.subtotal_text]),
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("ส่วนลด (Discount):", size=14, color=ft.Colors.GREY_700), self.discount_input]),
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Service Charge (10%):", size=14, color=ft.Colors.GREY_700), self.sc_text]),
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("VAT (7%):", size=14, color=ft.Colors.GREY_700), self.vat_text]),
                            ft.Divider(height=1, color=ft.Colors.GREY_200),
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("ยอดสุทธิ:", size=20, weight=ft.FontWeight.BOLD), self.net_total_text]),
                            self.payment_dropdown,
                            ft.Row(
                                spacing=15,
                                controls=[
                                    ft.ElevatedButton("หารจ่าย", icon=ft.Icons.CALL_SPLIT, style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_50, color=ft.Colors.INDIGO_700, padding=15, shape=ft.RoundedRectangleBorder(radius=8)), expand=1, on_click=self._handle_split_bill),
                                    ft.ElevatedButton("ชำระเงิน", icon=ft.Icons.PAYMENT, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE, padding=15, shape=ft.RoundedRectangleBorder(radius=8)), expand=2, on_click=self._handle_checkout)
                                ]
                            )
                        ]
                    )
                ]
            )
        )

        main_body = ft.ResponsiveRow(
            expand=True,
            spacing=0,
            controls=[left_layout, right_layout]
        )

        super().__init__(
            route="/pos",
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[nav_header, main_body]
                )
            ],
            padding=0,
            spacing=0
        )

        self._load_categories_and_menu()
        self._load_cart()

    def _load_categories_and_menu(self):
        db = SessionLocal()
        try:
            categories = MenuService.get_categories(db)
            self.category_row.controls.clear()
            
            # All category button
            btn_all = ft.ElevatedButton("ทั้งหมด", 
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
                                        on_click=lambda e: self._filter_menu(None))
            self.category_row.controls.append(btn_all)

            for cat in categories:
                btn = ft.ElevatedButton(cat.name, 
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
                                        on_click=lambda e, cid=cat.id: self._filter_menu(cid))
                self.category_row.controls.append(btn)

            self._filter_menu(None)
        finally:
            db.close()

    def _filter_menu(self, category_id):
        self.selected_category_id = category_id
        db = SessionLocal()
        try:
            items = MenuService.get_menu_items(db, category_id=category_id, active_only=True)

            self.menu_grid.controls.clear()
            for item in items:
                card = ft.Card(
                    elevation=2,
                    shadow_color=ft.Colors.BLACK12,
                    shape=ft.RoundedRectangleBorder(radius=16),
                    content=ft.Container(
                        padding=15,
                        ink=True,
                        border_radius=16,
                        on_click=lambda e, m=item: self._on_menu_item_click(m),
                        content=ft.Column(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(item.name, size=15, weight=ft.FontWeight.W_600, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, color=ft.Colors.BLUE_GREY_900),
                                ft.Text(f"{item.price:,.2f} ฿", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_600),
                                ft.Container(
                                    bgcolor=ft.Colors.BLUE_50,
                                    padding=ft.Padding.symmetric(vertical=8),
                                    border_radius=8,
                                    content=ft.Row([ft.Icon(ft.Icons.ADD, size=16, color=ft.Colors.BLUE_700), ft.Text("เพิ่มลงตะกร้า", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_700)], alignment=ft.MainAxisAlignment.CENTER),
                                    alignment=ft.Alignment.CENTER
                                )
                            ]
                        )
                    )
                )
                self.menu_grid.controls.append(card)
            try:
                self.menu_grid.update()
            except Exception:
                pass
        finally:
            db.close()

    def _on_menu_item_click(self, item: MenuItem):
        # If item is steak, pop up options dialog
        db = SessionLocal()
        try:
            if "สเต๊ก" in item.name:
                mod_groups = db.query(ModifierGroup).all()
                doneness_options = []
                sauce_options = []
                for g in mod_groups:
                    if "ความสุก" in g.name:
                        doneness_options = [opt.name for opt in g.options]
                    elif "ซอส" in g.name:
                        sauce_options = [opt.name for opt in g.options]

                sel_doneness = ft.Dropdown(label="ระดับความสุก", value=doneness_options[1] if len(doneness_options)>1 else "Medium Rare", options=[ft.dropdown.Option(d) for d in doneness_options])
                sel_sauce = ft.Dropdown(label="เลือกซอส", value=sauce_options[0] if len(sauce_options)>0 else "ซอสพริกไทยดำ", options=[ft.dropdown.Option(s) for s in sauce_options])

                def add_with_options(e):
                    options_json = json.dumps({"doneness": sel_doneness.value, "sauce": sel_sauce.value}, ensure_ascii=False)
                    dialog.open = False
                    try:
                        self.page_ref.update()
                    except Exception:
                        pass
                    self._add_to_cart(item.id, options_json=options_json)

                dialog = ft.AlertDialog(
                    title=ft.Text(f"ตัวเลือก: {item.name}"),
                    content=ft.Column([sel_doneness, sel_sauce], height=160),
                    actions=[ft.ElevatedButton("ยืนยันเพิ่มรายการ", on_click=add_with_options)],
                    actions_alignment=ft.MainAxisAlignment.END
                )
                try:
                    self.page_ref.overlay.append(dialog)
                    dialog.open = True
                    self.page_ref.update()
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"Failed to open options dialog: {e}")
            else:
                self._add_to_cart(item.id)
        finally:
            db.close()

    def _add_to_cart(self, menu_item_id: int, options_json: str = None):
        if not self.order_id:
            return
        db = SessionLocal()
        try:
            OrderService.add_item_to_order(db, self.order_id, menu_item_id, qty=1, options_json=options_json)
            self._load_cart()
        finally:
            db.close()

    def _load_cart(self):
        if not self.order_id:
            return
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == self.order_id).first()
            if not order:
                return
            
            self.order_title_text.value = f"ออเดอร์ #{order.order_number} ({order.customer_name})"
            self.cart_items_list.controls.clear()

            for item in order.items:
                opt_str = ""
                if item.options_json:
                    try:
                        opts = json.loads(item.options_json)
                        opt_str = f" ({opts.get('doneness', '')}, {opts.get('sauce', '')})"
                    except:
                        pass

                row = ft.Container(
                    padding=8,
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=8,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                expand=True,
                                controls=[
                                    ft.Text(f"{item.menu_item.name}{opt_str}", size=13, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{item.price_per_unit:,.2f} x {item.quantity} = {item.price_per_unit * item.quantity:,.2f} ฿", size=12, color=ft.Colors.GREY_700)
                                ]
                            ),
                            ft.Row(
                                spacing=0,
                                controls=[
                                    ft.IconButton(ft.Icons.REMOVE, icon_size=16, icon_color=ft.Colors.BLUE_GREY_700, on_click=lambda e, iid=item.id: self._update_item_qty(iid, -1)),
                                    ft.Text(str(item.quantity), size=14, weight=ft.FontWeight.BOLD),
                                    ft.IconButton(ft.Icons.ADD, icon_size=16, icon_color=ft.Colors.BLUE_GREY_700, on_click=lambda e, iid=item.id: self._update_item_qty(iid, 1)),
                                    ft.IconButton(ft.Icons.DELETE_OUTLINED, icon_color=ft.Colors.RED_400, on_click=lambda e, iid=item.id: self._remove_item(iid))
                                ]
                            )
                        ]
                    )
                )
                self.cart_items_list.controls.append(row)

            self.subtotal_text.value = f"{order.subtotal:,.2f} THB"
            self.sc_text.value = f"{getattr(order, 'service_charge_amount', 0.0):,.2f} THB"
            self.vat_text.value = f"{order.vat_amount:,.2f} THB"
            self.net_total_text.value = f"{order.net_amount:,.2f} THB"
            self._cached_net_amount = float(order.net_amount)
            try:
                self.update()
            except Exception:
                pass
        finally:
            db.close()

    def _remove_item(self, order_item_id: int):
        db = SessionLocal()
        try:
            OrderService.remove_item_from_order(db, order_item_id)
            self._load_cart()
        finally:
            db.close()

    def _update_item_qty(self, order_item_id: int, delta: int):
        db = SessionLocal()
        try:
            OrderService.update_item_quantity(db, order_item_id, delta)
            self._load_cart()
        finally:
            db.close()

    def _on_discount_change(self, e):
        self._calculate_totals()

    def _handle_split_bill(self, e):
        if not self.order_id:
            return
        
        persons_input = ft.TextField(label="จำนวนคน (เช่น 2, 3, 4)", value="2", keyboard_type=ft.KeyboardType.NUMBER, width=160)
        net_text = ft.Text(f"ยอดสุทธิรวมทั้งบิล: {self._cached_net_amount:,.2f} ฿", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)
        per_person_text = ft.Text("...", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
        breakdown_col = ft.Column(spacing=6)

        def set_persons(n: int):
            persons_input.value = str(n)
            calculate_split(None)

        chips_row = ft.Row([
            ft.ActionChip(label=ft.Text("2 คน"), on_click=lambda e: set_persons(2)),
            ft.ActionChip(label=ft.Text("3 คน"), on_click=lambda e: set_persons(3)),
            ft.ActionChip(label=ft.Text("4 คน"), on_click=lambda e: set_persons(4)),
            ft.ActionChip(label=ft.Text("5 คน"), on_click=lambda e: set_persons(5)),
        ], spacing=8)
        
        def calculate_split(e_calc):
            try:
                raw_p = (persons_input.value or "1").strip()
                p = int(raw_p) if raw_p else 1
                if p <= 0:
                    p = 1
                net = self._cached_net_amount
                per_head = net / p
                per_person_text.value = f"ตกคนละ: {per_head:,.2f} ฿"

                breakdown_col.controls.clear()
                for i in range(1, p + 1):
                    breakdown_col.controls.append(
                        ft.Container(
                            bgcolor=ft.Colors.GREY_50,
                            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                            border_radius=6,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(f"คนที่ #{i}", weight=ft.FontWeight.W_500, size=13),
                                    ft.Text(f"{per_head:,.2f} ฿", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800, size=13),
                                ]
                            )
                        )
                    )
                self._update_ui()
            except Exception:
                pass
                
        persons_input.on_change = calculate_split
        calculate_split(None)

        def copy_summary(e_copy):
            try:
                p = int(persons_input.value or "1")
                per_head = self._cached_net_amount / p
                summary = f"🥩 สรุปยอดหารค่าอาหาร Steakhouse POS\nยอดสุทธิ: {self._cached_net_amount:,.2f} บาท\nจำนวน {p} คน\n➡️ ตกคนละ: {per_head:,.2f} บาท"
                self.page_ref.clipboard = summary
                self.page_ref.snack_bar = ft.SnackBar(ft.Text("📋 คัดลอกสรุปยอดหารรายคนแล้ว! นำไปวางใน LINE ได้ทันที"), bgcolor=ft.Colors.GREEN_700, open=True)
                self.page_ref.update()
            except Exception:
                pass
        
        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.CALL_SPLIT, color=ft.Colors.BLUE_900),
                ft.Text("ระบบหารจ่ายรายคน (Split Bill)", weight=ft.FontWeight.BOLD, size=16)
            ]),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    spacing=12,
                    tight=True,
                    controls=[
                        net_text,
                        chips_row,
                        ft.Row([persons_input, per_person_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=1),
                        ft.Text("สรุปยอดชำระรายบุคคล:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                        ft.Container(
                            height=140,
                            content=ft.ListView([breakdown_col])
                        )
                    ]
                )
            ),
            actions=[
                ft.OutlinedButton("📋 คัดลอกสรุปส่ง LINE", icon=ft.Icons.CONTENT_COPY, on_click=copy_summary),
                ft.TextButton("ปิด", on_click=lambda e: self._close_dialog(dialog))
            ]
        )
        self._open_dialog(dialog)

    def _handle_checkout(self, e):
        if not self.order_id:
            return
        db = SessionLocal()
        user_id = self.page_ref.session.store.get("user_id")
        if user_id is None:
            self.page_ref.snack_bar = ft.SnackBar(ft.Text("เกิดข้อผิดพลาด: ไม่พบข้อมูลผู้ใช้ กรุณาเข้าสู่ระบบใหม่"), bgcolor=ft.Colors.RED_600, open=True)
            self.page_ref.update()
            return
        try:
            try:
                discount = float(self.discount_input.value or 0)
            except ValueError:
                discount = 0.0
            payment_method = self.payment_dropdown.value
            
            # Checkout & Deduct Stock
            order = OrderService.checkout_order(db, self.order_id, payment_method=payment_method, discount_amount=discount, user_id=user_id)

            # Build E-Receipt Data
            items_data = []
            for item in order.items:
                opt_str = ""
                if item.options_json:
                    try:
                        opts = json.loads(item.options_json)
                        opt_str = f" ({opts.get('doneness', '')}, {opts.get('sauce', '')})"
                    except:
                        pass
                items_data.append({
                    "name": f"{item.menu_item.name}{opt_str}",
                    "qty": item.quantity,
                    "price": float(item.price_per_unit),
                    "total": float(item.price_per_unit) * item.quantity
                })

            receipt_payload = {
                "order_number": order.order_number,
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else "",
                "order_type": order.order_type.value if hasattr(order.order_type, "value") else str(order.order_type),
                "table_or_customer": order.customer_name,
                "items": items_data,
                "subtotal": float(order.subtotal),
                "discount": float(order.discount_amount),
                "net_total": float(order.net_amount),
                "payment_method": payment_method
            }

            # Show E-Receipt Popup Modal
            modal = EReceiptModal(order_data=receipt_payload, page=self.page_ref)
            
            def close_and_redirect(e):
                self._close_dialog(modal)
                # Clear active order and navigate to tables
                self.page_ref.session.store.remove("active_order_id")
                from utils.navigation import navigate_to
                navigate_to(self.page_ref, "/tables")

            # Override the modal's close button to redirect
            if hasattr(modal, "actions") and modal.actions:
                modal.actions[0].on_click = close_and_redirect

            self._open_dialog(modal)

        except Exception as err:
            import traceback
            traceback.print_exc()
            self.page_ref.snack_bar = ft.SnackBar(ft.Text(f"เกิดข้อผิดพลาดในการคิดเงิน: {err}"), bgcolor=ft.Colors.RED_600, open=True)
            try:
                self.page_ref.update()
            except Exception:
                pass
        finally:
            db.close()

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

