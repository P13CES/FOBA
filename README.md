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
- `app/models.py` — SQLAlchemy models: `event_logs`, `skus`, `inventory_levels`, `bom_components`
- `app/db.py` — async engine, session factory, `get_db` dependency, startup table init
- `app/events.py` — idempotent webhook ingestion keyed on `(source, event_id)`
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

- [x] PostgreSQL + async SQLAlchemy (pooling safe for Vercel serverless cold starts)
- [x] Idempotent webhook handlers backed by an `event_logs` table
- [x] `bom_components` table laid for the BOM engine
- [ ] `X-Sync-Source: FOBA-Engine` header — ignore circular webhook updates
- [ ] BOM engine: finished SKUs → raw components; atomic `SELECT FOR UPDATE`
      deductions so a sale decrements ingredients without race conditions
- [ ] Webhook signature verification (Square + Shopify)
- [ ] Sheets audit log writer
- [ ] Zebra label print trigger on receiving
- [ ] Multi-tenant: one deploy, many shops
- [ ] Alembic migrations (currently `create_all` on startup; migrate before prod data)
