"""Engine tests use SYNTHETIC fixtures (FIXTURE-*), not real product records."""

from app.schemas.recommendation import FindingsIn, ProductIn, ProfileIn, RecommendationRequest
from app.services.recommendation import recommend


def _p(pid, **kw):
    base = dict(
        id=pid,
        brand="FIXTURE",
        name=pid,
        category="serum",
        routine_slot="pm",
        inci=["AQUA"],
        targets=["acne_care"],
        verification_status="verified",
    )
    base.update(kw)
    return ProductIn(**base)


CATALOG = [
    _p("FIXTURE-A"),
    _p("FIXTURE-ALLERGEN", inci=["AQUA", "PARFUM"]),
    _p("FIXTURE-UNVERIFIED", verification_status="pending"),
    _p("FIXTURE-PRICEY", price=999),
    _p("FIXTURE-SPF", category="sunscreen", routine_slot="am", targets=["sun_protection"]),
]


def _req(mode="multimodal"):
    return RecommendationRequest(
        mode=mode,
        profile=ProfileIn(skin_type="oily", sensitivity="none", allergies=["parfum"], budget_max=50),
        findings=FindingsIn(acne_severity="moderate"),
    )


def test_hard_filters_exclude_before_scoring():
    res = recommend(_req(), CATALOG)
    ex = {e.product_id: e.reasons for e in res.excluded}
    assert "FIXTURE-ALLERGEN" in ex and ex["FIXTURE-ALLERGEN"][0].startswith("contains_blocked")
    assert ex["FIXTURE-UNVERIFIED"] == ["product_not_verified"]
    assert ex["FIXTURE-PRICEY"] == ["over_budget"]
    ranked = {r.product_id for r in res.morning + res.evening}
    assert ranked == {"FIXTURE-A", "FIXTURE-SPF"}


def test_scores_within_weight_bounds_and_deterministic():
    a = recommend(_req(), CATALOG)
    b = recommend(_req(), CATALOG)
    assert a == b
    for r in a.morning + a.evening:
        assert 0 < r.total_score <= 100


def test_image_only_does_not_use_profile_constraints():
    res = recommend(_req("image_only"), CATALOG)
    assert "allergies" in res.missing_information
    assert "FIXTURE-ALLERGEN" not in {e.product_id for e in res.excluded}


def test_profile_only_ignores_findings():
    res = recommend(_req("profile_only"), CATALOG)
    assert "acne_care" not in res.needs


def test_past_reactions_and_unavailable_are_hard_filtered():
    cat = [
        _p("FIXTURE-REACT", inci=["AQUA", "FIXTURE-X"]),
        _p("FIXTURE-GONE", available=False),
        _p("FIXTURE-A"),
    ]
    req = _req()
    req.profile.past_reaction_ingredients = ["fixture-x"]
    ex = {e.product_id: e.reasons for e in recommend(req, cat).excluded}
    assert ex["FIXTURE-REACT"][0].startswith("contains_blocked_ingredient")
    assert ex["FIXTURE-GONE"] == ["not_available"]


def test_low_confidence_findings_are_withheld():
    req = _req()
    req.findings.triage_action = "limited"
    res = recommend(req, CATALOG)
    assert "acne_care" not in res.needs
    assert "image_findings_withheld:limited" in res.missing_information


def test_routines_ordered_and_sunscreen_morning_only():
    cat = CATALOG + [
        _p("FIXTURE-CLEANSER", category="cleanser", routine_slot="both"),
        _p("FIXTURE-SPF-PM", category="sunscreen", routine_slot="both", targets=["sun_protection"]),
    ]
    res = recommend(_req(), cat)
    am = [s.category for s in res.morning_routine]
    pm = [s.category for s in res.evening_routine]
    assert am[0] == "cleanser" and am[-1] == "sunscreen"
    assert "sunscreen" not in pm and pm == ["cleanser", "serum"]
    assert [s.step for s in res.morning_routine] == list(range(1, len(am) + 1))
    assert set(res.pending_rules) == set(res.needs)  # no expert ingredient rules yet


def test_incompatible_pair_is_skipped():
    from app.services.recommendation import build_routine

    cat = [
        _p("FIXTURE-P1", category="serum", inci=["FIXTURE-ACTIVE-1"]),
        _p("FIXTURE-P2", category="moisturizer", inci=["FIXTURE-ACTIVE-2"], targets=["acne_care"]),
    ]
    res = recommend(_req(), cat)
    ranked = res.evening
    steps, skipped = build_routine(
        "pm", ranked, {p.id: p for p in cat}, pairs=[("FIXTURE-ACTIVE-1", "FIXTURE-ACTIVE-2")]
    )
    assert len(steps) == 1 and skipped[0].reason.startswith("incompatible_with")
