import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from decimal import Decimal, ROUND_HALF_UP
from database.models import (
    Table, TableStatus, Order, OrderItem, OrderType, OrderStatus,
    MenuItem, AuditLog
)
from services.bom_engine import BOMEngine

class OrderService:
    @staticmethod
    def get_tables(db: Session) -> List[Table]:
        return db.query(Table).order_by(Table.table_number.asc()).all()

    @staticmethod
    def create_or_get_open_order(
        db: Session,
        table_id: Optional[int],
        order_type: OrderType,
        customer_name: Optional[str],
        user_id: int
    ) -> Order:
        if order_type == OrderType.DINE_IN and table_id:
            table = db.query(Table).filter(Table.id == table_id).first()
            if table and table.current_order_id:
                existing_order = db.query(Order).filter(
                    Order.id == table.current_order_id,
                    Order.status == OrderStatus.OPEN
                ).first()
                if existing_order:
                    return existing_order

        # Create new order — use 8 hex chars (4 billion combos) to avoid collisions
        order_num = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        order = Order(
            order_number=order_num,
            table_id=table_id if order_type == OrderType.DINE_IN else None,
            order_type=order_type,
            status=OrderStatus.OPEN,
            customer_name=customer_name or ("หน้าร้าน" if order_type == OrderType.DINE_IN else "ลูกค้า Takeaway"),
            user_id=user_id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(order)
        db.flush()

        if order_type == OrderType.DINE_IN and table_id:
            table = db.query(Table).filter(Table.id == table_id).first()
            if table:
                table.status = TableStatus.OCCUPIED
                table.current_order_id = order.id

        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def add_item_to_order(
        db: Session,
        order_id: int,
        menu_item_id: int,
        qty: int = 1,
        options_json: Optional[str] = None,
        notes: Optional[str] = None
    ) -> OrderItem:
        order = db.query(Order).filter(Order.id == order_id).first()
        menu_item = db.query(MenuItem).filter(MenuItem.id == menu_item_id).first()
        if not order or not menu_item:
            raise ValueError("Order or MenuItem not found")

        extra_price = 0.0
        if options_json:
            try:
                opts = json.loads(options_json)
                from database.models import ModifierOption
                for opt_name in opts.values():
                    mod_opt = db.query(ModifierOption).filter(ModifierOption.name == opt_name).first()
                    if mod_opt and mod_opt.extra_price:
                        extra_price += float(mod_opt.extra_price)
            except Exception as e:
                print(f"[WARN] Failed to parse options_json for pricing: {e}")

        unit_price = float(menu_item.price) + extra_price

        item = OrderItem(
            order_id=order.id,
            menu_item_id=menu_item.id,
            quantity=qty,
            price_per_unit=unit_price,
            options_json=options_json,
            notes=notes
        )
        db.add(item)
        db.flush()

        # Recalculate order total
        OrderService._recalculate_order_totals(db, order)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def remove_item(db: Session, order_item_id: int) -> bool:
        item = db.query(OrderItem).filter(OrderItem.id == order_item_id).first()
        if not item:
            return False
        order = item.order
        db.delete(item)
        db.flush()

        OrderService._recalculate_order_totals(db, order)
        db.commit()
        return True

    @staticmethod
    def _recalculate_order_totals(db: Session, order: Order, discount=None):
        """Recalculate order totals with high financial Decimal precision (ROUND_HALF_UP)."""
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        subtotal = Decimal('0.00')
        for item in items:
            unit_p = Decimal(str(item.price_per_unit))
            subtotal += unit_p * Decimal(str(item.quantity))

        order.subtotal = float(subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        # Preserve existing discount if not explicitly passed
        if discount is not None:
            disc_in = Decimal(str(discount))
            order.discount_amount = float(max(Decimal('0.00'), min(disc_in, subtotal)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        disc = Decimal(str(order.discount_amount or 0.0))
        sub_after_disc = max(Decimal('0.00'), subtotal - disc)
        
        # 10% Service Charge
        sc_val = (sub_after_disc * Decimal('0.10')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        order.service_charge_amount = float(sc_val)
        
        # 7% VAT (Exclude VAT logic: calculate on subtotal + SC)
        vat_val = ((sub_after_disc + sc_val) * Decimal('0.07')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        order.vat_amount = float(vat_val)
        
        net_val = (sub_after_disc + sc_val + vat_val).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        order.net_amount = float(net_val)

    @staticmethod
    def checkout_order(
        db: Session,
        order_id: int,
        payment_method: str,
        discount_amount: float,
        user_id: int
    ) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or order.status != OrderStatus.OPEN:
            raise ValueError("สถานะบิลไม่ถูกต้องสำหรับชำระเงิน (ต้องเป็น OPEN เท่านั้น)")

        if not order.items or len(order.items) == 0:
            raise ValueError("ไม่สามารถชำระเงินบิลว่างได้ กรุณาเลือกรายการอาหารก่อน")

        # Recalculate totals with discount
        OrderService._recalculate_order_totals(db, order, discount=discount_amount)
        order.payment_method = payment_method
        order.status = OrderStatus.PAID
        order.closed_at = datetime.now(timezone.utc)

        # Execute BOM Stock Deduction in same transaction
        BOMEngine.deduct_stock_for_order(db, order, user_id)

        # Update Table Status
        if order.table_id:
            table = db.query(Table).filter(Table.id == order.table_id).first()
            if table:
                table.status = TableStatus.VACANT
                table.current_order_id = None

        # Audit Log
        audit = AuditLog(
            user_id=user_id,
            action="CHECKOUT_ORDER",
            target_type="Order",
            target_id=order.id,
            details_json=json.dumps({
                "order_number": order.order_number,
                "amount": float(order.net_amount),
                "payment": payment_method
            }, ensure_ascii=False)
        )
        db.add(audit)
        db.commit()
        db.refresh(order)
        return order
