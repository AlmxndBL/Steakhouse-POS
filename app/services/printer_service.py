import json
import logging
from datetime import datetime
from typing import Optional, List
from database.models import Order, OrderItem

class PrinterService:
    @staticmethod
    def format_customer_receipt(
        order: Order,
        store_name: str = "STEAKHOUSE & GRILL RESTAURANT",
        store_branch: str = "สาขาหลัก (Main Branch)",
        tax_id: str = "0105559012345",
        paper_width: int = 42 # Standard 80mm column width
    ) -> str:
        """
        Formats a standard 80mm/58mm text receipt suitable for ESC/POS thermal printers.
        """
        divider = "=" * paper_width
        sub_divider = "-" * paper_width
        
        lines = []
        lines.append(store_name.center(paper_width))
        lines.append(store_branch.center(paper_width))
        lines.append(f"เลขประจำตัวผู้เสียภาษี: {tax_id}".center(paper_width))
        lines.append(divider)
        
        # Order Meta
        order_time_str = order.closed_at.strftime("%d/%m/%Y %H:%M:%S") if order.closed_at else datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        lines.append(f"บิลเลขที่: #{order.order_number}")
        lines.append(f"โต๊ะ/ลูกค้า: {order.customer_name or 'Dine-In'}")
        lines.append(f"วันที่: {order_time_str}")
        lines.append(sub_divider)
        
        # Column Header: รายการ, จำนวน, รวม
        lines.append(f"{'รายการ':<24}{'จำนวน':>6}{'รวม (บาท)':>12}")
        lines.append(sub_divider)
        
        for item in order.items:
            item_name = item.menu_item.name if item.menu_item else "อาหาร"
            if len(item_name) > 22:
                item_name = item_name[:20] + ".."
            total_item_p = float(item.price_per_unit) * item.quantity
            lines.append(f"{item_name:<24}{item.quantity:>6}{total_item_p:>12.2f}")
            
            # Print Modifiers if present
            if item.options_json:
                try:
                    opts = json.loads(item.options_json)
                    opt_details = []
                    if opts.get("doneness"):
                        opt_details.append(opts['doneness'])
                    if opts.get("sauce"):
                        opt_details.append(opts['sauce'])
                    if opt_details:
                        lines.append(f"  * {', '.join(opt_details)}")
                except (TypeError, ValueError, json.JSONDecodeError) as err:
                    logging.debug("Receipt modifier formatting skipped: %s", err)

        lines.append(sub_divider)
        
        # Financial Totals
        subtotal = float(order.subtotal or 0.0)
        disc = float(order.discount_amount or 0.0)
        sc = float(order.service_charge_amount or 0.0)
        vat = float(order.vat_amount or 0.0)
        net = float(order.net_amount or 0.0)
        
        lines.append(f"{'ราคารวม (Subtotal):':<28}{subtotal:>14.2f}")
        if disc > 0:
            lines.append(f"{'ส่วนลด (Discount):':<28}{-disc:>14.2f}")
        lines.append(f"{'Service Charge (10%):':<28}{sc:>14.2f}")
        lines.append(f"{'ภาษีมูลค่าเพิ่ม VAT (7%):':<28}{vat:>14.2f}")
        lines.append(divider)
        lines.append(f"{'ยอดสุทธิชำระ (TOTAL):':<26}{net:>16.2f} ฿")
        lines.append(divider)
        
        # Payment info
        lines.append(f"วิธีชำระเงิน: {order.payment_method or 'เงินสด (CASH)'}")
        lines.append("")
        lines.append("ขอบคุณที่มาอุดหนุน โอกาสหน้าเชิญใหม่ครับ".center(paper_width))
        lines.append("".center(paper_width))
        
        return "\n".join(lines)

    @staticmethod
    def format_kitchen_chit(
        order: Order,
        paper_width: int = 40
    ) -> str:
        """
        Formats a kitchen production ticket (Kitchen Chit) for cook station.
        """
        divider = "#" * paper_width
        sub_divider = "-" * paper_width
        
        lines = []
        lines.append(divider)
        lines.append("ใบสั่งเข้าครัว (KITCHEN ORDER)".center(paper_width))
        lines.append(divider)
        
        created_str = order.created_at.strftime("%H:%M:%S") if order.created_at else datetime.now().strftime("%H:%M:%S")
        lines.append(f"โต๊ะ: {order.customer_name or 'Dine-In'}")
        lines.append(f"เลขออเดอร์: #{order.order_number} | เวลา: {created_str}")
        lines.append(sub_divider)
        
        for idx, item in enumerate(order.items, start=1):
            name = item.menu_item.name if item.menu_item else "อาหาร"
            lines.append(f"[{idx}] {name}  x{item.quantity}")
            if item.options_json:
                try:
                    opts = json.loads(item.options_json)
                    opts_text = ", ".join(f"{k}: {v}" for k, v in opts.items() if v)
                    if opts_text:
                        lines.append(f"    >> ระบุ: {opts_text}")
                except (TypeError, ValueError, json.JSONDecodeError) as err:
                    logging.debug("Kitchen modifier formatting skipped: %s", err)
            if item.notes:
                lines.append(f"    >> หมายเหตุ: {item.notes}")
            lines.append("")
            
        lines.append(divider)
        return "\n".join(lines)
