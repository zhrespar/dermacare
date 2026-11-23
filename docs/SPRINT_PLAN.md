# 14-Day Development Plan (Sprint 1–2)

Ownership is **unassigned** — owners are set in Trello. Day 0 = this initial-infrastructure PR merged.
These 14 days start the project's longer 12-month work-package plan (WP1–WP7 in the TÜBİTAK proposal, to be copied from the original document).

| Day | Track | Task | Done when |
|---|---|---|---|
| 1 | Repo | Merge infra PR; enable branch protection on `main` (PR + green CI) | CI green on `main` |
| 1 | Mobile | Run `flutter create` for android/ios, commit platform folders; verify app runs on Android emulator + iOS simulator | Both launch to Welcome |
| 2 | Backend | Auth: register/login/JWT, password hashing, consent fields | Tests for register/login/401 |
| 2 | Data | Record licence terms for ACNE04, FFHQ-Wrinkle, CelebA in Drive `LICENSE_NOTES` | All three documented |
| 2 | RAG | Shortlist knowledge-base sources (guidelines, CosIng, manufacturer pages); check excerpt licence; fill `knowledge_template.csv` | ≥ 10 candidate rows with licence noted |
| 3 | Backend | Profile GET/PUT endpoints + tests (null = unknown) | Contract matches API_SPEC |
| 3 | Mobile | Auth + Skin Profile forms wired to API | Profile saved end-to-end |
| 4 | ML | MediaPipe landmark + ROI extraction module with unit tests on synthetic images | ROI boxes for face skin + under-eye |
| 4 | Catalog | Catalog curation sheet from `database/seed/product_template.csv`; first 20 candidates (Open Beauty Facts) | Rows with source + access date |
| 5 | ML | Quality check v0: blur (Laplacian var), exposure, face size, ROI visibility | Returns accepted/retake/out_of_scope |
| 5 | Mobile | Guided camera capture screen (permissions, oval guide) | Photo captured on device |
| 6 | Backend | Object storage abstraction (local dir in dev), EXIF strip, retention field | Upload persisted with expiry |
| 6 | ML | Colab notebook: ACNE04 loader + split check + baseline detector config | Notebook runs on sample subset |
| 7 | Integration | Mobile → `/api/v1/analyses` (mock) → Results screen showing MOCK banner | End-to-end demo |
| 7 | Review | Sprint 1 review + retro; update Trello | Notes in Drive Meeting_Notes |
| 8 | ML | FFHQ-Wrinkle loader; weak-mask pre-training config; manual-mask eval split | Data pipeline verified |
| 8 | RAG | Ingest first verified sources with `RAG_EMBEDDING_BACKEND=sentence_transformers` + `RAG_STORE=pgvector`; labelled query set for hit rate | Retrieval returns cited chunks |
| 8 | Catalog | INCI verification vs manufacturer for first 20; CosIng normalisation script | Verified/rejected statuses set |
| 9 | ML | CelebA under-eye loader (attribute + periocular crop); class balance report | Report saved |
| 9 | Backend | Catalog import script (CSV → products/ingredients) with validation | Only complete rows import |
| 10 | Rules | Draft need→ingredient table + compatibility pairs (each with source) for expert/advisor review | `rules.py` v0.2 proposal |
| 10 | Mobile | Results screen: boxes overlay, mask overlay, under-eye card | Renders mock data |
| 11 | Backend | `/api/v1/recommendations` from stored analysis + profile + catalog version; persist `llm_call_logs` | Deterministic tests |
| 11 | Mobile | Routine (AM/PM) + Products screens with score breakdown and exclusions | Renders engine output |
| 12 | LLM | If API access is confirmed: set provider keys/models in `.env`, run `compare_providers` on fixture scenarios; record latency, cost estimate, groundedness, guard pass rate | Comparison table in experiment log (only configured providers) |
| 12 | ML | Landmark adapter → `face_regions.Keypoints`; quality `compute_metrics` on sample images | Regions + quality on sample subset |
| 13 | Mobile | History screen + delete-my-data; explanation view with citations (`ApiClient.explain`) | Works against API |
| 13 | Docs | Update API_SPEC, DATABASE_SCHEMA with changes | Docs match code |
| 14 | QA | End-to-end test on one Android + one iOS device; fix blockers | Checklist passed |
| 14 | Review | Sprint 2 review; demo recording to Drive `06_Demo_and_Reports` | Demo saved |

Already done before Day 1 (architecture PR): triage/abstention layer, facial region mapping, quality decision logic,
evaluation metrics on toy data, transfer-learning configs, RAG pipeline (chunking, embeddings, in-memory + pgvector store,
citations), provider-independent LLM layer (Anthropic / OpenAI / Gemini) with guard and metrics, AM/PM routine builder,
`/api/v1/explanations`, Dart API models.

Also done (backend-core PR): register/login (argon2 + JWT, consent), profile GET/PUT, stored analyses + history,
`POST /api/v1/recommendations` from stored profile/analysis + current catalog version, `DELETE /api/v1/me`, catalog CSV
importer with validation (`python -m app.cli.import_catalog`), LLM call-metric logging.

Out of scope for these 14 days: training final models, A/B/C expert study, any production deployment, paid APIs.
