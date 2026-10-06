"""Google Sheets audit log and purchasing view."""


def log_adjustment(sku: str, before: dict, after: int, reason: str) -> None:
    """Append one row to the audit log sheet."""
    # TODO: gspread append_row with timestamp
    raise NotImplementedError


def get_purchasing_view() -> list:
    """Return rows flagged for reorder."""
    # TODO: read the purchasing sheet
    raise NotImplementedError
