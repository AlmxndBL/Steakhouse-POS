"""Container health probe: verify the configured database is reachable."""

from sqlalchemy import text

from database.connection import engine


def main() -> int:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    print("database healthcheck ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
