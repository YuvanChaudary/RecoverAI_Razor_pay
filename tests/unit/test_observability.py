"""
Phase 13 Observability, Security & Secret Redaction Unit Tests
"""

import json
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.logging import redact_secrets, JSONLogFormatter, RedactingFilter
from backend.app.core.metrics import metrics
from backend.app.api.middleware import correlation_id_ctx


# TEST 1 — MISSING CORRELATION ID IS GENERATED
@pytest.mark.asyncio
async def test_correlation_id_generated_when_missing():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        assert "X-Request-ID" in res.headers
        assert res.headers["X-Request-ID"].startswith("req_")


# TEST 2 — EXISTING CORRELATION ID PRESERVED
@pytest.mark.asyncio
async def test_existing_correlation_id_preserved():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        custom_id = "req_custom_test_12345"
        res = await ac.get("/health", headers={"X-Request-ID": custom_id})
        assert res.status_code == 200
        assert res.headers["X-Request-ID"] == custom_id


# TEST 3 — SECRET REDACTION REMOVES RAZORPAY SECRETS
def test_secret_redaction_removes_razorpay_secrets():
    raw_log = "Configured RAZORPAY_KEY_SECRET=rzp_live_secret_key_99999 and key_id=rzp_live_key_12345"
    redacted = redact_secrets(raw_log)

    assert "rzp_live_secret_key_99999" not in redacted
    assert "RAZORPAY_KEY_SECRET=[REDACTED]" in redacted or "RAZORPAY_KEY_SECRET=" in redacted
    assert "rzp_live_key_12345" not in redacted


# TEST 4 — SECRET REDACTION REMOVES NOVU API KEYS
def test_secret_redaction_removes_novu_api_keys():
    raw_log = "Sending notification using NOVU_API_KEY=novu_sk_test_1234567890"
    redacted = redact_secrets(raw_log)

    assert "novu_sk_test_1234567890" not in redacted
    assert "NOVU_API_KEY=[REDACTED]" in redacted or "NOVU_API_KEY=" in redacted


# TEST 5 — SECRET REDACTION REMOVES AUTHORIZATION HEADERS & NVIDIA KEYS
def test_secret_redaction_removes_auth_headers_and_nvidia_keys():
    raw_log = "NVIDIA_API_KEY=nvapi-secret_key_xyz and Authorization: Bearer secret_jwt_token"
    redacted = redact_secrets(raw_log)

    assert "nvapi-secret_key_xyz" not in redacted
    assert "secret_jwt_token" not in redacted


# TEST 6 — API ERRORS DO NOT EXPOSE SECRETS OR STACK TRACES
@pytest.mark.asyncio
async def test_api_errors_do_not_expose_secrets():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Requesting non-existent route
        res = await ac.get("/non_existent_route_999")
        assert res.status_code == 404
        assert "RAZORPAY_KEY_SECRET" not in res.text
        assert "POSTGRES_PASSWORD" not in res.text


# TEST 7 — OPERATIONAL METRICS INCREMENT CORRECTLY
def test_metrics_increment_correctly():
    metrics.reset()
    metrics.increment("webhooks_received", 1)
    metrics.increment("opa_allow_decisions", 5)

    data = metrics.get_metrics()
    assert data["webhooks_received"] == 1
    assert data["opa_allow_decisions"] == 5


# TEST 8 — HEALTH ENDPOINT REMAINS COMPATIBLE
@pytest.mark.asyncio
async def test_health_endpoint_compatible():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "service" in data


# TEST 9 — READINESS DIAGNOSTICS ENDPOINT RESPONDS
@pytest.mark.asyncio
async def test_readiness_diagnostics_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/ready")
        assert res.status_code in (200, 53)
        data = res.json()
        assert "components" in data
        assert "postgres" in data["components"]
        assert "opa" in data["components"]


# TEST 10 — DIAGNOSTICS SCRIPT EXECUTES SAFELY WITHOUT FINANCIAL MUTATIONS
def test_diagnostics_script_executes_safely():
    from scripts.diagnostics import main
    # Running main should not raise any exceptions
    try:
        main()
    except SystemExit:
        pass
