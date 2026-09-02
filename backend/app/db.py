"""資料庫連線與建表。"""

from __future__ import annotations

import os

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.environ.get("ATELIER_DATABASE_URL", "sqlite:///./atelier.db")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """FastAPI 依賴注入用。"""
    with Session(engine) as session:
        yield session
