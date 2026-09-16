from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy import nullslast
from sqlalchemy.orm import Session
from database.models import (
    Order, OrderItem, RecipeBOM, Ingredient, StockLot, StockTransaction, StockTxType, AuditLog
)
from utils.validators import Validator

class BOMEngine:
    @staticmethod
    def get_inventory_task_center(db: Session, expiring_days: int = 7) -> Dict[str, Any]:
        """Aggregate actionable inventory work for the classroom dashboard."""
        inventory = BOMEngine.get_inventory_status(db)
        expiring = BOMEngine.get_expiring_soon_lots(db, days=expiring_days)
        low_stock = [item for item in inventory if item["status"] in {"LOW_STOCK", "OUT_OF_STOCK"}]
        purchase_suggestions = [
            {
                "ingredient_id": item["id"],
                "ingredient_name": item["name"],
                "unit": item["unit"],
                "current_stock": item["current_stock"],
                "suggested_quantity": max(item["min_stock_alert"] - item["current_stock"], item["min_stock_alert"]),
            }
            for item in low_stock
        ]
        anomaly_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        wastage_rows = db.query(StockTransaction, Ingredient).join(
            StockLot, StockLot.id == StockTransaction.lot_id
        ).join(Ingredient, Ingredient.id == StockLot.ingredient_id).filter(
            StockTransaction.tx_type == StockTxType.WASTAGE,
            StockTransaction.timestamp >= anomaly_cutoff,
        ).all()
        wastage_totals = {}
        for transaction, ingredient in wastage_rows:
            wastage_totals.setdefault(ingredient.id, {"ingredient_id": ingredient.id, "ingredient_name": ingredient.name, "unit": ingredient.unit, "quantity": 0.0})
            wastage_totals[ingredient.id]["quantity"] += abs(float(transaction.quantity))
        wastage_anomalies = [
            row for row in wastage_totals.values()
            if row["quantity"] >= 2 * float(db.query(Ingredient.min_stock_alert).filter(Ingredient.id == row["ingredient_id"]).scalar() or 0)
        ]
        return {
            "low_stock": low_stock,
            "expiring_lots": expiring,
            "purchase_suggestions": purchase_suggestions,
            "wastage_anomalies": wastage_anomalies,
            "counts": {
                "low_stock": len(low_stock),
                "expiring_lots": len(expiring),
                "wastage_anomalies": len(wastage_anomalies),
                "pending_actions": len(low_stock) + len(expiring) + len(wastage_anomalies),
            },
        }

    @staticmethod
    def deduct_stock_for_order(db: Session, order: Order, user_id: int) -> bool:
        """
        Deducts stock for all items in an order using BOM & FIFO/FEFO rules.
        Must be executed within an active database transaction.
        """
        for item in order.items:
            boms = db.query(RecipeBOM).filter(RecipeBOM.menu_item_id == item.menu_item_id).all()
            for bom in boms:
                needed_qty = Decimal(str(bom.quantity_required)) * Decimal(str(item.quantity))
                ingredient_id = bom.ingredient_id
                
                # Fetch active lots sorted by FEFO (Expiry Date nulls last) then FIFO (Received Date)
                lots = db.query(StockLot).filter(
                    StockLot.ingredient_id == ingredient_id,
                    StockLot.remaining_quantity > 0,
                    StockLot.is_depleted == False
                ).order_by(
                    nullslast(StockLot.expiry_date.asc()),
                    StockLot.received_date.asc(),
                    StockLot.id.asc()
                ).all()

                remaining_to_deduct = needed_qty
                available_qty = sum((Decimal(str(lot.remaining_quantity)) for lot in lots), Decimal("0"))
                if available_qty < needed_qty:
                    raise ValueError(
                        f"วัตถุดิบไม่พอสำหรับออเดอร์ #{order.order_number} "
                        f"(ingredient_id={ingredient_id}, ต้องการ {needed_qty}, มี {available_qty})"
                    )
                for lot in lots:
                    if remaining_to_deduct <= Decimal('0'):
                        break
                    
                    deduct_from_lot = min(lot.remaining_quantity, remaining_to_deduct)
                    lot.remaining_quantity -= deduct_from_lot
                    if lot.remaining_quantity <= Decimal('0'):
                        lot.is_depleted = True
                    
                    remaining_to_deduct -= deduct_from_lot

                    # Create StockTransaction
                    st_tx = StockTransaction(
                        lot_id=lot.id,
                        order_id=order.id,
                        tx_type=StockTxType.SALE_OUT,
                        quantity=-float(deduct_from_lot),
                        reason=f"ขายตามบิล #{order.order_number}",
                        user_id=user_id,
                        timestamp=datetime.now(timezone.utc)
                    )
                    db.add(st_tx)

        return True

    @staticmethod
    def record_wastage(db: Session, ingredient_id: int, qty: float, reason: str, user_id: int) -> bool:
        """
        Records ingredient wastage (เนื้อเสีย / ทำหล่น) using FIFO/FEFO deduction from active lots.
        """
        q_res = Validator.validate_float(qty, field_name="จำนวนของเสีย", min_val=0.001, max_val=1000000.0)
        if not q_res.is_valid:
            raise ValueError(q_res.error)

        r_res = Validator.validate_required_text(reason, field_name="เหตุผลของเสีย", min_len=2, max_len=255)
        if not r_res.is_valid:
            raise ValueError(r_res.error)

        lots = db.query(StockLot).filter(
            StockLot.ingredient_id == ingredient_id,
            StockLot.remaining_quantity > 0,
            StockLot.is_depleted == False
        ).order_by(
            nullslast(StockLot.expiry_date.asc()),
            StockLot.received_date.asc()
        ).all()

        remaining_to_deduct = Decimal(str(q_res.value))
        for lot in lots:
            if remaining_to_deduct <= Decimal('0'):
                break
            
            deduct_from_lot = min(lot.remaining_quantity, remaining_to_deduct)
            lot.remaining_quantity -= deduct_from_lot
            if lot.remaining_quantity <= Decimal('0'):
                lot.is_depleted = True
            
            remaining_to_deduct -= deduct_from_lot

            st_tx = StockTransaction(
                lot_id=lot.id,
                tx_type=StockTxType.WASTAGE,
                quantity=-float(deduct_from_lot),
                reason=r_res.value,
                user_id=user_id,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(st_tx)

        # Audit Log
        audit = AuditLog(
            user_id=user_id,
            action="RECORD_WASTAGE",
            target_type="Ingredient",
            target_id=ingredient_id,
            details_json=f'{{"qty": {q_res.value}, "reason": "{r_res.value}"}}'
        )
        db.add(audit)
        db.commit()
        return True

    @staticmethod
    def receive_stock(db: Session, ingredient_id: int, lot_number: str, qty: float, unit_cost: float, expiry_date: Optional[date], user_id: int) -> StockLot:
        """
        Records receiving new stock (Purchase In).
        Creates a new StockLot and records a StockTransaction.
        """
        q_res = Validator.validate_float(qty, field_name="จำนวนที่รับเข้า", min_val=0.001, max_val=1000000.0)
        if not q_res.is_valid:
            raise ValueError(q_res.error)

        c_res = Validator.validate_float(unit_cost, field_name="ต้นทุนต่อหน่วย", min_val=0.0, max_val=1000000.0)
        if not c_res.is_valid:
            raise ValueError(c_res.error)

        lot_clean = str(lot_number).strip() if lot_number else f"LOT-{datetime.now().strftime('%Y%m%d%H%M')}"
        if not lot_clean:
            lot_clean = f"LOT-{datetime.now().strftime('%Y%m%d%H%M')}"

        ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        if not ingredient:
            raise ValueError(f"Ingredient ID {ingredient_id} not found")

        # Create StockLot
        new_lot = StockLot(
            ingredient_id=ingredient_id,
            lot_number=lot_clean,
            initial_quantity=Decimal(str(q_res.value)),
            remaining_quantity=Decimal(str(q_res.value)),
            unit_cost=Decimal(str(c_res.value)),
            expiry_date=expiry_date,
            received_date=datetime.now(timezone.utc),
            is_depleted=False
        )
        db.add(new_lot)
        db.flush() # To get lot id

        # Record Transaction
        st_tx = StockTransaction(
            lot_id=new_lot.id,
            tx_type=StockTxType.PURCHASE_IN,
            quantity=Decimal(str(qty)),
            reason="รับวัตถุดิบเข้าคลัง",
            user_id=user_id,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(st_tx)

        # Update latest unit cost
        ingredient.cost_per_unit = Decimal(str(unit_cost))

        # Audit Log
        audit = AuditLog(
            user_id=user_id,
            action="RECEIVE_STOCK",
            target_type="Ingredient",
            target_id=ingredient_id,
            details_json=f'{{"lot": "{lot_number}", "qty": {qty}, "cost": {unit_cost}}}'
        )
        db.add(audit)
        db.commit()
        db.refresh(new_lot)
        return new_lot

    @staticmethod
    def adjust_stock(db: Session, ingredient_id: int, new_actual_qty: float, reason: str, user_id: int) -> Dict[str, Any]:
        """
        Physical Stock Take: Adjusts system stock to match physically counted stock.
        Records a StockTransaction of type ADJUSTMENT and logs the variance.
        """
        ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        if not ingredient:
            raise ValueError(f"ไม่พบวัตถุดิบ ID {ingredient_id}")

        active_lots = db.query(StockLot).filter(
            StockLot.ingredient_id == ingredient_id,
            StockLot.remaining_quantity > 0,
            StockLot.is_depleted == False
        ).order_by(StockLot.received_date.desc()).all()

        current_system_qty = sum(float(l.remaining_quantity) for l in active_lots)
        variance = float(new_actual_qty) - current_system_qty

        if abs(variance) < 1e-4:
            return {
                "ingredient_id": ingredient_id,
                "ingredient_name": ingredient.name,
                "system_qty": current_system_qty,
                "actual_qty": new_actual_qty,
                "variance": 0.0,
                "status": "MATCHED"
            }

        target_lot = active_lots[0] if active_lots else None
        if not target_lot:
            # Create an adjustment lot if no active lots exist
            target_lot = StockLot(
                ingredient_id=ingredient_id,
                lot_number=f"ADJ-{datetime.now().strftime('%Y%m%d%H%M')}",
                initial_quantity=Decimal(str(max(0.0, new_actual_qty))),
                remaining_quantity=Decimal(str(max(0.0, new_actual_qty))),
                unit_cost=ingredient.cost_per_unit or Decimal('0'),
                expiry_date=None,
                received_date=datetime.now(timezone.utc),
                is_depleted=False
            )
            db.add(target_lot)
            db.flush()
        else:
            new_lot_qty = float(target_lot.remaining_quantity) + variance
            target_lot.remaining_quantity = Decimal(str(max(0.0, new_lot_qty)))
            if target_lot.remaining_quantity <= 0:
                target_lot.is_depleted = True

        st_tx = StockTransaction(
            lot_id=target_lot.id,
            tx_type=StockTxType.ADJUSTMENT,
            quantity=Decimal(str(variance)),
            reason=reason or f"ปรับปรุงยอดจากการนับสต๊อกจริง (Physical Count: {new_actual_qty} {ingredient.unit})",
            user_id=user_id,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(st_tx)

        audit = AuditLog(
            user_id=user_id,
            action="PHYSICAL_STOCK_ADJUSTMENT",
            target_type="Ingredient",
            target_id=ingredient_id,
            details_json=f'{{"system_qty": {current_system_qty}, "actual_qty": {new_actual_qty}, "variance": {variance}, "reason": "{reason}"}}'
        )
        db.add(audit)
        db.commit()

        return {
            "ingredient_id": ingredient_id,
            "ingredient_name": ingredient.name,
            "system_qty": current_system_qty,
            "actual_qty": new_actual_qty,
            "variance": variance,
            "status": "ADJUSTED"
        }

    @staticmethod
    def get_inventory_status(db: Session) -> List[Dict[str, Any]]:
        """
        Calculates total remaining stock per ingredient and flags low stock alerts.
        """
        ingredients = db.query(Ingredient).filter(Ingredient.is_active == True).all()
        result = []
        for ing in ingredients:
            total_stock = sum(float(lot.remaining_quantity) for lot in ing.lots if not lot.is_depleted)
            status = "NORMAL"
            if total_stock == 0:
                status = "OUT_OF_STOCK"
            elif total_stock <= float(ing.min_stock_alert):
                status = "LOW_STOCK"
            
            result.append({
                "id": ing.id,
                "code": ing.code,
                "name": ing.name,
                "unit": ing.unit,
                "min_stock_alert": float(ing.min_stock_alert),
                "current_stock": total_stock,
                "cost_per_unit": float(ing.cost_per_unit),
                "status": status,
                "active_lots_count": sum(1 for lot in ing.lots if not lot.is_depleted)
            })
        return result

    @staticmethod
    def get_expiring_soon_lots(db: Session, days: int = 7) -> List[Dict[str, Any]]:
        """
        Returns active lots that are expiring within the specified number of days.
        """
        threshold_date = date.today() + timedelta(days=days)
        lots = db.query(StockLot).filter(
            StockLot.is_depleted == False,
            StockLot.remaining_quantity > 0,
            StockLot.expiry_date != None,
            StockLot.expiry_date <= threshold_date
        ).order_by(StockLot.expiry_date.asc()).all()

        results = []
        today = date.today()
        for lot in lots:
            days_left = (lot.expiry_date - today).days if lot.expiry_date else 999
            results.append({
                "lot_id": lot.id,
                "lot_number": lot.lot_number,
                "ingredient_name": lot.ingredient.name if lot.ingredient else "-",
                "unit": lot.ingredient.unit if lot.ingredient else "",
                "remaining_quantity": float(lot.remaining_quantity),
                "expiry_date": lot.expiry_date.strftime("%Y-%m-%d") if lot.expiry_date else "-",
                "days_left": days_left,
                "is_expired": days_left < 0
            })
        return results
