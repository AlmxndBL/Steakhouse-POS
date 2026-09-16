from datetime import datetime, timezone
import flet as ft
from database.models import Table, TableStatus
from components.theme import ThemeColors, create_badge

class TableCard(ft.Container):
    def __init__(self, table: Table, on_click, on_manage=None):
        self.table = table
        self.on_click_callback = on_click

        status_val = getattr(table.status, "value", table.status)

        if status_val == "VACANT":
            bg_color = ThemeColors.SURFACE_WHITE
            border_color = ThemeColors.EMERALD
            status_text = "โต๊ะว่าง (พร้อมรับลูกค้า)"
            status_color = ThemeColors.EMERALD
            status_bg = f"{ThemeColors.EMERALD}18"
            icon = ft.Icons.CHECK_CIRCLE_ROUNDED
        elif status_val == "OCCUPIED":
            bg_color = f"{ThemeColors.AMBER_GOLD}0D"
            border_color = ThemeColors.AMBER_DARK
            
            current_order = getattr(table, "current_order", None)
            net_amt = current_order.net_amount if current_order else 0.0
                
            status_text = f"มีลูกค้า ({net_amt:,.0f} ฿)"
            status_color = ThemeColors.AMBER_DARK
            status_bg = f"{ThemeColors.AMBER_GOLD}22"
            icon = ft.Icons.RESTAURANT_ROUNDED
        else:
            bg_color = f"{ThemeColors.SAPPHIRE}0D"
            border_color = ThemeColors.SAPPHIRE
            status_text = "รอทำความสะอาด"
            status_color = ThemeColors.SAPPHIRE
            status_bg = f"{ThemeColors.SAPPHIRE}18"
            icon = ft.Icons.CLEANING_SERVICES_ROUNDED

        order = getattr(table, "current_order", None)
        order_items = list(getattr(order, "items", []) or []) if order else []
        item_count = sum(int(getattr(item, "quantity", 0) or 0) for item in order_items)
        new_item_count = sum(
            int(getattr(item, "quantity", 0) or 0)
            for item in order_items
            if getattr(item, "sent_to_kitchen_at", None) is None
        )
        opened_text = "ยังไม่มีเวลาเปิดบิล"
        created_at = getattr(order, "created_at", None) if order else None
        if created_at:
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            minutes = max(0, int((datetime.now(timezone.utc) - created_at).total_seconds() // 60))
            opened_text = f"เปิดบิล {minutes} นาที"

        footer_controls = [
            ft.Text(
                f"{item_count} รายการ • {opened_text}" if order else opened_text,
                size=11,
                color=ThemeColors.TEXT_MUTED,
            ),
            ft.Text(
                f"รายการใหม่ {new_item_count} รายการ" if new_item_count else "ส่งครัวแล้ว",
                size=11,
                weight=ft.FontWeight.BOLD if new_item_count else ft.FontWeight.W_500,
                color=ThemeColors.AMBER_DARK if new_item_count else ThemeColors.TEXT_MUTED,
            ),
        ]
        if order and on_manage:
            footer_controls.append(ft.TextButton("จัดการบิล", on_click=lambda e: on_manage(table)))

        super().__init__(
            bgcolor=bg_color,
            border=ft.Border.all(1.5, border_color),
            border_radius=12,
            padding=16,
            ink=True,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=6, color="#0000000D", offset=ft.Offset(0, 2)),
            on_click=lambda e: self.on_click_callback(self.table),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(table.table_number, size=20, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN),
                            ft.Icon(icon, color=status_color, size=22)
                        ]
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            create_badge(table.zone or "Indoor", f"{ThemeColors.INDIGO}18", ThemeColors.INDIGO),
                            ft.Text(f"{table.capacity} ที่นั่ง", size=12, color=ThemeColors.TEXT_MUTED, weight=ft.FontWeight.W_500)
                        ]
                    ),
                    ft.Container(
                        content=ft.Text(status_text, size=11, weight=ft.FontWeight.BOLD, color=status_color),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                        bgcolor=status_bg,
                        border_radius=6,
                        alignment=ft.Alignment(0, 0)
                    ),
                    *footer_controls
                ]
            )
        )
