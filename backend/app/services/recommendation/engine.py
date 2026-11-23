"""Rule-based recommendation engine (rules v0.1.0).

Pipeline (TÜBİTAK 2209-B proposal):
 1. derive care needs from findings + goals
 2. map needs -> ingredient/category rules
 3. hard filters: unverified, unavailable, allergy/avoid/past-reaction INCI, sensitivity warnings, budget
 4. score survivors: need+ingredient 50, profile/goal 25, routine/category 15, preference 10
 5. explain every score component
 6. build ordered AM/PM routines (routine.py)

Rule tables and weights live in rules.py (PROVISIONAL). The LLM never runs here: it only
explains this engine's validated output afterwards (services/llm/explain.py).
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
from app.services.recommendation.routine import build_routine
from app.services.recommendation.rules import (
    NEED_CATEGORIES,
    NEED_INGREDIENTS,
    RULES_VERSION,
    SENSITIVE_WARNING_TAGS,
    W_NEED,
    W_PREF,
    W_PROFILE,
    W_ROUTINE,
)


def _norm(s: str) -> str:
    return s.strip().lower()


def derive_needs(req: RecommendationRequest) -> list[str]:
    needs: list[str] = []
    f: FindingsIn | None = req.findings if req.mode != "profile_only" else None
    if f and f.triage_action not in (None, "proceed"):
        f = None  # abstention: low-confidence / out-of-scope findings never drive needs
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
    if req.findings and req.mode != "profile_only" and req.findings.triage_action not in (None, "proceed"):
        missing.append(f"image_findings_withheld:{req.findings.triage_action}")

    blocked = (
        {
            _norm(x)
            for x in (profile.allergies or []) + profile.avoid_ingredients + profile.past_reaction_ingredients
        }
        if profile
        else set()
    )
    ranked: list[RankedProduct] = []
    excluded: list[ExcludedProduct] = []

    for prod in catalog:
        reasons: list[str] = []
        if prod.verification_status != "verified":
            reasons.append("product_not_verified")
        if prod.available is False:
            reasons.append("not_available")
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
        key = {i.strip().upper() for i in (prod.key_ingredients or prod.inci)}
        matched = []
        for n in needs:
            rule = NEED_INGREDIENTS.get(n, set())
            if n in prod.targets and (not rule or key & rule):
                matched.append(n)
        need_score = W_NEED * (len(matched) / len(needs)) if needs else 0.0
        if matched:
            why.append(f"addresses: {', '.join(matched)}")
        hits_ing = sorted(key & set().union(*(NEED_INGREDIENTS.get(n, set()) for n in matched)))
        if hits_ing:
            why.append(f"key ingredients: {', '.join(hits_ing)}")
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
    by_id = {p.id: p for p in catalog}
    am_steps, am_skip = build_routine("am", ranked, by_id)
    pm_steps, pm_skip = build_routine("pm", ranked, by_id)
    return RecommendationResponse(
        rules_version=RULES_VERSION,
        mode=req.mode,
        needs=needs,
        missing_information=missing,
        morning=[r for r in ranked if r.routine_slot in ("am", "both")],
        evening=[r for r in ranked if r.routine_slot in ("pm", "both")],
        morning_routine=am_steps,
        evening_routine=pm_steps,
        skipped_for_compatibility=am_skip + pm_skip,
        excluded=excluded,
        pending_rules=[n for n in needs if not NEED_INGREDIENTS.get(n)],
    )
