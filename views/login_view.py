import flet as ft
from database.connection import SessionLocal
from services.auth_service import AuthService
from components.numpad import PinNumpad
from utils.navigation import navigate_to

class LoginView(ft.View):
    def __init__(self, page: ft.Page):
        self.page_ref = page
        
        self.numpad = PinNumpad(on_submit=self._handle_pin_submit)

        content = ft.Container(
            alignment=ft.Alignment.CENTER,
            expand=True,
            bgcolor=ft.Colors.BLUE_GREY_50,
            content=ft.Card(
                elevation=8,
                shape=ft.RoundedRectangleBorder(radius=24),
                content=ft.Container(
                    width=420,
                    padding=35,
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20,
                        controls=[
                            ft.Icon(ft.Icons.RESTAURANT_MENU, size=60, color=ft.Colors.BLUE_700),
                            ft.Text("STEAKHOUSE POS", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                            ft.Text("ระบบจัดการร้านสเต๊กและคลังวัตถุดิบ", size=14, color=ft.Colors.GREY_600),
                            ft.Divider(height=1, color=ft.Colors.GREY_300),
                            self.numpad
                        ]
                    )
                )
            )
        )

        super().__init__(
            route="/login",
            controls=[content],
            padding=0,
            spacing=0
        )

    def _handle_pin_submit(self, pin: str):
        db = SessionLocal()
        try:
            user = AuthService.verify_pin(db, pin)
            if user:
                self.page_ref.session.store.set("user_id", user.id)
                self.page_ref.session.store.set("user_name", user.name)
                self.page_ref.session.store.set("user_role", user.role.value)
                navigate_to(self.page_ref, "/tables")
            else:
                self.numpad.show_error("PIN ไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง")
        finally:
            db.close()
