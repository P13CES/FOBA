"""Canonical data model: SKUs, inventory levels, webhook event log, BOM.

PostgreSQL is the production target (JSONB payloads, asyncpg). For local
dev/tests the JSONB column falls back to plain JSON on SQLite.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


PayloadJSON = JSONB().with_variant(JSON(), "sqlite")


def _utcnow() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EventLog(Base):
    """Every inbound webhook, exactly once.

    Idempotency key is (source, event_id): the provider's own event id.
    A duplicate delivery returns the existing row instead of inserting.
    """

    __tablename__ = "event_logs"
    __table_args__ = (
        UniqueConstraint("source", "event_id", name="uq_event_logs_source_event"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(24), nullable=False)  # square | shopify | manual
    event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(PayloadJSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="received")
    # received -> processed | failed ; duplicates are returned, never re-inserted
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = _utcnow()
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Sku(Base):
    """One canonical product, mapped to its channel-specific identifiers."""

    __tablename__ = "skus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    square_variation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shopify_inventory_item_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    track: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = _utcnow()
    updated_at: Mapped[datetime] = _utcnow()

    levels: Mapped[list["InventoryLevel"]] = relationship(
        back_populates="sku", cascade="all, delete-orphan"
    )


class InventoryLevel(Base):
    """A stock count for one SKU in one channel.

    channel = "canonical" is FOBA's reconciled truth; "square" / "shopify"
    are the last observed counts pushed back from each channel.
    """

    __tablename__ = "inventory_levels"
    __table_args__ = (
        UniqueConstraint("sku_id", "channel", name="uq_levels_sku_channel"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku_id: Mapped[int] = mapped_column(
        ForeignKey("skus.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(24), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False, default=0)
    updated_at: Mapped[datetime] = _utcnow()

    sku: Mapped[Sku] = relationship(back_populates="levels")


class BomComponent(Base):
    """Finished SKU -> raw component mapping for the BOM engine.

    quantity is in the component's own unit (e.g. 0.5 lb of flour per loaf).
    """

    __tablename__ = "bom_components"
    __table_args__ = (
        UniqueConstraint("parent_sku_id", "component_sku_id", name="uq_bom_parent_component"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_sku_id: Mapped[int] = mapped_column(
        ForeignKey("skus.id", ondelete="CASCADE"), nullable=False
    )
    component_sku_id: Mapped[int] = mapped_column(
        ForeignKey("skus.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
