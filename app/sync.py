"""Reconciliation: one canonical count, adjustments pushed outward."""

from app import shopify_client, sheets_client, square_client
from app.config import settings


def reconcile(sku: str) -> dict:
    """Pull counts from every channel, decide the truth, push corrections."""
    square_counts = square_client.get_counts(settings.square_location_id)
    shopify_counts = shopify_client.get_counts()

    sq = square_counts.get(sku, 0)
    sh = shopify_counts.get(sku, 0)

    # Rule v0: physical count (Square POS) wins; Shopify is adjusted to match.
    # TODO: make rules configurable per shop (e.g. safety stock buffers).
    canonical = sq

    adjustments = []
    if sh != canonical:
        shopify_client.adjust(sku, canonical)
        adjustments.append({"channel": "shopify", "from": sh, "to": canonical})

    sheets_client.log_adjustment(sku, {"square": sq, "shopify": sh}, canonical, "reconcile")

    return {"sku": sku, "canonical": canonical, "adjustments": adjustments}
