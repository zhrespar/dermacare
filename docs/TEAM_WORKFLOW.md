# Team Workflow

Task ownership lives in **Trello**; this repo does not assign people.

## Tools

| Purpose | Tool |
|---|---|
| Code, docs, reviews, CI | GitHub `zhrespar/dermacare` |
| Task board | Trello (Backlog → Ready → In Progress → Review → Done) |
| Training | Google Colab |
| Datasets (licence-cleared), model artifacts, admin docs, meeting notes, demos | Google Drive `DermaCare - Project Workspace` |

Source code and technical documentation live **only** in GitHub (not duplicated in Drive).

## Branching

- `main` is protected: PR + green CI required, no force-push.
- Branch names: `feature/<short-desc>`, `fix/<short-desc>`, `ml/<task>-<desc>`, `docs/<desc>`.
- Small PRs (< ~400 changed lines where possible). Link the Trello card in the PR description.
- Squash-merge; delete branch after merge.

## Commits

Imperative, scoped: `backend: add profile endpoints`, `mobile: capture screen`, `ml: acne loader`.

## Definition of Done

- Code + tests; `ruff`/`flutter analyze` clean; CI green.
- API changes reflected in `docs/API_SPEC.yaml`; schema changes have an Alembic migration and update `DATABASE_SCHEMA.md`.
- No secrets, images, datasets or weights committed.
- Any mock/placeholder output is explicitly labelled.
- ML results only reported with experiment ID, config and commit (see `ML_EXPERIMENTS.md`).

## Reviews

At least one reviewer. Reviewer checks correctness, privacy (no PII in logs), claims (no medical/diagnostic wording), and reproducibility.

## Meetings

Weekly planning + short async stand-ups; notes in Drive `01_Project_Management/Meeting_Notes/` as `YYYY-MM-DD_<topic>`.
