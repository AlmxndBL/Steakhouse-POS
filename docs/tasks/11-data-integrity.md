# Task 11: Transaction and Data Integrity

## Goal

ป้องกัน order, payment, stock และ audit ขาดความสอดคล้อง

## Scope

- กำหนด transaction boundary ของ checkout
- stock deduction + payment + audit ต้อง atomic ตาม use case
- ตรวจ Decimal/Numeric สำหรับเงินและ quantity
- เพิ่ม idempotency/double-submit guard
- วางแผนและใช้งาน versioned migration สำหรับ PostgreSQL

## Acceptance criteria

- failure กลาง checkout rollback ตาม policy
- double checkout ไม่สร้าง payment/stock ซ้ำ
- migration ทดสอบบน fresh และ existing database
