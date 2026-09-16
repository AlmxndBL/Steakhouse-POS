import unittest
from datetime import datetime, timezone, timedelta

from components.theme import STATUS_REGISTRY, get_status_meta
from components.table_card import TableCard


class TestUIStatusRegistry(unittest.TestCase):
    def test_core_statuses_have_text_color_and_icon(self):
        required = {"VACANT", "OCCUPIED", "PENDING", "COOKING", "SERVED", "PAID", "CANCELLED"}
        self.assertTrue(required.issubset(STATUS_REGISTRY))
        for status in required:
            with self.subTest(status=status):
                meta = get_status_meta(status)
                self.assertTrue(meta["text"])
                self.assertTrue(meta["color"])
                self.assertTrue(meta["icon"])

    def test_unknown_status_has_safe_fallback(self):
        meta = get_status_meta("NOT_A_REAL_STATUS")
        self.assertEqual(meta["text"], "NOT_A_REAL_STATUS")
        self.assertTrue(meta["icon"])

    def test_table_card_surfaces_order_work_state(self):
        class Item:
            quantity = 2
            sent_to_kitchen_at = None

        class Order:
            net_amount = 240.0
            created_at = datetime.now(timezone.utc) - timedelta(minutes=7)
            items = [Item()]

        class Table:
            table_number = "T-UI"
            capacity = 4
            zone = "Indoor"
            status = "OCCUPIED"
            current_order = Order()

        card = TableCard(Table(), lambda _: None)
        texts = [control.value for control in card.content.controls if hasattr(control, "value")]
        self.assertTrue(any("2 รายการ" in value for value in texts))
        self.assertTrue(any("รายการใหม่ 2 รายการ" in value for value in texts))


if __name__ == "__main__":
    unittest.main()
