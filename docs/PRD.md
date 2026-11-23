# DermaCare — Product Requirements Document

**Status:** v0.1 (initial infrastructure) · **Source of truth:** TÜBİTAK 2209-B research proposal
*"Çok Modlu Cilt Analizi ve Açıklanabilir Yapay Zekâ Tabanlı Kişiselleştirilmiş Cilt Bakım Öneri Sistemi"*
(local file `2209-BDermacare.docx`, 2026–2027 term, 1st period). Where this PRD and the proposal differ, the proposal wins.

> Note on sources: the proposal's Tables 2–8 (datasets, model plan, schedule, risks, facilities, outputs) and figures are
> embedded as images/objects and could not be extracted as text. Their contents are summarised only where the body text
> states them. The detailed work-package schedule (WP1–WP7) must be copied in from the original document.

## 1. Problem

Growing numbers of skincare products and ingredients make it hard for users to choose products that fit their visible
skin characteristics, sensitivities and personal constraints. Approaches based only on images or only on self-reported
data may not personalise sufficiently.

## 2. Goal

Build a **mobile decision-support research prototype** that:

1. analyses a single standardised frontal face photo for three visible characteristics;
2. combines the findings with a user-declared skin profile;
3. filters and ranks products from a **verified** product/ingredient catalog with transparent, versioned rules;
4. explains every finding and every recommendation.

**Research question:** Does combining image analysis with the user profile (C) improve recommendation suitability
compared with profile-only (A) or image-only (B) approaches?

## 3. Non-goals

- No medical diagnosis, disease naming, drug or treatment advice.
- No "best product" claims; no brand favouritism.
- No claim that dataset test performance transfers to real user photos (no external real-world validation in scope).
- No commercial use of non-commercial datasets (FFHQ-Wrinkle CC BY-NC-SA 4.0, CelebA non-commercial research licence).

## 4. Users

Adults seeking cosmetic skincare routine guidance via Android or iOS. Research evaluators (blinded experts) and the
industry advisor use exported scenario outputs, not the app.

## 5. User journey (mobile)

| # | Screen | Requirement |
|---|---|---|
| 1 | Welcome | Value proposition + non-medical disclaimer |
| 2 | Authentication | Email sign-up/sign-in; explicit consent to privacy notice (KVKK/GDPR) |
| 3 | Skin Profile | Skin type, sensitivity, known allergies / ingredients to avoid, current routine, past reactions, goal, budget, preferences. Unanswered critical fields (allergy, sensitivity) are **unknown**, never assumed "no" |
| 4 | Frontal Face Photo | Guided single frontal capture (no three-angle requirement): lighting, position, neutral expression, no filters |
| 5 | Quality Check | Face detected; blur; over/under exposure; face size in frame; required regions visible; occlusion → accepted / retake / out of scope |
| 6 | Skin Analysis | Server-side inference for the three tasks |
| 7 | Explainable Results | Acne boxes + severity; wrinkle mask; under-eye result + Grad-CAM; confidence; plain language |
| 8 | Morning/Evening Routine | Categories placed into AM/PM respecting usage instructions and compatibility rules |
| 9 | Product Recommendations | Ranked verified products with score breakdown and reasons; excluded products with reasons |
| 10 | History | Past analyses/recommendations; delete my data |

## 6. Functional requirements

### 6.1 Computer vision (three independent tasks)

| Task | Formulation | Dataset (per proposal) | Notes |
|---|---|---|---|
| Acne | Lesion **detection** (bounding boxes) + image-level **4-level severity** classification | ACNE04 | Detection and severity are separate outputs/metrics |
| Wrinkles / fine lines | Pixel-level **segmentation** | FFHQ-Wrinkle | 50k weak masks for pre-training only; final evaluation on 1,000 manual annotations |
| Under-eye bags | **Binary** classification | CelebA `Bags_Under_Eyes` | Binary facial attribute, **not** a medical severity |

Candidate architectures named in the proposal's references: Faster R-CNN, YOLOv8 (detection); U-Net, SwinUNETR (2D adaptation)
(segmentation); ResNet, MobileNetV2 (classification); Grad-CAM (explanation). No model is assumed best in advance.

Only these three CV components are trained/fine-tuned by the project, using pretrained backbones and transfer learning
(configs in `ml/training/configs.py`). No LLM, recommendation model or embedding model is trained.

Explainable visual outputs: lesion boxes with confidence and facial region, wrinkle mask overlay, under-eye Grad-CAM,
per-region lesion counts.

### 6.2 Preprocessing

- MediaPipe face landmarks → OpenCV ROI extraction (face skin area for acne/wrinkles; periocular/under-eye for bags).
- Resize/normalise per model; regional masks; augmentation on training split only, never altering visible skin features.
- Facial region mapping (forehead, cheeks, nose, chin, under-eyes) from pretrained landmarks.
- Quality decision: no face / multiple faces → out of scope; blur, exposure, face size, ROI visibility → retake.
- Quality and confidence thresholds fixed on the validation split before final testing (current values provisional).

### 6.3 Safety / triage layer (not a disease classifier)

Stops or limits the normal recommendation flow when: quality thresholds fail; required region not visible; input cannot
be reliably explained by the three targets; model confidence below a validation-fixed threshold. In those cases: no
disease name, suggest dermatologist evaluation. Also triggered by missing critical profile information.

Actions: `retake` (image problem), `limited` (low confidence → CV findings are withheld from the recommendation, which
falls back to the declared profile), `refer_dermatologist` (out-of-scope finding), `proceed`.

### 6.4 Product / ingredient catalog

- ≥ 100 cosmetic products, verifiable, structured, PostgreSQL, versioned and **frozen before A/B/C evaluation**.
- Candidates from Open Beauty Facts (ODbL); INCI verified against manufacturer page / technical doc / packaging;
  manufacturer wins on conflicts (logged); INCI names normalised via EU CosIng (COSMILE Europe optional).
- Per product: id, barcode (if any), brand, manufacturer, name, category, full INCI, key ingredients, intended use,
  manufacturer usage instructions, warnings, price, currency, price-check date, availability, discovery URL (Open Beauty
  Facts — discovery only), authoritative source URL + type, access date, verification date, verification status.
- 100 verified products is the research **target**; the current catalog is empty and no real product records are committed.
- Incomplete / unverifiable / conflicting products are excluded from the pool.
- No copying of unlicensed product images.

### 6.5 Recommendation engine (rule-based, deterministic)

1. Derive care needs from findings + goals.
2. Map needs → ingredient / product categories (versioned rule table, expert-informed).
3. **Hard filters** before scoring: unverified/unavailable products, allergy / avoid / past-adverse-reaction INCI,
   sensitivity vs manufacturer warnings, category constraints, budget.
4. **Score (100):** need + ingredient match **50**, goal/profile fit **25**, routine/category fit **15**, preference **10**
   (provisional; justified with expert input and frozen before scenarios run).
5. Build AM/PM routines: fixed step order, manufacturer routine slot, sunscreen morning-only, one product per category,
   source-cited incompatibility pairs.
6. Explain: finding, user need, applied constraints, ingredient/product attribute, score components.

No recommendation model is trained for the MVP. Rule tables (`backend/app/services/recommendation/rules.py`) are empty
placeholders until expert-reviewed, source-cited rules are added and a new `rules_version` is frozen.

Same input + same catalog version ⇒ same output.

### 6.6 Explanations (RAG + ready-made LLM APIs — project stack addition)

The proposal does not specify an LLM. The stack adds:

- **RAG** over a vetted knowledge base (scientific, dermatology-guideline, ingredient-database, manufacturer and
  regulatory sources): configurable pretrained embedding model, sentence-aware chunking, source metadata, PostgreSQL +
  pgvector retrieval with topic filters, `[S-n]` citations that always map to stored sources. Only `verified` sources are
  ingested. RAG supplies evidence; it never replaces SQL product filtering.
- **Ready-made LLMs via API** (Anthropic, OpenAI, Google Gemini) behind one provider-independent interface. The LLM
  explains only already-validated recommendations using retrieved sources; it cannot override hard filters, add products,
  diagnose, or suggest treatment. A guard rejects outputs with invalid citations, unknown products, medical wording or low
  groundedness, and the rule-based template is shown instead.
- Disabled by default. No API keys or model ids are assumed; paid access must be enabled explicitly.
- Every call records latency, token usage, cost estimate (from configured prices), groundedness ratio and safety flag
  (`llm_call_logs`, no prompt text) for later provider comparison. Conversational assistance reuses the same interface
  and guard (post-MVP).

## 7. Evaluation requirements (from proposal)

- CV: same splits, same preprocessing, same metrics per task; official test split used once; validation-based model selection.
- A/B/C study: 30 controlled scenarios (10 acne, 10 wrinkle, 10 under-eye) × 3 approaches = 90 outputs; synthetic profiles;
  ≥ 2 independent blinded experts; 4 rubric dimensions scored 1–5; weighted Cohen's κ (target ≥ 0.60); Friedman +
  Wilcoxon signed-rank with Holm correction; primary comparison C vs A; secondary C vs B, constraint-violation rate.
  See `ML_EXPERIMENTS.md`.

## 8. Non-functional requirements

- Privacy by design (see `SECURITY_PRIVACY.md`); no raw images in the DB; minimal retention.
- Server-side inference; mobile app works on mid-range devices.
- Reproducibility: versioned models, rules, catalog; experiment logs.
- Accessibility: readable contrast, scalable text, screen-reader labels.

## 9. Deliverables (12-month research project)

Model results for the three tasks; verified product/ingredient database; explainable recommendation engine; working mobile
prototype; comparative A/B/C evaluation results.

## 10. Open items

- Copy WP1–WP7 schedule, risk table and facilities table from the original proposal (not extractable).
- Expert-reviewed need→ingredient rule table and compatibility pairs (with sources).
- Curate and verify the RAG knowledge base (licence allows storing excerpts).
- Decide which LLM providers/models are available to the project (API access, budget).
- Ethics: if any real participant images are collected, ethics approval/exemption and consent procedures first.
