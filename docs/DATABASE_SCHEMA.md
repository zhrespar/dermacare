# Database Schema

PostgreSQL 16 · SQLAlchemy 2 models in `backend/app/models/entities.py` · migration `database/migrations/versions/0001_initial_schema.py`.

```mermaid
erDiagram
  users ||--o{ skin_profiles : has
  users ||--o{ face_images : uploads
  users ||--o{ analyses : runs
  face_images ||--o{ analyses : "analysed in"
  users ||--o{ recommendations : receives
  analyses ||--o{ recommendations : informs
  catalog_versions ||--o{ products : contains
  catalog_versions ||--o{ recommendations : "pinned by"
  products ||--o{ product_ingredients : lists
  ingredients ||--o{ product_ingredients : "used in"
  recommendations ||--o{ recommendation_items : contains
  products ||--o{ recommendation_items : "recommended as"
```

## Tables

### users
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| email | varchar(320) unique | |
| password_hash | varchar(255) | argon2/bcrypt; never plain |
| is_active | bool | |
| consent_version, consent_at | varchar, timestamptz | privacy-notice version accepted |
| deleted_at | timestamptz | soft delete → hard purge job |
| created_at | timestamptz | |

### skin_profiles (user-declared; NULL = unknown, never "no")
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK users (cascade) | |
| skin_type | varchar(16) | dry / oily / combination / normal |
| sensitivity | varchar(16) | none / mild / high |
| allergies, avoid_ingredients | json | INCI names |
| goals | json | acne_care, wrinkle_care, under_eye_care, hydration, sun_protection |
| current_routine | json | |
| past_reactions | text | |
| budget_max, currency | numeric(10,2), char(3) | |
| preferences | json | categories, texture, etc. |

### face_images (metadata only)
id, user_id, storage_key (private bucket), sha256, width, height, quality_status (accepted/retake/out_of_scope), quality_reasons json, expires_at, created_at.

### analyses
id, user_id, face_image_id (FK, set null), status (completed/limited/referred/failed), **is_mock**, acne json, wrinkles json, under_eye json, triage json, model_versions json, created_at.

### catalog_versions
id, label (unique, e.g. `2026.12-v1`), frozen bool, notes. A frozen version is immutable; the A/B/C study pins one.

### ingredients
id, inci_name (unique, CosIng-normalised), cosing_ref, functions json.

### products
id, catalog_version_id, barcode, brand, name, category, routine_slot (am/pm/both), intended_use, warnings json, price, currency, source_url, source_type (manufacturer / open_beauty_facts / package), accessed_at, verified_at, verification_status (pending/verified/rejected), created_at.

### product_ingredients
PK (product_id, ingredient_id), position (INCI order), is_key.

### recommendations
id, user_id, analysis_id, catalog_version_id, rules_version, mode (profile_only / image_only / multimodal), needs json, explanation, created_at.

### recommendation_items
id, recommendation_id, product_id, routine_slot, step_order, total_score, score_breakdown json (`need_ingredient`, `profile_goal`, `routine_category`, `preference`), reasons json.

## Catalog verification workflow

1. Candidate from Open Beauty Facts (record ODbL attribution) → `pending`.
2. Compare INCI with manufacturer official page / technical doc / packaging; manufacturer wins; log differences.
3. Normalise INCI via CosIng; store functions.
4. Complete all required fields → `verified` (with `verified_at`); otherwise `rejected`.
5. Freeze catalog version (≥ 100 verified) before A/B/C scenarios.

## Commands

```bash
cd backend && export PYTHONPATH=$PWD:$PWD/..
alembic upgrade head                         # apply
alembic revision --autogenerate -m "msg"     # new migration (review before commit)
alembic check                                # model/migration drift
alembic downgrade -1
```
