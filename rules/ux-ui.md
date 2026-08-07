# UX/UI & Flet Development Standards

> กฎการพัฒนาส่วน User Interface ด้วย **Python Flet** สำหรับระบบ POS

## 1. Flet Component Modularity
- แยก View และ Component ออกเป็นสัดส่วน (เช่น `views/pos_view.py`, `components/table_card.py`, `components/receipt_modal.py`)
- UI Logic และ Business Logic ต้องแยกจากกัน (ใช้ Controller/Service pattern)
- UI Controls ทุกตัวต้องเป็น Reusable และ Clean Code

## 2. POS Screen Layout & Touch Ergonomics
- ออกแบบโดยคำนึงถึง **POS Touch Screen / Tablet** หน้าจอต้องปุ่มใหญ่ กดง่าย มี Touch Target อย่างน้อย 48x48px
- ใช้ Color Palette ที่ดูดีและสะอาดตา (เช่น Charcoal, Warm Slate, Emerald/Amber Accent) ห้ามใช้สีฉูดฉาดแบบ Default
- รองรับทั้ง Dark Mode และ Light Mode ผ่าน `page.theme_mode`

## 3. View Management & Navigation
- ใช้ Flet Route/Navigation หรือ Container Swapping สำหรับการเปลี่ยนหน้า (เช่น หน้าขายหน้าร้าน, จัดการผังโต๊ะ, จัดการสต๊อก, รายงาน)
- มี Status Bar และ Header บ่งบอกสถานะการเชื่อมต่อเครื่องพิมพ์/ลิ้นชัก/DB

## 4. State & Reaction
- ใช้ State Management Pattern ภายใน Flet App (เช่น Dataclass/State class ร่วมกับ Callback handlers)
- เมื่อมี Event (กดปุ่ม, ยิง Barcode, เพิ่มรายการสินค้า) ต้องอัปเดต UI ทันทีและมี Micro-feedback (เช่น Visual Feedback, Toast Alert, Snackbar)

## 5. Performance & Dynamic Updating
- ใช้ `page.update()` เฉพาะ Control ที่เปลี่ยนแปลง หรือใช้ Reactive Controls ป้องกันการ Re-render ทั้งหน้ากระตุก
- กรณีแสดงผล List รายการสินค้า/วัตถุดิบจำนวนมาก ให้ใช้ `ListView` หรือ Paginated Grid เพื่อประสิทธิภาพสูงสุด

## 6. Form & Input Validation
- มีการ Validation ข้อมูลฝั่ง UI ก่อนบันทึกเสมอ (เช่น ตัวเลขจำนวนวัตถุดิบ, ราคาสินค้า, เบอร์โทรศัพท์)
- แสดง Error Text ชัดเจนใต้ TextField หรือแสดง Alert Dialog ให้ผู้ใช้งานเข้าใจง่าย

