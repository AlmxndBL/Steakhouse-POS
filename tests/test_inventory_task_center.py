import unittest
from datetime import date, timedelta
from uuid import uuid4

from database.connection import SessionLocal
from database.models import AuditLog, Ingredient, StockLot, User
from services.bom_engine import BOMEngine


class TestInventoryTaskCenter(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.user_id = self.db.query(User).filter_by(username="owner").one().id

    def tearDown(self):
        self.db.close()

    def test_task_center_reports_low_stock_and_expiring_lot(self):
        suffix = uuid4().hex[:8]
        ingredient = Ingredient(
            code=f"TASK_{suffix}", name="Task center ingredient", unit="kg",
            min_stock_alert=10.0, cost_per_unit=2.0, is_active=True
        )
        self.db.add(ingredient)
        self.db.flush()
        self.db.add(StockLot(
            ingredient_id=ingredient.id, lot_number=f"LOT_{suffix}",
            initial_quantity=5.0, remaining_quantity=5.0, unit_cost=2.0,
            expiry_date=date.today() + timedelta(days=2), is_depleted=False
        ))
        self.db.commit()

        center = BOMEngine.get_inventory_task_center(self.db, expiring_days=7)
        self.assertGreaterEqual(center["counts"]["low_stock"], 1)
        self.assertGreaterEqual(center["counts"]["expiring_lots"], 1)
        self.assertGreaterEqual(center["counts"]["pending_actions"], 2)

    def test_receive_stock_creates_audited_positive_lot(self):
        ingredient = self.db.query(Ingredient).filter(Ingredient.is_active == True).first()
        lot = BOMEngine.receive_stock(
            self.db, ingredient.id, f"RECEIVE_{uuid4().hex[:8]}", 12.5, 3.25,
            date.today() + timedelta(days=30), user_id=self.user_id
        )
        self.assertEqual(float(lot.remaining_quantity), 12.5)
        self.assertGreater(float(lot.unit_cost), 0)
        audit = self.db.query(AuditLog).filter(
            AuditLog.action.in_(["RECEIVE_STOCK", "STOCK_RECEIVE"]),
            AuditLog.target_id == ingredient.id,
        ).order_by(AuditLog.id.desc()).first()
        self.assertIsNotNone(audit)

    def test_task_center_exposes_purchase_suggestion_and_wastage_anomaly(self):
        suffix = uuid4().hex[:8]
        ingredient = Ingredient(
            code=f"ANOM_{suffix}", name="Anomaly ingredient", unit="g",
            min_stock_alert=10.0, cost_per_unit=1.0, is_active=True
        )
        self.db.add(ingredient)
        self.db.flush()
        self.db.add(StockLot(
            ingredient_id=ingredient.id, lot_number=f"ANOM_LOT_{suffix}",
            initial_quantity=100.0, remaining_quantity=100.0,
            unit_cost=1.0, expiry_date=date.today() + timedelta(days=30), is_depleted=False
        ))
        self.db.commit()
        BOMEngine.record_wastage(self.db, ingredient.id, 25.0, "anomaly test", user_id=self.user_id)
        center = BOMEngine.get_inventory_task_center(self.db)
        self.assertTrue(any(row["ingredient_id"] == ingredient.id for row in center["wastage_anomalies"]))
        self.assertTrue(all(row["suggested_quantity"] > 0 for row in center["purchase_suggestions"]))


if __name__ == "__main__":
    unittest.main()
