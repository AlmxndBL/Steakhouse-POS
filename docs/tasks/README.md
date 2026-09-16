# POS Flet Task Board

เอกสารชุดนี้แยกงานสำหรับให้ sub-agent ทำแบบ loop โดยแต่ละ task ต้องทำตามลำดับ Discovery → Plan → Implement → Verify และห้ามแก้งานนอก scope

## สถานะสำหรับโปรเจกต์ห้องเรียน

- **Active delivery:** Task 01–12 อยู่ในขอบเขตการส่งมอบรอบนี้ตามคำสั่งของผู้ใช้
- **Verified evidence:** automated verification 57/57 ผ่าน; UI interactive และ Docker/PostgreSQL ยังต้องตรวจแยกตาม environment
- **Known limitation:** task board นี้ไม่ถือว่า task เสร็จเพียงเพราะ service-level tests ผ่าน ต้องมี evidence ตาม acceptance ของแต่ละ task

## ลำดับแนะนำ

1. `01-repository-structure.md` — จัด package/import และ baseline
2. `02-production-auth.md` — แยก local/dev กับ production auth
3. `03-order-table-flow.md` — โต๊ะ → ออเดอร์ → ครัว → ชำระเงิน
4. `04-pos-speed.md` — quick add, repeat order, modifier UX
5. `05-kds.md` — kitchen queue และ SLA timer
6. `06-table-operations.md` — table states, transfer, merge, split bill
7. `07-shift-and-approval.md` — shift, discount, cancellation approval
8. `08-inventory-operations.md` — stock task center และ purchase workflow
9. `09-role-home-dashboard.md` — role-based landing และ action dashboard
10. `10-ui-states.md` — loading/empty/error/ready และ visual consistency
11. `11-data-integrity.md` — transaction, migration, Decimal, idempotency
12. `12-release-verification.md` — Docker, PostgreSQL, E2E, backup/restore

## กติกาสำหรับ sub-agent

- อ่าน `AGENTS.md`, `README.md`, `AI-Context-Index.md` และ task file ของตัวเองก่อนเริ่ม
- งานที่กระทบตั้งแต่ 4 ไฟล์ต้องรายงาน blast radius ก่อนแก้
- ห้ามแก้ business behavior นอก acceptance criteria
- ห้ามใช้ `except Exception: pass` ในโค้ดที่แตะ
- รัน `python tests/run_all_tests.py` หลังแก้ logic หรือ import
- ถ้า verification ล้มเหลว 2 ครั้งติด ให้หยุดและส่ง Failure Report
- รายงาน Files Changed, Verification Command, Terminal Result และ next steps
