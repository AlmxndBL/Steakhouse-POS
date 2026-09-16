# 🥩 Steakhouse POS - ระบบจัดการร้านสเต๊กและคลังวัตถุดิบครบวงจร

ระบบ Point of Sale (POS) และระบบบริหารจัดการร้านอาหารที่พัฒนาขึ้นมาโดยเฉพาะสำหรับร้านสเต๊ก (รองรับทั้ง Dine-in, Takeaway, และ Kitchen Queue) โดดเด่นด้วยการควบคุมต้นทุนวัตถุดิบแบบเรียลไทม์ผ่าน **Recipe BOM (Bill of Materials)**, การตัดสต๊อกเนื้อสัตว์แบบ **FIFO/FEFO**, ระบบ **Multi-Role RBAC**, และแดชบอร์ดสรุปยอดขายพร้อม **Interactive Charts & CSV Export**

---

## 🎯 จุดเด่นและฟังก์ชันของระบบ (Key Features)

### 1. 🔑 ระบบยืนยันตัวตนและความปลอดภัย (Authentication & RBAC)
- **Username + Password (Bcrypt Hashing):** ระบบล็อกอินความปลอดภัยสูง บันทึกประวัติการเข้าใช้งาน (Audit Logs)
- **5 ระดับสิทธิ์ (RBAC Matrix):** 
  - `👑 OWNER (เจ้าของร้าน)`: สิทธิ์สูงสุด จัดการร้าน พนักงาน เมนู โต๊ะ สต๊อก และดูรายงานการเงิน
  - `👔 MANAGER (ผู้จัดการ)`: บริหารจัดการทั่วไป เมนู สต๊อก พนักงาน และรายงาน
  - `💵 CASHIER (แคชเชียร์)`: รับออเดอร์หน้าร้าน คิดเงิน ออกสลิป E-Receipt
  - `🍽️ WAITER (พนักงานเสิร์ฟ)`: ดูผังโต๊ะ รับออเดอร์ ปรับแต่งระดับความสุก/ซอส
  - `👨‍🍳 KITCHEN (เชฟในครัว)`: ดูจอคิวทำอาหาร (KDS) และอัปเดตสถานะอาหาร
- **🚀 1-Click Dev Persona Quick Login:** ปุ่มลัดสลับบทบาทบนหน้า Login สำหรับโหมดพัฒนา/ทดสอบ สลับ Role ได้ทันทีในคลิกเดียว

---

### 2. 👑 ระบบบริหารจัดการผู้บริหาร (Executive Back-office Workspaces)
- **📊 Executive Dashboard (`/admin`):** สรุป KPI สำคัญประจำวัน (ยอดขายรวม, จำนวนบิล, โต๊ะที่มีลูกค้า, การแจ้งเตือนวัตถุดิบใกล้หมด)
- **👥 Staff Management (`/admin/staff`):** เพิ่ม/แก้ไขข้อมูลพนักงาน กำหนดตำแหน่ง และรีเซ็ตรหัสผ่าน
- **🥩 Menu & Category Management (`/admin/menus`):** จัดการรายการอาหาร หมวดหมู่ ปรับราคา และเปิด/ปิดการขาย
- **🪑 Table & Zone Layout (`/admin/tables`):** เพิ่ม/ลบโต๊ะอาหาร กำหนดจำนวนที่นั่ง และจัดโซนร้าน (Indoor, Terrace, VIP, Outdoor)
- **📦 Stock & Recipe BOM (`/admin/stock`):** รับวัตถุดิบเข้าคลัง (Purchase In), บันทึกของเสีย (Wastage), และผูกสูตรอาหาร (BOM)
- **📈 Visual Analytics & Reports (`/admin/reports`):**
  - กราฟแท่งแนวโน้มยอดขาย 7 วันล่าสุด (`BarChart`)
  - กราฟวงกลมสัดส่วนยอดขายตามหมวดหมู่อาหาร (`PieChart`)
  - กราฟโดนัทเปรียบเทียบช่องทางชำระเงิน เงินสด vs QR PromptPay
  - 5 อันดับเมนูขายดีที่สุด (Top 5 Best Sellers)
  - คำนวณ Food Cost % และ Gross Margin % อัตโนมัติ
  - ปุ่มส่งออกข้อมูลยอดขายเป็นไฟล์ **Excel / CSV**

---

### 3. 🍽️ งานหน้าร้านและคิดเงิน (Front of House POS)
- **Interactive Floor Plan (`/tables`):** ผังโต๊ะอาหารแบบเรียลไทม์ แสดงสถานะโต๊ะว่าง (สีเขียว) / มีลูกค้า (สีส้ม)
- **Steak Customization & Modifiers (`/pos`):** ปรับแต่งระดับความสุกของเนื้อ (Rare, Medium Rare, Medium, Medium Well, Well Done) และเลือกซอสสเต๊ก
- **Billing & Discount Engine:** คำนวณ Service Charge 10%, VAT 7%, และส่วนลด (บาท / %)
- **🧾 E-Receipt Generation:** สร้างสลิปใบเสร็จดิจิทัลแบบ Base64 พร้อมแสดงผลและบันทึกภาพได้ทันที

---

### 4. 👨‍🍳 ระบบจอแสดงผลในครัว (Kitchen Display System - KDS)
- **Live Order Queue (`/kds`):** จอแสดงรายการอาหารที่ต้องทำแบบเรียลไทม์ แยกตามโต๊ะและเวลาสั่ง
- **Status Workflow:** อัปเดตสถานะจาก `รอทำ (Pending)` ➔ `กำลังปรุง (Cooking)` ➔ `พร้อมเสิร์ฟ (Ready)`

---

## 🛠️ เทคโนโลยีที่ใช้ (Tech Stack)

- **UI & Frontend Framework:** [Python Flet 0.86.5](https://flet.dev/) (Flutter-powered Native GUI & Web Engine)
- **Backend Language:** Python 3.11+
- **Database:** PostgreSQL (Docker or local PostgreSQL server)
- **ORM:** SQLAlchemy
- **Containerization:** Docker & Docker Compose (Multi-stage build)
- **Security:** `bcrypt`, `pydantic`, `cryptography`
- **Image & Receipt:** `Pillow`, `qrcode`

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
POS flet/
├── AGENTS.md                  # Master Agent Rules & Multi-Role Blueprint
├── AI-Context-Index.md        # Single Source of Truth (Nexus)
├── docker-compose.yml         # Docker Compose Config (App & PostgreSQL DB)
├── Dockerfile                 # Multi-stage Python 3.11 Image Definition
├── main.py                    # App Entry Point & RBAC Route Guard
│
├── app/                       # Application package
│   ├── database/              # การเชื่อมต่อฐานข้อมูลและ Data Seeder
│   ├── connection.py          # SQLAlchemy SessionLocal
│   ├── models.py              # Models (User, Table, Menu, BOM, Lot, Order)
│   └── seed.py                # Database Seeder & Auto Migration
│
│   ├── views/                 # หน้าจอแยกตาม Workspace
│   ├── login_view.py          # หน้า Login + 1-Click Persona Switcher
│   ├── admin_dashboard_view.py# แดชบอร์ดผู้บริหาร
│   ├── admin_menu_view.py     # จัดการเมนูอาหาร (/admin/menus)
│   ├── admin_table_view.py    # จัดการผังโต๊ะ (/admin/tables)
│   ├── staff_view.py          # จัดการพนักงาน (/admin/staff)
│   ├── stock_view.py          # จัดการคลังและ BOM (/admin/stock)
│   ├── reports_view.py        # แดชบอร์ดรายงานและกราฟ (/admin/reports)
│   ├── table_map_view.py      # ผังโต๊ะหน้าร้าน (/tables)
│   ├── pos_main_view.py       # ระบบรับออเดอร์และคิดเงิน (/pos)
│   └── kds_view.py            # จอคิวครัว KDS (/kds)
│
│   ├── services/              # Business Logic & Engines
│   ├── auth_service.py        # Bcrypt Authentication
│   ├── bom_engine.py          # Recipe BOM & FIFO Lot Deduction
│   ├── order_service.py       # Order & Payment Calculations
│   ├── report_service.py      # Financial Metrics, Charts & CSV Export
│   ├── receipt_service.py     # Base64 E-Receipt Generator
│   ├── staff_service.py       # Staff CRUD & Password Reset
│   └── table_service.py       # Table CRUD & Seating Layout
│
│   ├── components/            # Reusable UI & Dialogs
│   └── utils/                 # Navigation, dialogs และ validators
├── docs/                      # Task checklist และ agent prompts
└── tests/                     # Automated Sandbox Test Suite (58/58 Passed)
```

---

## 🚀 การติดตั้งและเริ่มใช้งาน (Getting Started)

### 💻 วิธีที่ 1: รันในเครื่องแบบ Local
ต้องมี PostgreSQL 15+ ทำงานอยู่ก่อน แล้วตั้งค่า `DATABASE_URL` ให้ชี้ไปยังฐานข้อมูลนั้น

```powershell
$env:DATABASE_URL="postgresql://posadmin:pospassword@localhost:5432/pos_db"
```
1. ติดตั้ง Python 3.11+
2. ติดตั้ง Dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. รันโปรแกรม:
   ```bash
   python main.py
   ```
4. รันชุดทดสอบ:
   ```bash
   python tests/run_all_tests.py
   ```

ระบบใช้ PostgreSQL โดยกำหนด `DATABASE_URL` ใน environment; Docker Compose เตรียมฐานข้อมูลสำหรับการพัฒนาและสาธิตไว้ให้แล้ว

### 🐳 วิธีที่ 2: รันด้วย Docker (แนะนำสำหรับ Tester)
ติดตั้ง [Docker Desktop](https://www.docker.com/) แล้วรันคำสั่ง:
```bash
docker compose up -d --build
```
เข้าใช้งานผ่าน Web Browser ได้ทันทีที่: **[http://localhost:8000](http://localhost:8000)**

ตรวจสอบสถานะบริการ:

```bash
docker compose ps
docker compose exec -T db pg_isready -U posadmin -d pos_db
```

หยุดบริการโดยเก็บข้อมูลไว้:

```bash
docker compose down
```

---

Docker mode ใช้ PostgreSQL และ Flet Web ที่ `http://localhost:8000` เหมาะสำหรับสาธิตแบบหลายบริการ แต่ยังไม่ใช่ managed cloud deployment

---

## 🔐 บัญชีสำหรับทดสอบระบบ (Seeded Test Accounts)

| Username | Password | Role | สิทธิ์การเข้าถึงหน้าจอ |
|---|---|---|---|
| `owner` | `admin1234` | `OWNER` | เข้าถึงได้ทุกหน้า (Dashboard, Staff, Menus, Tables, Stock, Reports, POS, KDS) |
| `manager` | `mgr1234` | `MANAGER` | เข้าถึงได้ทุกหน้า (Dashboard, Staff, Menus, Tables, Stock, Reports, POS, KDS) |
| `cashier` | `cash1234` | `CASHIER` | หน้าร้าน POS (`/tables`, `/pos`) และจอครัว (`/kds`) |
| `waiter` | `waiter1234` | `WAITER` | ผังโต๊ะ & รับออเดอร์หน้าร้าน (`/tables`, `/pos`) |
| `kitchen` | `cook1234` | `KITCHEN` | จอคิวครัวเท่านั้น (`/kds`) |

> 💡 *บนหน้าจอ Login ในโหมด Dev จะมีปุ่มชิป **🚀 Quick Demo Login** ให้กด 1-Click เข้าใช้งานได้ทันทีโดยไม่ต้องพิมพ์รหัสผ่าน*

---

## 🎬 Demo Flow สำหรับการนำเสนอ

```text
Login ด้วย demo account
→ เลือกโต๊ะจาก /tables
→ เพิ่มเมนูและ modifier ใน /pos
→ ส่งรายการเข้า /kds
→ เปลี่ยนสถานะอาหาร
→ กลับไป checkout และสร้าง E-Receipt
→ ตรวจยอดขายและ CSV ที่ /admin/reports
```

บัญชี demo มีไว้สำหรับ local/classroom demonstration เท่านั้น ไม่ควรใช้เป็น production credentials

## 🧪 การทดสอบระบบ (Automated Sandbox Test Suite)

รันชุดทดสอบอัตโนมัติครอบคลุมทั้งระบบ (58/58 Tests Passed 100%):
```bash
python tests/run_all_tests.py
```

ผล verification ล่าสุด: `Ran 58 tests`, `OK`, `Failures: 0`, `Errors: 0`

รายละเอียด task สำหรับการพัฒนาต่ออยู่ที่ [`docs/tasks/README.md`](docs/tasks/README.md)

---
*Developed with Python, Flet & Modern Software Engineering Standards.*
