import unittest
from sqlalchemy import inspect, text

from database.connection import SessionLocal, engine
from database.models import MenuItem, OrderStatus, OrderType
from database.seed import SCHEMA_VERSION, seed_data
from services.order_service import OrderService


class TestDataIntegrity(unittest.TestCase):
    def test_existing_database_has_version_marker(self):
        inspector = inspect(engine)
        self.assertIn("schema_migrations", inspector.get_table_names())
        with engine.connect() as connection:
            version = connection.execute(text("SELECT MAX(version) FROM schema_migrations")).scalar()
        self.assertEqual(version, SCHEMA_VERSION)

    def test_seed_is_idempotent_for_users_and_menu(self):
        db = SessionLocal()
        try:
            before = (db.query(MenuItem).count(), db.execute(text("SELECT COUNT(*) FROM users")).scalar())
            seed_data()
            db.expire_all()
            after = (db.query(MenuItem).count(), db.execute(text("SELECT COUNT(*) FROM users")).scalar())
            self.assertEqual(after, before)
        finally:
            db.close()

    def test_double_checkout_is_rejected(self):
        db = SessionLocal()
        try:
            menu = db.query(MenuItem).filter(MenuItem.is_active == True).first()
            order = OrderService.create_or_get_open_order(db, None, OrderType.TAKEAWAY, "integrity test", 1)
            OrderService.add_item_to_order(db, order.id, menu.id, qty=1)
            paid = OrderService.checkout_order(db, order.id, "เงินสด (CASH)", 0.0, 1)
            self.assertEqual(paid.status, OrderStatus.PAID)
            with self.assertRaises(ValueError):
                OrderService.checkout_order(db, order.id, "เงินสด (CASH)", 0.0, 1)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
