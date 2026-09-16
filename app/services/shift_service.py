import json
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from database.models import AuditLog, Order, OrderStatus, User


class ShiftService:
    """Small classroom shift ledger backed by the existing audit log table."""

    @staticmethod
    def start_shift(db: Session, user_id: int, opening_float: float = 0.0) -> AuditLog:
        if opening_float < 0:
            raise ValueError("เงินทอนเริ่มต้นต้องไม่ติดลบ")
        event = AuditLog(
            user_id=user_id,
            action="SHIFT_START",
            target_type="Shift",
            details_json=json.dumps({"opening_float": round(opening_float, 2)}, ensure_ascii=False),
            timestamp=datetime.now(timezone.utc),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def close_shift(db: Session, user_id: int, actual_cash: float, reason: str = "") -> dict:
        if actual_cash < 0:
            raise ValueError("ยอดเงินจริงต้องไม่ติดลบ")
        start = db.query(AuditLog).filter(
            AuditLog.action == "SHIFT_START"
        ).order_by(AuditLog.timestamp.desc()).first()
        if not start:
            raise ValueError("ยังไม่มีการเปิดกะ")
        start_data = json.loads(start.details_json or "{}")
        opening_float = Decimal(str(start_data.get("opening_float", 0)))
        cash_orders = db.query(Order).filter(
            Order.status == OrderStatus.PAID,
            Order.payment_method.ilike("%CASH%"),
            Order.closed_at >= start.timestamp,
        ).all()
        sales_cash = sum((Decimal(str(order.net_amount or 0)) for order in cash_orders), Decimal("0"))
        expected_cash = opening_float + sales_cash
        actual = Decimal(str(actual_cash))
        result = {
            "opening_float": float(opening_float),
            "cash_sales": float(sales_cash),
            "expected_cash": float(expected_cash),
            "actual_cash": float(actual),
            "variance": float(actual - expected_cash),
        }
        db.add(AuditLog(
            user_id=user_id,
            action="SHIFT_END",
            target_type="Shift",
            details_json=json.dumps({**result, "reason": reason}, ensure_ascii=False),
            timestamp=datetime.now(timezone.utc),
        ))
        db.commit()
        return result
