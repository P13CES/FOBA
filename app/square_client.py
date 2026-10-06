"""Square inventory reads and writes. Wraps the Square SDK."""


def get_counts(location_id: str) -> dict:
    """Return {sku: quantity_on_hand} for the location."""
    # TODO: squareup inventory API — batch retrieve counts
    raise NotImplementedError


def adjust(sku: str, location_id: str, quantity: int, reason: str) -> None:
    """Set quantity on hand for a SKU."""
    # TODO: squareup inventory API — batch change inventory
    raise NotImplementedError
