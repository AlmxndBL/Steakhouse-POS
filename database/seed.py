from datetime import datetime, date, timedelta, timezone
from database.connection import engine, SessionLocal, Base
from database.models import (
    User, UserRole, Table, TableStatus, Category, MenuItem,
    ModifierGroup, ModifierOption, Ingredient, RecipeBOM, StockLot
)
from services.auth_service import hash_password

def seed_data():
    Base.metadata.create_all(bind=engine)
    
    # Defensive column migration for existing tables
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(50);
                ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
                ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
                DO $$ 
                BEGIN 
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='pin_hash') THEN
                        ALTER TABLE users ALTER COLUMN pin_hash DROP NOT NULL;
                    END IF;
                END $$;
            """))
            conn.commit()
    except Exception as e:
        print(f"[INFO] Column migration check: {e}")

    db = SessionLocal()

    try:
        # 1. Seed Users (ensure all standard roles exist)
        standard_users = [
            ("owner", "admin1234", "เจ้าของร้าน (Owner)", UserRole.OWNER, "081-111-1111"),
            ("manager", "mgr1234", "ผู้จัดการ (Manager)", UserRole.MANAGER, "082-222-2222"),
            ("cashier", "cash1234", "แคชเชียร์ (Cashier)", UserRole.CASHIER, "083-333-3333"),
            ("waiter", "waiter1234", "พนักงานเสิร์ฟ (Waiter)", UserRole.WAITER, "084-444-4444"),
            ("kitchen", "cook1234", "พนักงานครัว (Kitchen)", UserRole.KITCHEN, "085-555-5555"),
        ]
        for username, password, name, role, phone in standard_users:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                db.add(User(
                    username=username,
                    name=name,
                    password_hash=hash_password(password),
                    role=role,
                    phone=phone,
                    is_active=True
                ))
            else:
                # Update password hash if needed
                user.password_hash = hash_password(password)
                user.is_active = True
        db.commit()

        # 2. Seed Tables
        if db.query(Table).count() == 0:
            tables = [
                Table(table_number="T01", capacity=2, zone="Indoor"),
                Table(table_number="T02", capacity=2, zone="Indoor"),
                Table(table_number="T03", capacity=4, zone="Indoor"),
                Table(table_number="T04", capacity=4, zone="Indoor"),
                Table(table_number="T05", capacity=6, zone="Indoor"),
                Table(table_number="T06", capacity=4, zone="Terrace"),
                Table(table_number="T07", capacity=4, zone="Terrace"),
                Table(table_number="VIP1", capacity=8, zone="VIP Room"),
            ]
            db.add_all(tables)
            db.commit()

        # 3. Seed Categories
        if db.query(Category).count() == 0:
            cat_beef = Category(name="สเต๊กเนื้อ (Beef Steak)", sort_order=1)
            cat_pork = Category(name="สเต๊กหมู/ไก่ (Pork & Chicken)", sort_order=2)
            cat_sides = Category(name="เครื่องเคียง & ทานเล่น", sort_order=3)
            cat_drinks = Category(name="เครื่องดื่ม", sort_order=4)
            db.add_all([cat_beef, cat_pork, cat_sides, cat_drinks])
            db.commit()

            # 4. Seed Menu Items
            item_ribeye = MenuItem(category_id=cat_beef.id, code="STK001", name="สเต๊กเนื้อริบอาย (Ribeye 250g)", price=450.0, description="เนื้อริบอายออสเตรเลีย นุ่ม ชุ่มฉ่ำ")
            item_tbone = MenuItem(category_id=cat_beef.id, code="STK002", name="สเต๊กทีโบน (T-Bone 350g)", price=550.0, description="เนื้อทีโบนเกรดพรีเมียม สัมผัสเข้มข้น")
            item_porkchop = MenuItem(category_id=cat_pork.id, code="STK003", name="พอร์คชอปสเต๊ก (Pork Chop)", price=220.0, description="พอร์คชอปหมักนุ่ม เสิร์ฟพร้อมซอส gravies")
            item_fries = MenuItem(category_id=cat_sides.id, code="SID001", name="เฟรนช์ฟรายส์ (French Fries)", price=89.0, description="มันฝรั่งทอดกรอบเสิร์ฟร้อน")
            item_cola = MenuItem(category_id=cat_drinks.id, code="DRK001", name="โค้กเย็น (Coke)", price=35.0, description="เครื่องดื่มอัดลม 325ml")

            db.add_all([item_ribeye, item_tbone, item_porkchop, item_fries, item_cola])
            db.commit()

            # 5. Seed Modifiers
            group_done = ModifierGroup(name="ระดับความสุก (Doneness)")
            db.add(group_done)
            db.commit()

            opt_rare = ModifierOption(group_id=group_done.id, name="Rare (ดิบมาก)", extra_price=0.0)
            opt_med_rare = ModifierOption(group_id=group_done.id, name="Medium Rare (กึ่งดิบกึ่งสุก)", extra_price=0.0)
            opt_medium = ModifierOption(group_id=group_done.id, name="Medium (ปานกลาง)", extra_price=0.0)
            opt_well = ModifierOption(group_id=group_done.id, name="Well Done (สุกทั่ว)", extra_price=0.0)

            group_sauce = ModifierGroup(name="เลือกซอส (Sauces)")
            db.add(group_sauce)
            db.commit()

            opt_sauce_pepper = ModifierOption(group_id=group_sauce.id, name="ซอสพริกไทยดำ", extra_price=0.0)
            opt_sauce_mushroom = ModifierOption(group_id=group_sauce.id, name="ซอสเห็ดทรัฟเฟิล", extra_price=20.0)

            db.add_all([opt_rare, opt_med_rare, opt_medium, opt_well, opt_sauce_pepper, opt_sauce_mushroom])
            db.commit()

            # 6. Seed Ingredients & BOM
            ing_ribeye = Ingredient(code="ING001", name="เนื้อริบอาย (Ribeye Beef)", unit="g", min_stock_alert=1000.0, cost_per_unit=1.2) # 1.2 THB/g
            ing_tbone = Ingredient(code="ING002", name="เนื้อทีโบน (T-Bone Beef)", unit="g", min_stock_alert=1500.0, cost_per_unit=1.1)
            ing_pork = Ingredient(code="ING003", name="เนื้อพอร์คชอป (Pork Chop)", unit="g", min_stock_alert=1000.0, cost_per_unit=0.5)
            ing_fries = Ingredient(code="ING004", name="มันฝรั่งแช่แข็ง (Fries)", unit="g", min_stock_alert=2000.0, cost_per_unit=0.2)

            db.add_all([ing_ribeye, ing_tbone, ing_pork, ing_fries])
            db.commit()

            # BOM Mapping
            bom_ribeye = RecipeBOM(menu_item_id=item_ribeye.id, ingredient_id=ing_ribeye.id, quantity_required=250.0, unit="g")
            bom_tbone = RecipeBOM(menu_item_id=item_tbone.id, ingredient_id=ing_tbone.id, quantity_required=350.0, unit="g")
            bom_pork = RecipeBOM(menu_item_id=item_porkchop.id, ingredient_id=ing_pork.id, quantity_required=200.0, unit="g")
            bom_fries = RecipeBOM(menu_item_id=item_fries.id, ingredient_id=ing_fries.id, quantity_required=150.0, unit="g")

            db.add_all([bom_ribeye, bom_tbone, bom_pork, bom_fries])
            db.commit()

            # 7. Seed Initial Stock Lots (FIFO/FEFO Testing)
            today = date.today()
            lot1_ribeye = StockLot(
                ingredient_id=ing_ribeye.id,
                lot_number="LOT-RIB-001",
                initial_quantity=2500.0, # 2.5 kg
                remaining_quantity=2500.0,
                unit_cost=1.2,
                expiry_date=today + timedelta(days=5), # Expiring in 5 days (FEFO Priority 1)
                received_date=datetime.now(timezone.utc) - timedelta(days=2)
            )
            lot2_ribeye = StockLot(
                ingredient_id=ing_ribeye.id,
                lot_number="LOT-RIB-002",
                initial_quantity=5000.0, # 5.0 kg
                remaining_quantity=5000.0,
                unit_cost=1.18,
                expiry_date=today + timedelta(days=12), # Expiring in 12 days (FEFO Priority 2)
                received_date=datetime.now(timezone.utc)
            )

            lot1_tbone = StockLot(
                ingredient_id=ing_tbone.id,
                lot_number="LOT-TB-001",
                initial_quantity=3500.0,
                remaining_quantity=3500.0,
                unit_cost=1.1,
                expiry_date=today + timedelta(days=7),
                received_date=datetime.now(timezone.utc) - timedelta(days=1)
            )

            lot1_pork = StockLot(
                ingredient_id=ing_pork.id,
                lot_number="LOT-PC-001",
                initial_quantity=4000.0,
                remaining_quantity=4000.0,
                unit_cost=0.5,
                expiry_date=today + timedelta(days=10),
                received_date=datetime.now(timezone.utc)
            )

            lot1_fries = StockLot(
                ingredient_id=ing_fries.id,
                lot_number="LOT-FRY-001",
                initial_quantity=10000.0,
                remaining_quantity=10000.0,
                unit_cost=0.2,
                expiry_date=today + timedelta(days=30),
                received_date=datetime.now(timezone.utc)
            )

            db.add_all([lot1_ribeye, lot2_ribeye, lot1_tbone, lot1_pork, lot1_fries])
            db.commit()

        print("[SEED SUCCESS] Database initialized with default users, menu, BOM, and stock lots.")
    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Failed to seed database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
