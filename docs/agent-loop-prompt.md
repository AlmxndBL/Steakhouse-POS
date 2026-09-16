# Prompt สำหรับสั่งงาน Sub-agent แบบ Loop

คัดลอก prompt นี้ แล้วแทนที่ `<TASK_FILE>` ด้วยไฟล์ task ที่ต้องการทำ เช่น `docs/tasks/03-order-table-flow.md`

```text
ทำงานใน repository POS flet ตาม Apex-core และ AGENTS.md อย่างเคร่งครัด

Task file: <TASK_FILE>

ขั้นตอนบังคับ:
1. อ่าน AGENTS.md, README.md, AI-Context-Index.md และ task file
2. ทำ Discovery แบบ read-only: ตรวจ stack, imports, affected files, existing user changes
3. รายงาน blast radius สั้น ๆ ก่อนแก้ หากกระทบตั้งแต่ 4 ไฟล์
4. ทำเฉพาะ scope และ acceptance criteria ใน task file ห้าม refactor นอกเรื่อง
5. รักษา existing behavior ที่ไม่ได้อยู่ใน scope
6. แก้ด้วย diff ที่เล็กและตรวจสอบได้
7. รัน verification ที่เหมาะสม โดยเริ่มจาก:
   python tests/run_all_tests.py
8. ถ้า verification ล้มเหลว 2 ครั้งติด ให้หยุดทันทีและส่ง Failure Report
9. ห้ามอ้างว่าเสร็จถ้าไม่มี terminal evidence

รูปแบบรายงานสุดท้าย:
- Summary
- Facts found
- Files Changed
- Acceptance Criteria status
- Verification Command
- Terminal Result
- Risks / Known limitations
- Next task recommendation
```
