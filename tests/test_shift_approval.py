import json
import unittest

from database.connection import SessionLocal
from database.models import AuditLog, OrderType, UserRole, OrderStatus, MenuItem
from services.order_service import OrderService
from services.shift_service import ShiftService


class TestShiftAndApprovalControls(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_shift_reconciliation_records_expected_and_variance(self):
        ShiftService.start_shift(self.db, user_id=1, opening_float=100.0)
        result = ShiftService.close_shift(self.db, user_id=1, actual_cash=97.5, reason="ทอนขาด")
        self.assertEqual(result["opening_float"], 100.0)
        self.assertEqual(result["expected_cash"], 100.0)
        self.assertEqual(result["variance"], -2.5)
        event = self.db.query(AuditLog).filter(AuditLog.action == "SHIFT_END").order_by(AuditLog.id.desc()).first()
        self.assertEqual(json.loads(event.details_json)["reason"], "ทอนขาด")

    def test_discount_threshold_requires_manager_or_owner(self):
        self.assertTrue(OrderService.validate_discount_approval(500.0, UserRole.CASHIER))
        with self.assertRaises(ValueError):
            OrderService.validate_discount_approval(500.01, UserRole.CASHIER)
        self.assertTrue(OrderService.validate_discount_approval(500.01, UserRole.MANAGER))

    def test_cancel_requires_reason_and_audits(self):
        order = OrderService.create_or_get_open_order(self.db, None, OrderType.TAKEAWAY, "cancel test", 1)
        with self.assertRaises(ValueError):
            OrderService.cancel_order(self.db, order.id, 1, "")
        cancelled = OrderService.cancel_order(self.db, order.id, 1, "ลูกค้ายกเลิก")
        self.assertEqual(cancelled.status.value, "CANCELLED")
        event = self.db.query(AuditLog).filter(AuditLog.action == "CANCEL_ORDER", AuditLog.target_id == order.id).first()
        self.assertEqual(json.loads(event.details_json)["reason"], "ลูกค้ายกเลิก")

    def test_paid_refund_requires_approval_and_audits(self):
        order = OrderService.create_or_get_open_order(self.db, None, OrderType.TAKEAWAY, "refund test", 1)
        menu = self.db.query(MenuItem).filter_by(is_active=True).first()
        OrderService.add_item_to_order(self.db, order.id, menu.id, qty=1)
        OrderService.checkout_order(self.db, order.id, "เงินสด (CASH)", 0.0, 1)
        with self.assertRaises(PermissionError):
            OrderService.refund_order(self.db, order.id, 1, "ลูกค้าคืนสินค้า", approver_role=UserRole.CASHIER)
        refunded = OrderService.refund_order(self.db, order.id, 1, "ลูกค้าคืนสินค้า", approver_role=UserRole.MANAGER)
        self.assertEqual(refunded.status, OrderStatus.CANCELLED)
        event = self.db.query(AuditLog).filter(AuditLog.action == "REFUND_ORDER", AuditLog.target_id == order.id).first()
        self.assertIsNotNone(event)


if __name__ == "__main__":
    unittest.main()
