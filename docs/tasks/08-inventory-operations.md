# Task 08: Inventory Task Center

## Goal

ทำให้ stock page บอก “ต้องทำอะไรต่อ” แทนการเป็นเพียงตารางข้อมูล

## Scope

- low stock, expired/expiring lot, wastage anomaly และ pending count cards
- action ตรงจาก alert: receive, purchase suggestion, stock take, wastage
- ตรวจ FEFO/FIFO behavior
- เพิ่ม reason และ audit สำหรับ adjustments

## Acceptance criteria

- manager เห็นงานเร่งด่วนจากหน้าเดียว
- ทุก alert drill-down ไป operation ที่เกี่ยวข้อง
- stock quantity และ cost ไม่ติดลบโดยไม่มี explicit adjustment
