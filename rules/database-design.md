# Database Design & Operations (Local Embedded DB - SQLite)

> กฎเกณฑ์และข้อปฏิบัติด้าน Database สำหรับ Local Embedded Database (SQLite + SQLAlchemy + Alembic)

## 1. Schema Design & SQLite Optimization
- ใช้ **SQLite** เป็น Local Embedded Database ทำงานแบบ Standalone และ Offline-First 100%
- เปิดใช้งาน **WAL Mode (Write-Ahead Logging)** เสมอ (`PRAGMA journal_mode=WAL;`) เพื่อรองรับ Concurrent Read/Write โดยไม่เกิด Database Locked
- เปิดใช้งาน **Foreign Key Constraints** ทุกครั้งที่สร้าง Connection (`PRAGMA foreign_keys=ON;`)
- ทุก Table ต้องมี Primary Key (`id` Integer Autoincrement หรือ UUID String) และ Audit Timestamps (`created_at`, `updated_at`)

## 2. Tools & ORM
- ใช้ **SQLAlchemy 2.0+ (Declarative Mapping)** สำหรับ Python ORM ร่วมกับ Type Hints
- ใช้ **Alembic** จัดการ Database Migrations (ห้ามปรับโครงสร้าง Table โดยตรง)

## 3. Query Performance & Safety
- **ห้าม** ยิง Raw SQL ด้วย String Formatting/Concatenation เพื่อป้องกัน SQL Injection (ให้ใช้ SQLAlchemy Query Builder/ORM หรือ Parameterized Query)
- สร้าง Index ในคอลัมน์ที่ถูกค้นหาบ่อย เช่น `sku`, `batch_number`, `expiry_date`, `table_number`, `status`

## 4. Transaction Management & Stock Consistency
- ใช้ SQLAlchemy Session Transaction ในการจัดการการตัดสต๊อก BOM (Bill of Materials) และ Lot FIFO/FEFO
- การตัดสต๊อกและเปิด/ปิดบิลต้องอยู่ใน **Single Transaction (ACID)** เสมอ หากมีขั้นตอนใดล้มเหลวต้อง `rollback()` ทั้งหมด
- ใช้ Context Manager `with session.begin():` เพื่อความปลอดภัยในการบริหาร Connection/Transaction

## 5. Soft Deletion & Data Retention
- ข้อมูลหลัก (เช่น เมนู, วัตถุดิบ, ผู้ใช้งาน) ใช้ Soft Delete (`is_active = Column(Boolean, default=True)` หรือ `deleted_at`)
- รายการบิลขายและประวัติการตัดสต๊อก **ห้ามลบเด็ดขาด** (ให้บันทึกเป็น Cancelled/Voided status พร้อม Audit Log)

## 6. Backup & Recovery Strategy
- ระบบต้องมีฟังก์ชัน Auto-Backup ไฟล์ `.db` อัตโนมัติ (เช่น สำรองข้อมูลรายวัน หรือก่อนปิดกะประจำวัน)
- ใช้ SQLite `backup()` API หรือการคัดลอกไฟล์ DB ในขณะเปิด WAL mode ได้อย่างปลอดภัย

## 7. Data Seeding & Initialization
- มี script สตรีมข้อมูลเริ่มต้น (Initial Seed) สำหรับสร้าง Default Roles, Admin User, Categories, และ Unit Master Tables
- Seed Script ต้องเป็น Idempotent (รันซ้ำได้โดยไม่เกิดข้อมูลซ้ำซ้อน)

