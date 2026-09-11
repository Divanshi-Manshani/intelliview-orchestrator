"""E3 end-to-end verification for rate limiting on login and admin endpoints."""

import os


import httpx
import pytest


@pytest.mark.e2e
def test_login_rate_limit_is_enforced():
    """Login requests should be rate limited by the running API stack."""
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    api_token = os.getenv("API_TOKEN", "ci-test-token")
    client_ip = "198.51.100.30"

    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        body = {"api_token": api_token}
        headers = {"X-Forwarded-For": client_ip}

        responses = [
            client.post("/login", json=body, headers=headers),
            client.post("/login", json=body, headers=headers),
            client.post("/login", json=body, headers=headers),
        ]

    assert responses[0].status_code == 200
    assert responses[1].status_code == 200
    assert responses[2].status_code == 429
    assert responses[2].json()["detail"] == "Rate limit exceeded"


@pytest.mark.e2e
def test_admin_rate_limit_is_enforced():
    """Admin requests should also be rate limited by the running API stack."""
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    api_token = os.getenv("API_TOKEN", "ci-test-token")
    client_ip = "198.51.100.31"

    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        headers = {
            "X-API-Token": api_token,
            "X-Forwarded-For": client_ip,
        }

        responses = [
            client.post(
                "/retry-session/e3-rate-limit-test-automated",
                headers=headers,
            ),
            client.post(
                "/retry-session/e3-rate-limit-test-automated",
                headers=headers,
            ),
            client.post(
                "/retry-session/e3-rate-limit-test-automated",
                headers=headers,
            ),
        ]

    assert responses[0].status_code != 429
    assert responses[1].status_code != 429
    assert responses[2].status_code == 429
    assert responses[2].json()["detail"] == "Rate limit exceeded"
