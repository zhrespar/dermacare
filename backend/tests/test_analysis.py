import io

# Synthetic bytes with a JPEG header — not a face, not a real photo.
FAKE_JPEG = b"\xff\xd8\xff" + b"\x00" * 4096


def test_mock_analysis_is_flagged(client):
    r = client.post("/api/v1/analyses", files={"image": ("x.jpg", io.BytesIO(FAKE_JPEG), "image/jpeg")})
    assert r.status_code == 200
    body = r.json()
    assert body["is_mock"] is True
    assert body["quality"]["status"] == "accepted"
    assert set(body["model_versions"].values()) == {"mock-0"}
    assert body["acne"]["severity"] in {"mild", "moderate", "severe", "very_severe"}


def test_rejects_non_image(client):
    r = client.post("/api/v1/analyses", files={"image": ("x.txt", io.BytesIO(b"hello"), "text/plain")})
    assert r.status_code == 200
    body = r.json()
    assert body["quality"]["status"] == "out_of_scope"
    assert body["triage"]["action"] == "retake"
    assert body["acne"] is None
