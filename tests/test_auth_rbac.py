import unittest
from database.connection import SessionLocal
from database.models import UserRole
from services.auth_service import AuthService

class TestAuthRBAC(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_all_five_roles_exist_and_can_authenticate(self):
        """Test that all 5 roles can authenticate with their default usernames & passwords."""
        credentials = [
            ("owner", "admin1234", UserRole.OWNER),
            ("manager", "mgr1234", UserRole.MANAGER),
            ("cashier", "cash1234", UserRole.CASHIER),
            ("waiter", "waiter1234", UserRole.WAITER),
            ("kitchen", "cook1234", UserRole.KITCHEN),
        ]
        for username, password, expected_role in credentials:
            user = AuthService.authenticate(self.db, username, password)
            self.assertIsNotNone(user, f"Authentication failed for user '{username}'")
            self.assertEqual(user.role, expected_role)
            self.assertTrue(user.is_active)

    def test_invalid_credentials_rejected(self):
        """Test that incorrect username or password fails gracefully and returns None."""
        user_bad_pw = AuthService.authenticate(self.db, "owner", "wrongpass")
        self.assertIsNone(user_bad_pw)

        user_nonexist = AuthService.authenticate(self.db, "nobody", "admin1234")
        self.assertIsNone(user_nonexist)

        user_empty = AuthService.authenticate(self.db, "", "")
        self.assertIsNone(user_empty)

    def test_role_permissions(self):
        """Test RBAC role permission checks."""
        self.assertTrue(AuthService.has_permission(UserRole.OWNER, [UserRole.OWNER, UserRole.MANAGER]))
        self.assertTrue(AuthService.has_permission(UserRole.MANAGER, [UserRole.OWNER, UserRole.MANAGER]))
        self.assertFalse(AuthService.has_permission(UserRole.WAITER, [UserRole.OWNER, UserRole.MANAGER]))
        self.assertFalse(AuthService.has_permission(UserRole.KITCHEN, [UserRole.CASHIER, UserRole.WAITER]))

if __name__ == '__main__':
    unittest.main()
