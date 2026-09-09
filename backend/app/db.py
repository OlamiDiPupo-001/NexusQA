"""
Database setup using SQLAlchemy 2.0's typed ORM style. Starts on SQLite
for local development (zero setup — it's just a file), and swaps to
Postgres in Phase 9 via the DB_URL environment variable, with no code
changes needed here.
"""

import os
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = os.getenv("NEXUSQA_DB_URL", "sqlite:///./nexusqa.db")

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class OrderRecord(Base):
    """The actual DB table — separate from the Pydantic Order model.
    Pydantic models validate data in transit; this class defines what's
    stored on disk."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    total_cents: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(nullable=True)


class ProcessedWebhookEvent(Base):
    """Tracks which webhook event_ids have already been processed.
    This table is the actual mechanism behind idempotency — used
    directly in Phase 7."""

    __tablename__ = "processed_webhook_events"

    event_id: Mapped[str] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(nullable=False)


class StockRecord(Base):
    """A single limited-stock item, used ONLY to give Layer 3's
    concurrency tests a real shared resource to race over. This is
    intentionally not a general inventory system — that's out of scope
    for v1 per the Phase 0 scoping decision."""

    __tablename__ = "stock"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_name: Mapped[str] = mapped_column(unique=True)
    quantity: Mapped[int] = mapped_column(nullable=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_event_processed(db, event_id: str) -> bool:
    return (
        db.query(ProcessedWebhookEvent).filter(ProcessedWebhookEvent.event_id == event_id).first()
        is not None
    )


def mark_event_processed(db, event_id: str, order_id: int) -> None:
    db.add(ProcessedWebhookEvent(event_id=event_id, order_id=order_id))
    db.commit()


def seed_stock(quantity: int = 3) -> None:
    """(Re)sets the flash-sale stock item to a known quantity. Tests call
    this directly before each run so leftover state never affects the
    next test's result."""
    db = SessionLocal()
    existing = db.query(StockRecord).filter_by(item_name="flash_sale_item").first()
    if existing:
        existing.quantity = quantity
    else:
        db.add(StockRecord(item_name="flash_sale_item", quantity=quantity))
    db.commit()
    db.close()
