"""Versioned rule tables for the deterministic recommendation engine.

STATUS: PROVISIONAL (v0.1.0). The need -> ingredient table and compatibility pairs are
intentionally EMPTY: they must come from expert/advisor-reviewed, source-cited rules and be
frozen (new RULES_VERSION) before the A/B/C evaluation. Do not fill them from memory or LLM output.
"""

from __future__ import annotations

RULES_VERSION = "0.1.0-provisional"

# Score weights (TÜBİTAK 2209-B proposal): sum = 100.
W_NEED, W_PROFILE, W_ROUTINE, W_PREF = 50.0, 25.0, 15.0, 10.0

# need -> INCI names (upper-case) that evidence a fit. Empty set = rule pending expert review.
NEED_INGREDIENTS: dict[str, set[str]] = {
    "acne_care": set(),
    "wrinkle_care": set(),
    "under_eye_care": set(),
    "hydration": set(),
    "sun_protection": set(),
}

# need -> product categories that can address it.
NEED_CATEGORIES: dict[str, set[str]] = {
    "acne_care": {"cleanser", "serum", "treatment"},
    "wrinkle_care": {"serum", "moisturizer"},
    "under_eye_care": {"eye"},
    "hydration": {"moisturizer"},
    "sun_protection": {"sunscreen"},
}

# Manufacturer warning tags that conflict with declared high sensitivity.
SENSITIVE_WARNING_TAGS = {"not_for_sensitive_skin", "may_irritate"}

# Routine step order per slot. Sunscreen is morning-only.
ROUTINE_ORDER: dict[str, list[str]] = {
    "am": ["cleanser", "treatment", "serum", "eye", "moisturizer", "sunscreen"],
    "pm": ["cleanser", "treatment", "serum", "eye", "moisturizer"],
}

# Pairs of INCI names that must not be placed in the same routine slot.
# Each entry needs a cited source before it is added.
INCOMPATIBLE_PAIRS: list[tuple[str, str]] = []
