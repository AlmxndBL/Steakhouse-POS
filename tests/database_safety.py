"""Fail-closed guard for test modules that write to the database."""
import os
from urllib.parse import urlsplit


def require_isolated_test_database():
    if os.environ.get("APP_ENV", "").strip().lower() != "test":
        raise RuntimeError("Database tests require APP_ENV=test")

    database_url = os.environ.get("DATABASE_URL", "")
    parsed = urlsplit(database_url)
    if (
        parsed.scheme not in {"postgresql", "postgresql+psycopg2"}
        or parsed.hostname != "test-db"
        or parsed.port != 5432
        or parsed.username != "pos_test"
        or parsed.path.lstrip("/") != "pos_test_db"
    ):
        raise RuntimeError(
            "Refusing database tests: DATABASE_URL must target the isolated Docker "
            "service test-db/pos_test_db as pos_test on port 5432"
        )
