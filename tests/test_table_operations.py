import unittest
from uuid import uuid4

from database.connection import SessionLocal
from database.models import User, UserRole, Table, TableStatus, OrderType, OrderStatus, MenuItem, AuditLog, Category
from services.order_service import OrderService
from services.table_service import TableService


class TestTableOperationAuthorization(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_kitchen_cannot_mutate_table_orders(self):
        kitchen = self.db.query(User).filter(User.role == UserRole.KITCHEN).first()
        self.assertIsNotNone(kitchen)
        with self.assertRaises(PermissionError):
            TableService._require_operation_role(self.db, kitchen.id)

    def test_cashier_can_mutate_table_orders(self):
        cashier = self.db.query(User).filter(User.role == UserRole.CASHIER).first()
        self.assertIsNotNone(cashier)
        TableService._require_operation_role(self.db, cashier.id)

    def test_transfer_moves_order_and_audits(self):
        suffix = uuid4().hex[:8]
        first = Table(table_number=f"AUTH_T1_{suffix}", capacity=2, zone="Test", status=TableStatus.VACANT)
        second = Table(table_number=f"AUTH_T2_{suffix}", capacity=2, zone="Test", status=TableStatus.VACANT)
        self.db.add_all([first, second])
        self.db.commit()
        order = OrderService.create_or_get_open_order(self.db, first.id, OrderType.DINE_IN, "test", 1)
        moved = TableService.transfer_order(self.db, order.id, second.id, 1)
        self.assertEqual(moved.table_id, second.id)
        self.db.refresh(first)
        self.db.refresh(second)
        self.assertEqual(first.status, TableStatus.VACANT)
        self.assertEqual(second.current_order_id, order.id)
        self.assertIsNotNone(self.db.query(AuditLog).filter(AuditLog.action == "TRANSFER_ORDER_TABLE", AuditLog.target_id == order.id).first())

    def test_split_recalculates_both_orders(self):
        category = self.db.query(Category).first()
        menu = MenuItem(code=f"TEST_{uuid4().hex[:8]}", name="Split Test Item", price=100.0, category_id=category.id, is_active=True)
        self.db.add(menu)
        self.db.commit()
        order = OrderService.create_or_get_open_order(self.db, None, OrderType.TAKEAWAY, "test", 1)
        item = OrderService.add_item_to_order(self.db, order.id, menu.id, qty=3)
        unit_price = float(item.price_per_unit)
        new_order = OrderService.split_item_to_new_order(self.db, order.id, item.id, 1, 1)
        self.db.refresh(order)
        self.assertEqual(order.items[0].quantity, 2)
        self.assertEqual(new_order.items[0].quantity, 1)
        self.assertEqual(float(order.subtotal) + float(new_order.subtotal), unit_price * 3)

    def test_merge_moves_items_closes_secondary_and_audits(self):
        suffix = uuid4().hex[:8]
        primary_table = Table(table_number=f"MERGE_T1_{suffix}", capacity=2, zone="Test", status=TableStatus.VACANT)
        secondary_table = Table(table_number=f"MERGE_T2_{suffix}", capacity=2, zone="Test", status=TableStatus.VACANT)
        self.db.add_all([primary_table, secondary_table])
        self.db.commit()
        primary = OrderService.create_or_get_open_order(self.db, primary_table.id, OrderType.DINE_IN, "primary", 1)
        secondary = OrderService.create_or_get_open_order(self.db, secondary_table.id, OrderType.DINE_IN, "secondary", 1)
        menu = self.db.query(MenuItem).first()
        primary_item = OrderService.add_item_to_order(self.db, primary.id, menu.id, qty=1)
        secondary_item = OrderService.add_item_to_order(self.db, secondary.id, menu.id, qty=2)
        expected_total = float(primary_item.price_per_unit) + float(secondary_item.price_per_unit) * 2

        merged = TableService.merge_orders(self.db, primary.id, secondary.id, 1)
        self.db.refresh(primary)
        self.db.refresh(secondary)
        self.assertEqual(merged.id, primary.id)
        self.assertEqual(secondary.status, OrderStatus.CANCELLED)
        self.assertEqual(sum(item.quantity for item in primary.items), 3)
        self.assertEqual(float(primary.subtotal), expected_total)
        self.assertEqual(secondary_table.status, TableStatus.VACANT)
        self.assertIsNotNone(self.db.query(AuditLog).filter(AuditLog.action == "MERGE_ORDERS", AuditLog.target_id == primary.id).first())


if __name__ == "__main__":
    unittest.main()
