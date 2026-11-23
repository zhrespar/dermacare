# DermaCare API (FastAPI)

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export PYTHONPATH=$PWD:$PWD/..          # backend + repo root (for ml/)
alembic upgrade head                     # needs DATABASE_URL (see ../.env.example)
uvicorn app.main:app --reload
```

Tests (from repo root): `pytest` · Lint: `ruff check . && ruff format --check backend ml tests`

Layout: `app/core` config · `app/db` engine/session · `app/models` SQLAlchemy · `app/schemas` Pydantic ·
`app/api/routes` endpoints · `app/services` mock analysis, rule-based recommendation, LLM provider.
Migrations live in `../database/migrations` (configured in `alembic.ini`).
