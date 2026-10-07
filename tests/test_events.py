"""Idempotency and model smoke tests (SQLite; Postgres is the deploy target)."""
import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import events
from app.models import Base, BomComponent, EventLog, InventoryLevel, Sku


async def main() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        # 1. First delivery inserts; redelivery returns the same row as duplicate.
        log1, dup1 = await events.ingest_event(
            db, source="square", event_id="evt_123",
            event_type="inventory.count.updated", payload={"sku": "LOAF-01"},
        )
        assert not dup1, "first delivery must not be a duplicate"
        await db.commit()

        log2, dup2 = await events.ingest_event(
            db, source="square", event_id="evt_123",
            event_type="inventory.count.updated", payload={"sku": "LOAF-01"},
        )
        assert dup2 and log2.id == log1.id, "redelivery must return existing row"

        # 2. Same event_id from a different source is a different event.
        _, dup3 = await events.ingest_event(
            db, source="shopify", event_id="evt_123",
            event_type="inventory_levels/update", payload={},
        )
        assert not dup3, "cross-source event_id must not collide"
        await db.commit()

        # 3. SKU + levels + BOM wiring.
        loaf = Sku(sku="LOAF-01", name="Sourdough Loaf", square_variation_id="var_1")
        flour = Sku(sku="FLOUR-AP", name="All-purpose flour")
        db.add_all([loaf, flour])
        await db.flush()
        db.add(InventoryLevel(sku_id=loaf.id, channel="canonical", quantity=12))
        db.add(BomComponent(parent_sku_id=loaf.id, component_sku_id=flour.id, quantity=0.5))
        await db.commit()

        await events.mark_processed(db, log1)
        assert log1.status == "processed" and log1.processed_at is not None

    await engine.dispose()
    print("all foba db tests passed")


if __name__ == "__main__":
    asyncio.run(main())
