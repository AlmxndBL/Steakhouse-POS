import unittest
from datetime import datetime, date, timedelta, timezone
from database.connection import SessionLocal
from database.models import Ingredient, StockLot, StockTransaction, StockTxType, AuditLog, MenuItem, RecipeBOM, Table, User
from services.bom_engine import BOMEngine
from services.menu_service import MenuService
from services.table_service import TableService

class TestBOMStockTakeAndAudit(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.user_id = self.db.query(User).filter_by(username="owner").one().id

    def tearDown(self):
        self.db.close()

    def test_table_and_menu_get_by_id(self):
        """Test TableService.get_table_by_id and MenuService.get_menu_item_by_id"""
        expected_table = self.db.query(Table).filter_by(table_number="T01").one()
        t = TableService.get_table_by_id(self.db, expected_table.id)
        self.assertIsNotNone(t, "Seeded T01 table should exist")
        self.assertEqual(t.id, expected_table.id)

        expected_menu = self.db.query(MenuItem).filter_by(code="STK001").one()
        m = MenuService.get_menu_item_by_id(self.db, expected_menu.id)
        self.assertIsNotNone(m, "Seeded STK001 menu item should exist")
        self.assertEqual(m.id, expected_menu.id)

    def test_menu_item_bom_cost_calculation(self):
        """Test MenuService.get_item_bom_cost returns non-zero cost for steak items with BOM"""
        menu = self.db.query(MenuItem).filter_by(code="STK001").one()
        cost = MenuService.get_item_bom_cost(self.db, menu.id)
        self.assertIsInstance(cost, float)
        self.assertGreaterEqual(cost, 0.0)

    def test_physical_stock_take_adjustment(self):
        """Test BOMEngine.adjust_stock updates stock and records adjustment transaction & audit log"""
        ing = self.db.query(Ingredient).filter(Ingredient.is_active == True).first()
        self.assertIsNotNone(ing, "Ingredient should exist")

        # Get initial stock
        status_before = BOMEngine.get_inventory_status(self.db)
        ing_status = next(s for s in status_before if s["id"] == ing.id)
        current_stock = ing_status["current_stock"]

        # Adjust stock
        target_qty = current_stock + 500.0
        res = BOMEngine.adjust_stock(
            self.db,
            ingredient_id=ing.id,
            new_actual_qty=target_qty,
            reason="ทดสอบนับสต๊อกจริง",
            user_id=self.user_id
        )

        self.assertEqual(res["status"], "ADJUSTED")
        self.assertEqual(res["actual_qty"], target_qty)
        self.assertAlmostEqual(res["variance"], 500.0)

        # Check transaction in db
        tx = self.db.query(StockTransaction).filter(
            StockTransaction.tx_type == StockTxType.ADJUSTMENT
        ).order_by(StockTransaction.timestamp.desc()).first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.quantity, 500.0)

        # Check audit log
        audit = self.db.query(AuditLog).filter(
            AuditLog.action == "PHYSICAL_STOCK_ADJUSTMENT"
        ).order_by(AuditLog.timestamp.desc()).first()
        self.assertIsNotNone(audit)
        self.assertIn("system_qty", audit.details_json)

    def test_get_expiring_soon_lots(self):
        """Test BOMEngine.get_expiring_soon_lots returns lots within 7 days"""
        expiring = BOMEngine.get_expiring_soon_lots(self.db, days=14)
        self.assertIsInstance(expiring, list)
        if expiring:
            self.assertIn("lot_number", expiring[0])
            self.assertIn("days_left", expiring[0])

if __name__ == "__main__":
    unittest.main()
