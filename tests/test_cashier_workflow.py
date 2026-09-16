"""Detailed cashier payment tests; requires the isolated PostgreSQL service."""
import json
import sys
import unittest
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from tests.database_safety import require_isolated_test_database

require_isolated_test_database()

if "app" not in sys.path:
    sys.path.insert(0, "app")

from database.connection import Base, engine
from database.models import (
    AuditLog, Category, Ingredient, MenuItem, Order, OrderItemStatus,
    OrderStatus, OrderType, RecipeBOM, StockLot, StockTransaction,
    StockTxType, Table, TableStatus, User, UserRole,
)
from services.order_service import OrderService
from services.shift_service import ShiftService


class TestCashierWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # DDL is allowed only after the module-level fail-closed DB guard.
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.connection = engine.connect()
        self.outer_transaction = self.connection.begin()
        from sqlalchemy.orm import Session

        self.db = Session(bind=self.connection, join_transaction_mode="create_savepoint")
        self.owner = self._user("owner", UserRole.OWNER)
        self.manager = self._user("manager", UserRole.MANAGER)
        self.cashier = self._user("cashier", UserRole.CASHIER)
        self.waiter = self._user("waiter", UserRole.WAITER)
        self.kitchen = self._user("kitchen", UserRole.KITCHEN)
        self.category = Category(name=f"QA category {id(self)}", sort_order=1)
        self.ingredient = Ingredient(
            code=f"QA-{id(self)}", name="QA steak", unit="g",
            min_stock_alert=Decimal("100"), cost_per_unit=Decimal("0.50"),
        )
        self.table = Table(
            table_number=f"QA-{id(self)}", capacity=2,
            zone="Test", status=TableStatus.VACANT,
        )
        self.db.add_all([self.category, self.ingredient, self.table])
        self.db.flush()
        self.menu = self._menu("100.00")
        self.lot = StockLot(
            ingredient_id=self.ingredient.id, lot_number=f"QA-LOT-{id(self)}",
            initial_quantity=Decimal("1000"), remaining_quantity=Decimal("1000"),
            unit_cost=Decimal("0.50"), expiry_date=date.today() + timedelta(days=30),
            received_date=datetime.now(timezone.utc), is_depleted=False,
        )
        self.db.add(self.lot)
        self.db.flush()

    def tearDown(self):
        self.db.close()
        if self.outer_transaction.is_active:
            self.outer_transaction.rollback()
        self.connection.close()

    def _user(self, name, role, active=True):
        user = User(
            username=f"qa-{name}-{id(self)}", name=f"QA {name}",
            password_hash="test-only-not-used", role=role, is_active=active,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def _menu(self, price):
        menu = MenuItem(
            category_id=self.category.id,
            code=f"QA-MENU-{uuid.uuid4().hex}",
            name="QA steak", price=Decimal(price),
            description="cashier test fixture", is_active=True,
        )
        self.db.add(menu)
        self.db.flush()
        self.db.add(RecipeBOM(
            menu_item_id=menu.id, ingredient_id=self.ingredient.id,
            quantity_required=Decimal("250"), unit="g",
        ))
        self.db.flush()
        return menu

    def _order(self, *, table=False, qty=1, menu=None, user=None):
        order = OrderService.create_or_get_open_order(
            self.db,
            table_id=self.table.id if table else None,
            order_type=OrderType.DINE_IN if table else OrderType.TAKEAWAY,
            customer_name="QA cashier order",
            user_id=(user or self.cashier).id,
        )
        if qty:
            OrderService.add_item_to_order(
                self.db, order_id=order.id,
                menu_item_id=(menu or self.menu).id, qty=qty,
            )
        return order

    def _remaining_stock(self):
        self.db.refresh(self.lot)
        return Decimal(self.lot.remaining_quantity)

    def test_cashier_cash_checkout_closes_table_deducts_stock_and_audits(self):
        order = self._order(table=True, qty=2)
        self.assertEqual(self.table.status, TableStatus.OCCUPIED)
        queue_ids = [o.id for o in OrderService.get_cashier_payment_queue(self.db)]
        self.assertIn(order.id, queue_ids)

        self.assertEqual(OrderService.send_new_items_to_kitchen(self.db, order.id, self.cashier.id), 1)
        self.db.refresh(order.items[0])
        self.assertIsNotNone(order.items[0].sent_to_kitchen_at)
        self.assertEqual(order.items[0].item_status, OrderItemStatus.PENDING)

        paid = OrderService.checkout_order(
            self.db, order.id, "เงินสด (CASH)", discount_amount=0, user_id=self.cashier.id
        )
        self.assertEqual(paid.status, OrderStatus.PAID)
        self.assertEqual(paid.payment_method, "เงินสด (CASH)")
        self.assertEqual(Decimal(paid.subtotal), Decimal("200.00"))
        self.assertEqual(Decimal(paid.service_charge_amount), Decimal("20.00"))
        self.assertEqual(Decimal(paid.vat_amount), Decimal("15.40"))
        self.assertEqual(Decimal(paid.net_amount), Decimal("235.40"))

        self.db.refresh(self.table)
        self.assertEqual(self.table.status, TableStatus.VACANT)
        self.assertIsNone(self.table.current_order_id)
        self.assertEqual(self._remaining_stock(), Decimal("500.0000"))
        sale_txs = self.db.query(StockTransaction).filter(
            StockTransaction.order_id == order.id,
            StockTransaction.tx_type == StockTxType.SALE_OUT,
        ).all()
        self.assertEqual(sum(Decimal(tx.quantity) for tx in sale_txs), Decimal("-500.0000"))
        audit = self.db.query(AuditLog).filter(
            AuditLog.action == "CHECKOUT_ORDER", AuditLog.target_id == order.id,
        ).one()
        details = json.loads(audit.details_json)
        self.assertEqual(details["payment"], "เงินสด (CASH)")
        self.assertEqual(details["amount"], 235.4)
        remaining_queue_ids = [
            queued_order.id for queued_order in OrderService.get_cashier_payment_queue(self.db)
        ]
        self.assertNotIn(order.id, remaining_queue_ids)

    def test_cashier_queue_includes_only_open_orders_with_items(self):
        empty = self._order(qty=0)
        payable = self._order(qty=1)
        paid = self._order(qty=1)
        OrderService.checkout_order(self.db, paid.id, "เงินสด (CASH)", 0, self.cashier.id)
        queue_ids = [order.id for order in OrderService.get_cashier_payment_queue(self.db)]
        self.assertIn(payable.id, queue_ids)
        self.assertNotIn(empty.id, queue_ids)
        self.assertNotIn(paid.id, queue_ids)

    def test_empty_bill_cannot_be_paid(self):
        order = self._order(qty=0)
        with self.assertRaisesRegex(ValueError, "บิลว่าง"):
            OrderService.checkout_order(self.db, order.id, "เงินสด (CASH)", 0, self.cashier.id)
        self.db.refresh(order)
        self.assertEqual(order.status, OrderStatus.OPEN)
        self.assertEqual(self._remaining_stock(), Decimal("1000.0000"))

    def test_waiter_and_kitchen_cannot_checkout_directly(self):
        order = self._order(qty=1)
        for actor in (self.waiter, self.kitchen):
            with self.subTest(role=actor.role):
                with self.assertRaises(PermissionError):
                    OrderService.checkout_order(self.db, order.id, "เงินสด (CASH)", 0, actor.id)
                self.db.refresh(order)
                self.assertEqual(order.status, OrderStatus.OPEN)
                self.assertEqual(self._remaining_stock(), Decimal("1000.0000"))

    def test_inactive_cashier_cannot_checkout(self):
        actor = self._user("inactive-cashier", UserRole.CASHIER, active=False)
        order = self._order(qty=1)
        with self.assertRaises(PermissionError):
            OrderService.checkout_order(self.db, order.id, "เงินสด (CASH)", 0, actor.id)
        self.db.refresh(order)
        self.assertEqual(order.status, OrderStatus.OPEN)

    def test_checkout_rejects_negative_and_over_subtotal_discounts(self):
        order = self._order(qty=1)
        for discount in (-0.01, 100.01):
            with self.subTest(discount=discount):
                with self.assertRaises(ValueError):
                    OrderService.checkout_order(
                        self.db, order.id, "เงินสด (CASH)", discount, self.cashier.id
                    )
                self.db.refresh(order)
                self.assertEqual(order.status, OrderStatus.OPEN)
                self.assertEqual(self._remaining_stock(), Decimal("1000.0000"))

    def test_cashier_cannot_apply_discount_above_approval_threshold(self):
        menu = self._menu("1000.00")
        order = self._order(qty=1, menu=menu)
        with self.assertRaisesRegex(ValueError, "เกิน 500"):
            OrderService.checkout_order(self.db, order.id, "เงินสด (CASH)", 500.01, self.cashier.id)
        self.db.refresh(order)
        self.assertEqual(order.status, OrderStatus.OPEN)
        self.assertEqual(self._remaining_stock(), Decimal("1000.0000"))

    def test_manager_can_approve_discount_above_cashier_threshold(self):
        menu = self._menu("1000.00")
        order = self._order(qty=1, menu=menu)
        paid = OrderService.checkout_order(self.db, order.id, "เงินสด (CASH)", 501.00, self.manager.id)
        self.assertEqual(paid.status, OrderStatus.PAID)
        self.assertEqual(Decimal(paid.discount_amount), Decimal("501.00"))
        self.assertEqual(Decimal(paid.net_amount), Decimal("587.32"))

    def test_second_checkout_is_rejected_without_duplicate_stock_sale(self):
        order = self._order(qty=1)
        OrderService.checkout_order(self.db, order.id, "เงินสด (CASH)", 0, self.cashier.id)
        with self.assertRaisesRegex(ValueError, "สถานะบิลไม่ถูกต้อง"):
            OrderService.checkout_order(self.db, order.id, "เงินสด (CASH)", 0, self.cashier.id)
        count = self.db.query(StockTransaction).filter(
            StockTransaction.order_id == order.id,
            StockTransaction.tx_type == StockTxType.SALE_OUT,
        ).count()
        self.assertEqual(count, 1)

    def test_insufficient_inventory_rolls_back_payment_table_and_stock(self):
        order = self._order(table=True, qty=1)
        self.lot.remaining_quantity = Decimal("100")
        self.db.commit()
        with self.assertRaisesRegex(ValueError, "วัตถุดิบไม่พอ"):
            OrderService.checkout_order(self.db, order.id, "เงินสด (CASH)", 0, self.cashier.id)

        self.db.expire_all()
        persisted_order = self.db.query(Order).filter(Order.id == order.id).one()
        persisted_table = self.db.query(Table).filter(Table.id == self.table.id).one()
        persisted_lot = self.db.query(StockLot).filter(StockLot.id == self.lot.id).one()
        self.assertEqual(persisted_order.status, OrderStatus.OPEN)
        self.assertEqual(persisted_table.status, TableStatus.OCCUPIED)
        self.assertEqual(Decimal(persisted_lot.remaining_quantity), Decimal("100.0000"))
        checkout_audits = self.db.query(AuditLog).filter(
            AuditLog.action == "CHECKOUT_ORDER",
            AuditLog.target_id == order.id,
        ).count()
        self.assertEqual(checkout_audits, 0)

    def test_cash_shift_counts_cash_and_excludes_qr_sales(self):
        ShiftService.start_shift(self.db, self.cashier.id, opening_float=50.00)
        cash_order = self._order(qty=1)
        qr_order = self._order(qty=1)
        OrderService.checkout_order(self.db, cash_order.id, "เงินสด (CASH)", 0, self.cashier.id)
        OrderService.checkout_order(self.db, qr_order.id, "สแกน QR พร้อมเพย์", 0, self.cashier.id)
        result = ShiftService.close_shift(
            self.db, self.cashier.id, actual_cash=167.70, reason="ปิดกะ QA"
        )
        self.assertEqual(result["opening_float"], 50.0)
        self.assertEqual(result["cash_sales"], 117.7)
        self.assertEqual(result["expected_cash"], 167.7)
        self.assertEqual(result["variance"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
