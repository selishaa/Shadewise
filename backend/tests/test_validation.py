"""API input validation tests — no live LLM calls."""


def test_analyze_rejects_empty_brand(client, sample_request_payload):
    sample_request_payload["brand"] = ""
    response = client.post("/api/analyze-shade", json=sample_request_payload)
    assert response.status_code == 422


def test_analyze_rejects_oversized_description(client, sample_request_payload):
    sample_request_payload["description"] = "x" * 501
    response = client.post("/api/analyze-shade", json=sample_request_payload)
    assert response.status_code == 422


def test_analyze_rejects_invalid_depth_feedback(client, sample_request_payload):
    sample_request_payload["depth_feedback"] = "perfect_match"
    response = client.post("/api/analyze-shade", json=sample_request_payload)
    assert response.status_code == 422


def test_analyze_rejects_invalid_undertone_issue(client, sample_request_payload):
    sample_request_payload["undertone_issues"] = ["too_sparkly"]
    response = client.post("/api/analyze-shade", json=sample_request_payload)
    assert response.status_code == 422


def test_analyze_missing_key_returns_503(client, sample_request_payload):
    """Without OPENAI_API_KEY, the endpoint should fail gracefully."""
    response = client.post("/api/analyze-shade", json=sample_request_payload)
    assert response.status_code == 503
    assert "API key" in response.json()["detail"]
