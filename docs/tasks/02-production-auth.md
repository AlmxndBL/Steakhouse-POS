# Task 02: Production Authentication Boundary

## Goal

แยก dev/test quick login และ seeded accounts ออกจาก production อย่างชัดเจน

## Scope

- ใช้ `APP_ENV` หรือ `ENVIRONMENT` เป็นตัวควบคุม
- quick demo login แสดงเฉพาะ development/test
- production ห้าม reset default passwords ทุก startup
- เพิ่ม password policy production อย่างน้อย 8 ตัวอักษร
- เพิ่ม login failure feedback ที่ปลอดภัยและไม่เผยข้อมูลเกินจำเป็น

## Acceptance criteria

- production ไม่มี quick-login
- production ไม่สร้างหรือ reset default accounts โดยอัตโนมัติ
- dev/test ยัง seed accounts ได้
- tests ครอบคลุมทั้ง production และ development paths
