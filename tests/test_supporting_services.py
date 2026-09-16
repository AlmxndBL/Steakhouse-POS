"""Regression coverage for secondary catalog, staff, table, and report services."""
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from tests.database_safety import require_isolated_test_database

require_isolated_test_database()

if "app" not in sys.path:
    sys.path.insert(0, "app")

from database.connection import Base, engine
from database.models import (
    Category, Ingredient, MenuItem, Order, OrderItem, OrderStatus,
    OrderType, RecipeBOM, Table, TableStatus, User, UserRole,
)
from services.auth_service import check_password
from services.menu_service import MenuService
from services.report_service import ReportService
from services.staff_service import StaffService
from services.table_service import TableService


class TestSupportingServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        from sqlalchemy.orm import Session

        self.connection = engine.connect()
        self.outer_transaction = self.connection.begin()
        self.db = Session(bind=self.connection, join_transaction_mode="create_savepoint")
        suffix = uuid.uuid4().hex[:10].upper()
        self.owner = User(
            username=f"qa-owner-{suffix.lower()}", name="QA Owner",
            password_hash="test-only-not-used", role=UserRole.OWNER, is_active=True,
        )
        self.category = Category(name=f"QA Category {suffix}", sort_order=10)
        self.ingredient = Ingredient(
            code=f"QA-ING-{suffix}", name="QA ingredient", unit="g",
            min_stock_alert=Decimal("10"), cost_per_unit=Decimal("0.40"), is_active=True,
        )
        self.table = Table(
            table_number=f"QA-{suffix}", capacity=2, zone="QA Zone",
            status=TableStatus.VACANT,
        )
        self.db.add_all([self.owner, self.category, self.ingredient, self.table])
        self.db.flush()

    def tearDown(self):
        self.db.close()
        if self.outer_transaction.is_active:
            self.outer_transaction.rollback()
        self.connection.close()

    def _menu(self, code_suffix, name, active=True, price="100.00"):
        item = MenuItem(
            category_id=self.category.id,
            code=f"QA_{code_suffix}_{uuid.uuid4().hex[:6].upper()}",
            name=name,
            price=Decimal(price),
            description="support service test fixture",
            is_active=active,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def _paid_order(self, order_number, *, created_at=None, status=OrderStatus.PAID):
        order = Order(
            order_number=f"{order_number}-{uuid.uuid4().hex[:6]}",
            table_id=None,
            order_type=OrderType.TAKEAWAY,
            status=status,
            customer_name="QA report order",
            subtotal=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            service_charge_amount=Decimal("10.00"),
            vat_amount=Decimal("7.70"),
            net_amount=Decimal("117.70"),
            payment_method="เงินสด (CASH)",
            user_id=self.owner.id,
            created_at=created_at or datetime.now(timezone.utc),
        )
        self.db.add(order)
        self.db.flush()
        return order

    def test_menu_search_filters_by_name_code_category_and_active_state(self):
        tag = uuid.uuid4().hex[:8].upper()
        other_category = MenuService.create_category(
            self.db, f"QA other {uuid.uuid4().hex[:6]}", sort_order=20
        )
        soup = MenuService.create_menu_item(
            self.db, self.category.id, f"qa_{tag}_soup", f"QA {tag} Tomato Soup", 89.0, "  warm soup  "
        )
        fries = MenuService.create_menu_item(
            self.db, self.category.id, f"qa_{tag}_fries", f"QA {tag} Crispy Fries", 75.0
        )
        other = MenuService.create_menu_item(
            self.db, other_category.id, f"qa_{tag}_tea", f"QA {tag} Iced Tea", 45.0
        )
        self.assertEqual(soup.code, f"QA_{tag}_SOUP")
        self.assertEqual(soup.description, "warm soup")

        self.assertEqual([item.id for item in MenuService.search_menu_items(self.db, f"{tag} Tomato")], [soup.id])
        self.assertEqual([item.id for item in MenuService.search_menu_items(self.db, f"QA_{tag}_FRIES")], [fries.id])
        self.assertEqual(
            [item.id for item in MenuService.get_menu_items(self.db, category_id=other_category.id)],
            [other.id],
        )

        MenuService.toggle_menu_item_status(self.db, fries.id)
        self.assertEqual(MenuService.search_menu_items(self.db, f"{tag} Fries"), [])
        self.assertNotIn(fries.id, [item.id for item in MenuService.get_menu_items(self.db)])
        self.assertIn(fries.id, [item.id for item in MenuService.get_menu_items(self.db, active_only=False)])

    def test_menu_update_missing_item_soft_delete_and_hard_delete(self):
        item = MenuService.create_menu_item(
            self.db, self.category.id, f"QA_{uuid.uuid4().hex[:8]}", "QA Grill Plate", 150.0
        )
        updated = MenuService.update_menu_item(
            self.db, item.id, "QA Special Grill", 175.25, self.category.id, "  updated  ", False
        )
        self.assertEqual(updated.name, "QA Special Grill")
        self.assertEqual(Decimal(updated.price), Decimal("175.25"))
        self.assertEqual(updated.description, "updated")
        self.assertFalse(updated.is_active)
        self.assertIsNone(MenuService.update_menu_item(self.db, -1, "Missing", 10, self.category.id))

        self.assertTrue(MenuService.delete_menu_item(self.db, item.id, soft=True))
        self.assertFalse(MenuService.get_menu_item_by_id(self.db, item.id).is_active)
        hard_delete = self._menu("HARD", "QA Temporary Menu")
        self.assertTrue(MenuService.delete_menu_item(self.db, hard_delete.id, soft=False))
        self.assertIsNone(MenuService.get_menu_item_by_id(self.db, hard_delete.id))
        self.assertFalse(MenuService.delete_menu_item(self.db, -1))

    def test_menu_creation_rejects_duplicate_code_and_invalid_fields(self):
        code = f"QA_{uuid.uuid4().hex[:8]}"
        created = MenuService.create_menu_item(self.db, self.category.id, code, "QA Valid Item", 10)
        self.assertIsNotNone(created.id)
        with self.assertRaisesRegex(ValueError, "มีอยู่ในระบบแล้ว"):
            MenuService.create_menu_item(self.db, self.category.id, code.lower(), "QA Duplicate", 10)
        with self.assertRaises(ValueError):
            MenuService.create_menu_item(self.db, self.category.id, "bad code!", "QA Invalid", 10)
        with self.assertRaises(ValueError):
            MenuService.create_menu_item(self.db, self.category.id, "QA_PRICE", "QA Invalid Price", 0)

    def test_popular_menu_ranks_paid_quantity_excludes_inactive_and_clamps_limit(self):
        # Hide any pre-existing test-fixture catalog for deterministic ranking;
        # the enclosing outer transaction restores those rows at teardown.
        self.db.query(MenuItem).update({MenuItem.is_active: False}, synchronize_session=False)
        best = self._menu("BEST", "QA Best Seller")
        next_best = self._menu("NEXT", "QA Next Seller")
        inactive = self._menu("OFF", "QA Disabled Seller", active=False)
        paid = self._paid_order("QA-PAID")
        open_order = self._paid_order("QA-OPEN", status=OrderStatus.OPEN)
        self.db.add_all([
            OrderItem(order_id=paid.id, menu_item_id=best.id, quantity=5, price_per_unit=100),
            OrderItem(order_id=paid.id, menu_item_id=next_best.id, quantity=2, price_per_unit=100),
            OrderItem(order_id=paid.id, menu_item_id=inactive.id, quantity=99, price_per_unit=100),
            OrderItem(order_id=open_order.id, menu_item_id=next_best.id, quantity=50, price_per_unit=100),
        ])
        self.db.flush()

        ranked = MenuService.get_popular_menu_items(self.db, limit=2)
        self.assertEqual([item.id for item in ranked], [best.id, next_best.id])
        self.assertEqual(MenuService.get_popular_menu_items(self.db, limit=0), [best])

    def test_menu_bom_cost_sums_all_recipe_ingredients(self):
        second_ingredient = Ingredient(
            code=f"QA-SECOND-{uuid.uuid4().hex[:6]}", name="QA second",
            unit="ml", min_stock_alert=Decimal("1"), cost_per_unit=Decimal("0.20"),
        )
        item = self._menu("BOM", "QA BOM Menu")
        self.db.add(second_ingredient)
        self.db.flush()
        self.db.add_all([
            RecipeBOM(menu_item_id=item.id, ingredient_id=self.ingredient.id,
                      quantity_required=Decimal("2.5"), unit="g"),
            RecipeBOM(menu_item_id=item.id, ingredient_id=second_ingredient.id,
                      quantity_required=Decimal("3"), unit="ml"),
        ])
        self.db.flush()
        self.assertAlmostEqual(MenuService.get_item_bom_cost(self.db, item.id), 1.60)
        self.assertEqual(MenuService.get_item_bom_cost(self.db, -1), 0.0)

    def test_staff_queries_password_hashing_updates_and_missing_records(self):
        username = f"qa_{uuid.uuid4().hex[:8]}"
        staff = StaffService.create_staff(
            self.db, username.upper(), "QA Cashier", "initial-pass", UserRole.CASHIER, "0891234567"
        )
        self.assertEqual(staff.username, username)
        self.assertNotEqual(staff.password_hash, "initial-pass")
        self.assertTrue(check_password("initial-pass", staff.password_hash))
        self.assertEqual(staff.phone, "089-123-4567")
        self.assertEqual(StaffService.get_staff_by_id(self.db, staff.id).id, staff.id)
        self.assertIsNone(StaffService.get_staff_by_id(self.db, -1))
        self.assertIn(staff.id, [row.id for row in StaffService.get_all_staff(self.db, active_only=True)])

        updated = StaffService.update_staff(
            self.db, staff.id, "QA Senior Cashier", UserRole.MANAGER, "0891234568", is_active=True
        )
        self.assertEqual(updated.role, UserRole.MANAGER)
        self.assertEqual(updated.phone, "089-123-4568")
        self.assertTrue(StaffService.reset_password(self.db, staff.id, "replacement-pass"))
        self.db.refresh(staff)
        self.assertTrue(check_password("replacement-pass", staff.password_hash))
        self.assertFalse(check_password("initial-pass", staff.password_hash))
        self.assertFalse(StaffService.toggle_active_status(self.db, staff.id).is_active)
        self.assertNotIn(staff.id, [row.id for row in StaffService.get_all_staff(self.db, active_only=True)])

        with self.assertRaises(ValueError):
            StaffService.update_staff(self.db, -1, "QA Missing", UserRole.CASHIER)
        with self.assertRaises(ValueError):
            StaffService.reset_password(self.db, -1, "valid-password")
        with self.assertRaises(ValueError):
            StaffService.reset_password(self.db, staff.id, "x")
        with self.assertRaises(ValueError):
            StaffService.toggle_active_status(self.db, -1)

    def test_staff_creation_rejects_duplicate_username_without_creating_second_user(self):
        username = f"qa_dup_{uuid.uuid4().hex[:6]}"
        StaffService.create_staff(self.db, username, "QA Original", "valid-pass", UserRole.WAITER)
        with self.assertRaisesRegex(ValueError, "ถูกใช้งานแล้ว"):
            StaffService.create_staff(self.db, username.upper(), "QA Duplicate", "valid-pass", UserRole.CASHIER)
        self.assertEqual(self.db.query(User).filter(User.username == username).count(), 1)

    def test_table_zone_queries_normalization_duplicates_and_delete_guards(self):
        number = f"qa_{uuid.uuid4().hex[:6]}"
        table = TableService.create_table(self.db, number, capacity=4, zone="Terrace QA")
        self.assertEqual(table.table_number, number.upper())
        self.assertEqual(table.status, TableStatus.VACANT)
        self.assertIn("Terrace QA", TableService.get_zones(self.db))
        self.assertEqual([row.id for row in TableService.get_tables(self.db, "Terrace QA")], [table.id])
        self.assertEqual(TableService.get_table_by_id(self.db, table.id).id, table.id)
        self.assertIsNone(TableService.get_table_by_id(self.db, -1))

        with self.assertRaisesRegex(ValueError, "มีอยู่ในระบบแล้ว"):
            TableService.create_table(self.db, number, capacity=4, zone="Terrace QA")
        with self.assertRaises(ValueError):
            TableService.create_table(self.db, "QA_BAD_CAP", capacity=0, zone="Terrace QA")

        updated = TableService.update_table(self.db, table.id, number, 8, "VIP QA")
        self.assertEqual(updated.capacity, 8)
        self.assertEqual(updated.zone, "VIP QA")
        self.assertIsNone(TableService.update_table(self.db, -1, "QA_MISSING", 4, "QA"))

        table.status = TableStatus.OCCUPIED
        self.db.flush()
        with self.assertRaisesRegex(ValueError, "มีลูกค้าใช้งานอยู่"):
            TableService.delete_table(self.db, table.id)
        self.db.refresh(table)
        self.assertEqual(table.status, TableStatus.OCCUPIED)
        table.status = TableStatus.VACANT
        self.db.flush()
        self.assertTrue(TableService.delete_table(self.db, table.id))
        self.assertFalse(TableService.delete_table(self.db, -1))

    def test_sales_report_period_filters_include_only_paid_orders(self):
        recent = self._paid_order("QA-REPORT-RECENT")
        old = self._paid_order(
            "QA-REPORT-OLD", created_at=datetime.now(timezone.utc) - timedelta(days=45)
        )
        cancelled = self._paid_order("QA-REPORT-CANCELLED", status=OrderStatus.CANCELLED)

        all_report = ReportService.get_sales_report(self.db, period="all")
        today_report = ReportService.get_sales_report(self.db, period="today")
        month_report = ReportService.get_sales_report(self.db, period="month")
        self.assertIn(recent.order_number, [order.order_number for order in all_report["orders"]])
        self.assertIn(old.order_number, [order.order_number for order in all_report["orders"]])
        self.assertNotIn(cancelled.order_number, [order.order_number for order in all_report["orders"]])
        self.assertIn(recent.order_number, [order.order_number for order in today_report["orders"]])
        self.assertNotIn(old.order_number, [order.order_number for order in today_report["orders"]])
        self.assertNotIn(old.order_number, [order.order_number for order in month_report["orders"]])
        self.assertEqual(all_report["period"], "all")
        self.assertEqual(len(all_report["daily_trend"]), 7)


if __name__ == "__main__":
    unittest.main(verbosity=2)
