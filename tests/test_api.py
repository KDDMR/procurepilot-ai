from fastapi.testclient import TestClient


def test_health_exposes_provider(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "ai_provider": "mock"}


def test_dashboard_is_served(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "ProcurePilot AI" in response.text


def test_low_risk_assessment_is_persisted(
    client: TestClient,
    low_risk_payload: dict[str, object],
) -> None:
    created = client.post("/api/v1/assessments", json=low_risk_payload)

    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "auto_approved"
    assert body["risk_level"] == "low"
    assert body["model_mode"] == "deterministic-mock"
    assert len(body["agent_trace"]) == 4
    assert len(body["policy_evidence"]) == 4

    fetched = client.get(f"/api/v1/assessments/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]

    listed = client.get("/api/v1/assessments?limit=10")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [body["id"]]


def test_high_risk_assessment_requires_human_decision(
    client: TestClient,
    high_risk_payload: dict[str, object],
) -> None:
    created = client.post("/api/v1/assessments", json=high_risk_payload)
    body = created.json()

    assert body["risk_level"] == "high"
    assert body["status"] == "pending_review"
    assert "executive-board" in body["approval_route"]
    assert "security-and-data-protection" in body["approval_route"]

    reviewed = client.post(
        f"/api/v1/assessments/{body['id']}/decision",
        json={
            "approved": False,
            "reviewer": "Maria Reviewer",
            "note": "Supplier assessment is incomplete.",
        },
    )

    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "rejected"
    assert reviewed.json()["reviewer"] == "Maria Reviewer"

    duplicate = client.post(
        f"/api/v1/assessments/{body['id']}/decision",
        json={
            "approved": True,
            "reviewer": "Maria Reviewer",
            "note": "Trying to change the final decision.",
        },
    )
    assert duplicate.status_code == 409


def test_api_validation_rejects_invalid_request(
    client: TestClient,
    low_risk_payload: dict[str, object],
) -> None:
    low_risk_payload["amount_eur"] = -1
    response = client.post("/api/v1/assessments", json=low_risk_payload)

    assert response.status_code == 422


def test_missing_assessment_returns_404(client: TestClient) -> None:
    missing = "00000000-0000-0000-0000-000000000000"

    assert client.get(f"/api/v1/assessments/{missing}").status_code == 404
    response = client.post(
        f"/api/v1/assessments/{missing}/decision",
        json={"approved": True, "reviewer": "Jane Doe", "note": "Reviewed and approved."},
    )
    assert response.status_code == 404


def test_metrics_endpoint(client: TestClient) -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "procurepilot_assessments_total" in response.text
