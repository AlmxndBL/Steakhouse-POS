# Task 05: Kitchen Display Workflow

## Goal

เปลี่ยน KDS ให้เป็น work queue ที่ช่วยครัวจัดลำดับงาน

## Scope

- sort ตามเวลาสั่ง
- แสดง elapsed timer และ SLA warning
- action ใหญ่ `เริ่มทำ`, `พร้อมเสิร์ฟ`, `เสิร์ฟแล้ว`
- filter ตามสถานะ
- แสดง modifier และ note เด่น
- แจ้งรายการใหม่และรายการล่าช้า

## Acceptance criteria

- สถานะใน KDS สอดคล้องกับ `OrderItemStatus`
- รายการหนึ่งโต๊ะทำเสร็จบางส่วนได้
- timer ไม่ทำให้ UI ค้างและ refresh ได้ปลอดภัย
