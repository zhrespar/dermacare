"""Auth, profile, stored analyses, catalog import and stored recommendations on an in-memory DB.

Catalog rows are SYNTHETIC FIXTURES (example.invalid), not real products.
"""

import csv

import app.models  # noqa: F401
import pytest
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import LLMCallLog
from app.services.catalog import import_csv, validate_row
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PNG = b"\x89PNG" + b"\x00" * 2048


@pytest.fixture
def db_client():
    eng = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    Session = sessionmaker(bind=eng, expire_on_commit=False)

    def _db():
        with Session() as s:
            yield s

    app.dependency_overrides[get_db] = _db
    yield TestClient(app), Session
    app.dependency_overrides.clear()


def _register(c, email="fixture@example.com"):
    r = c.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "long-enough-pw", "consent_version": "2026-11"},
    )
    assert r.status_code == 201
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


ROW = {
    "brand": "FIXTURE", "manufacturer": "FIXTURE Inc", "name": "Fixture Serum", "category": "serum",
    "routine_slot": "pm", "inci_full": "AQUA;1,2-HEXANEDIOL;FIXTURE-ACTIVE",
    "key_ingredients": "FIXTURE-ACTIVE",
    "targets": "acne_care", "suitable_skin_types": "oily", "warnings": "", "price": "10", "currency": "TRY",
    "available": "true", "source_url": "https://example.invalid/serum", "source_type": "manufacturer",
    "accessed_at": "2026-11-01", "verified_at": "2026-11-02", "verification_status": "verified",
}  # fmt: skip


def _csv(tmp_path, rows):
    p = tmp_path / "cat.csv"
    header = open("database/seed/product_template.csv").read().strip().split(",")
    with p.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in header})
    return p


def test_register_login_and_auth_errors(db_client):
    c, _ = db_client
    _register(c)
    assert (
        c.post(
            "/api/v1/auth/register",
            json={"email": "FIXTURE@example.com", "password": "long-enough-pw", "consent_version": "x"},
        ).status_code
        == 409
    )
    assert (
        c.post(
            "/api/v1/auth/login", json={"email": "fixture@example.com", "password": "wrong-password"}
        ).status_code
        == 401
    )
    assert (
        c.post(
            "/api/v1/auth/login", json={"email": "fixture@example.com", "password": "long-enough-pw"}
        ).status_code
        == 200
    )
    assert c.get("/api/v1/profile").status_code == 401
    assert c.get("/api/v1/profile", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_profile_roundtrip_keeps_unknown_as_null(db_client):
    c, _ = db_client
    h = _register(c)
    assert c.get("/api/v1/profile", headers=h).json()["allergies"] is None
    body = {
        "skin_type": "oily",
        "sensitivity": "high",
        "allergies": ["PARFUM"],
        "goals": ["acne_care"],
        "past_reaction_ingredients": ["X"],
    }
    assert c.put("/api/v1/profile", json=body, headers=h).status_code == 200
    got = c.get("/api/v1/profile", headers=h).json()
    assert (
        got["allergies"] == ["PARFUM"]
        and got["past_reaction_ingredients"] == ["X"]
        and got["budget_max"] is None
    )


def test_analysis_stored_only_when_logged_in(db_client):
    c, _ = db_client
    c.post("/api/v1/analyses", files={"image": ("f.png", PNG, "image/png")})
    h = _register(c)
    r = c.post("/api/v1/analyses", files={"image": ("f.png", PNG, "image/png")}, headers=h)
    hist = c.get("/api/v1/analyses", headers=h).json()
    assert len(hist) == 1 and hist[0]["id"] == r.json()["id"] and hist[0]["is_mock"] is True


def test_catalog_validation_rules():
    assert validate_row(ROW) == []
    assert "not_verified" in validate_row({**ROW, "verification_status": "pending"})
    assert "open_beauty_facts_is_discovery_only" in validate_row(
        {**ROW, "source_url": "https://world.openbeautyfacts.org/p/1"}
    )
    assert "key_ingredient_not_in_inci" in validate_row({**ROW, "key_ingredients": "NOPE"})
    assert "missing:source_url" in validate_row({**ROW, "source_url": ""})


def test_import_and_stored_recommendation_end_to_end(db_client, tmp_path):
    c, Session = db_client
    path = _csv(tmp_path, [ROW, {**ROW, "name": "Bad", "verification_status": "pending"}])
    with Session() as db:
        rep = import_csv(db, path, "FIXTURE-v1", freeze=True)
        with pytest.raises(ValueError):
            import_csv(db, path, "FIXTURE-v1")
    assert rep.imported == 1 and rep.rejected[0][2] == ["not_verified"]

    h = _register(c)
    c.put(
        "/api/v1/profile",
        json={"skin_type": "oily", "sensitivity": "none", "allergies": [], "goals": ["acne_care"]},
        headers=h,
    )
    res = c.post("/api/v1/recommendations", json={}, headers=h).json()
    assert res["catalog_version"] == "FIXTURE-v1" and res["recommendation_id"]
    assert [s["category"] for s in res["evening_routine"]] == ["serum"]

    c.put("/api/v1/profile", json={"allergies": ["1,2-hexanediol"], "goals": ["acne_care"]}, headers=h)
    res = c.post("/api/v1/recommendations", json={}, headers=h).json()
    assert res["evening_routine"] == [] and res["excluded"][0]["reasons"][0].startswith("contains_blocked")


def test_delete_me_purges_everything(db_client, tmp_path):
    c, Session = db_client
    with Session() as db:
        import_csv(db, _csv(tmp_path, [ROW]), "FIXTURE-v2")
    h = _register(c)
    c.put("/api/v1/profile", json={"goals": ["acne_care"], "allergies": []}, headers=h)
    c.post("/api/v1/analyses", files={"image": ("f.png", PNG, "image/png")}, headers=h)
    c.post("/api/v1/recommendations", json={}, headers=h)
    assert c.delete("/api/v1/me", headers=h).status_code == 204
    assert c.get("/api/v1/profile", headers=h).status_code == 401
    with Session() as db:
        from app.models import Analysis, Recommendation, SkinProfile, User

        for m in (User, SkinProfile, Analysis, Recommendation):
            assert db.scalars(select(m)).first() is None


def test_llm_attempts_are_logged_without_prompt(db_client):
    from app.api.routes.explanations import record_call
    from app.schemas.explanation import ExplanationMetrics, ExplanationResponse

    _, Session = db_client
    e = ExplanationResponse(
        mode="rule_template",
        text="t",
        citations=[],
        provider="fake",
        model="m",
        rules_version="r",
        fallback_reason="guard_rejected",
        metrics=ExplanationMetrics(latency_ms=5),
        disclaimer="d",
    )
    with Session() as db:
        record_call(db, e)
        row = db.scalars(select(LLMCallLog)).one()
    assert row.provider == "fake" and row.latency_ms == 5 and not hasattr(row, "prompt")
