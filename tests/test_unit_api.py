from unittest.mock import MagicMock, patch

from orchestrator.audit_logger import AuditLogger

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


def test_admin_audit_events_contain_actor_action_and_timestamp():
    audit_logger = AuditLogger()

    audit_logger.log_admin_action(
        action="clear-cache",
        actor="admin@example.com",
    )
    audit_logger.log_admin_action(
        action="sync-to-database",
        actor="admin@example.com",
        details={"session_id": "session-123"},
    )

    events = audit_logger.get_recent_events(limit=2)

    assert len(events) == 2

    clear_cache_event = events[1]
    sync_event = events[0]

    assert clear_cache_event["actor"] == "admin@example.com"
    assert clear_cache_event["target"] == "clear-cache"
    assert clear_cache_event["event_type"] == "ADMIN_ACTION"
    assert clear_cache_event["timestamp"]

    assert sync_event["actor"] == "admin@example.com"
    assert sync_event["target"] == "sync-to-database"
    assert sync_event["event_type"] == "ADMIN_ACTION"
    assert sync_event["timestamp"]


def test_sync_to_database_audit_uses_authenticated_actor():
    from orchestrator.security import get_current_user

    app.dependency_overrides[get_current_user] = lambda: {
        "role": "admin",
        "user_id": "admin-123",
        "email": "admin@example.com",
    }

    try:
        with patch(
            "orchestrator.main.audit_logger.log_admin_action"
        ) as mock_log_admin_action:
            with patch(
                "orchestrator.main.state_sync.get_active_sessions",
                return_value=[],
            ):
                response = client.post("/sync-to-database")

        assert response.status_code == 200

        mock_log_admin_action.assert_called_once()

        call = mock_log_admin_action.call_args.kwargs

        assert call["action"] == "sync-to-database"
        assert call["actor"] == "admin@example.com"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


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
