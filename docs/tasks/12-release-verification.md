# Task 12: Release Verification

## Goal

ยืนยันระบบก่อน pilot/production โดยไม่พึ่ง unit tests อย่างเดียว

## Scope

- local smoke test
- Docker Compose + PostgreSQL smoke test
- role login and route guard checks
- order/KDS/payment end-to-end checks
- backup and restore drill
- healthcheck ที่ตรวจ database จริง

## Acceptance criteria

- `python tests/run_all_tests.py` ผ่าน
- Docker app start และ healthcheck ผ่าน
- PostgreSQL path ผ่าน critical workflows
- มี evidence log และ known limitations
