import time
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_security_headers_present():
    """Verify OWASP recommended security headers on all responses."""
    response = client.get("/api/status")
    assert response.status_code == 200
    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_payload_size_limit():
    """Verify requests with excessive body size are rejected with 413."""
    oversized_headers = {"content-length": str(5 * 1024 * 1024)}  # 5 MB
    response = client.post("/predict", headers=oversized_headers, json={"symptoms": ["itching"]})
    assert response.status_code == 413
    assert "Payload Too Large" in response.json()["error"]


def test_rate_limiter_throttling():
    """Verify rate limiter blocks excessive requests with HTTP 429."""
    # Send rapid login requests to trigger rate limit
    limited = False
    for _ in range(35):
        resp = client.post(
            "/login",
            json={"email": "spam_test@test.com", "password": "WrongPassword!"},
            headers={"x-forwarded-for": "198.51.100.42"}
        )
        if resp.status_code == 429:
            limited = True
            assert "Retry-After" in resp.headers
            assert "Rate limit exceeded" in resp.json()["error"]
            break

    assert limited, "Rate limiter should have triggered 429 on spam attempts"


def test_heavy_traffic_concurrent_load():
    """Simulate heavy traffic with 50 concurrent requests."""
    def make_request(i):
        start = time.time()
        resp = client.get("/symptoms", headers={"x-forwarded-for": f"10.0.{i % 20}.{i}"})
        duration = time.time() - start
        return resp.status_code, duration

    total_requests = 50
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(make_request, range(total_requests)))

    status_codes = [r[0] for r in results]
    durations = [r[1] for r in results]

    # All requests must succeed (200 OK)
    assert all(code == 200 for code in status_codes), f"Some requests failed: {status_codes}"

    avg_time = sum(durations) / len(durations)
    max_time = max(durations)

    # Average response time should be well under 100ms
    assert avg_time < 0.25, f"Average response time too high: {avg_time:.3f}s"
    assert max_time < 1.0, f"Max response time spike: {max_time:.3f}s"
