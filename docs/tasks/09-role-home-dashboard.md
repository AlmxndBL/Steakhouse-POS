# Task 09: Role-based Home and Action Dashboard

## Goal

ให้หน้าแรกของแต่ละ role ตรงกับงานที่ต้องทำจริง

## Scope

- Owner: sales, margin, anomalies
- Manager: tasks, stock, staff, shift
- Cashier: payment queue, orders, receipts
- Waiter: tables, new orders, ready-to-serve
- Kitchen: KDS only
- admin dashboard เน้น actionable cards พร้อม drill-down

## Acceptance criteria

- login แล้ว redirect ไป workspace ที่เหมาะกับ role
- ไม่มี module ที่ไม่เกี่ยวข้องใน primary navigation
- ทุก KPI สำคัญมี link ไป action/detail
