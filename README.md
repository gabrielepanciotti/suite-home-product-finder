# HomeProductFinder

HomeProductFinder is a self-hosted FastAPI and React application for building a private, searchable catalogue of household products. It turns product notes and photos into Markdown records, compares offers, keeps a shopping shortlist, and helps match objects to storage containers by their dimensions.

## Features

- Markdown-and-JSON vault for product records, comparisons, and shopping choices
- FastAPI API for comparisons, catalogues, storage-space fitting, and preferences
- React interface for browsing comparisons and planning purchases
- Reusable geometry engine for fitting objects into containers

## Requirements

- Python 3.13
- Node.js 20 and npm
- PostgreSQL 16 (optional for local JSON-only use; required for persistence)
- The Life framework checkout beside this repository for the shared `suite_core`, `suite_backend_core`, and `@suite/design-system` packages

## Quickstart

```bash
git clone <your-fork-url> home-product-finder
cd home-product-finder
cp .env.example .env

# Backend
python3.13 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt pytest aiosqlite
pip install ../Life/packages/shared ../Life/packages/backend-core
PYTHONPATH=backend uvicorn home_product_finder_backend.app:app --reload --port 10008

# In another terminal, frontend
cd frontend
npm ci
npm run dev
```

Alternatively, from the repository root run `docker compose --env-file .env -f deploy/docker-compose.example.yml up --build`. The example compose file expects no private network or host-specific ports.

## Tests

The Python suite is self-contained apart from the Life framework packages:

```bash
PYTHONPATH=backend pytest
```

For the frontend, run `npm test` and `npm run build` from `frontend/`. CI checks out the Life framework as a sibling repository; set the repository variable `LIFE_FRAMEWORK_REPO` when your framework fork has a different name.

## Configuration

| Variable | Purpose |
| --- | --- |
| `PORT` | Backend listen port |
| `DATABASE_URL` | SQLAlchemy database URL |
| `DB_USER` | PostgreSQL user |
| `DB_PASSWORD` | PostgreSQL password |
| `DB_NAME` | PostgreSQL database name |
| `DB_HOST_PORT` | Published PostgreSQL port |
| `EBAY_BROWSE_CLIENT_ID` | eBay Browse API client ID |
| `EBAY_BROWSE_CLIENT_SECRET` | eBay Browse API client secret |
| `VITE_BACKEND_PROXY_TARGET` | Frontend development API proxy |

## License

MIT — see [LICENSE](LICENSE).
