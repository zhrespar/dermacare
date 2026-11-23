# Architecture

## System context

```mermaid
flowchart LR
  U[User] -->|Android / iOS| M[Flutter app]
  M -->|HTTPS JSON + multipart| API[FastAPI backend]
  API --> DB[(PostgreSQL + pgvector\napp data, catalog, knowledge chunks)]
  API --> OBJ[(Private object storage\nface images, masks, Grad-CAM)]
  API --> INF[CV inference\nPyTorch + OpenCV + landmarks]
  API -. optional, configured .-> LLM[LLM API\nAnthropic / OpenAI / Gemini]
  COLAB[Google Colab training] -->|weights + model cards| DRIVE[(Google Drive\n03_Model_Artifacts)]
  DRIVE -->|release| INF
```

## What is trained, pretrained, rule-based or external

| Component | Kind | Code | Status |
|---|---|---|---|
| Acne lesion detection + 4-level severity | **Trained by us** (transfer learning from COCO / ImageNet) | `ml/training/configs.py` | Configs only; not trained |
| Wrinkle segmentation | **Trained by us** (U-Net, ImageNet encoder; weak → manual masks) | `ml/training/configs.py` | Configs only; not trained |
| Under-eye bag binary classification | **Trained by us** (ImageNet CNN) + Grad-CAM | `ml/training/configs.py` | Configs only; not trained |
| Face landmarks | **Pretrained** (e.g. MediaPipe), not retrained | adapter → `ml/preprocessing/face_regions.py` | Region geometry implemented; adapter pending |
| Image quality check | **Rule-based** (OpenCV metrics + thresholds) | `ml/preprocessing/quality.py` | Decision logic implemented; thresholds provisional |
| Triage / abstention | **Rule-based** | `backend/app/services/analysis/triage.py` | Implemented; thresholds provisional |
| Recommendation engine | **Rule-based**, deterministic | `backend/app/services/recommendation/` | Implemented; rule tables await expert review |
| RAG embeddings | **Pretrained** sentence-embedding model (configurable) | `backend/app/services/rag/embeddings.py` | Implemented (optional dependency) |
| RAG retrieval | pgvector cosine search | `backend/app/services/rag/store.py` | Implemented; knowledge base empty |
| Explanations / assistant | **External LLM API** (Anthropic / OpenAI / Gemini) | `backend/app/services/llm/` | Implemented; disabled by default |

We do **not** train an LLM, a recommendation model or an embedding model.
`GET /api/v1/system/components` returns this table plus the active configuration.

## Analysis pipeline

```mermaid
flowchart TD
  A[Frontal photo upload] --> G[Upload gate\nformat, size]
  G --> Q{Quality check\nface count, blur, exposure,\nface size, ROI visibility}
  Q -->|retake / out of scope| R[Ask for retake]
  Q -->|accepted| L[Pretrained landmarks]
  L --> ROI[Facial regions\nforehead, cheeks, nose, chin, under-eyes]
  ROI --> AC[Acne detector + severity classifier]
  ROI --> WR[Wrinkle segmenter]
  ROI --> UE[Under-eye classifier + Grad-CAM]
  AC & WR & UE --> T{Triage\nconfidence + scope thresholds}
  T -->|limited| LIM[Findings withheld from\nrecommendation; profile-only]
  T -->|refer_dermatologist| D[Stop cosmetic flow\nno disease name]
  T -->|proceed| F[Findings + confidences + regions\nboxes / mask / Grad-CAM]
```

`ANALYSIS_BACKEND=mock` (default) runs labelled placeholder models (`is_mock=true`, `model_version=mock-0`) through the
same quality → regions → triage path. Real inference (`torch`) is a separate backend that loads registered weights; mock
code and demo data never mix with it.

## Recommendation + explanation pipeline

```mermaid
flowchart LR
  IN[CV findings\nonly if triage=proceed\n+ declared profile] --> N[A. Derive needs]
  N --> C[B. Need → ingredient / category\nversioned expert rules]
  C --> HF[C. Hard filters\nunverified, unavailable,\nallergy / avoid / past-reaction INCI,\nsensitivity vs warnings, budget]
  HF -->|reason| EX[Excluded list]
  HF --> S[D. Score /100\n50 need+ingredient · 25 profile/goal\n15 routine/category · 10 preference]
  S --> RT[E. AM / PM routine\norder, manufacturer slot,\ncompatibility pairs]
  RT --> OUT[Validated recommendation\nrules_version]
  OUT --> RAG[F. Retrieve verified sources\npgvector, topic filter]
  RAG --> LLM[LLM explains ONLY validated items\nwith S-n citations]
  LLM --> GU{Guard\ncitations valid, products known,\nno medical wording, groundedness}
  GU -->|pass| EXP[llm_grounded explanation]
  GU -->|fail / disabled / no sources| TPL[rule_template explanation]
```

Authority order: **hard filters & scores (rules) > retrieved verified sources > LLM wording.** The LLM receives only
products that passed the filters and cannot add, remove or re-rank them. RAG supplies evidence; it never filters
products (exact filtering is SQL + rules). If no verified source is retrieved, the LLM is not called.

## Typed contracts

| Boundary | Contract |
|---|---|
| Flutter ↔ FastAPI | `docs/API_SPEC.yaml`; Pydantic schemas in `backend/app/schemas/`; Dart mirrors in `mobile/lib/core/models.dart` |
| FastAPI ↔ CV inference | `ml/inference/interfaces.py` (`AcneDetector`, `WrinkleSegmenter`, `UnderEyeClassifier`) |
| Analysis → recommendation | `FindingsIn` (incl. `triage_action`, `is_mock`) |
| Recommendation → explanation | `RecommendationResponse` sent unchanged in `ExplanationRequest` |
| Business logic ↔ LLM | `LLMProvider.generate(LLMRequest) -> LLMResponse` (`backend/app/services/llm/base.py`) |
| Business logic ↔ vector DB | `Embedder`, `VectorStore`, `Retriever` (`backend/app/services/rag/`) |

## Repository mapping

| Path | Contents |
|---|---|
| `backend/app/services/analysis/` | upload gate, mock pipeline, triage |
| `backend/app/services/recommendation/` | `rules.py`, `engine.py`, `routine.py` |
| `backend/app/services/rag/` | documents + chunking, embeddings, in-memory / pgvector stores, retriever, citations |
| `backend/app/services/llm/` | provider interface, Anthropic / OpenAI / Gemini adapters, guard, explain, provider comparison |
| `backend/app/models/knowledge.py` | `knowledge_documents`, `knowledge_chunks` (vector), `llm_call_logs` |
| `ml/preprocessing/` | quality check, facial regions |
| `ml/training/` | transfer-learning configs per task |
| `ml/inference/` | task interfaces, labelled mocks |
| `ml/evaluation/` | mAP, macro-F1, QWK, Dice/IoU, F1, ROC-AUC (pure Python) |

## Key decisions

1. **Server-side inference**: reduces device load and compatibility issues.
2. **Framework-free ML contracts** so backend and tests run without torch.
3. **Rules, not ML or LLM, choose products**: auditable and reproducible (`rules_version` + `catalog_version`).
4. **Provider-independent LLM layer**: same prompt, guard and metrics for every provider; comparisons change config, not code.
5. **pgvector inside PostgreSQL** as the starting vector store (one database to operate); swappable via `VectorStore`.
6. **Images never stored in PostgreSQL**: metadata + object-storage key with expiry.
7. **Separate provenance**: image findings and declared data kept apart so each recommendation is traceable.

## Sequence: analyse, recommend, explain

```mermaid
sequenceDiagram
  participant App
  participant API
  participant Inf as CV inference
  participant DB
  participant LLM
  App->>API: POST /api/v1/analyses (image)
  API->>Inf: quality + regions + 3 models
  Inf-->>API: findings, confidences, versions
  API-->>App: AnalysisResponse (triage action)
  App->>API: POST /api/v1/recommendations/preview (profile + findings)
  API->>DB: load frozen catalog version
  API-->>App: routines + ranked products + excluded
  App->>API: POST /api/v1/explanations (recommendation)
  API->>DB: pgvector retrieve verified chunks
  API->>LLM: validated items + sources (if configured)
  LLM-->>API: text with [S-n]
  API-->>App: explanation + citations (or rule template)
```
