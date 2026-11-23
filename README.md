# dermacare
DermaCare is an AI-powered mobile skincare platform combining computer vision, explainable AI, and personalized skincare recommendations.

> Research prototype (TÜBİTAK 2209-B). Cosmetic decision support only — **not** a medical device; no diagnosis or treatment.

## What it does

Single frontal photo → quality check → three analyses (acne lesion detection + 4-level severity, wrinkle segmentation,
under-eye bag binary classification) → combined with the user's skin profile → rule-based, explainable morning/evening
routine from a verified product catalog.

## Repository

| Path | Contents |
|---|---|
| `mobile/` | Flutter app (Android/iOS): navigation + placeholder screens for the full journey |
| `backend/` | FastAPI: `/health`, analysis (mock CV + triage), rule-based recommendation + routines, RAG, LLM explanations, tests |
| `ml/` | `preprocessing/`, `training/`, `inference/` (task interfaces + labelled mocks), `evaluation/`, `notebooks/` |
| `database/` | Alembic `migrations/`, `seed/` templates |
| `docs/` | PRD, architecture, DB schema, OpenAPI spec, ML methodology, deployment, security, sprint plan, workflow |
| `tests/` | Cross-component tests |

## Quick start

```bash
cp .env.example .env
docker compose up --build          # PostgreSQL + API on :8000
curl localhost:8000/health
```

Without Docker: see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). Mobile: see [mobile/README.md](mobile/README.md).

## How the AI parts work

| Part | Approach |
|---|---|
| Acne, wrinkles, under-eye bags | **Trained by us** via transfer learning from pretrained CV models |
| Landmarks, embeddings | **Pretrained**, used as-is |
| Quality check, triage, recommendations | **Rule-based**, deterministic and auditable |
| Explanations | **Ready-made LLM APIs** (Anthropic / OpenAI / Gemini), grounded by RAG over verified sources; disabled by default |

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Status

Prototype infrastructure. Analysis uses **mock models** (`is_mock: true`, `model_version: mock-0`). No trained models,
no verified product catalog, no knowledge-base sources and no LLM provider configured yet.
