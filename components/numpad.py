import flet as ft
from typing import Callable

class PinNumpad(ft.Container):
    def __init__(self, on_submit: Callable[[str], None]):
        super().__init__()
        self.on_submit = on_submit
        self.pin = ""
        
        # Display Dots for 6 digits
        self.dots_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=15,
            controls=[
                ft.Container(
                    width=20, height=20,
                    border_radius=10,
                    bgcolor=ft.Colors.GREY_300,
                    border=ft.Border.all(2, ft.Colors.BLUE_GREY_400)
                ) for _ in range(6)
            ]
        )

        self.error_text = ft.Text("", color=ft.Colors.RED_500, size=14, weight=ft.FontWeight.BOLD)

        # Build Keypad Buttons
        buttons = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            ["C", "0", "⌫"]
        ]

        grid_controls = []
        for row in buttons:
            row_controls = []
            for btn_text in row:
                btn = ft.ElevatedButton(
                    btn_text,
                    width=85,
                    height=75,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=16),
                        color=ft.Colors.WHITE if btn_text not in ["C", "⌫"] else ft.Colors.BLUE_GREY_900,
                        bgcolor=ft.Colors.BLUE_600 if btn_text not in ["C", "⌫"] else ft.Colors.BLUE_GREY_200,
                        text_style=ft.TextStyle(size=26, weight=ft.FontWeight.BOLD)
                    ),
                    on_click=lambda e, val=btn_text: self._on_key_click(val)
                )
                row_controls.append(btn)
            grid_controls.append(ft.Row(controls=row_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=15))

        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            controls=[
                ft.Text("กรอก PIN 6 หลักเพื่อเข้าใช้งาน", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                self.dots_row,
                self.error_text,
                ft.Column(controls=grid_controls, spacing=15)
            ]
        )

    def _on_key_click(self, val: str):
        if val == "C":
            self.pin = ""
            self.error_text.value = ""
        elif val == "⌫":
            self.pin = self.pin[:-1]
            self.error_text.value = ""
        elif len(self.pin) < 6 and val.isdigit():
            self.pin += val
            self.error_text.value = ""

        self._update_dots()

        if len(self.pin) == 6:
            self.on_submit(self.pin)

    def show_error(self, message: str):
        self.error_text.value = message
        self.pin = ""
        self._update_dots()
        try:
            self.update()
        except Exception:
            pass

    def _update_dots(self):
        for i, dot in enumerate(self.dots_row.controls):
            if i < len(self.pin):
                dot.bgcolor = ft.Colors.GREEN_500
                dot.border = ft.Border.all(2, ft.Colors.GREEN_700)
            else:
                dot.bgcolor = ft.Colors.GREY_300
                dot.border = ft.Border.all(2, ft.Colors.BLUE_GREY_400)
        try:
            self.update()
        except Exception:
            pass
