"""Rule-based recommendation engine (rules v0.1.0).

Pipeline (TÜBİTAK 2209-B proposal):
 1. derive care needs from findings + goals
 2. map needs -> ingredient/category rules
 3. hard filters: unverified, allergy/avoid INCI, sensitivity warnings, budget
 4. score survivors: need+ingredient 50, profile/goal 25, routine/category 15, preference 10
 5. explain every score component

Weights and the NEED_INGREDIENTS table are PROVISIONAL: they must be reviewed with the
industry advisor / expert input and frozen before the A/B/C evaluation.
"""

from __future__ import annotations

from app.schemas.recommendation import (
    ExcludedProduct,
    FindingsIn,
    ProductIn,
    ProfileIn,
    RankedProduct,
    RecommendationRequest,
    RecommendationResponse,
    ScoreBreakdown,
)

RULES_VERSION = "0.1.0-provisional"
W_NEED, W_PROFILE, W_ROUTINE, W_PREF = 50.0, 25.0, 15.0, 10.0

# Placeholder mapping — to be replaced by an expert-reviewed, versioned rule table.
NEED_INGREDIENTS: dict[str, set[str]] = {
    "acne_care": set(),
    "wrinkle_care": set(),
    "under_eye_care": set(),
    "hydration": set(),
    "sun_protection": set(),
}
NEED_CATEGORIES: dict[str, set[str]] = {
    "acne_care": {"cleanser", "serum", "treatment"},
    "wrinkle_care": {"serum", "moisturizer"},
    "under_eye_care": {"eye"},
    "hydration": {"moisturizer"},
    "sun_protection": {"sunscreen"},
}
SENSITIVE_WARNING_TAGS = {"not_for_sensitive_skin", "may_irritate"}


def _norm(s: str) -> str:
    return s.strip().lower()


def derive_needs(req: RecommendationRequest) -> list[str]:
    needs: list[str] = []
    f: FindingsIn | None = req.findings if req.mode != "profile_only" else None
    p: ProfileIn | None = req.profile if req.mode != "image_only" else None
    if f:
        if f.acne_severity is not None:
            needs.append("acne_care")
        if f.wrinkle_area_ratio is not None and f.wrinkle_area_ratio > 0:
            needs.append("wrinkle_care")
        if f.under_eye_present:
            needs.append("under_eye_care")
    if p:
        needs.extend(g for g in p.goals if g not in needs)
    if "sun_protection" not in needs:
        needs.append("sun_protection")
    return needs


def recommend(req: RecommendationRequest, catalog: list[ProductIn]) -> RecommendationResponse:
    profile = req.profile if req.mode != "image_only" else None
    needs = derive_needs(req)
    missing: list[str] = []
    if profile is None or profile.allergies is None:
        missing.append("allergies")
    if profile is None or profile.sensitivity is None:
        missing.append("sensitivity")

    blocked = (
        {_norm(x) for x in ((profile.allergies or []) + profile.avoid_ingredients)} if profile else set()
    )
    ranked: list[RankedProduct] = []
    excluded: list[ExcludedProduct] = []

    for prod in catalog:
        reasons: list[str] = []
        if prod.verification_status != "verified":
            reasons.append("product_not_verified")
        hits = blocked & {_norm(i) for i in prod.inci}
        if hits:
            reasons.append(f"contains_blocked_ingredient:{','.join(sorted(hits))}")
        if profile and profile.sensitivity == "high" and SENSITIVE_WARNING_TAGS & set(prod.warnings):
            reasons.append("warning_conflicts_with_sensitivity")
        if profile and profile.budget_max is not None and prod.price is not None:
            if prod.price > profile.budget_max:
                reasons.append("over_budget")
        if reasons:
            excluded.append(ExcludedProduct(product_id=prod.id, reasons=reasons))
            continue

        why: list[str] = []
        matched = [n for n in needs if n in prod.targets]
        need_score = W_NEED * (len(matched) / len(needs)) if needs else 0.0
        if matched:
            why.append(f"addresses: {', '.join(matched)}")
        prof_score = 0.0
        if profile:
            if profile.skin_type and profile.skin_type in prod.suitable_skin_types:
                prof_score += W_PROFILE * 0.6
                why.append(f"suitable for {profile.skin_type} skin")
            if set(profile.goals) & set(prod.targets):
                prof_score += W_PROFILE * 0.4
                why.append("matches stated goal")
        cat_ok = any(prod.category in NEED_CATEGORIES.get(n, set()) for n in needs)
        routine_score = W_ROUTINE if cat_ok else 0.0
        pref_score = 0.0
        if profile and prod.category in profile.preferred_categories:
            pref_score = W_PREF
            why.append("preferred category")
        bd = ScoreBreakdown(
            need_ingredient=round(need_score, 2),
            profile_goal=round(prof_score, 2),
            routine_category=routine_score,
            preference=pref_score,
        )
        total = round(bd.need_ingredient + bd.profile_goal + bd.routine_category + bd.preference, 2)
        if total == 0:
            excluded.append(ExcludedProduct(product_id=prod.id, reasons=["no_relevant_need"]))
            continue
        ranked.append(
            RankedProduct(
                product_id=prod.id,
                brand=prod.brand,
                name=prod.name,
                routine_slot=prod.routine_slot,
                total_score=total,
                breakdown=bd,
                reasons=why,
            )
        )

    ranked.sort(key=lambda r: (-r.total_score, r.product_id))  # deterministic
    return RecommendationResponse(
        rules_version=RULES_VERSION,
        mode=req.mode,
        needs=needs,
        missing_information=missing,
        morning=[r for r in ranked if r.routine_slot in ("am", "both")],
        evening=[r for r in ranked if r.routine_slot in ("pm", "both")],
        excluded=excluded,
    )
