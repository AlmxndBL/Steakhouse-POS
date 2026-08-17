import os
import unittest
from database.connection import SessionLocal, DB_PATH
from database.models import OrderType
from services.order_service import OrderService
from services.backup_service import BackupService
from services.printer_service import PrinterService

class TestProductionReadiness(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_database_backup_service(self):
        """Test that BackupService successfully creates a valid SQLite backup and lists it."""
        backup_file = BackupService.create_backup(db_path=DB_PATH)
        self.assertTrue(os.path.exists(backup_file))
        self.assertGreater(os.path.getsize(backup_file), 0)

        backups = BackupService.list_backups()
        self.assertGreater(len(backups), 0)
        self.assertEqual(backups[0]["filepath"], backup_file)

    def test_printer_service_receipt_and_kitchen_chit(self):
        """Test formatting customer receipt and kitchen ticket chits."""
        # Create an open order
        order = OrderService.create_or_get_open_order(
            self.db, table_id=1, order_type=OrderType.DINE_IN, customer_name="โต๊ะ T01", user_id=1
        )
        # Add item
        item = OrderService.add_item_to_order(self.db, order_id=order.id, menu_item_id=1, qty=2)
        
        # Test Kitchen Chit formatting
        chit_text = PrinterService.format_kitchen_chit(order)
        self.assertIn("ใบสั่งเข้าครัว", chit_text)
        self.assertIn("โต๊ะ T01", chit_text)
        self.assertIn("x2", chit_text)

        # Checkout order
        paid_order = OrderService.checkout_order(
            self.db, order_id=order.id, payment_method="เงินสด (CASH)", discount_amount=50.0, user_id=1
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
            self.db, table_id=None, order_type=OrderType.TAKEAWAY, customer_name="ลูกค้า Takeaway", user_id=1
        )
        # Add 3 items
        OrderService.add_item_to_order(self.db, order_id=order.id, menu_item_id=1, qty=1) # 450.0
        OrderService.add_item_to_order(self.db, order_id=order.id, menu_item_id=4, qty=1) # 89.0
        OrderService.add_item_to_order(self.db, order_id=order.id, menu_item_id=5, qty=1) # 35.0
        
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
            self.db, order_id=order.id, payment_method="เงินสด (CASH)", discount_amount=0.0, user_id=1
        )

if __name__ == '__main__':
    unittest.main()
