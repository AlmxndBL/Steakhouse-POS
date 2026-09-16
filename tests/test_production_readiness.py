import os
import unittest
from uuid import uuid4

from database.connection import SessionLocal, DATABASE_URL
from database.models import OrderType, Ingredient, MenuItem, Table, TableStatus, User
from services.order_service import OrderService
from services.backup_service import BackupService
from services.bom_engine import BOMEngine
from services.printer_service import PrinterService

class TestProductionReadiness(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.user_id = self.db.query(User).filter_by(username="owner").one().id
        self.assertIsNotNone(self.user_id, "Seeded owner account is required")
        # Keep these formatting/precision tests independent from stock consumed
        # by earlier tests while exercising the real receive-stock path.
        for ingredient in self.db.query(Ingredient).all():
            current = sum(float(lot.remaining_quantity) for lot in ingredient.lots if not lot.is_depleted)
            if current < 1000.0:
                BOMEngine.receive_stock(
                    self.db, ingredient.id, f"TEST-{ingredient.id}", 1000.0 - current,
                    float(ingredient.cost_per_unit or 0), None, user_id=self.user_id
                )

    def tearDown(self):
        self.db.close()

    def test_database_backup_service(self):
        """Test that BackupService creates a PostgreSQL custom-format backup."""
        backup_file = BackupService.create_backup(database_url=DATABASE_URL)
        self.assertTrue(os.path.exists(backup_file))
        self.assertGreater(os.path.getsize(backup_file), 0)

        backups = BackupService.list_backups()
        self.assertGreater(len(backups), 0)
        self.assertEqual(backups[0]["filepath"], backup_file)

    def test_printer_service_receipt_and_kitchen_chit(self):
        """Test formatting customer receipt and kitchen ticket chits."""
        table = Table(
            table_number=f"PRINT_{uuid4().hex[:8]}", capacity=2,
            zone="Test", status=TableStatus.VACANT,
        )
        self.db.add(table)
        self.db.commit()
        order = OrderService.create_or_get_open_order(
            self.db, table_id=table.id, order_type=OrderType.DINE_IN,
            customer_name=table.table_number, user_id=self.user_id
        )
        # Add item
        menu = self.db.query(MenuItem).filter_by(code="STK001").one()
        OrderService.add_item_to_order(self.db, order_id=order.id, menu_item_id=menu.id, qty=2)
        
        # Test Kitchen Chit formatting
        chit_text = PrinterService.format_kitchen_chit(order)
        self.assertIn("ใบสั่งเข้าครัว", chit_text)
        self.assertIn(table.table_number, chit_text)
        self.assertIn("x2", chit_text)

        # Checkout order
        paid_order = OrderService.checkout_order(
            self.db, order_id=order.id, payment_method="เงินสด (CASH)", discount_amount=50.0,
            user_id=self.user_id
        )

        # Test Customer Receipt formatting
        receipt_text = PrinterService.format_customer_receipt(paid_order)
        self.assertIn("STEAKHOUSE & GRILL", receipt_text)
        self.assertIn("ราคารวม (Subtotal):", receipt_text)
        self.assertIn("ส่วนลด (Discount):", receipt_text)
        self.assertIn("Service Charge (10%):", receipt_text)
        self.assertIn("ภาษีมูลค่าเพิ่ม VAT (7%):", receipt_text)
        self.assertIn("ยอดสุทธิชำระ (TOTAL):", receipt_text)

    def test_strict_financial_decimal_precision(self):
        """Test that OrderService calculation maintains strict precision without floating-point errors."""
        order = OrderService.create_or_get_open_order(
            self.db, table_id=None, order_type=OrderType.TAKEAWAY,
            customer_name="ลูกค้า Takeaway", user_id=self.user_id
        )
        # Add 3 items
        menu_ids = {
            item.code: item.id
            for item in self.db.query(MenuItem).filter(MenuItem.code.in_(["STK001", "SID001", "DRK001"]))
        }
        self.assertEqual(set(menu_ids), {"STK001", "SID001", "DRK001"})
        OrderService.add_item_to_order(self.db, order.id, menu_ids["STK001"], qty=1) # 450.0
        OrderService.add_item_to_order(self.db, order.id, menu_ids["SID001"], qty=1) # 89.0
        OrderService.add_item_to_order(self.db, order.id, menu_ids["DRK001"], qty=1) # 35.0
        
        self.db.refresh(order)
        expected_subtotal = 450.0 + 89.0 + 35.0 # 574.00
        self.assertEqual(float(order.subtotal), expected_subtotal)

        # 10% Service Charge on 574.00 = 57.40
        self.assertEqual(float(order.service_charge_amount), 57.40)

        # 7% VAT on (574.00 + 57.40 = 631.40) = 44.198 -> 44.20
        self.assertEqual(float(order.vat_amount), 44.20)

        # Net = 574.00 + 57.40 + 44.20 = 675.60
        self.assertEqual(float(order.net_amount), 675.60)

        # Checkout
        OrderService.checkout_order(
            self.db, order_id=order.id, payment_method="เงินสด (CASH)", discount_amount=0.0,
            user_id=self.user_id
        )

if __name__ == '__main__':
    unittest.main()
