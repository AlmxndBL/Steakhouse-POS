import json
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import AuditLog, Order, OrderStatus, Table, TableStatus, User, UserRole
from services.order_service import OrderService
from utils.validators import Validator

class TableService:
    @staticmethod
    def _require_operation_role(db: Session, user_id: int) -> None:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        allowed = {UserRole.OWNER, UserRole.MANAGER, UserRole.CASHIER, UserRole.WAITER}
        if not user or user.role not in allowed:
            raise PermissionError("ผู้ใช้ไม่มีสิทธิ์ดำเนินการกับโต๊ะหรือออเดอร์")

    @staticmethod
    def merge_orders(db: Session, primary_order_id: int, secondary_order_id: int, user_id: int) -> Order:
        """Merge two open dine-in orders, preserving item rows and table auditability."""
        TableService._require_operation_role(db, user_id)
        if primary_order_id == secondary_order_id:
            raise ValueError("ไม่สามารถรวมบิลเดียวกันได้")
        primary = db.query(Order).filter(Order.id == primary_order_id).with_for_update().first()
        secondary = db.query(Order).filter(Order.id == secondary_order_id).with_for_update().first()
        if not primary or not secondary:
            raise ValueError("ไม่พบบิลที่ต้องการรวม")
        if primary.status != OrderStatus.OPEN or secondary.status != OrderStatus.OPEN:
            raise ValueError("รวมได้เฉพาะบิลที่ยังเปิดอยู่")
        if not primary.table_id or not secondary.table_id:
            raise ValueError("รวมได้เฉพาะออเดอร์แบบ dine-in")

        moved_item_ids = []
        for item in secondary.items:
            item.order_id = primary.id
            moved_item_ids.append(item.id)
        db.flush()
        OrderService._recalculate_order_totals(db, primary)
        secondary.status = OrderStatus.CANCELLED
        secondary.closed_at = datetime.now(timezone.utc)
        source = db.query(Table).filter(Table.current_order_id == secondary.id).with_for_update().first()
        if source:
            source.current_order_id = None
            source.status = TableStatus.VACANT
        primary_table = db.query(Table).filter(Table.current_order_id == primary.id).first()
        if primary_table:
            primary_table.status = TableStatus.OCCUPIED
        db.add(AuditLog(
            user_id=user_id,
            action="MERGE_ORDERS",
            target_type="Order",
            target_id=primary.id,
            details_json=json.dumps({"secondary_order_id": secondary.id, "moved_item_ids": moved_item_ids}, ensure_ascii=False),
            timestamp=datetime.now(timezone.utc)
        ))
        db.commit()
        db.refresh(primary)
        return primary

    @staticmethod
    def transfer_order(db: Session, order_id: int, target_table_id: int, user_id: int) -> Order:
        """Move an open dine-in order atomically to a vacant table and audit it."""
        TableService._require_operation_role(db, user_id)
        order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
        target = db.query(Table).filter(Table.id == target_table_id).with_for_update().first()
        if not order or not target:
            raise ValueError("ไม่พบออเดอร์หรือโต๊ะปลายทาง")
        if order.status != "OPEN" and getattr(order.status, "value", order.status) != "OPEN":
            raise ValueError("ย้ายได้เฉพาะบิลที่ยังเปิดอยู่")
        if target.current_order_id and target.current_order_id != order.id:
            raise ValueError("โต๊ะปลายทางมีออเดอร์อยู่แล้ว")
        source = db.query(Table).filter(Table.current_order_id == order.id).with_for_update().first()
        old_table_id = source.id if source else order.table_id
        if source and source.id != target.id:
            source.current_order_id = None
            source.status = TableStatus.VACANT
        order.table_id = target.id
        target.current_order_id = order.id
        target.status = TableStatus.OCCUPIED
        db.add(AuditLog(
            user_id=user_id,
            action="TRANSFER_ORDER_TABLE",
            target_type="Order",
            target_id=order.id,
            details_json=json.dumps({"from_table_id": old_table_id, "to_table_id": target.id}, ensure_ascii=False),
            timestamp=datetime.now(timezone.utc)
        ))
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def get_tables(db: Session, zone: Optional[str] = None) -> List[Table]:
        query = db.query(Table)
        if zone:
            query = query.filter(Table.zone == zone)
        return query.order_by(Table.table_number.asc()).all()

    @staticmethod
    def get_table_by_id(db: Session, table_id: int) -> Optional[Table]:
        return db.query(Table).filter(Table.id == table_id).first()

    @staticmethod
    def get_zones(db: Session) -> List[str]:
        results = db.query(Table.zone).distinct().all()
        return [r[0] for r in results if r[0]]

    @staticmethod
    def create_table(
        db: Session,
        table_number: str,
        capacity: int = 4,
        zone: str = "Indoor"
    ) -> Table:
        t_res = Validator.validate_table_number(table_number)
        if not t_res.is_valid:
            raise ValueError(t_res.error)
        clean_tbl = t_res.value

        c_res = Validator.validate_integer(capacity, field_name="จำนวนที่นั่ง", min_val=1, max_val=50)
        if not c_res.is_valid:
            raise ValueError(c_res.error)

        z_res = Validator.validate_required_text(zone, field_name="โซนที่นั่ง", min_len=1, max_len=50)
        if not z_res.is_valid:
            raise ValueError(z_res.error)

        existing = db.query(Table).filter(Table.table_number == clean_tbl).first()
        if existing:
            raise ValueError(f"โต๊ะหมายเลข {clean_tbl} มีอยู่ในระบบแล้ว")
        
        table = Table(
            table_number=clean_tbl,
            capacity=c_res.value,
            zone=z_res.value,
            status=TableStatus.VACANT
        )
        db.add(table)
        db.commit()
        db.refresh(table)
        return table

    @staticmethod
    def update_table(
        db: Session,
        table_id: int,
        table_number: str,
        capacity: int,
        zone: str
    ) -> Optional[Table]:
        t_res = Validator.validate_table_number(table_number)
        if not t_res.is_valid:
            raise ValueError(t_res.error)
        clean_tbl = t_res.value

        c_res = Validator.validate_integer(capacity, field_name="จำนวนที่นั่ง", min_val=1, max_val=50)
        if not c_res.is_valid:
            raise ValueError(c_res.error)

        z_res = Validator.validate_required_text(zone, field_name="โซนที่นั่ง", min_len=1, max_len=50)
        if not z_res.is_valid:
            raise ValueError(z_res.error)

        table = db.query(Table).filter(Table.id == table_id).first()
        if not table:
            return None

        # Check unique if changed
        if table.table_number != clean_tbl:
            existing = db.query(Table).filter(Table.table_number == clean_tbl).first()
            if existing:
                raise ValueError(f"โต๊ะหมายเลข {clean_tbl} มีอยู่ในระบบแล้ว")

        table.table_number = clean_tbl
        table.capacity = c_res.value
        table.zone = z_res.value
        db.commit()
        db.refresh(table)
        return table

    @staticmethod
    def delete_table(db: Session, table_id: int) -> bool:
        table = db.query(Table).filter(Table.id == table_id).first()
        if not table:
            return False
        # Do not delete if currently occupied
        if table.status == TableStatus.OCCUPIED:
            raise ValueError("ไม่สามารถลบโต๊ะที่มีลูกค้าใช้งานอยู่ได้")
        db.delete(table)
        db.commit()
        return True
