# 🗺️ AI Context Index & Project Architecture Map (Nexus)

> **Single Source of Truth สำหรับ AI Agent:** สรุปโครงสร้าง สถาปัตยกรรม ฐานข้อมูล และสถานะของโปรเจกต์ Steakhouse POS เพื่อให้ Agent ทุกตัวเข้ามาทำงานต่อได้ทันทีโดยไม่ต้องสแกนหาไฟล์ทั้งระบบ
> ⚠️ **Security Notice:** ห้ามใส่ Connection String, API Keys, Passwords หรือ Secrets จริงลงในไฟล์นี้โดยเด็ดขาด

---

## 📌 1. ภาพรวมโปรเจกต์ (Project Overview)

- **ชื่อโปรเจกต์:** Steakhouse POS & Recipe Inventory Management System
- **คำอธิบาย:** ระบบบริหารจัดการร้านสเต๊กและคลังวัตถุดิบแบบครบวงจร รองรับทั้งหน้าร้าน (POS), จอคิวครัว (KDS), และระบบหลังบ้านผู้บริหาร (Executive Back-office) พร้อมระบบคำนวณต้นทุนวัตถุดิบ Recipe BOM แบบอัตโนมัติ
- **Tech Stack หลัก:**
  - **Core Framework:** Python 3.11+ + Flet 0.86.5 (GUI & Web App)
  - **Database & ORM:** PostgreSQL (Docker) / SQLite (`pos_data.db` Local) + SQLAlchemy ORM
  - **Security & Auth:** Username + Password (bcrypt hashing) + RBAC 5 Roles + 1-Click Dev Persona Switcher
  - **Infrastructure:** Docker Compose (Multi-stage build, Port 8000)
- **Environment Status:** Development & Sandbox Tested (100% Pass)

---

## 📁 2. โครงสร้างโฟลเดอร์หลัก (Project Directory Blueprint)

```text
POS flet/
├── AGENTS.md                  # 🧠 Master Agent Rules & Multi-Role System Blueprint
├── AI-Context-Index.md        # 🗺️ แผนที่สรุปบริบทโปรเจกต์ (ไฟล์นี้)
├── docker-compose.yml         # 🐳 Docker Compose (App & PostgreSQL DB)
├── Dockerfile                 # 📦 Multi-stage Python 3.11 build
├── main.py                    # 🚦 App Entrypoint & RBAC Route Dispatcher
│
├── database/                  # 🗄️ ฐานข้อมูลและ Seeding
│   ├── connection.py          # SQLAlchemy SessionLocal & Engine setup
│   ├── models.py              # Database Models (User, Table, Menu, BOM, Lot, Order)
│   └── seed.py                # Database Seeder & Defensive Migration Scripts
│
├── views/                     # 🖥️ หน้าจอหลักแยกตาม Workspace (Separation of Concerns)
│   ├── login_view.py          # 🔑 หน้า Login + 1-Click Dev Persona Quick Login
│   ├── admin_dashboard_view.py# 👑 Executive Admin Dashboard & Summary KPIs
│   ├── admin_menu_view.py     # 🥩 จัดการเมนูอาหาร & หมวดหมู่ (/admin/menus)
│   ├── admin_table_view.py    # 🪑 จัดการผังโต๊ะ & โซนที่นั่ง (/admin/tables)
│   ├── staff_view.py          # 👥 จัดการพนักงาน & กำหนดสิทธิ์ (/admin/staff)
│   ├── stock_view.py          # 📦 คลังวัตถุดิบ, รับของเข้า, BOM, ของเสีย (/admin/stock)
│   ├── reports_view.py        # 📊 รายงานยอดขาย, Interactive Charts & CSV (/admin/reports)
│   ├── table_map_view.py      # 🍽️ ผังโต๊ะหน้าร้าน POS (/tables)
│   ├── pos_main_view.py       # 💵 ตะกร้าสั่งอาหาร & คิดเงิน (/pos)
│   └── kds_view.py            # 👨‍🍳 จอคิวครัวสำหรับเชฟ (/kds)
│
├── services/                  # ⚙️ Business Domain Engines & Logic
│   ├── auth_service.py        # Bcrypt Authentication & RBAC Checks
│   ├── bom_engine.py          # Recipe BOM Calculation & FIFO Stock Lot Deduction
│   ├── order_service.py       # Order Lifecycle, Modifiers & Checkout Calculations
│   ├── report_service.py      # Financial Metrics, Top Sellers, Category Share & CSV Generator
│   ├── receipt_service.py     # PIL Dynamic E-Receipt Generator (Base64)
│   ├── staff_service.py       # Staff Lifecycle, Duplicate Username Check & Password Reset
│   └── table_service.py       # Table Management & Seating Layout
│
├── components/                # 🧩 Reusable Dumb & Modal Components
│   ├── ereceipt_modal.py      # E-Receipt Viewer & Dialog
│   ├── modifier_dialog.py     # Steak Doneness & Sauce Customization Modal
│   └── payment_dialog.py      # Cash / QR PromptPay Checkout Modal
│
├── tests/                     # 🧪 Automated Sandbox Test Suite (DoD Gate)
│   ├── run_all_tests.py       # 🚀 Master Test Runner (ANSI/ASCII Summary)
│   ├── test_auth_rbac.py      # 👥 Multi-role Persona Matrix Tests
│   ├── test_bom_inventory.py  # 📦 Stock Purchase In, Lots, Wastage & BOM Tests
│   ├── test_form_validation.py# 🛡️ Input Validation Tests (Prices, Dates, Capacity)
│   ├── test_pos_order_flow.py # 💵 End-to-End Dine-in & Checkout Flow Tests
│   ├── test_reports_analytics.py # 📊 Sales Aggregation, Charts & CSV Export Tests
│   ├── test_settings_crud.py  # 🥩 Menu & Table CRUD Lifecycle Tests
│   └── test_staff_management.py # 👥 Staff CRUD & Duplicate Prevention Tests
│
└── utils/
    └── navigation.py          # Navigation helper with view pop safety
```

---

## 👥 3. ระบบยืนยันตัวตนและสิทธิ์ (Authentication & RBAC Matrix)

| Username | Password | Role | สิทธิ์การเข้าถึง (Accessible Workspaces) |
|---|---|---|---|
| `owner` | `admin1234` | `UserRole.OWNER` | ทุกหน้า (Dashboard, Staff, Menus, Tables, Stock, Reports, POS, KDS) |
| `manager` | `mgr1234` | `UserRole.MANAGER` | ทุกหน้า (Dashboard, Staff, Menus, Tables, Stock, Reports, POS, KDS) |
| `cashier` | `cash1234` | `UserRole.CASHIER` | หน้าร้าน POS (`/tables`, `/pos`), จอครัว (`/kds`) |
| `waiter` | `waiter1234` | `UserRole.WAITER` | ผังโต๊ะ & สั่งอาหาร (`/tables`, `/pos`) |
| `kitchen` | `cook1234` | `UserRole.KITCHEN` | จอคิวครัวเท่านั้น (`/kds`) |

---

## 🗄️ 4. ฐานข้อมูลและแบบจำลอง (Core Domain Models)

1. **`User`:** `id`, `username` (unique), `password_hash`, `name`, `role` (OWNER/MANAGER/CASHIER/WAITER/KITCHEN), `phone`, `is_active`
2. **`Table`:** `id`, `table_number`, `capacity`, `zone`, `status` (VACANT/OCCUPIED/RESERVED)
3. **`Category` & `MenuItem`:** หมวดหมู่อาหาร, ชื่อเมนู, ราคาขาย, สถานะเปิด/ปิดการขาย, Soft-delete (`is_active`)
4. **`Ingredient` & `RecipeBOM`:** วัตถุดิบ, หน่วยนับ, ต้นทุนเฉลี่ย, สูตรอาหารผูกกับ Menu Item
5. **`StockLot` & `StockTransaction`:** วัตถุดิบราย Lot (FIFO), วันหมดอายุ, ประวัติการรับของเข้า (Purchase In) และของเสีย (Wastage)
6. **`Order` & `OrderItem`:** รายการสั่งอาหาร, ประเภทบิล (Dine-in/Takeaway), ส่วนลด, Service Charge 10%, VAT 7%, ยอดสุทธิ, สถานะบิล (PENDING/CONFIRMED/COOKING/READY/PAID/CANCELLED)
7. **`PaymentAuditLog`:** บันทึกประวัติการรับชำระเงิน ตรวจสอบความถูกต้องของกระแสเงินสด

---

## 🧪 5. การทดสอบและการรันระบบ (Verification & Run Commands)

### 🚀 รันระบบในโหมด Docker:
```bash
docker-compose up -d --build
# เข้าใช้งานผ่าน Web Browser: http://localhost:8000
```

### 🧪 รัน Master Sandbox Test Suite (17/17 Passed 100%):
```bash
docker-compose exec -e PYTHONPATH=/app -T app python tests/run_all_tests.py
```

---

## 📌 6. สถานะงานปัจจุบันและสิ่งที่ต้องทำต่อในรอบถัดไป (Pending Tasks & Next Steps)

- **สถานะระบบปัจจุบัน:** ฟังก์ชันหลักทั้งหมด (Auth, RBAC, Back-office, POS, KDS, Stock BOM, Reports, Sandbox Tests 17/17) ทำงานสมบูรณ์
- **📋 ประเด็นที่ค้างอยู่ (Pending Issue for Next Session):**
  - **ปัญหา:** ปุ่ม *"📥 ดาวน์โหลดไฟล์ (Download)"* บนโมดอล Export CSV ในหน้ารายงาน (`/admin/reports`) เมื่อรันผ่าน Web Browser (Docker) ยังไม่สามารถทริกเกอร์ให้ Browser โหลดไฟล์ลงเครื่อง Client ได้ทันที
  - **การทำงานปัจจุบัน:** ไฟล์ถูกเซฟลงโฟลเดอร์ `exports/` บน Server เรียบร้อยแล้ว และสามารถใช้ปุ่ม *"📋 คัดลอกข้อมูล"* นำไปวางใน Excel / Sheets ได้ แต่ปุ่มดาวน์โหลดตรงผ่านบราวเซอร์ยังต้องปรับปรุง
  - **แนวทางแก้ไขในรอบหน้า (Action Plan):**
    1. ทำ REST API Endpoint ดาวน์โหลดไฟล์ตรง เช่น `/api/download/{filename}` โดยใช้ FastAPI `FileResponse(..., headers={"Content-Disposition": "attachment; filename=..."})`
    2. หรือใช้ JavaScript Blob Download Trigger ผ่าน `page.run_javascript(...)`

