import os


class Settings:
    square_access_token: str = os.environ.get("SQUARE_ACCESS_TOKEN", "")
    square_location_id: str = os.environ.get("SQUARE_LOCATION_ID", "")
    shopify_shop: str = os.environ.get("SHOPIFY_SHOP", "")
    shopify_access_token: str = os.environ.get("SHOPIFY_ACCESS_TOKEN", "")
    sheets_id: str = os.environ.get("GOOGLE_SHEETS_ID", "")
    sheets_creds: str = os.environ.get("GOOGLE_CREDS_JSON", "")


settings = Settings()
