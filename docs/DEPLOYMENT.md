# Deployment

**Current state:** local development only. No cloud resources have been provisioned or purchased.

## Local setup

```bash
git clone https://github.com/zhrespar/dermacare.git && cd dermacare
cp .env.example .env            # edit secrets
```

### Option A — Docker Compose (PostgreSQL + API)

```bash
docker compose up --build
curl http://localhost:8000/health
open http://localhost:8000/docs
```

### Option B — native

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export PYTHONPATH=$PWD:$PWD/..
export DATABASE_URL=postgresql+psycopg://dermacare:dermacare@localhost:5432/dermacare
alembic upgrade head
uvicorn app.main:app --reload
```

Tests and lint (repo root):

```bash
backend/.venv/bin/pytest
backend/.venv/bin/ruff check . && backend/.venv/bin/ruff format --check backend ml tests
```

### Mobile

```bash
cd mobile
flutter create --org com.dermacare --project-name dermacare --platforms=android,ios .   # first time only
flutter pub get && flutter test
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

## Target deployment architecture (prototype stage, not provisioned)

```mermaid
flowchart LR
  subgraph Clients
    A[Android app]
    I[iOS app]
  end
  A & I -->|TLS| LB[Reverse proxy / HTTPS]
  LB --> API[FastAPI container\nstateless, N replicas]
  API --> PG[(Managed PostgreSQL\nencrypted, daily backups)]
  API --> S3[(Private object storage\nshort retention, SSE)]
  API --> GPU[Inference container\nCPU or small GPU]
  API -. optional .-> LLM[LLM provider API]
  CI[GitHub Actions] -->|image| REG[Container registry]
  REG --> API & GPU
```

Environments: `development` (local) → `staging` (CI-deployed from `main`) → `production` (tagged releases, only after the research prototype phase and licence review).

Release checklist: migrations reviewed and reversible; `ANALYSIS_BACKEND` and model versions pinned; secrets in a secret manager;
`LLM_PROVIDER` explicitly chosen (default `disabled`); data-retention job active; mobile builds signed via CI secrets.

Commercial deployment additionally requires commercially licensed training data or retraining (FFHQ-Wrinkle and CelebA are non-commercial).
