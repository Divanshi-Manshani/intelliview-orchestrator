from unittest.mock import patch
from fastapi.testclient import TestClient

from orchestrator.main import app


def test_returns_503_when_no_workers_available():
    from config import API_TOKEN

    client = TestClient(app)
    with patch("orchestrator.main.scheduler") as mock_scheduler, \
         patch("orchestrator.main.session_manager") as mock_session_manager:
        mock_scheduler.can_accept_task.return_value = False
        mock_session_manager.create_session.return_value = "test-session-123"
        mock_session_manager.QUEUED = "QUEUED"
        mock_session_manager.update_session_status.return_value = None
        mock_session_manager.get_session.return_value = {"created_at": "2026-08-28T00:00:00"}
        
        response = client.post(
            "/start-interview",
            json={"candidate_id": "test123"},
            headers={"X-API-Token": API_TOKEN},
        )
    assert response.status_code == 503
    assert response.headers.get("Retry-After") == "5"
    body = response.json()
    assert body["error"] == "service_unavailable"


def test_capacity_check_exception_fails_safe_to_503():
    from config import API_TOKEN

    client = TestClient(app)
    with patch("orchestrator.main.scheduler") as mock_scheduler, \
         patch("orchestrator.main.session_manager") as mock_session_manager:
        mock_scheduler.can_accept_task.side_effect = RuntimeError("redis down")
        mock_session_manager.create_session.return_value = "test-session-456"
        mock_session_manager.QUEUED = "QUEUED"
        mock_session_manager.update_session_status.return_value = None
        mock_session_manager.get_session.return_value = {"created_at": "2026-08-28T00:00:00"}
        
        response = client.post(
            "/start-interview",
            json={"candidate_id": "test456"},
            headers={"X-API-Token": API_TOKEN},
        )
    assert response.status_code == 503
