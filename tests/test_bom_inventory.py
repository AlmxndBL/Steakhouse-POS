import unittest
from datetime import date, timedelta
from database.connection import SessionLocal
from database.models import Ingredient, StockLot, StockTransaction, StockTxType
from services.bom_engine import BOMEngine

class TestBOMInventory(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_stock_receipt_and_lot_creation(self):
        """Test receiving stock (Purchase In) creates a lot and updates remaining stock."""
        ing = self.db.query(Ingredient).filter(Ingredient.code == "ING001").first()
        self.assertIsNotNone(ing)
        
        initial_stock = sum(float(lot.remaining_quantity) for lot in ing.lots if not lot.is_depleted)
        lot_number = f"TEST-LOT-{date.today().strftime('%Y%m%d%H%M%S')}"
        received_qty = 500.0
        unit_cost = 1.35
        exp_date = date.today() + timedelta(days=30)
        
        lot = BOMEngine.receive_stock(self.db, ing.id, lot_number, received_qty, unit_cost, exp_date, user_id=1)
        self.assertIsNotNone(lot.id)
        self.assertEqual(float(lot.initial_quantity), received_qty)
        self.assertEqual(float(lot.remaining_quantity), received_qty)
        
        # Verify ingredient remaining lot stock increased
        self.db.refresh(ing)
        new_stock = sum(float(l.remaining_quantity) for l in ing.lots if not l.is_depleted)
        self.assertEqual(new_stock, initial_stock + received_qty)

    def test_record_wastage(self):
        """Test recording wastage deducts from active lots."""
        ing = self.db.query(Ingredient).filter(Ingredient.code == "ING004").first()
        self.assertIsNotNone(ing)
        
        initial_stock = sum(float(lot.remaining_quantity) for lot in ing.lots if not lot.is_depleted)
        wastage_qty = 50.0
        
        success = BOMEngine.record_wastage(self.db, ing.id, wastage_qty, reason="Spilled on floor", user_id=1)
        self.assertTrue(success)
        
        self.db.refresh(ing)
        new_stock = sum(float(l.remaining_quantity) for l in ing.lots if not l.is_depleted)
        self.assertEqual(new_stock, initial_stock - wastage_qty)

    def test_get_inventory_status(self):
        """Test getting inventory summary and stock status."""
        status_list = BOMEngine.get_inventory_status(self.db)
        self.assertGreater(len(status_list), 0)
        first_item = status_list[0]
        self.assertIn("code", first_item)
        self.assertIn("name", first_item)
        self.assertIn("current_stock", first_item)
        self.assertIn("status", first_item)
        self.assertIn(first_item["status"], ["NORMAL", "LOW_STOCK", "OUT_OF_STOCK"])

if __name__ == '__main__':
    unittest.main()
