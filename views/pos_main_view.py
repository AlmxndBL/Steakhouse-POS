import json
import flet as ft
from database.connection import SessionLocal
from database.models import Order, Category, MenuItem, ModifierGroup, OrderStatus
from services.order_service import OrderService
from components.ereceipt_modal import EReceiptModal
from utils.navigation import navigate_to

class PosMainView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        self.order_id = page.session.store.get("active_order_id")
        user_name = page.session.store.get("user_name") or "พนักงาน"

        self.selected_category_id = None
        self.cart_items_list = ft.ListView(expand=True, spacing=10, padding=10)
        self.subtotal_text = ft.Text("0.00 THB", size=18, weight=ft.FontWeight.BOLD)
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

        # Header Navigation
        nav_header = ft.Container(
            padding=ft.Padding.symmetric(horizontal=25, vertical=12),
            bgcolor=ft.Colors.BLUE_900,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=15,
                        controls=[
                            ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, on_click=lambda e: navigate_to(self.page_ref, "/tables")),
                            ft.Text("รับออเดอร์ & คิดเงิน (POS Checkout)", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]
                    ),
                    ft.Text(f"พนักงาน: {user_name}", size=14, color=ft.Colors.BLUE_200)
                ]
            )
        )

        # Categories & Menu Grid
        self.category_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=10)
        self.menu_grid = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=200,
            child_aspect_ratio=1.1,
            spacing=15,
            run_spacing=15,
            padding=15
        )

        # Left Column: Menu Items
        left_layout = ft.Column(
            expand=True,
            spacing=15,
            controls=[
                ft.Container(content=self.category_row, padding=ft.Padding.only(left=15, top=15, right=15)),
                ft.Container(expand=True, content=self.menu_grid, bgcolor=ft.Colors.GREY_100)
            ]
        )

        # Right Column: Cart & Payment Sidebar
        right_layout = ft.Container(
            width=420,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.only(left=ft.BorderSide(1, ft.Colors.GREY_300)),
            padding=20,
            content=ft.Column(
                expand=True,
                spacing=15,
                controls=[
                    self.order_title_text,
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    ft.Container(expand=True, content=self.cart_items_list),
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("ราคารวม (Subtotal):", size=14), self.subtotal_text]),
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("ส่วนลด (Discount):", size=14), self.discount_input]),
                            ft.Divider(height=1, color=ft.Colors.GREY_300),
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("ยอดชำระสุทธิ:", size=18, weight=ft.FontWeight.BOLD), self.net_total_text]),
                            self.payment_dropdown,
                            ft.ElevatedButton(
                                "ชำระเงิน & ออก E-Receipt",
                                icon=ft.Icons.PAYMENT,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE, padding=18),
                                width=380,
                                on_click=self._handle_checkout
                            )
                        ]
                    )
                ]
            )
        )

        main_body = ft.Row(
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
            categories = db.query(Category).order_by(Category.sort_order.asc()).all()
            self.category_row.controls.clear()
            
            # All category button
            btn_all = ft.ElevatedButton("ทั้งหมด", on_click=lambda e: self._filter_menu(None))
            self.category_row.controls.append(btn_all)

            for cat in categories:
                btn = ft.ElevatedButton(cat.name, on_click=lambda e, cid=cat.id: self._filter_menu(cid))
                self.category_row.controls.append(btn)

            self._filter_menu(None)
        finally:
            db.close()

    def _filter_menu(self, category_id):
        self.selected_category_id = category_id
        db = SessionLocal()
        try:
            query = db.query(MenuItem).filter(MenuItem.is_active == True)
            if category_id:
                query = query.filter(MenuItem.category_id == category_id)
            items = query.all()

            self.menu_grid.controls.clear()
            for item in items:
                card = ft.Card(
                    elevation=3,
                    shape=ft.RoundedRectangleBorder(radius=12),
                    content=ft.Container(
                        padding=12,
                        ink=True,
                        on_click=lambda e, m=item: self._on_menu_item_click(m),
                        content=ft.Column(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(item.name, size=14, weight=ft.FontWeight.BOLD, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(f"{item.price:,.2f} ฿", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                                ft.Container(
                                    content=ft.Row([ft.Icon(ft.Icons.ADD, size=16, color=ft.Colors.BLUE_700), ft.Text("สั่งเพิ่ม", size=12, color=ft.Colors.BLUE_700)]),
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
            try:
                discount = float(self.discount_input.value or 0)
            except ValueError:
                discount = 0.0
            net = max(0.0, order.subtotal - discount)
            self.net_total_text.value = f"{net:,.2f} THB"
            try:
                self.update()
            except Exception:
                pass
        finally:
            db.close()

    def _remove_item(self, item_id: int):
        db = SessionLocal()
        try:
            OrderService.remove_item(db, item_id)
            self._load_cart()
        finally:
            db.close()

    def _update_item_qty(self, item_id: int, delta: int):
        db = SessionLocal()
        try:
            from database.models import OrderItem
            item = db.query(OrderItem).filter(OrderItem.id == item_id).first()
            if item:
                if item.quantity + delta > 0:
                    item.quantity += delta
                    # Recalculate totals
                    OrderService._recalculate_order_totals(db, item.order)
                    db.commit()
                else:
                    OrderService.remove_item(db, item_id)
            self._load_cart()
        finally:
            db.close()

    def _on_discount_change(self, e):
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == self.order_id).first()
            if order:
                try:
                    discount = float(self.discount_input.value or 0)
                except ValueError:
                    discount = 0.0
                net = max(0.0, order.subtotal - discount)
                self.net_total_text.value = f"{net:,.2f} THB"
                try:
                    self.net_total_text.update()
                except Exception:
                    pass
        except:
            pass
        finally:
            db.close()

    def _handle_checkout(self, e):
        if not self.order_id:
            return
        db = SessionLocal()
        user_id = self.page_ref.session.store.get("user_id") or 1
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
                    "price": item.price_per_unit,
                    "total": item.price_per_unit * item.quantity
                })

            receipt_payload = {
                "order_number": order.order_number,
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "order_type": order.order_type.value,
                "table_or_customer": order.customer_name,
                "items": items_data,
                "subtotal": order.subtotal,
                "discount": order.discount_amount,
                "net_total": order.net_amount,
                "payment_method": payment_method
            }

            # Show E-Receipt Popup Modal
            modal = EReceiptModal(order_data=receipt_payload, page=self.page_ref)
            
            def close_and_redirect(e):
                modal.open = False
                self.page_ref.update()
                # Clear active order and navigate to tables
                self.page_ref.session.store.remove("active_order_id")
                self.page_ref.route = "/tables"
                self.page_ref.update()
                from utils.navigation import navigate_to
                navigate_to(self.page_ref, "/tables")

            # Override the modal's close button to redirect
            if hasattr(modal, "actions") and modal.actions:
                modal.actions[0].on_click = close_and_redirect

            try:
                self.page_ref.overlay.append(modal)
                modal.open = True
                self.page_ref.update()
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Failed to append modal to overlay: {e}")

        except Exception as err:
            import traceback
            traceback.print_exc()
            print(f"CRITICAL ERROR IN CHECKOUT: {err}")
            snack = ft.SnackBar(ft.Text(f"เกิดข้อผิดพลาดในการคิดเงิน: {err}"), bgcolor=ft.Colors.RED_600)
            self.page_ref.overlay.append(snack)
            snack.open = True
            try:
                self.page_ref.update()
            except Exception as inner_err:
                print(f"Failed to show snackbar: {inner_err}")
        finally:
            db.close()
