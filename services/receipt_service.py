import io
import base64
import qrcode
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any

class ReceiptService:
    @staticmethod
    def generate_qr_base64(data_string: str) -> str:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(data_string)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    @staticmethod
    def generate_ereceipt_image_base64(order_data: Dict[str, Any]) -> str:
        """
        Renders a clean, high-resolution E-Receipt image using PIL and returns base64 PNG string.
        """
        width = 440
        header_height = 140
        item_height = 30 * len(order_data.get("items", []))
        footer_height = 220
        total_height = header_height + item_height + footer_height

        img = Image.new("RGB", (width, total_height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Draw Decorative Top Header
        draw.rectangle([(0, 0), (width, 8)], fill=(40, 167, 69)) # Green Accent Bar

        # Use TrueType Font for Thai Support
        try:
            font_large = ImageFont.truetype("tahoma.ttf", 20)
            font_medium = ImageFont.truetype("tahoma.ttf", 16)
            font_small = ImageFont.truetype("tahoma.ttf", 14)
        except IOError:
            font_large = font_medium = font_small = ImageFont.load_default()
        
        y = 20
        # Title Header
        draw.text((width // 2 - 80, y), "=== STEAKHOUSE POS ===", fill=(0, 0, 0), font=font_large)
        y += 25
        draw.text((width // 2 - 95, y), "ใบเสร็จรับเงินอิเล็กทรอนิกส์ (E-Receipt)", fill=(60, 60, 60), font=font_medium)
        y += 25
        draw.text((20, y), f"เลขที่บิล: {order_data.get('order_number', '-')}", fill=(0, 0, 0), font=font_medium)
        y += 20
        draw.text((20, y), f"วันที่: {order_data.get('created_at', '-')}", fill=(0, 0, 0), font=font_medium)
        y += 20
        draw.text((20, y), f"ประเภท: {order_data.get('order_type', '-')} | โต๊ะ/ลูกค้า: {order_data.get('table_or_customer', '-')}", fill=(0, 0, 0), font=font_medium)
        y += 25
        draw.line([(20, y), (width - 20, y)], fill=(200, 200, 200), width=1)
        y += 10

        # Items
        for item in order_data.get("items", []):
            item_name = item.get("name", "")[:26]
            qty_price = f"{item.get('qty', 1)} x {item.get('price', 0):,.2f} = {item.get('total', 0):,.2f}"
            draw.text((20, y), item_name, fill=(0, 0, 0), font=font_medium)
            y += 20
            draw.text((30, y), qty_price, fill=(100, 100, 100), font=font_small)
            y += 20

        y += 10
        draw.line([(20, y), (width - 20, y)], fill=(200, 200, 200), width=1)
        y += 15

        # Totals
        draw.text((20, y), f"ราคารวม (Subtotal):", fill=(0, 0, 0), font=font_medium)
        draw.text((width - 120, y), f"{order_data.get('subtotal', 0):,.2f} THB", fill=(0, 0, 0), font=font_medium)
        y += 20
        
        discount = order_data.get('discount', 0)
        if discount > 0:
            draw.text((20, y), f"ส่วนลด (Discount):", fill=(220, 53, 69), font=font_medium)
            draw.text((width - 120, y), f"-{discount:,.2f} THB", fill=(220, 53, 69), font=font_medium)
            y += 20

        draw.text((20, y), f"ยอดชำระสุทธิ (Net Total):", fill=(40, 167, 69), font=font_large)
        draw.text((width - 120, y), f"{order_data.get('net_total', 0):,.2f} THB", fill=(40, 167, 69), font=font_large)
        y += 25
        draw.text((20, y), f"ชำระโดย: {order_data.get('payment_method', '-')}", fill=(0, 0, 0), font=font_medium)
        y += 30

        # Footer
        draw.line([(20, y), (width - 20, y)], fill=(200, 200, 200), width=1)
        y += 15
        draw.text((width // 2 - 90, y), "ขอบคุณที่ใช้บริการ สเต๊กเฮาส์!", fill=(80, 80, 80), font=font_medium)

        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
