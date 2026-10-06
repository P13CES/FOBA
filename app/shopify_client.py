"""Shopify inventory reads and writes. Wraps the Shopify API."""


def get_counts() -> dict:
    """Return {sku: available} across locations."""
    # TODO: ShopifyAPI inventory levels for each variant
    raise NotImplementedError


def adjust(sku: str, available: int) -> None:
    """Set available quantity for a SKU."""
    # TODO: ShopifyAPI inventory adjust / set
    raise NotImplementedError
