import unittest
from datetime import date, timedelta
from utils.validators import Validator

class TestValidatorsEngine(unittest.TestCase):
    def test_validate_username(self):
        # Valid cases
        res = Validator.validate_username("somchai_01")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.value, "somchai_01")
        self.assertIsNone(res.error)

        # Auto lowercase
        res = Validator.validate_username("  SOMCHAI  ")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.value, "somchai")

        # Invalid cases
        self.assertFalse(Validator.validate_username("").is_valid)
        self.assertFalse(Validator.validate_username("ab").is_valid) # Too short
        self.assertFalse(Validator.validate_username("a" * 31).is_valid) # Too long
        self.assertFalse(Validator.validate_username("user@name").is_valid) # Special char
        self.assertFalse(Validator.validate_username("สมชาย").is_valid) # Thai chars

    def test_validate_password(self):
        self.assertTrue(Validator.validate_password("1234").is_valid)
        self.assertTrue(Validator.validate_password("secret_pass").is_valid)
        self.assertFalse(Validator.validate_password("123", min_len=4).is_valid)
        self.assertFalse(Validator.validate_password("").is_valid)
        self.assertFalse(Validator.validate_password("   ").is_valid)

    def test_validate_phone(self):
        # Valid formats
        res = Validator.validate_phone("0812345678")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.value, "081-234-5678")

        res2 = Validator.validate_phone("081-234-5678")
        self.assertTrue(res2.is_valid)
        self.assertEqual(res2.value, "081-234-5678")

        # Optional phone empty
        res_empty = Validator.validate_phone("", required=False)
        self.assertTrue(res_empty.is_valid)
        self.assertIsNone(res_empty.value)

        # Invalid
        self.assertFalse(Validator.validate_phone("12345").is_valid)
        self.assertFalse(Validator.validate_phone("9991234567").is_valid) # Not start with 0
        self.assertFalse(Validator.validate_phone("เบอร์โทร").is_valid)

    def test_validate_price(self):
        # Valid
        res = Validator.validate_price("450.50")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.value, 450.50)

        res_comma = Validator.validate_price("1,250.00")
        self.assertTrue(res_comma.is_valid)
        self.assertEqual(res_comma.value, 1250.00)

        # Invalid
        self.assertFalse(Validator.validate_price("0").is_valid) # Default min is 0.01
        self.assertFalse(Validator.validate_price("-50").is_valid)
        self.assertFalse(Validator.validate_price("abc").is_valid)
        self.assertFalse(Validator.validate_price("").is_valid)
        self.assertFalse(Validator.validate_price("9999999").is_valid) # Over max

    def test_validate_integer(self):
        res = Validator.validate_integer("4", min_val=1, max_val=50)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.value, 4)

        self.assertFalse(Validator.validate_integer("0", min_val=1).is_valid)
        self.assertFalse(Validator.validate_integer("55", min_val=1, max_val=50).is_valid)
        self.assertFalse(Validator.validate_integer("สี่").is_valid)

    def test_validate_date(self):
        # Future date
        future = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")
        res = Validator.validate_date(future, allow_past=False)
        self.assertTrue(res.is_valid)

        # Past date with allow_past=False
        past = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        self.assertFalse(Validator.validate_date(past, allow_past=False).is_valid)
        self.assertTrue(Validator.validate_date(past, allow_past=True).is_valid)

        # Invalid formats
        self.assertFalse(Validator.validate_date("31/12/2026").is_valid)
        self.assertFalse(Validator.validate_date("2026-13-45").is_valid)
        self.assertFalse(Validator.validate_date("").is_valid)

    def test_validate_discount(self):
        res = Validator.validate_discount("100", subtotal=500.0)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.value, 100.0)

        self.assertFalse(Validator.validate_discount("600", subtotal=500.0).is_valid) # Exceeds subtotal
        self.assertFalse(Validator.validate_discount("-10", subtotal=500.0).is_valid)

    def test_validate_menu_code(self):
        res = Validator.validate_menu_code("stk001")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.value, "STK001")

        self.assertFalse(Validator.validate_menu_code("").is_valid)
        self.assertFalse(Validator.validate_menu_code("A").is_valid) # Too short
        self.assertFalse(Validator.validate_menu_code("STK@01").is_valid)

    def test_validate_table_number(self):
        res = Validator.validate_table_number("t01")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.value, "T01")

        self.assertFalse(Validator.validate_table_number("").is_valid)

if __name__ == '__main__':
    unittest.main()
