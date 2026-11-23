# Architecture

## System context

```mermaid
flowchart LR
  U[User] -->|Android / iOS| M[Flutter app]
  M -->|HTTPS JSON + multipart| API[FastAPI backend]
  API --> DB[(PostgreSQL)]
  API --> OBJ[(Private object storage\nface images, masks, Grad-CAM)]
  API --> INF[Inference service\nPyTorch + OpenCV + MediaPipe]
  API -. optional .-> LLM[LLM provider\nRAG explanations]
  COLAB[Google Colab training] -->|weights + model cards| DRIVE[(Google Drive\n03_Model_Artifacts)]
  DRIVE -->|release| INF
```

## Analysis pipeline

```mermaid
flowchart TD
  A[Frontal photo upload] --> Q{Quality check\nface, blur, exposure,\nsize, ROI visibility, occlusion}
  Q -->|retake / out of scope| R[Ask for retake]
  Q -->|accepted| L[MediaPipe landmarks]
  L --> ROI[OpenCV ROI extraction]
  ROI --> AC[Acne detector + severity classifier]
  ROI --> WR[Wrinkle segmenter]
  ROI --> UE[Under-eye classifier + Grad-CAM]
  AC & WR & UE --> T{Safety / triage\nconfidence, scope, quality}
  T -->|low confidence / out of scope| D[Limit flow, suggest dermatologist\nno disease name]
  T -->|proceed| F[Findings + confidences]
  F --> P[Multimodal profile\nfindings + declared profile]
  P --> RE[Rule-based recommendation engine]
  RE --> X[Explanations\n+ optional RAG rephrasing]
```

## Recommendation engine

```mermaid
flowchart LR
  N[1. Derive needs] --> C[2. Need -> ingredient/category rules]
  C --> HF[3. Hard filters\nunverified, allergy/avoid INCI,\nsensitivity vs warnings, budget]
  HF -->|excluded + reason| EX[Excluded list]
  HF --> S[4. Score /100\n50 need+ingredient\n25 profile/goal\n15 routine/category\n10 preference]
  S --> RT[AM / PM routine assembly]
  RT --> E[5. Explanation per component]
```

Deterministic: pinned `rules_version` + `catalog_version` ⇒ reproducible output.

## Components and repository mapping

| Component | Path | Tech | Status |
|---|---|---|---|
| Mobile app | `mobile/` | Flutter, go_router, http | Navigation + placeholder screens |
| API | `backend/app` | FastAPI, Pydantic v2 | `/health`, mock analysis, recommendation preview |
| Data model | `backend/app/models`, `database/migrations` | SQLAlchemy 2, Alembic | Initial schema (`0001`) |
| ML contracts | `ml/inference/interfaces.py` | Pure Python Protocols | Done |
| Mock models | `ml/inference/mock_models.py`, `backend/app/services/mock_analysis.py` | — | Labeled `mock-0`, `is_mock=true` |
| Quality check | `ml/preprocessing/quality.py` | OpenCV, MediaPipe | Contract only |
| Training | `ml/training`, `ml/notebooks` | PyTorch on Colab | Not started |
| LLM/RAG | `backend/app/services/llm.py` | Provider interface | Disabled stub |
| CI | `.github/workflows/ci.yml` | GitHub Actions | Lint, migrations, tests |

## Key decisions

1. **Server-side inference** (proposal): reduces device load and device-compatibility issues.
2. **Framework-free ML contracts** so backend and tests run without torch; real models plug in behind `ANALYSIS_BACKEND=torch`.
3. **Rules, not ML, choose products**: auditable and reproducible; LLM may only rephrase.
4. **Images never stored in PostgreSQL**: only metadata and an object-storage key with expiry.
5. **Separate provenance**: image-derived findings and user-declared data stored in separate fields so each recommendation is traceable to its source.

## Sequence: analyse and recommend

```mermaid
sequenceDiagram
  participant App
  participant API
  participant Inf as Inference
  participant DB
  App->>API: POST /api/v1/analyses (image)
  API->>Inf: quality + ROI + 3 models
  Inf-->>API: findings, confidences, versions
  API->>DB: save analysis (no raw image)
  API-->>App: AnalysisResponse (triage action)
  App->>API: POST /api/v1/recommendations (analysis_id, profile)
  API->>DB: load frozen catalog version
  API-->>App: AM/PM ranked products + reasons + excluded
```
