import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
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

        # Create new order
        order_num = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
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
                        extra_price += mod_opt.extra_price
            except Exception:
                pass

        unit_price = menu_item.price + extra_price

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
    def _recalculate_order_totals(db: Session, order: Order, discount: float = 0.0):
        subtotal = 0.0
        for item in order.items:
            subtotal += item.price_per_unit * item.quantity

        order.subtotal = subtotal
        order.discount_amount = discount
        order.net_amount = max(0.0, subtotal - discount)

    @staticmethod
    def checkout_order(
        db: Session,
        order_id: int,
        payment_method: str,
        discount_amount: float,
        user_id: int
    ) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or order.status == OrderStatus.PAID:
            raise ValueError("สถานะบิลไม่ถูกต้องสำหรับชำระเงิน")

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
            details_json=f'{{"order_number": "{order.order_number}", "amount": {order.net_amount}, "payment": "{payment_method}"}}'
        )
        db.add(audit)
        db.commit()
        db.refresh(order)
        return order
