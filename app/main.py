from fastapi import FastAPI, Request

from app.config import settings

app = FastAPI(title="FOBA", description="Multi-channel inventory middleware")


@app.get("/health")
def health():
    return {"status": "ok", "service": "foba"}


@app.post("/webhooks/square")
async def square_webhook(request: Request):
    # TODO: verify Square webhook signature, then enqueue the inventory event
    payload = await request.json()
    return {"received": True, "event": payload.get("type")}


@app.post("/webhooks/shopify")
async def shopify_webhook(request: Request):
    # TODO: verify Shopify HMAC, then enqueue the inventory event
    payload = await request.json()
    return {"received": True}


@app.post("/sync/run")
def run_sync(sku: str):
    # TODO: reconcile one SKU across Square, Shopify, Sheets; push adjustments
    from app.sync import reconcile

    return reconcile(sku)
