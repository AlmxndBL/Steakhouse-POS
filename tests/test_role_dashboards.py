import unittest

from database.models import UserRole
from services.auth_service import AuthService


class TestRoleHomeDashboards(unittest.TestCase):
    def test_each_role_redirects_to_task_workspace(self):
        expected = {
            UserRole.OWNER: "/admin",
            UserRole.MANAGER: "/admin",
            UserRole.CASHIER: "/tables",
            UserRole.WAITER: "/tables",
            UserRole.KITCHEN: "/kds",
        }
        for role, route in expected.items():
            with self.subTest(role=role):
                self.assertEqual(AuthService.get_role_home_route(role), route)

    def test_unknown_role_fails_closed(self):
        self.assertEqual(AuthService.get_role_home_route("UNKNOWN"), "/login")
        self.assertEqual(AuthService.get_role_action_routes("UNKNOWN"), ["/login"])

    def test_role_actions_match_primary_work(self):
        self.assertEqual(AuthService.get_role_action_routes(UserRole.OWNER), ["/admin/reports", "/admin/stock", "/admin/audit"])
        self.assertEqual(AuthService.get_role_action_routes(UserRole.MANAGER), ["/admin/stock", "/admin/staff", "/admin/audit"])
        self.assertEqual(AuthService.get_role_action_routes(UserRole.CASHIER), ["/tables", "/pos", "/admin/reports"])
        self.assertEqual(AuthService.get_role_action_routes(UserRole.WAITER), ["/tables", "/pos", "/kds"])
        self.assertEqual(AuthService.get_role_action_routes(UserRole.KITCHEN), ["/kds"])


if __name__ == "__main__":
    unittest.main()
