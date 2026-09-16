import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from decimal import Decimal, ROUND_HALF_UP
from database.models import (
    Table, TableStatus, Order, OrderItem, OrderType, OrderStatus,
    MenuItem, AuditLog, User, UserRole, StockTransaction, StockTxType
)
from services.bom_engine import BOMEngine

class OrderService:
    @staticmethod
    def get_cashier_payment_queue(db: Session) -> List[Order]:
        """Return open orders with items, oldest first, for cashier action cards."""
        return db.query(Order).join(OrderItem, OrderItem.order_id == Order.id).filter(
            Order.status == OrderStatus.OPEN
        ).distinct().order_by(Order.created_at.asc(), Order.id.asc()).all()

    @staticmethod
    def cancel_order(db: Session, order_id: int, user_id: int, reason: str, approver_role=None) -> Order:
        """Cancel an order with an explicit reason and approval for paid orders."""
        clean_reason = (reason or "").strip()
        if len(clean_reason) < 2:
            raise ValueError("การยกเลิกต้องระบุเหตุผลอย่างน้อย 2 ตัวอักษร")
        order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
        if not order:
            raise ValueError("ไม่พบบิลที่ต้องการยกเลิก")
        current = getattr(order.status, "value", order.status)
        if current in {"PAID", "CANCELLED"}:
            role = getattr(approver_role, "value", approver_role)
            if role not in {"OWNER", "MANAGER"}:
                raise ValueError("การยกเลิกบิลที่ชำระแล้วต้องได้รับอนุมัติจากผู้จัดการหรือเจ้าของร้าน")
        order.status = OrderStatus.CANCELLED
        order.closed_at = datetime.now(timezone.utc)
        if order.table_id:
            table = db.query(Table).filter(Table.id == order.table_id).first()
            if table and table.current_order_id == order.id:
                table.current_order_id = None
                table.status = TableStatus.VACANT
        db.add(AuditLog(
            user_id=user_id,
            action="CANCEL_ORDER",
            target_type="Order",
            target_id=order.id,
            details_json=json.dumps({"reason": clean_reason, "previous_status": current}, ensure_ascii=False),
            timestamp=datetime.now(timezone.utc)
        ))
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def refund_order(db: Session, order_id: int, user_id: int, reason: str, approver_role=None) -> Order:
        """Refund a paid classroom order with explicit manager/owner approval."""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or order.status != OrderStatus.PAID:
            raise ValueError("คืนเงินได้เฉพาะบิลที่ชำระเงินแล้ว")
        role = getattr(approver_role, "value", approver_role)
        if role not in {"OWNER", "MANAGER"}:
            raise PermissionError("การคืนเงินต้องได้รับอนุมัติจากผู้จัดการหรือเจ้าของร้าน")
        clean_reason = (reason or "").strip()
        if len(clean_reason) < 2:
            raise ValueError("การคืนเงินต้องระบุเหตุผลอย่างน้อย 2 ตัวอักษร")
        refunded = OrderService.cancel_order(db, order_id, user_id, clean_reason, approver_role=role)
        db.add(AuditLog(
            user_id=user_id,
            action="REFUND_ORDER",
            target_type="Order",
            target_id=order_id,
            details_json=json.dumps({"reason": clean_reason, "approver_role": role}, ensure_ascii=False),
            timestamp=datetime.now(timezone.utc),
        ))
        db.commit()
        db.refresh(refunded)
        return refunded

    @staticmethod
    def update_item_status(db: Session, order_item_id: int, new_status, user_id: int) -> OrderItem:
        """Apply the allowed kitchen item transition and record an audit event."""
        item = db.query(OrderItem).filter(OrderItem.id == order_item_id).with_for_update().first()
        if not item:
            raise ValueError("ไม่พบรายการอาหาร")
        if item.sent_to_kitchen_at is None:
            raise ValueError("รายการยังไม่ถูกส่งเข้าครัว")
        current = getattr(item.item_status, "value", item.item_status)
        target = getattr(new_status, "value", new_status)
        allowed = {"PENDING": "COOKING", "COOKING": "SERVED"}
        if allowed.get(current) != target:
            raise ValueError(f"ไม่สามารถเปลี่ยนสถานะจาก {current} เป็น {target}")
        item.item_status = new_status
        db.add(AuditLog(
            user_id=user_id,
            action="UPDATE_ORDER_ITEM_STATUS",
            target_type="OrderItem",
            target_id=item.id,
            details_json=json.dumps({"from": current, "to": target}, ensure_ascii=False),
            timestamp=datetime.now(timezone.utc)
        ))
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def split_item_to_new_order(db: Session, order_id: int, order_item_id: int, quantity: int, user_id: int) -> Order:
        """Split part of an open order item into a new open order."""
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user or user.role not in {UserRole.OWNER, UserRole.MANAGER, UserRole.CASHIER, UserRole.WAITER}:
            raise PermissionError("ผู้ใช้ไม่มีสิทธิ์แยกรายการออกเป็นบิลใหม่")
        order = db.query(Order).filter(Order.id == order_id, Order.status == OrderStatus.OPEN).with_for_update().first()
        item = db.query(OrderItem).filter(OrderItem.id == order_item_id, OrderItem.order_id == order_id).with_for_update().first()
        if not order or not item:
            raise ValueError("ไม่พบออเดอร์หรือรายการที่ต้องการแยกบิล")
        if quantity < 1 or quantity >= item.quantity:
            raise ValueError("จำนวนที่แยกต้องน้อยกว่าจำนวนเดิมและมากกว่า 0")

        new_order = Order(
            order_number=f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}",
            table_id=None,
            order_type=order.order_type,
            status=OrderStatus.OPEN,
            customer_name=f"แยกจาก {order.customer_name or order.order_number}",
            user_id=order.user_id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_order)
        db.flush()
        item.quantity -= quantity
        db.add(OrderItem(
            order_id=new_order.id,
            menu_item_id=item.menu_item_id,
            quantity=quantity,
            price_per_unit=item.price_per_unit,
            options_json=item.options_json,
            item_status=item.item_status,
            sent_to_kitchen_at=item.sent_to_kitchen_at,
            notes=item.notes
        ))
        db.flush()
        OrderService._recalculate_order_totals(db, order)
        OrderService._recalculate_order_totals(db, new_order)
        db.add(AuditLog(
            user_id=user_id,
            action="SPLIT_ORDER_ITEM",
            target_type="Order",
            target_id=order.id,
            details_json=json.dumps({"new_order_id": new_order.id, "order_item_id": item.id, "quantity": quantity}, ensure_ascii=False),
            timestamp=datetime.now(timezone.utc)
        ))
        db.commit()
        db.refresh(new_order)
        return new_order

    @staticmethod
    def send_new_items_to_kitchen(db: Session, order_id: int, user_id: int) -> int:
        """Mark unsent open items as sent and return the number of newly sent items."""
        order = db.query(Order).filter(Order.id == order_id, Order.status == OrderStatus.OPEN).first()
        if not order:
            raise ValueError("ไม่พบบิลที่เปิดอยู่สำหรับส่งเข้าครัว")

        new_items = [item for item in order.items if item.sent_to_kitchen_at is None and item.item_status != "CANCELLED"]
        if not new_items:
            return 0

        sent_at = datetime.now(timezone.utc)
        for item in new_items:
            item.sent_to_kitchen_at = sent_at
        db.add(AuditLog(
            user_id=user_id,
            action="SEND_NEW_ITEMS_TO_KITCHEN",
            target_type="Order",
            target_id=order.id,
            details_json=json.dumps({"item_ids": [item.id for item in new_items]}, ensure_ascii=False)
        ))
        db.commit()
        return len(new_items)

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
    def validate_discount_approval(discount_amount: float, approver_role=None, threshold: float = 500.0) -> bool:
        """Require manager/owner approval for discounts above the classroom threshold."""
        amount = Decimal(str(discount_amount or 0))
        if amount <= Decimal(str(threshold)):
            return True
        role = getattr(approver_role, "value", approver_role)
        if role not in {"OWNER", "MANAGER"}:
            raise ValueError("ส่วนลดเกิน 500 บาทต้องได้รับอนุมัติจากผู้จัดการหรือเจ้าของร้าน")
        return True

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

        existing_sale = db.query(StockTransaction.id).filter(
            StockTransaction.order_id == order.id,
            StockTransaction.tx_type == StockTxType.SALE_OUT,
        ).first()
        if existing_sale:
            raise ValueError("บิลนี้ถูกตัดสต็อกแล้ว ไม่สามารถชำระเงินซ้ำได้")

        approver = db.query(User).filter(User.id == user_id).first()
        OrderService.validate_discount_approval(discount_amount, approver_role=approver.role if approver else None)

        # Recalculate totals with discount
        OrderService._recalculate_order_totals(db, order, discount=discount_amount)
        order.payment_method = payment_method
        order.status = OrderStatus.PAID
        order.closed_at = datetime.now(timezone.utc)

        # Execute BOM Stock Deduction in same transaction. Any stock failure
        # must leave order/payment/table state unchanged.
        try:
            BOMEngine.deduct_stock_for_order(db, order, user_id)
        except Exception:
            db.rollback()
            raise

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
