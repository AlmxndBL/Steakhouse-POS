# 🗺️ AI Context Index & Project Architecture Map (Apex 4.0)

> **Single Source of Truth สำหรับ AI Agent:** สรุปโครงสร้าง สถาปัตยกรรม ฐานข้อมูล และสถานะของโปรเจกต์ Steakhouse POS เพื่อให้ Agent ทุกตัวเข้ามาทำงานต่อได้ทันทีโดยไม่ต้องสแกนหาไฟล์ทั้งระบบ
> ⚠️ **Security Notice:** ห้ามใส่ Connection String, API Keys, Passwords หรือ Secrets จริงลงในไฟล์นี้โดยเด็ดขาด ให้ใช้ Environment Variables หรือ Pattern `<secret:VAR_NAME>` แทนเสมอ

---

## 📌 1. ภาพรวมโปรเจกต์ (Project Overview)

- **ชื่อโปรเจกต์:** Steakhouse POS & Recipe Inventory Management System
- **คำอธิบาย:** ระบบบริหารจัดการร้านสเต๊กและคลังวัตถุดิบแบบครบวงจร รองรับทั้งหน้าร้าน (POS), จอคิวครัว (KDS), และระบบหลังบ้านผู้บริหาร (Executive Back-office) พร้อมระบบคำนวณต้นทุนวัตถุดิบ Recipe BOM แบบอัตโนมัติ
- **AI Agent Protocol:** Apex-core v4.0 (Clean `.apex` Container Architecture)
- **Tech Stack หลัก:**
  - **Core Framework:** Python 3.11+ + Flet 0.86.5 (GUI & Web App)
  - **Database & ORM:** SQLite (`pos_data.db` Local) / PostgreSQL (Docker) + SQLAlchemy ORM
  - **Security & Auth:** Username + Password (bcrypt hashing) + RBAC 5 Roles + 1-Click Dev Persona Switcher
  - **Infrastructure:** Docker Compose (Multi-stage build, Port 8000)
- **Environment Status:** Development & Sandbox Tested (100% Pass)

---

## 📁 2. โครงสร้างโฟลเดอร์หลัก (Project Directory Blueprint)

```text
POS flet/
├── .apex/                     # ⚡ Apex-core v4.0 Container (Rules, Skills, Templates, Scripts)
│   ├── rules/                 # 6 Core Engineering Pillars (01-security to 06-testing)
│   ├── skills/                # 4 Consolidated Skills (backend-data, cartography, frontend, quality-verify)
│   ├── templates/             # Architecture Blueprints, UI & Utils
│   └── scripts/               # Context Scanner, Git Shield, Framework Verifier
├── AGENTS.md                  # 🧠 Master AI Agent Operating Protocol (v4.0)
├── AI-Context-Index.md        # 🗺️ แผนที่สรุปบริบทโปรเจกต์ (ไฟล์นี้)
├── docker-compose.yml         # 🐳 Docker Compose (App & PostgreSQL DB)
├── Dockerfile                 # 📦 Multi-stage Python 3.11 build
├── main.py                    # 🚦 App Entrypoint & RBAC Route Dispatcher
├── requirements.txt           # 📦 Python Dependencies
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
├── utils/                     # 🛠️ Utility Functions & Helpers
│   ├── export_csv.py          # CSV File Export Engine
│   └── formatters.py          # Currency & Date/Time Formatting
│
└── tests/                     # 🧪 Unit & Integration Test Suite
```

---

## 🗄️ 3. Core Domain Models (ฐานข้อมูลหลัก)

- **User (`users`):** ระบบบัญชีและสิทธิ์ RBAC (Admin, Manager, Cashier, Chef, Waiter) + Password Hash (bcrypt)
- **DiningTable (`dining_tables`):** ผังโต๊ะ โซน (Indoor, VIP, Outdoor) และสถานะโต๊ะ (Available, Occupied, Reserved, Billed)
- **MenuCategory & MenuItem (`menu_categories`, `menu_items`):** เมนูอาหาร หมวดหมู่ ราคา ต้นทุนโดยประมาณ และสถานะเปิด/ปิดขาย
- **Ingredient & StockLot (`ingredients`, `stock_lots`):** คลังวัตถุดิบ รายการล็อตนำเข้า (FIFO), วันหมดอายุ, ต้นทุนต่อหน่วย, Reorder Point
- **RecipeItem (`recipe_items`):** สูตรอาหาร (BOM) เชื่อมโยงเมนูกับวัตถุดิบและสัดส่วนปริมาณที่ใช้ตัดสต็อก
- **StockMovement (`stock_movements`):** ประวัติการเคลื่อนไหวสต็อก (In, Out, Waste, Adjustment, Sale)
- **Order & OrderItem (`orders`, `order_items`):** ข้อมูลบิล รายการอาหารที่สั่ง สถานะออเดอร์ (Pending, Cooking, Served, Completed, Cancelled) และ Options/Modifiers (เช่น ความสุก, ซอส)
- **Payment (`payments`):** บันทึกการชำระเงิน (Cash, QR PromptPay, Credit Card), ยอดเงินที่รับ, เงินทอน, และเลขอ้างอิง E-Receipt

---

## 🔌 4. Key Workspaces & Route Map

- `🔑 /login` $\rightarrow$ Authentication Screen + 1-Click Dev Persona Switcher
- `👑 /admin` $\rightarrow$ Executive Dashboard (KPI Cards, Real-time Sales, Daily Revenue)
- `🥩 /admin/menus` $\rightarrow$ Menu Management (Create/Edit Menu, Category, Cost Estimator)
- `🪑 /admin/tables` $\rightarrow$ Table & Zone Floor Plan Management
- `👥 /admin/staff` $\rightarrow$ Employee Lifecycle & Role Permission Assignment
- `📦 /admin/stock` $\rightarrow$ Inventory, Stock Inbound, Recipe BOM, Waste Log
- `📊 /admin/reports` $\rightarrow$ Sales Analytics, Category Share, Export CSV
- `🍽️ /tables` $\rightarrow$ Interactive Dine-in Table Floor Map (POS Front)
- `💵 /pos` $\rightarrow$ Point of Sale Ordering & Payment Terminal
- `👨‍🍳 /kds` $\rightarrow$ Kitchen Display System (Real-time Order Queue for Chefs)

---

## 🚨 5. Project-Specific Red-Lines (ข้อห้ามเฉพาะโปรเจกต์นี้)

1. **ห้ามตัดสต็อกแบบข้าม FIFO:** การตัดสต็อกวัตถุดิบผ่าน `bom_engine.py` ต้องเรียงตามล็อตเข้าก่อนออกก่อน (FIFO by `created_at` / `expiry_date`) เสมอ
2. **ห้าม Hardcode Password:** รหัสผ่านพนักงานทุกคนต้องถูก Hash ด้วย `bcrypt` ก่อนบันทึกลงใน Database เสมอ
3. **ห้าม Bypass RBAC Layer:** ทุก Action ที่เกี่ยวกับ Admin (จัดการพนักงาน, ปรับแต่งสต็อก, ดูรายงานยอดขาย) ต้องผ่านการตรวจ Role Permission ที่ `auth_service.py` เสมอ
4. **Dev Persona Quick Login Gate:** ปุ่มลัดสำหรับ Login ทดสอบในหน้า `login_view.py` ต้องทำงานเฉพาะในโหมด Development และต้องไม่เปิดช่องโหว่เมื่อ Build ขึ้น Production
5. **No Blind Global Git Restores:** ในกรณีเกิดข้อผิดพลาด ให้ Rollback เฉพาะไฟล์ที่แก้ไขในรอบนั้น ห้ามสั่ง `git restore .` หรือ `git reset --hard` เด็ดขาด
