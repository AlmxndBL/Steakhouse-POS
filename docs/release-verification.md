# Release Verification Evidence

## Verified in the local classroom environment

| Check | Command | Result |
|---|---|---|
| Regression suite | `uv run --python 3.11 --with-requirements requirements.txt tests/run_all_tests.py` | 58/58 passed |
| Import baseline | `uv run --python 3.11 --with-requirements requirements.txt python -c "import main"` | Passed |
| Syntax compilation | `python -m compileall -q app main.py healthcheck.py` | Passed |
| PostgreSQL healthcheck | `python healthcheck.py` | `database healthcheck ok` |
| Schema marker | Query `schema_migrations` | Version 2 |
| Role routing | `AuthService.get_role_home_route()` | 5 roles mapped |
| Shift smoke test | `ShiftService.start_shift/close_shift` | variance calculation passed |
| PostgreSQL backup | `TestProductionReadiness.test_database_backup_service` | custom-format dump created |
| Docker Compose smoke test | `docker compose up -d --build && docker compose ps` | `app` and `db` healthy |
| PostgreSQL readiness | `docker compose exec -T db pg_isready -U postgres -d pos_db` | accepting connections |
| Web endpoint | `curl.exe -I http://localhost:8000` | HTTP 200 |
| Interactive POS smoke flow | Browser: login → table → order → KDS → checkout → E-Receipt | Passed with screenshots |
| Existing PostgreSQL schema migration | Rebuild app against existing `pos_db` volume | `order_items.sent_to_kitchen_at` added; app healthy |

## Not verified in the current environment

- Full role-by-role Flet UI flow beyond the Owner smoke path remains manual.
- Backup uses `pg_dump`; restore remains an operator action using `pg_restore`.

## Required release command set

```text
python tests/run_all_tests.py
python -c "import main; print('imports ok')"
docker compose build
docker compose up -d
docker compose ps
docker compose exec -T db pg_isready -U postgres -d pos_db
curl.exe -I http://localhost:8000
```
