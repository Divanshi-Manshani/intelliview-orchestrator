from unittest.mock import MagicMock, patch

with (
    patch("redis.from_url", return_value=MagicMock()),
    patch("sqlalchemy.create_engine", return_value=MagicMock()),
):
    from orchestrator.main import app


from fastapi.testclient import TestClient

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert "timestamp" in data


@patch("orchestrator.main.scheduler.can_accept_task", return_value=True)
def test_start_interview_invalid_candidate_id(mock_capacity):
    response = client.post(
        "/start-interview",
        headers={"X-API-Token": "ci-test-token"},
        json={"candidate_id": "@@@###", "priority": "medium"},
    )

    assert response.status_code == 422


@patch("orchestrator.main.session_manager.get_session")
def test_session_status_not_found(mock_get_session):
    mock_get_session.return_value = None

    response = client.get("/session-status/fake-session-id")

    assert response.status_code == 404


def test_sync_to_database_without_token():
    response = client.post("/sync-to-database")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid or missing API token"


def test_sync_to_database_with_token():
    response = client.post(
        "/sync-to-database",
        headers={"X-API-Token": "ci-test-token"},
    )

    assert response.status_code == 200


def test_risk_config_returns_live_values(monkeypatch):
    monkeypatch.setenv("RISK_VIDEO_WEIGHT", "0.5")
    monkeypatch.setenv("RISK_AUDIO_WEIGHT", "0.25")
    monkeypatch.setenv("RISK_EVALUATION_WEIGHT", "0.25")

    monkeypatch.setenv("RISK_LOW_RISK_THRESHOLD", "0.2")
    monkeypatch.setenv("RISK_MEDIUM_RISK_THRESHOLD", "0.5")
    monkeypatch.setenv("RISK_HIGH_RISK_THRESHOLD", "0.75")

    response = client.get("/api/admin/risk-config")

    assert response.status_code == 200

    data = response.json()

    assert data["pipeline_weights"] == {
        "video": 0.5,
        "audio": 0.25,
        "evaluation": 0.25,
    }

    assert data["thresholds"] == {
        "low": 0.2,
        "medium": 0.5,
        "high": 0.75,
    }

    assert "multiple_persons" in data["video_factors"]
    assert "phone_detected" in data["video_factors"]
    assert "suspicious_head_movement" in data["video_factors"]
    assert "no_face_detected" in data["video_factors"]

    assert "background_voices" in data["audio_factors"]
    assert "suspicious_pattern" in data["audio_factors"]
    assert "no_transcription" in data["audio_factors"]

    assert "low_quality_answers" in data["evaluation_factors"]
    assert "low_accuracy" in data["evaluation_factors"]
    assert "poor_communication" in data["evaluation_factors"]
    assert "hallucination" in data["evaluation_factors"]


@patch("orchestrator.http_cache.invalidate")
@patch("orchestrator.main.scheduler.get_estimated_wait_time")
@patch("orchestrator.main.scheduler.schedule_task")
@patch("orchestrator.main.scheduler.can_accept_task")
@patch("orchestrator.main.session_manager.get_session")
@patch("orchestrator.main.session_manager.update_session_status")
@patch("orchestrator.main.session_manager.create_session")
def test_start_interview_valid(
    mock_create_session,
    mock_update_session_status,
    mock_get_session,
    mock_can_accept_task,
    mock_schedule_task,
    mock_get_estimated_wait_time,
    mock_invalidate,
):
    # `session_manager` and `scheduler` are shared instances injected into the
    # session router at startup, so their methods (not the module-level names
    # in orchestrator.main) must be patched for the mock to take effect.
    mock_create_session.return_value = "session-123"

    mock_update_session_status.return_value = None

    mock_get_session.return_value = {"created_at": "2026-07-16T10:00:00Z"}

    mock_can_accept_task.return_value = True

    mock_schedule_task.return_value = None

    mock_get_estimated_wait_time.return_value = 5

    mock_invalidate.return_value = None

    response = client.post(
        "/start-interview",
        headers={"X-API-Token": "ci-test-token"},
        json={
            "candidate_id": "candidate-123",
            "priority": "medium",
        },
    )

    assert response.status_code == 200
