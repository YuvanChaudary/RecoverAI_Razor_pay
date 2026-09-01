"""
Phase 13 E2E Integration Observability & Operational Metrics Tests
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.metrics import metrics


# TEST 1 — END-TO-END CORRELATION ID PROPAGATION & RESPONSE HEADERS
@pytest.mark.asyncio
async def test_e2e_correlation_id_propagation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        req_id = "req_e2e_obs_test_9999"
        res = await ac.get("/ready", headers={"X-Request-ID": req_id})
        assert res.status_code in (200, 503)
        assert res.headers.get("X-Request-ID") == req_id


# TEST 2 — OPERATIONAL METRICS ENDPOINT RESPONSE
@pytest.mark.asyncio
async def test_e2e_metrics_endpoint_response():
    metrics.reset()
    metrics.increment("webhooks_received", 3)
    metrics.increment("state_transitions_succeeded", 10)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/metrics")
        assert res.status_code == 200
        data = res.json()
        assert "metrics" in data
        assert data["metrics"]["webhooks_received"] == 3
        assert data["metrics"]["state_transitions_succeeded"] == 10
