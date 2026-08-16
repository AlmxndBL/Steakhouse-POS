import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pos_data.db")
# Use DATABASE_URL from env if available, otherwise fallback to SQLite
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    # Enable WAL Mode and Foreign Keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()
else:
    # PostgreSQL or other DB
    engine = create_engine(
        DATABASE_URL,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()
