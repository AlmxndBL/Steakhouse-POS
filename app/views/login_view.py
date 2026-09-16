import os
import logging
import flet as ft
from database.connection import SessionLocal
from services.auth_service import AuthService
from components.theme import ThemeColors, create_card, create_badge, create_button
from utils.navigation import navigate_to
from utils.validators import Validator

class LoginView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page

        # Form Inputs
        self.username_input = ft.TextField(
            label="ชื่อผู้ใช้ (Username)",
            prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
            border_radius=8,
            width=360,
            autofocus=True,
            on_submit=lambda e: self.password_input.focus()
        )

        self.password_input = ft.TextField(
            label="รหัสผ่าน (Password)",
            prefix_icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
            password=True,
            can_reveal_password=True,
            border_radius=8,
            width=360,
            on_submit=self._handle_login
        )

        self.error_text = ft.Text("", color=ThemeColors.CRIMSON, size=13, weight=ft.FontWeight.W_500, visible=False)

        self.btn_login = create_button(
            "เข้าสู่ระบบ (Sign In)",
            icon=ft.Icons.LOGIN_ROUNDED,
            bg_color=ThemeColors.BG_DARK,
            height=46,
            width=360,
            on_click=self._handle_login
        )

        # Quick Demo Login Chips
        demo_accounts = [
            ("👑 เจ้าของร้าน (Owner)", "owner", "admin1234", ThemeColors.AMBER_DARK),
            ("👔 ผู้จัดการ (Manager)", "manager", "mgr1234", ThemeColors.PURPLE),
            ("💵 แคชเชียร์ (Cashier)", "cashier", "cash1234", ThemeColors.SAPPHIRE),
            ("🍽️ พนักงานเสิร์ฟ (Waiter)", "waiter", "waiter1234", ThemeColors.EMERALD),
            ("👨‍🍳 ครัว (KDS Chef)", "kitchen", "cook1234", ThemeColors.CRIMSON),
        ]

        app_env = os.environ.get("APP_ENV", os.environ.get("ENVIRONMENT", "development")).strip().lower()
        demo_buttons = []
        if app_env not in {"production", "prod"}:
            for label, u, p, color in demo_accounts:
                demo_buttons.append(ft.OutlinedButton(
                    label,
                    style=ft.ButtonStyle(
                        color=color,
                        shape=ft.RoundedRectangleBorder(radius=8),
                        side=ft.BorderSide(1, f"{color}66"),
                        padding=ft.Padding.symmetric(horizontal=12, vertical=8)
                    ),
                    on_click=lambda e, user=u, pwd=p: self._fill_and_login(user, pwd)
                ))

        login_card = create_card(
            ft.Container(
                width=420,
                padding=ft.Padding.symmetric(horizontal=24, vertical=28),
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=14,
                    tight=True,
                    controls=[
                        ft.Container(
                            width=56,
                            height=56,
                            bgcolor=ThemeColors.AMBER_GOLD,
                            border_radius=12,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(ft.Icons.RESTAURANT_MENU_ROUNDED, size=32, color=ThemeColors.BG_DARK)
                        ),
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=2,
                            controls=[
                                ft.Text("STEAKHOUSE POS", size=22, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN),
                                ft.Text("ระบบจัดการร้านสเต๊กและคลังวัตถุดิบครบวงจร", size=12, color=ThemeColors.TEXT_MUTED)
                            ]
                        ),
                        ft.Container(height=4),
                        self.error_text,
                        self.username_input,
                        self.password_input,
                        ft.Container(height=2),
                        self.btn_login,
                        *([] if not demo_buttons else [
                            ft.Divider(height=16, color=ThemeColors.BORDER_LIGHT),
                            ft.Text("ทดสอบเข้าสู่ระบบด่วน (1-Click Dev Persona):", size=11, color=ThemeColors.TEXT_MUTED, weight=ft.FontWeight.BOLD),
                            ft.Row(alignment=ft.MainAxisAlignment.CENTER, wrap=True, spacing=6, run_spacing=6, controls=demo_buttons)
                        ])
                    ]
                )
            ),
            padding=0,
            border_radius=16
        )

        content_layout = ft.Container(
            expand=True,
            bgcolor=ThemeColors.BG_DARK,
            alignment=ft.Alignment(0, 0),
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
            username = u_res.value
            password = p_res.value
            user = AuthService.authenticate(db, username, password)
            if user:
                self.error_text.visible = False
                self.page_ref.session.store.set("user_id", user.id)
                self.page_ref.session.store.set("user_name", user.name)
                self.page_ref.session.store.set("user_role", user.role.value if hasattr(user.role, "value") else str(user.role))
                self.page_ref.session.store.set("username", user.username)

                navigate_to(self.page_ref, AuthService.get_role_home_route(user.role))
            else:
                self.error_text.value = "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"
                self.error_text.visible = True
                self._update_ui()
        finally:
            db.close()

    def _update_ui(self):
        try:
            self.update()
        except RuntimeError as err:
            logging.debug("Login view update skipped: %s", err)
        try:
            self.page_ref.update()
        except RuntimeError as err:
            logging.debug("Login page update skipped: %s", err)
