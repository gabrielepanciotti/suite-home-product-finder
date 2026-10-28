"""Database layer (additive) — the node now owns its own Postgres DB.

History: the comparisons' data source remains `vault/confronti/*.json` (see
store.py) and is NOT touched. This module ONLY adds a node-owned DB for the
domain's relational data (today: the choice/shopping-list log, previously
written only to `vault/log.md`). It is purely additive: without `DATABASE_URL`
the backend works exactly as before.

DSN from env `DATABASE_URL` (see .env). Node DB port (Life registry): 11120.
"""
from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from suite_backend_core import Base, make_engine, make_session_factory


class ChoiceLog(Base):
    """One comparison choice: which products ended up as `da-comprare`.

    Additive relational replica of the event previously logged only in vault/log.md.
    """

    __tablename__ = "choice_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), index=True)
    titolo: Mapped[str] = mapped_column(String(255))
    scelti: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Life standard: visibility per-row (public|private, default private).
    # Set at archiving time, not at write time.
    visibility: Mapped[str] = mapped_column(String(10), default="private", server_default="private")

    __table_args__ = (
        Index("ix_choice_log_visibility", "visibility"),
    )


def get_database_url() -> str | None:
    """The node DB DSN, or None when not configured (JSON-only mode)."""
    return os.environ.get("DATABASE_URL") or None


_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def session_factory() -> async_sessionmaker[AsyncSession] | None:
    """Lazy async session factory. None when DATABASE_URL is unset."""
    global _engine, _session_factory
    if _session_factory is not None:
        return _session_factory
    url = get_database_url()
    if not url:
        return None
    _engine = make_engine(url)
    _session_factory = make_session_factory(_engine)
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a session (only when the DB is configured)."""
    factory = session_factory()
    if factory is None:
        raise RuntimeError("DATABASE_URL not configured")
    async with factory() as session:
        yield session
