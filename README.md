# stockmiles-api

REST API for StockMiles, a multi-tenant POS and inventory platform for retail businesses that restock through purchase trips. Built with FastAPI, SQLAlchemy (async) and PostgreSQL.

The React frontend never talks to the database; everything goes through this API.

## What you need

| Tool | Version | Notes |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | 0.10 or newer | Python package and environment manager (`brew install uv`) |
| Python | 3.12 | uv downloads it for you; no manual install needed |
| PostgreSQL | any recent | A connection string to a Postgres database |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | any recent | Runs the local test database |
| git | any recent | |

## First-time setup

```bash
git clone https://github.com/stockmilesapp-ai/stockmiles-api.git
cd stockmiles-api
uv sync
cp .env.example .env
```

`uv sync` creates the `.venv` folder and installs everything from `uv.lock`. There is no need to create or activate a virtual environment by hand.

Then edit `.env` and set `DATABASE_URL`.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | yes | Postgres connection string |
| `TEST_DATABASE_URL` | no | Connection string of the local Docker test database (see below). Not set in production. |

Rules for `DATABASE_URL`:

- It must start with `postgresql+asyncpg://` (not `postgresql://`), so SQLAlchemy uses the async driver.
- Special characters in the password must be percent-encoded, for example `@` becomes `%40`.
- With a hosted pooler in transaction mode, use the pooler host and port `6543`.

`.env` holds secrets and is ignored by git. Never commit it. `.env.example` shows the format only.

## Developer commands

| Task | Command |
|---|---|
| Install or update dependencies | `uv sync` |
| Run the dev server (auto-reload) | `uv run fastapi dev app/main.py` |
| Lint | `uv run ruff check .` |
| Auto-fix lint problems | `uv run ruff check . --fix` |
| Format code | `uv run ruff format .` |
| Run tests (needs the test database, see below) | `uv run pytest` |
| Load seed data (see `app/seeds/README.md`) | `uv run python -m app.seeds.load_platform_members` |
| Add a dependency | `uv add <package>` |
| Add a dev-only dependency | `uv add --dev <package>` |

The dev server runs at `http://localhost:8000`.

- `GET /health` returns `{"db": "ok"}` when the database is reachable, and `503` with `{"db": "error"}` when it is not.
- `http://localhost:8000/docs` shows the generated API documentation.

## Test database (Docker)

`docker-compose.yml` defines `test-db`, a PostgreSQL 17 container for tests only. It listens on port `54329` of your machine and keeps its data in memory, so everything in it is gone when the container is removed. Development and migrations still use the database in `DATABASE_URL`.

`uv run pytest` always runs against `TEST_DATABASE_URL`, never `DATABASE_URL`. `tests/conftest.py` refuses to start if that variable is missing or does not point at `localhost`, and it applies the migrations to the test database before the first test. If the container is not running, the tests fail with a connection error.

Docker Desktop must be running first.

| Task | Command |
|---|---|
| Start the test database (in the background) | `docker compose up -d` |
| Check that it is running | `docker compose ps` |
| Check that it answers | `docker compose exec test-db psql -U stockmiles -d stockmiles_test -c "select version()"` |
| Open a SQL prompt in it (`\q` to leave) | `docker compose exec test-db psql -U stockmiles -d stockmiles_test` |
| See its logs | `docker compose logs test-db` |
| Stop and remove it (data is lost) | `docker compose down` |

Start it again after restarting your machine or Docker Desktop.

## Project layout

```
app/
  main.py        FastAPI app and routes
  core/
    settings.py  Settings loaded from .env
  db/
    engine.py    Async database engine
pyproject.toml   Dependencies and project metadata
uv.lock          Exact pinned versions (commit this)
.env.example     Template for .env
```

## Before you commit

```bash
uv run ruff format . && uv run ruff check .
```

Check that `git status` does not list `.env`.
