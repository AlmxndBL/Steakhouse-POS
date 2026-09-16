import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://posadmin:pospassword@localhost:5432/pos_db")
if not DATABASE_URL.startswith("postgresql"):
    raise RuntimeError("POS Flet requires PostgreSQL via DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()
