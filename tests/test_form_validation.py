import unittest
from datetime import datetime
from database.connection import SessionLocal
from services.menu_service import MenuService
from services.table_service import TableService

class TestFormValidation(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_price_input_validation(self):
        """Test validation behavior for prices (numbers vs strings/Thai characters)."""
        # Test valid price
        valid_price_str = "450.50"
        price = float(valid_price_str)
        self.assertEqual(price, 450.50)

        # Test Thai characters / invalid string should raise ValueError
        invalid_inputs = ["ฟหก", "abc", "12a", " ", "", "@@@"]
        for inp in invalid_inputs:
            with self.assertRaises(ValueError):
                float(inp.strip())

    def test_capacity_input_validation(self):
        """Test validation behavior for table seating capacity."""
        valid_cap_str = "6"
        cap = int(valid_cap_str)
        self.assertEqual(cap, 6)

        invalid_caps = ["สี่", "four", "4.5", "-1", ""]
        for inp in invalid_caps:
            try:
                val = int(inp.strip())
                # If parsed as int, check if <= 0
                is_valid = val > 0
            except ValueError:
                is_valid = False
            self.assertFalse(is_valid, f"Expected invalid capacity for input '{inp}'")

    def test_date_format_validation(self):
        """Test validation for expiration date format YYYY-MM-DD."""
        valid_date = "2026-12-31"
        parsed = datetime.strptime(valid_date, "%Y-%m-%d").date()
        self.assertEqual(parsed.year, 2026)

        invalid_dates = ["31/12/2026", "2026-13-40", "พรุ่งนี้", "invalid-date"]
        for inp in invalid_dates:
            with self.assertRaises(ValueError):
                datetime.strptime(inp, "%Y-%m-%d")

if __name__ == '__main__':
    unittest.main()
