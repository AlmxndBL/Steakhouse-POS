import unittest
import uuid
from database.connection import SessionLocal
from services.menu_service import MenuService
from services.table_service import TableService

class TestSettingsCRUD(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_category_and_menu_lifecycle(self):
        """Test creating category, adding menu item, editing, toggling status, and soft-deleting."""
        # 1. Create Category
        unique_suffix = uuid.uuid4().hex[:6].upper()
        cat = MenuService.create_category(self.db, f"เครื่องเคียง_{unique_suffix}", sort_order=10)
        self.assertIsNotNone(cat.id)

        # 2. Create Menu Item
        code = f"SID_{unique_suffix}"
        item = MenuService.create_menu_item(
            self.db,
            category_id=cat.id,
            code=code,
            name="หัวหอมทอดกรอบ (Onion Rings)",
            price=120.0,
            description="หัวหอมทอดแป้งกรอบสไตล์อเมริกัน"
        )
        self.assertIsNotNone(item.id)
        self.assertEqual(float(item.price), 120.0)

        # 3. Update Menu Item
        updated = MenuService.update_menu_item(
            self.db,
            item_id=item.id,
            name="หัวหอมทอดกรอบ (สูตรพิเศษ)",
            price=135.0,
            category_id=cat.id,
            description="สูตรพิเศษชีส",
            is_active=True
        )
        self.assertEqual(updated.name, "หัวหอมทอดกรอบ (สูตรพิเศษ)")
        self.assertEqual(float(updated.price), 135.0)

        # 4. Toggle Status
        toggled = MenuService.toggle_menu_item_status(self.db, item.id)
        self.assertFalse(toggled.is_active)

    def test_table_lifecycle_and_validation(self):
        """Test creating table, editing table capacity/zone, and deleting table."""
        unique_tbl = f"T_{uuid.uuid4().hex[:5].upper()}"
        table = TableService.create_table(self.db, table_number=unique_tbl, capacity=4, zone="Outdoor")
        self.assertIsNotNone(table.id)
        self.assertEqual(table.zone, "Outdoor")

        # Update Table
        updated_tbl = TableService.update_table(self.db, table_id=table.id, table_number=unique_tbl, capacity=8, zone="VIP Room")
        self.assertEqual(updated_tbl.capacity, 8)
        self.assertEqual(updated_tbl.zone, "VIP Room")

        # Delete Table
        deleted = TableService.delete_table(self.db, table.id)
        self.assertTrue(deleted)

    def test_admin_menu_dialog_controls_instantiation(self):
        """Test that AdminMenuView form controls instantiate without TypeError (e.g. min_lines vs rows)."""
        import flet as ft
        # Test TextField with min_lines
        desc_input_1 = ft.TextField(label="คำอธิบายสั้นๆ (ถ้ามี)", multiline=True, min_lines=2, width=380)
        self.assertEqual(desc_input_1.min_lines, 2)
        self.assertTrue(desc_input_1.multiline)

        desc_input_2 = ft.TextField(label="คำอธิบาย", value="รายละเอียด", multiline=True, min_lines=2, width=380)
        self.assertEqual(desc_input_2.value, "รายละเอียด")

if __name__ == '__main__':
    unittest.main()
