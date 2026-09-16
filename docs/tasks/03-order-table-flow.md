# Task 03: Order and Table Operational Flow

## Goal

ลดคลิกใน flow โต๊ะ → ออเดอร์ → ส่งครัว → ชำระเงิน

## Scope

- กดโต๊ะที่มี order ให้เปิด order เดิม
- แสดงจำนวนรายการ ยอดรวม เวลาเปิด และรายการใหม่บน table card
- แยก action `เพิ่มรายการ`, `ส่งครัว`, `ชำระเงิน`, `ปิดโต๊ะ`
- ส่งเฉพาะรายการใหม่เข้าครัว
- ป้องกันการส่งซ้ำและแสดงสถานะรายการชัดเจน

## Acceptance criteria

- waiter เปิดโต๊ะเดิมแล้วไม่เกิด order ซ้ำ
- cashier เห็น order ค้างและชำระเงินได้จาก table context
- duplicate send/checkout ถูกป้องกันและมี feedback
- ทดสอบ order lifecycle เดิมยังผ่าน
