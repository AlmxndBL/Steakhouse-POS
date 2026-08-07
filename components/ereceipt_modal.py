import flet as ft
from typing import Dict, Any
from services.receipt_service import ReceiptService

class EReceiptModal(ft.AlertDialog):
    def __init__(self, order_data: Dict[str, Any], page: ft.Page):
        self.page_ref = page
        
        # Generate base64 images
        receipt_b64 = ReceiptService.generate_ereceipt_image_base64(order_data)
        qr_b64 = ReceiptService.generate_qr_base64(f"E-RECEIPT:{order_data.get('order_number')}")

        content_layout = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
            controls=[
                ft.Text("ใบเสร็จรับเงินอิเล็กทรอนิกส์ (E-Receipt)", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800),
                ft.Image(src=f"data:image/png;base64,{receipt_b64}", width=380, fit="contain"),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Text("สแกนเพื่อรับใบเสร็จบนมือถือ", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_800),
                ft.Image(src=f"data:image/png;base64,{qr_b64}", width=150, height=150, fit="contain"),
            ]
        )

        super().__init__(
            title=ft.Text("ชำระเงินสำเร็จ!", weight=ft.FontWeight.BOLD),
            content=ft.Container(content=content_layout, width=420, height=520, padding=10),
            actions=[
                ft.ElevatedButton(
                    "เสร็จสิ้น / ปิดหน้าต่าง",
                    icon=ft.Icons.CHECK,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                    on_click=self._close_modal
                )
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER
        )

    def _close_modal(self, e):
        self.open = False
        try:
            self.page_ref.update()
        except Exception:
            pass
