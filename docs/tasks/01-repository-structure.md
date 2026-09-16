# Task 01: Repository Structure and Import Baseline

## Goal

ทำให้โครงสร้าง `app/` เป็น source root อย่างเป็นทางการ และให้ local, test runner และ Docker ใช้ import path เดียวกัน

## Current evidence

- application modules อยู่ใต้ `app/`
- `main.py` อยู่ root
- internal imports ยังใช้ `database`, `services`, `views`, `components`, `utils`
- ต้องรักษา behavior เดิม

## Scope

- ตรวจ `app/__init__.py`, package markers และ entrypoint
- ทำให้ `python main.py` และ `python tests/run_all_tests.py` ผ่าน
- อัปเดต README/AI-Context-Index ให้ตรงโครงสร้างจริง
- ห้าม refactor business logic

## Acceptance criteria

- ไม่มี import error
- test suite เดิมผ่าน 100%
- Docker CMD และ local command ใช้ได้
- เอกสารไม่อ้าง root directories ที่ไม่มีอยู่จริง
