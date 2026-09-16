# Task 10: UI States and Visual Consistency

## Goal

ทำให้ UI ดูเสถียรและสื่อสารสถานะได้ชัด

## Scope

- loading, empty, error, ready state ในหน้าหลัก
- retry action และ safe error message
- semantic color/status registry เดียวกัน
- Thai typography, spacing, primary action hierarchy
- responsive tablet layout

## Acceptance criteria

- ไม่มีหน้าว่างเงียบเมื่อ query ล้มเหลว
- ไม่มี `except Exception: pass` ใน code path ที่แก้
- status เดียวกันใช้สี/icon/ข้อความสอดคล้องกัน
