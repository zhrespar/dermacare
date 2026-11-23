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
