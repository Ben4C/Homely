"""PostgreSQL directory sessions; no implicit schema creation or fixture fallback."""

import os
from functools import lru_cache
from collections.abc import Iterator
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


# Purpose: Resolve an explicitly configured persistent store. Inputs: DATABASE_URL; outputs: SQLAlchemy engine.
# Constraints: SQLite is allowed for isolated tests only; deployment defaults to PostgreSQL.
@lru_cache(maxsize=4)
def engine_for(url: str) -> Engine:
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
    )


# Purpose: Supply request-scoped transactional directory access. Inputs: server configuration; outputs: session or safe 503.
def directory_session() -> Iterator[Session]:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise HTTPException(
            503,
            "The funding directory database is not configured. Set DATABASE_URL and run migrations/import.",
        )
    try:
        with Session(engine_for(url)) as session:
            yield session
    except SQLAlchemyError as exc:
        raise HTTPException(
            503,
            "The funding directory is unavailable. Check database connectivity and migrations.",
        ) from exc


# Purpose: Keep explicit demo compatibility independent of persistent-directory requests. Inputs: REGISTRY_MODE; outputs: session or None for demo-only domain routes.
def legacy_directory_session():
    if os.getenv("REGISTRY_MODE", "database") == "demo":
        yield None
    else:
        yield from directory_session()
