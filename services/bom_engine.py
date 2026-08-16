from datetime import datetime, date, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy import nullslast
from sqlalchemy.orm import Session
from database.models import (
    Order, OrderItem, RecipeBOM, Ingredient, StockLot, StockTransaction, StockTxType, AuditLog
)

class BOMEngine:
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

                if remaining_to_deduct > Decimal('0'):
                    # Not enough stock in active lots. We will overdraft the latest active lot.
                    latest_lot = lots[-1] if lots else None
                    if latest_lot:
                        latest_lot.remaining_quantity -= remaining_to_deduct
                        latest_lot.is_depleted = True
                        st_tx_overdraft = StockTransaction(
                            lot_id=latest_lot.id,
                            order_id=order.id,
                            tx_type=StockTxType.SALE_OUT,
                            quantity=-float(remaining_to_deduct),
                            reason=f"OVERDRAFT ขายตามบิล #{order.order_number}",
                            user_id=user_id,
                            timestamp=datetime.now(timezone.utc)
                        )
                        db.add(st_tx_overdraft)
                        audit_overdraft = AuditLog(
                            user_id=user_id,
                            action="STOCK_OVERDRAFT",
                            target_type="Ingredient",
                            target_id=ingredient_id,
                            details_json=f'{{"order": "{order.order_number}", "overdraft_qty": {float(remaining_to_deduct)}}}'
                        )
                        db.add(audit_overdraft)

        return True

    @staticmethod
    def record_wastage(db: Session, ingredient_id: int, qty: float, reason: str, user_id: int) -> bool:
        """
        Records ingredient wastage (เนื้อเสีย / ทำหล่น) using FIFO/FEFO deduction from active lots.
        """
        lots = db.query(StockLot).filter(
            StockLot.ingredient_id == ingredient_id,
            StockLot.remaining_quantity > 0,
            StockLot.is_depleted == False
        ).order_by(
            nullslast(StockLot.expiry_date.asc()),
            StockLot.received_date.asc()
        ).all()

        remaining_to_deduct = Decimal(str(qty))
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
                reason=reason or "ตัดของเสีย (Wastage)",
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
            details_json=f'{{"qty": {qty}, "reason": "{reason}"}}'
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
        ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        if not ingredient:
            raise ValueError(f"Ingredient ID {ingredient_id} not found")

        # Create StockLot
        new_lot = StockLot(
            ingredient_id=ingredient_id,
            lot_number=lot_number,
            initial_quantity=Decimal(str(qty)),
            remaining_quantity=Decimal(str(qty)),
            unit_cost=Decimal(str(unit_cost)),
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
    def get_inventory_status(db: Session) -> List[Dict[str, Any]]:
        """
        Calculates total remaining stock per ingredient and flags low stock alerts.
        """
        ingredients = db.query(Ingredient).filter(Ingredient.is_active == True).all()
        result = []
        for ing in ingredients:
            total_stock = sum(lot.remaining_quantity for lot in ing.lots if not lot.is_depleted)
            status = "NORMAL"
            if total_stock == 0:
                status = "OUT_OF_STOCK"
            elif total_stock <= ing.min_stock_alert:
                status = "LOW_STOCK"
            
            result.append({
                "id": ing.id,
                "code": ing.code,
                "name": ing.name,
                "unit": ing.unit,
                "min_stock_alert": ing.min_stock_alert,
                "current_stock": total_stock,
                "cost_per_unit": ing.cost_per_unit,
                "status": status,
                "active_lots_count": sum(1 for lot in ing.lots if not lot.is_depleted)
            })
        return result
