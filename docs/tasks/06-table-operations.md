# Task 06: Table Operations

## Goal

รองรับงานโต๊ะจริงและลดความผิดพลาดในการย้าย/รวม/แยกบิล

## Scope

- เพิ่มสถานะ `WAITING_PAYMENT` หากจำเป็นหลังตรวจ domain
- ย้ายโต๊ะ, รวมโต๊ะ, แยกบิล, split bill
- table card แสดง status text ไม่พึ่งสีอย่างเดียว
- audit ทุก operation ที่กระทบ order/table

## Acceptance criteria

- ย้ายโต๊ะไม่ทำให้ order หรือ stock relationship เสีย
- split/merge คำนวณยอดและ receipt ถูกต้อง
- unauthorized role ทำ operation ไม่ได้
