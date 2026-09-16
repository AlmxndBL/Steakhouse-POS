import unittest
import json
from database.connection import SessionLocal
from database.models import Order, OrderStatus, OrderType, MenuItem, Table, TableStatus, User
from services.order_service import OrderService
from services.receipt_service import ReceiptService

class TestPOSOrderFlow(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.user_id = self.db.query(User.id).filter_by(username="owner").one().id

    def tearDown(self):
        self.db.close()

    def test_complete_dine_in_order_lifecycle(self):
        """Test full lifecycle: open table -> add steak item -> apply discount -> checkout -> generate receipt."""
        table = self.db.query(Table).filter(Table.status == TableStatus.VACANT).first()
        if not table:
            # Create a test table if none vacant
            table = Table(table_number="T_TEST_FLOW", capacity=4, zone="Indoor", status=TableStatus.VACANT)
            self.db.add(table)
            self.db.commit()
            self.db.refresh(table)
        
        # 1. Create Dine-In Order
        order = OrderService.create_or_get_open_order(
            self.db,
            table_id=table.id,
            order_type=OrderType.DINE_IN,
            customer_name=f"โต๊ะ {table.table_number}",
            user_id=self.user_id
        )
        self.assertIsNotNone(order.id)
        self.assertEqual(order.status, OrderStatus.OPEN)
        
        # Verify table status changed to OCCUPIED
        self.db.refresh(table)
        self.assertEqual(table.status, TableStatus.OCCUPIED)

        # 2. Add Ribeye Steak with Modifiers
        menu_item = self.db.query(MenuItem).filter(MenuItem.code == "STK001").first()
        self.assertIsNotNone(menu_item)
        
        mod_json = json.dumps({"doneness": "Medium Rare", "sauce": "ซอสพริกไทยดำ"}, ensure_ascii=False)
        item = OrderService.add_item_to_order(
            self.db,
            order_id=order.id,
            menu_item_id=menu_item.id,
            qty=2,
            options_json=mod_json
        )
        self.assertEqual(item.quantity, 2)
        self.assertEqual(float(item.price_per_unit), 450.0)

        # 3. Checkout (Subtotal = 900, Discount = 100, SC 10% = 80, VAT 7% = 61.60, Net = 941.60)
        discount = 100.0
        updated_order = OrderService.checkout_order(
            self.db,
            order_id=order.id,
            payment_method="QR PromptPay",
            discount_amount=discount,
            user_id=self.user_id
        )
        self.assertEqual(updated_order.status, OrderStatus.PAID)
        self.assertEqual(float(updated_order.subtotal), 900.0)
        self.assertEqual(float(updated_order.discount_amount), 100.0)
        
        # (900 - 100) = 800. Service Charge 10% = 80. Subtotal after SC = 880. VAT 7% = 61.60. Total = 941.60
        self.assertAlmostEqual(float(updated_order.service_charge_amount), 80.0, places=2)
        self.assertAlmostEqual(float(updated_order.vat_amount), 61.60, places=2)
        self.assertAlmostEqual(float(updated_order.net_amount), 941.60, places=2)

        # 4. Generate E-Receipt Image
        receipt_payload = {
            "order_number": updated_order.order_number,
            "created_at": updated_order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "order_type": updated_order.order_type.value,
            "table_or_customer": updated_order.customer_name,
            "items": [{"name": menu_item.name, "qty": 2, "price": 450.0, "total": 900.0}],
            "subtotal": float(updated_order.subtotal),
            "discount": float(updated_order.discount_amount),
            "net_total": float(updated_order.net_amount),
            "payment_method": updated_order.payment_method
        }
        b64_img = ReceiptService.generate_ereceipt_image_base64(receipt_payload)
        self.assertTrue(len(b64_img) > 100, "Receipt base64 image should be generated successfully")

        # 5. Table Released
        self.db.refresh(table)
        self.assertEqual(table.status, TableStatus.VACANT)

if __name__ == '__main__':
    unittest.main()
