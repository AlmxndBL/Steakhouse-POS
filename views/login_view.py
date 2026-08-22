import flet as ft
from database.connection import SessionLocal
from services.auth_service import AuthService
from utils.navigation import navigate_to
from utils.validators import Validator

class LoginView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page

        # Theme Colors
        primary_color = ft.Colors.BLUE_900
        bg_color = ft.Colors.BLUE_GREY_50
        card_bg = ft.Colors.WHITE

        # Form Inputs
        self.username_input = ft.TextField(
            label="ชื่อผู้ใช้ (Username)",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            border_radius=10,
            width=360,
            autofocus=True,
            on_submit=lambda e: self.password_input.focus()
        )

        self.password_input = ft.TextField(
            label="รหัสผ่าน (Password)",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
            border_radius=10,
            width=360,
            on_submit=self._handle_login
        )

        self.error_text = ft.Text("", color=ft.Colors.RED_600, size=13, weight=ft.FontWeight.W_500, visible=False)

        self.btn_login = ft.ElevatedButton(
            "เข้าสู่ระบบ (Sign In)",
            icon=ft.Icons.LOGIN,
            style=ft.ButtonStyle(
                bgcolor=primary_color,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding.symmetric(vertical=18, horizontal=24)
            ),
            width=360,
            on_click=self._handle_login
        )

        # Quick Demo Login Chips
        demo_accounts = [
            ("เจ้าของร้าน", "owner", "admin1234", ft.Colors.INDIGO_700),
            ("ผู้จัดการ", "manager", "mgr1234", ft.Colors.BLUE_700),
            ("แคชเชียร์", "cashier", "cash1234", ft.Colors.GREEN_700),
            ("พนักงานเสิร์ฟ", "waiter", "waiter1234", ft.Colors.TEAL_700),
            ("ครัว (KDS)", "kitchen", "cook1234", ft.Colors.AMBER_800),
        ]

        demo_buttons = []
        for label, u, p, color in demo_accounts:
            btn = ft.OutlinedButton(
                label,
                style=ft.ButtonStyle(
                    color=color,
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8)
                ),
                on_click=lambda e, user=u, pwd=p: self._fill_and_login(user, pwd)
            )
            demo_buttons.append(btn)

        login_card = ft.Card(
            elevation=4,
            shadow_color=ft.Colors.BLACK26,
            shape=ft.RoundedRectangleBorder(radius=20),
            content=ft.Container(
                bgcolor=card_bg,
                width=440,
                padding=ft.Padding.symmetric(horizontal=40, vertical=40),
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                    tight=True,
                    controls=[
                        ft.Icon(ft.Icons.RESTAURANT_MENU, size=52, color=primary_color),
                        ft.Text("STEAKHOUSE POS", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                        ft.Text("ระบบจัดการร้านสเต๊กและคลังสินค้า", size=13, color=ft.Colors.GREY_600),
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        self.error_text,
                        self.username_input,
                        self.password_input,
                        ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                        self.btn_login,
                        ft.Divider(height=15, color=ft.Colors.GREY_200),
                        ft.Text("ทดสอบเข้าสู่ระบบด่วน (Quick Demo)", size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            wrap=True,
                            spacing=8,
                            run_spacing=8,
                            controls=demo_buttons
                        )
                    ]
                )
            )
        )

        content_layout = ft.Container(
            expand=True,
            bgcolor=bg_color,
            alignment=ft.Alignment.CENTER,
            content=login_card
        )

        super().__init__(
            route="/login",
            controls=[content_layout],
            padding=0,
            spacing=0
        )

    def _fill_and_login(self, username: str, password: str):
        self.username_input.value = username
        self.password_input.value = password
        self.username_input.error_text = None
        self.password_input.error_text = None
        self.error_text.visible = False
        self._update_ui()
        self._handle_login(None)

    def _handle_login(self, e):
        u_res = Validator.validate_required_text(self.username_input.value, field_name="ชื่อผู้ใช้", min_len=1)
        p_res = Validator.validate_required_text(self.password_input.value, field_name="รหัสผ่าน", min_len=1)

        has_error = False
        if not u_res.is_valid:
            self.username_input.error_text = u_res.error
            has_error = True
        else:
            self.username_input.error_text = None

        if not p_res.is_valid:
            self.password_input.error_text = p_res.error
            has_error = True
        else:
            self.password_input.error_text = None

        if has_error:
            self._update_ui()
            return

        db = SessionLocal()
        try:
            user = AuthService.authenticate(db, username, password)
            if user:
                self.error_text.visible = False
                self.page_ref.session.store.set("user_id", user.id)
                self.page_ref.session.store.set("user_name", user.name)
                self.page_ref.session.store.set("user_role", user.role.value)
                self.page_ref.session.store.set("username", user.username)

                # Smart redirect based on role
                if user.role.value == "KITCHEN":
                    navigate_to(self.page_ref, "/kds")
                elif user.role.value in ["OWNER", "MANAGER"]:
                    navigate_to(self.page_ref, "/admin")
                else:
                    navigate_to(self.page_ref, "/tables")
            else:
                self.error_text.value = "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"
                self.error_text.visible = True
                self._update_ui()
        finally:
            db.close()

    def _update_ui(self):
        try:
            self.update()
        except Exception:
            pass
        try:
            self.page_ref.update()
        except Exception:
            pass
