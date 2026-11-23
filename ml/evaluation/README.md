# Evaluation

See `docs/ML_EXPERIMENTS.md` for the full methodology. Planned primary metrics (not results):

| Task | Primary metric | Secondary |
|---|---|---|
| Acne lesion detection | mAP@0.5 | mAP@0.5:0.95, precision, recall |
| Acne severity (4-level) | macro-F1 | per-class recall, confusion matrix, quadratic weighted kappa |
| Wrinkle segmentation | Dice / IoU on the 1,000 manually annotated masks | precision, recall |
| Under-eye bags (binary) | F1 / balanced accuracy | ROC-AUC, PR-AUC, FP/FN breakdown, Grad-CAM ROI consistency |

No results exist yet.
