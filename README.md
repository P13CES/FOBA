# FOBA

Multi-channel inventory middleware. One canonical stock count across **Square POS**,
**Shopify**, and **Google Sheets** — so small retailers stop overselling.

## The problem

A shop sells in-store (Square) and online (Shopify) and tracks purchasing in
Sheets. Each system holds its own inventory count. Sell the last unit in-store,
and Shopify still shows it available. Oversell, cancel, apologize, repeat.

FOBA sits between the channels: inventory events flow in via webhooks, FOBA
reconciles them into one canonical count, and pushes adjustments back out.

## Architecture

```
Square webhooks ──┐
                  ├──▶ FOBA (FastAPI) ──▶ canonical inventory ──▶ push adjustments
Shopify webhooks ─┘         │
                            ▼
                     Google Sheets (audit log + purchasing view)
```

- `app/main.py` — FastAPI app: health check, webhook receivers, manual sync trigger
- `app/config.py` — environment-based settings, no secrets in code
- `app/square_client.py` — Square inventory reads/writes
- `app/shopify_client.py` — Shopify inventory reads/writes
- `app/sheets_client.py` — Sheets audit log + purchasing view
- `app/sync.py` — reconciliation: the canonical count and who gets adjusted

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn app.main:app --reload
```

## Clean-room note

FOBA is built from scratch. The domain knowledge comes from running retail
systems daily; none of the code is copied from any employer's systems.

## Roadmap

- [ ] Webhook signature verification (Square + Shopify)
- [ ] Canonical inventory store (SQLite to start, Postgres later)
- [ ] Reconciliation rules (which channel wins conflicts)
- [ ] Sheets audit log writer
- [ ] Zebra label print trigger on receiving
- [ ] Multi-tenant: one deploy, many shops
