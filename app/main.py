from fastapi import Depends, FastAPI, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app import events
from app.config import settings  # noqa: F401  (kept for env validation on import)
from app.db import get_db, lifespan

app = FastAPI(
    title="FOBA",
    description="Multi-channel inventory middleware",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "foba"}


@app.post("/webhooks/square")
async def square_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    # TODO: verify Square webhook signature before ingesting
    payload = await request.json()
    log, duplicate = await events.ingest_event(
        db,
        source="square",
        event_id=str(payload.get("event_id", "unknown")),
        event_type=str(payload.get("type", "unknown")),
        payload=payload,
    )
    if duplicate:
        return {"received": True, "duplicate": True, "event_log_id": log.id}
    # TODO: enqueue inventory reconciliation for this event
    await events.mark_processed(db, log)
    return {"received": True, "event_log_id": log.id}


@app.post("/webhooks/shopify")
async def shopify_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    # TODO: verify Shopify HMAC before ingesting
    payload = await request.json()
    log, duplicate = await events.ingest_event(
        db,
        source="shopify",
        event_id=request.headers.get("x-shopify-webhook-id", "unknown"),
        event_type=request.headers.get("x-shopify-topic", "unknown"),
        payload=payload,
    )
    if duplicate:
        return {"received": True, "duplicate": True, "event_log_id": log.id}
    # TODO: enqueue inventory reconciliation for this event
    await events.mark_processed(db, log)
    return {"received": True, "event_log_id": log.id}


@app.post("/sync/run")
def run_sync(sku: str):
    # TODO: reconcile one SKU across Square, Shopify, Sheets; push adjustments
    from app.sync import reconcile

    return reconcile(sku)
