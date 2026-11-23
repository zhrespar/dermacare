# Training

Training runs in Google Colab (GPU). Notebooks live in `ml/notebooks/`; reusable code lives here.

Rules:
- Datasets are mounted from the project Google Drive (`02_Datasets/`) only after licence terms are confirmed. Never commit datasets or weights.
- Every run logs: dataset version + split hash, preprocessing config, hyperparameters, seed, git commit, metrics on the validation split.
- The official test split is evaluated **once**, for the selected model only.
- Exported weights go to Drive `03_Model_Artifacts/<Task>/` with a model card.

No models have been trained yet.
