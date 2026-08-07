import flet as ft
from database.models import Table, TableStatus

class TableCard(ft.Container):
    def __init__(self, table: Table, on_click):
        self.table = table
        self.on_click_callback = on_click

        if table.status == TableStatus.VACANT:
            bg_color = ft.Colors.GREEN_50
            border_color = ft.Colors.GREEN_500
            status_text = "ว่าง (Vacant)"
            status_color = ft.Colors.GREEN_700
            icon = ft.Icons.CHECK_CIRCLE
        elif table.status == TableStatus.OCCUPIED:
            bg_color = ft.Colors.AMBER_50
            border_color = ft.Colors.AMBER_700
            
            # Fetch net amount from current order if available
            net_amt = table.current_order.net_amount if table.current_order else 0.0
            status_text = f"มีลูกค้า ({net_amt:,.2f} ฿)"
            status_color = ft.Colors.AMBER_900
            icon = ft.Icons.RESTAURANT
        else:
            bg_color = ft.Colors.BLUE_50
            border_color = ft.Colors.BLUE_400
            status_text = "รอเก็บโต๊ะ (Cleaning)"
            status_color = ft.Colors.BLUE_800
            icon = ft.Icons.CLEANING_SERVICES

        super().__init__(
            width=180,
            height=140,
            bgcolor=bg_color,
            border=ft.Border.all(2, border_color),
            border_radius=16,
            padding=15,
            ink=True,
            on_click=lambda e: self.on_click_callback(self.table),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(table.table_number, size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                            ft.Icon(icon, color=status_color, size=24)
                        ]
                    ),
                    ft.Text(f"โซน: {table.zone} ({table.capacity} ที่นั่ง)", size=12, color=ft.Colors.GREY_700),
                    ft.Container(
                        content=ft.Text(status_text, size=12, weight=ft.FontWeight.BOLD, color=status_color),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=8,
                        border=ft.Border.all(1, status_color)
                    )
                ]
            )
        )
