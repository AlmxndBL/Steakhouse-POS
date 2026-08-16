import unittest
import uuid
from database.connection import SessionLocal
from database.models import UserRole
from services.staff_service import StaffService
from services.auth_service import AuthService

class TestStaffManagement(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_staff_lifecycle(self):
        """Test full employee lifecycle: create -> duplicate check -> update -> reset password -> deactivate."""
        uid_str = uuid.uuid4().hex[:6].lower()
        test_username = f"emp_{uid_str}"
        test_pw = "pass1234"

        # 1. Create Staff
        staff = StaffService.create_staff(
            self.db,
            username=test_username,
            name="สมพงษ์ เด็กเสิร์ฟ",
            password=test_pw,
            role=UserRole.WAITER,
            phone="089-999-8888"
        )
        self.assertIsNotNone(staff.id)
        self.assertEqual(staff.username, test_username)
        self.assertEqual(staff.role, UserRole.WAITER)

        # 2. Test Duplicate Username Prevention
        with self.assertRaises(ValueError):
            StaffService.create_staff(
                self.db,
                username=test_username,
                name="คนชื่อซ้ำ",
                password="anypass123",
                role=UserRole.CASHIER
            )

        # 3. Authenticate with initial password
        auth_user = AuthService.authenticate(self.db, test_username, test_pw)
        self.assertIsNotNone(auth_user)
        self.assertEqual(auth_user.id, staff.id)

        # 4. Update Staff Details (promote to Cashier)
        updated = StaffService.update_staff(
            self.db,
            user_id=staff.id,
            name="สมพงษ์ เลื่อนขั้นเป็นแคชเชียร์",
            role=UserRole.CASHIER,
            phone="089-999-7777",
            is_active=True
        )
        self.assertEqual(updated.name, "สมพงษ์ เลื่อนขั้นเป็นแคชเชียร์")
        self.assertEqual(updated.role, UserRole.CASHIER)

        # 5. Reset Password
        new_pw = "newpass5678"
        reset_success = StaffService.reset_password(self.db, staff.id, new_pw)
        self.assertTrue(reset_success)

        # Old password must now fail
        old_auth = AuthService.authenticate(self.db, test_username, test_pw)
        self.assertIsNone(old_auth)

        # New password must succeed
        new_auth = AuthService.authenticate(self.db, test_username, new_pw)
        self.assertIsNotNone(new_auth)

        # 6. Deactivate Staff (e.g. employee left company)
        deactivated = StaffService.toggle_active_status(self.db, staff.id)
        self.assertFalse(deactivated.is_active)

        # Deactivated user cannot log in
        deact_auth = AuthService.authenticate(self.db, test_username, new_pw)
        self.assertIsNone(deact_auth, "Deactivated employee must not be able to log in")

if __name__ == '__main__':
    unittest.main()
