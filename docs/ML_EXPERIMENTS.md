# ML Experiments & Evaluation Methodology

**No models have been trained. No results exist. This file defines the protocol and the empty experiment log.**
Methodology follows the TÜBİTAK 2209-B proposal.

## 1. Datasets

| Task | Dataset | Labels used | Licence (per proposal) | Caveat |
|---|---|---|---|---|
| Acne | ACNE04 [Wu et al., ICCV 2019] | lesion boxes; image-level 4-level severity | free for academic use | boxes and severity are separate targets |
| Wrinkles | FFHQ-Wrinkle [Moon et al., ICPR 2024] | 50,000 weak masks (pre-training); 1,000 manual masks (final eval) | CC BY-NC-SA 4.0 | weak masks ≠ ground truth |
| Under-eye | CelebA [Liu et al., ICCV 2015] `Bags_Under_Eyes` | binary attribute | non-commercial research agreement | not a medical severity measure |

Datasets are independent and contain no paired records for the same person. They are never merged as if from one individual.
Before any download/upload: confirm licence terms and record them in Drive `02_Datasets/<Task>/LICENSE_NOTES`.

## 2. Data preparation checks

- Readability, label↔image matching, duplicate detection (hash + near-duplicate).
- **Leakage control:** an image and its derivatives appear in exactly one split. Use official splits where provided.
- Augmentation on training split only; box/mask transforms kept consistent; no augmentation that alters visible skin features.
- Class distribution report per split; class weighting or balanced sampling where imbalanced.
- Log: image size, normalisation, ROI parameters, seed, split hash.

## 3. Candidate models (none assumed best)

| Task | Candidates | Primary metric | Secondary |
|---|---|---|---|
| Acne detection | Faster R-CNN, YOLOv8 | mAP@0.5 | mAP@0.5:0.95, precision, recall |
| Acne severity (4 classes) | CNN classifiers (e.g. ResNet, MobileNetV2) | macro-F1 | per-class recall, confusion matrix, quadratic weighted κ |
| Wrinkle segmentation | U-Net, SwinUNETR (2D adaptation) | Dice (on 1,000 manual masks) | IoU, precision, recall, compute cost |
| Under-eye (binary) | ResNet, MobileNetV2 | F1 (positive class) / balanced accuracy | ROC-AUC, PR-AUC, FP/FN analysis, Grad-CAM ROI consistency |

All candidates start from public pretrained weights (transfer learning); starting hyperparameters are in
`ml/training/configs.py`. Metric implementations: `ml/evaluation/metrics.py` (unit-tested on toy arrays only).

Accuracy alone is never reported as the headline metric. Model size, inference latency and memory are recorded for integration.

## 4. Protocol

1. Same split, preprocessing pipeline and metrics for all candidates of a task.
2. Hyper-parameters / early stopping / model selection on **validation** only, by the pre-declared primary metric.
3. **Test split evaluated once** for the selected model; result reported as-is.
4. Report mean ± std over ≥ 3 seeds where compute allows.
5. Results are dataset-based; they are **not** claims about real mobile-photo performance (no external real-user validation in scope).
6. Safety thresholds (quality, confidence) fixed on validation before testing; never changed after seeing test results.
7. Grad-CAM: measure overlap of activation with the under-eye ROI (qualitative + simple overlap ratio).

## 4b. Non-trained AI components (measured, not trained)

| Component | Kind | What we record |
|---|---|---|
| Face landmarks | pretrained | region visibility failures on the validation split |
| Quality check / triage | rules | retake / limited / refer rates; thresholds + version |
| RAG embeddings | pretrained (`RAG_EMBEDDING_MODEL`) | model id, dim, retrieval hit rate on a labelled query set |
| LLM explanations | external API | per provider+model: latency, tokens, cost estimate, groundedness ratio, guard pass rate, safety flags |

Provider comparison uses `app.services.llm.compare_providers` over the same scenarios, same retrieved sources and same
prompt. Only configured providers are run; no rows are reported for providers without API access. Cost figures depend on
the prices entered in configuration at run time and are estimates.

## 5. Recommendation study (A/B/C)

| Item | Specification |
|---|---|
| Approaches | A profile-only · B image-only · C multimodal |
| Scenarios | 30 (10 acne, 10 wrinkle, 10 under-eye), synthetic profiles, fixed before running |
| Outputs | 90 (30 × 3), coded and shuffled |
| Raters | ≥ 2 independent experts (≥ 1 dermatologist / clinically experienced physician), not involved in development, blinded to method |
| Rubric | 4 dimensions × 1–5: fit to visible finding, fit to user profile, ingredient/product suitability, overall applicability; overall = mean |
| Agreement | weighted Cohen's κ, target ≥ 0.60; below target → rubric review, optional third rater |
| Tests | Friedman across A/B/C; Wilcoxon signed-rank pairwise with Holm correction; report direction and effect size |
| Primary | C vs A expert score · Secondary: C vs B, hard-constraint violation rate, inter-rater agreement |
| Fixed beforehand | catalog version (≥ 100 verified), rules version, weights, scenarios |

B does not receive profile-only constraints (e.g. allergies); this is recorded, not imputed. A non-supported hypothesis is a valid reported outcome.

## 6. Experiment log template

| ID | Date | Task | Model | Data/split hash | Config | Seed | Commit | Val metric | Test metric | Artifact (Drive) | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — | — | — | — | *no experiments yet* |

Artifacts: Drive `03_Model_Artifacts/<Task>/<ID>/` (weights + model card). Reports: `04_Experiments/Evaluation_Reports/`.
