# System Design & Architecture (9arm Style)

> กฎสำหรับการออกแบบระบบ สไตล์ Pragmatic Software Engineer (อ้างอิง mindset แบบพี่นายอาร์ม)

## 🧠 Core Philosophy
1. **Don't Over-engineer:** เลือกสิ่งที่แก้ปัญหาได้ตรงจุดที่สุด อย่าใช้ Tech ยิ่งใหญ่เกินความจำเป็นของโปรเจกต์
2. **Trade-off Analysis:** ทุกการเลือกมีข้อดีข้อเสีย ต้องอธิบายเหตุผลเปรียบเทียบได้ว่าทำไมถึงเลือกใช้ Stack นี้
3. **Operations Mindset:** คิดถึงตอน Deploy และ Maintain ด้วย ไม่ใช่แค่ตอนเขียนโค้ด
4. **Don't Reinvent the Wheel:** ถ้ามี Library/Framework หรือ Service ที่เสถียรและตอบโจทย์ ให้ใช้เลย ไม่ต้องเขียนเองใหม่หมดจากศูนย์

## 🛠️ Architecture Planning Step
เมื่อเริ่มต้นโปรเจกต์หรือฟีเจอร์ใหญ่ ให้คิดและนำเสนอสิ่งเหล่านี้:
- Tech Stack ที่เหมาะสม (อธิบายเหตุผลสั้นๆ)
- Data Flow หรือ Life Cycle ของฟีเจอร์นั้น
- การขยายตัวในอนาคต (Scalability แบบเบื้องต้น)

## 📊 Diagram Rules
- **ห้าม**สร้าง Architecture Diagram (เช่น Mermaid) ออกมาเองโดยพลการ
- **ต้องถามเจ้าของโปรเจกต์เสมอ** ว่า: *"ต้องการให้ผมวาด Architecture Diagram เพื่อดูภาพรวมก่อนเริ่มเขียนโค้ดไหมครับ?"*
- ถ้ายืนยันว่าให้วาด ค่อยเขียน Mermaid Diagram ออกมาให้ดูเข้าใจง่ายที่สุด

## 🏗️ Architecture Patterns Guidance
- Default สำหรับโปรเจกต์ POS Flet: **Layered Monolith (Desktop Standalone)**
  - **UI Layer (Flet Views/Components):** แสดงผลหน้าจอ รับ Event จากผู้ใช้
  - **Service Layer (Business Logic):** คำนวณ BOM Stock, Lot FIFO/FEFO, ราคา, ส่วนลด, ใบเสร็จ
  - **Data Layer (SQLAlchemy ORM + SQLite):** จัดการสืบค้นและบันทึกข้อมูลแบบ ACID Transaction
  - **Hardware Interface Layer:** สั่งงาน Receipt Printer, Cash Drawer, KDS Display

## 📦 Dependency Management
- ก่อนเพิ่ม Python library ใหม่ ต้องประเมินความจำเป็นและความเสถียร
- ระบุ version ใน `requirements.txt` หรือ `pyproject.toml` เสมอ
