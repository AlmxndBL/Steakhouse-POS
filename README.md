# Steakhouse POS - ระบบจัดการร้านสเต๊กและคลังวัตถุดิบ

ระบบ Point of Sale (POS) ที่พัฒนาขึ้นมาโดยเฉพาะสำหรับร้านสเต๊ก (Dine-in และ Takeaway) จุดเด่นของระบบคือการจัดการคลังวัตถุดิบที่ซับซ้อน เช่น การตัดสต๊อกเนื้อสัตว์แบบเรียลไทม์ผ่านระบบ BOM (Bill of Materials) การจัดการสูตรอาหาร และระบบสินค้าคงคลังแบบเข้าก่อนออกก่อน (FIFO/FEFO)

---

## 🎯 จุดเด่นของระบบ (Key Features)

### 1. งานหน้าร้าน (Front of House)
- **Table Management:** จัดการผังโต๊ะ ดูสถานะโต๊ะ (ว่าง/ไม่ว่าง) รองรับการเปิดบิล, ย้ายโต๊ะ, รวมบิล และแยกบิล
- **Order Management:** สั่งอาหารและปรับแต่งเมนู (เช่น ความสุกของเนื้อ Rare/Medium/Well-done, เลือกซอส) 
- **Checkout & E-Receipt:** รองรับการรับชำระเงินและออกใบเสร็จอิเล็กทรอนิกส์ (E-Receipt) พร้อม QR Code

### 2. ระบบคลังวัตถุดิบ (Inventory & BOM Engine)
- **BOM (Bill of Materials):** ผูกสูตรอาหารกับวัตถุดิบ ระบบจะตัดสต๊อกอัตโนมัติตามสัดส่วนที่ตั้งไว้เมื่อมีการสั่งเมนู
- **Lot/Batch Tracking:** รองรับการจัดการวัตถุดิบเป็น Lot พร้อมวันหมดอายุ เพื่อใช้ในการตัดสต๊อกแบบ FIFO (First-In, First-Out)
- **Wastage Management:** บันทึกของเสียหรือวัตถุดิบที่ต้องตัดทิ้งพร้อมระบุสาเหตุ

### 3. ระบบผู้ใช้งานและสิทธิ์ (Authentication & RBAC)
- ล็อกอินด้วยระบบ PIN Code เพื่อความสะดวกรวดเร็วของพนักงาน
- แบ่งสิทธิ์การใช้งาน (Role-Based Access Control): เจ้าของร้าน (Owner), ผู้จัดการ (Manager), แคชเชียร์/พนักงานเสิร์ฟ (Staff)
- ระบบจำกัดการเข้าถึงเมนูหลังร้าน (Stock & Reports) สำหรับผู้ที่มีสิทธิ์เท่านั้น

### 4. แดชบอร์ดและรายงาน (Reports)
- รายงานยอดขายและข้อมูลเชิงลึก
- ระบบตรวจสอบสต๊อกคงเหลือ

---

## 🛠️ เทคโนโลยีที่ใช้ (Tech Stack)

- **Frontend / GUI:** [Flet](https://flet.dev/) (Python UI Framework ใช้งานร่วมกับ Flutter)
- **Backend Language:** Python 3.11+
- **Database:** SQLite (Embedded Local DB) สำหรับการทำงานแบบออฟไลน์
- **ORM:** SQLAlchemy (จัดการโมเดลฐานข้อมูล)
- **Others:** `pillow`, `qrcode` (สำหรับ E-Receipt), `bcrypt` (สำหรับความปลอดภัยของ PIN)

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
POS flet/
│
├── components/          # UI Components ที่ใช้งานซ้ำ (เช่น Numpad, Modal ใบเสร็จ, การ์ดโต๊ะ)
├── database/            # การเชื่อมต่อฐานข้อมูล, โมเดล ORM, และไฟล์ Seed ข้อมูลเริ่มต้น
├── services/            # Business Logic หลัก (BOM Engine, ระบบ Order, ระบบ Auth, ระบบใบเสร็จ)
├── utils/               # ฟังก์ชันช่วยเหลือ (Utility) เช่น ระบบ Navigation
├── views/               # หน้าจอหลักของแอปพลิเคชัน (Login, POS, ผังโต๊ะ, สต๊อก, รายงาน)
├── main.py              # ไฟล์หลักสำหรับรันโปรแกรม (Entry Point)
├── requirements.txt     # รายการ Dependency ของ Python
└── scope.md             # เอกสารรายละเอียดขอบเขตของระบบ
```

---

## 🚀 การติดตั้งและเริ่มใช้งาน

### 1. ความต้องการของระบบ (Prerequisites)
- Python 3.11 ขึ้นไป

### 2. ติดตั้ง Dependencies
เปิด Terminal หรือ Command Prompt ในโฟลเดอร์โปรเจกต์ แล้วรันคำสั่ง:
```bash
pip install -r requirements.txt
```

### 3. การรันโปรแกรม
เมื่อติดตั้ง Dependencies เสร็จสิ้น สามารถรันระบบได้ด้วยคำสั่ง:
```bash
python main.py
```
*(เมื่อรันโปรแกรมครั้งแรก ระบบจะทำการสร้างฐานข้อมูล `pos_data.db` และสร้างข้อมูลพื้นฐาน (Seed Data) ให้โดยอัตโนมัติ)*

---

## 🔐 ข้อมูลสำหรับการทดสอบ (Test Accounts)

ระบบได้สร้างบัญชีทดสอบไว้ให้ใช้งานเบื้องต้น โดยใช้ PIN Code ดังนี้:
- **Owner / Admin:** `1234` (เข้าได้ทุกระบบ)
- **Manager:** `5678` (เข้าได้ทุกระบบ)
- **Staff / Cashier:** `9012` (เข้าได้เฉพาะหน้า POS และผังโต๊ะ ไม่สามารถเข้าดูสต๊อกและรายงานได้)

---
*Developed with Python & Flet.*
