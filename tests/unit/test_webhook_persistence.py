"""
Phase 2 — Webhook Persistence & Database Idempotency Unit & Integration Tests
"""

import hmac
import hashlib
import json
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func
from sqlalchemy.pool import NullPool

from backend.app.main import app
from backend.app.db.database import Base, get_db
from backend.app.db.models import WebhookEvent
from backend.app.core.config import get_settings

settings = get_settings()
TEST_SECRET = settings.RAZORPAY_WEBHOOK_SECRET or "OLW4y-M67FEULeYEfNYN5S0wDsD8XxFP0m-Lda-WpZQ"


def compute_signature(payload_bytes: bytes, secret: str = TEST_SECRET) -> str:
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()


@pytest_asyncio.fixture
async def async_client_with_db():
    engine = create_async_engine(settings.async_database_url, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, async_session_factory

    app.dependency_overrides.clear()
    await engine.dispose()


# TEST 1: Valid payment.failed webhook is persisted
@pytest.mark.asyncio
async def test_valid_payment_failed_webhook_persisted(async_client_with_db):
    client, session_factory = async_client_with_db
    evt_id = f"evt_failed_{uuid.uuid4().hex[:8]}"
    payload = {
        "event_id": evt_id,
        "event": "payment.failed",
        "account_id": "acc_PZ0001",
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_failed_{uuid.uuid4().hex[:8]}",
                    "amount": 49900,
                    "currency": "INR",
                    "status": "failed",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_reason": "insufficient_funds"
                }
            }
        }
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_signature(payload_bytes)

    response = await client.post(
        "/webhooks/razorpay",
        content=payload_bytes,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["event"] == "payment.failed"
    assert response.json()["duplicate"] is False

    async with session_factory() as session:
        result = await session.execute(select(WebhookEvent).where(WebhookEvent.event_id == evt_id))
        event = result.scalar_one_or_none()
        assert event is not None
        assert event.event_type == "payment.failed"


# TEST 2: Valid payment.captured webhook is persisted
@pytest.mark.asyncio
async def test_valid_payment_captured_webhook_persisted(async_client_with_db):
    client, session_factory = async_client_with_db
    evt_id = f"evt_captured_{uuid.uuid4().hex[:8]}"
    payload = {
        "event_id": evt_id,
        "event": "payment.captured",
        "account_id": "acc_PZ0001",
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_captured_{uuid.uuid4().hex[:8]}",
                    "amount": 299900,
                    "currency": "INR",
                    "status": "captured"
                }
            }
        }
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_signature(payload_bytes)

    response = await client.post(
        "/webhooks/razorpay",
        content=payload_bytes,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    )
    assert response.status_code == 200
    assert response.json()["event"] == "payment.captured"
    assert response.json()["duplicate"] is False

    async with session_factory() as session:
        result = await session.execute(select(WebhookEvent).where(WebhookEvent.event_id == evt_id))
        event = result.scalar_one_or_none()
        assert event is not None
        assert event.event_type == "payment.captured"


# TEST 3 & 4: Duplicate event_id does not create a second record & returns HTTP 200 with duplicate=true
@pytest.mark.asyncio
async def test_duplicate_event_id_handling(async_client_with_db):
    client, session_factory = async_client_with_db
    evt_id = f"evt_dup_{uuid.uuid4().hex[:8]}"
    payload = {
        "event_id": evt_id,
        "event": "payment.failed",
        "payload": {"payment": {"entity": {"id": f"pay_dup_{uuid.uuid4().hex[:8]}", "amount": 10000}}}
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_signature(payload_bytes)

    # First delivery
    res1 = await client.post(
        "/webhooks/razorpay",
        content=payload_bytes,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    )
    assert res1.status_code == 200
    assert res1.json()["duplicate"] is False

    # Second (duplicate) delivery
    res2 = await client.post(
        "/webhooks/razorpay",
        content=payload_bytes,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    )
    assert res2.status_code == 200
    assert res2.json()["duplicate"] is True

    # Verify exactly ONE record exists in DB
    async with session_factory() as session:
        count_res = await session.execute(
            select(func.count(WebhookEvent.id)).where(WebhookEvent.event_id == evt_id)
        )
        assert count_res.scalar() == 1


# TEST 5: Invalid signature does not create a database record
@pytest.mark.asyncio
async def test_invalid_signature_does_not_persist(async_client_with_db):
    client, session_factory = async_client_with_db
    evt_id = f"evt_invalid_{uuid.uuid4().hex[:8]}"
    payload = {"event_id": evt_id, "event": "payment.failed"}
    payload_bytes = json.dumps(payload).encode("utf-8")

    response = await client.post(
        "/webhooks/razorpay",
        content=payload_bytes,
        headers={"X-Razorpay-Signature": "invalid_sig_hash_999", "Content-Type": "application/json"}
    )
    assert response.status_code == 401

    async with session_factory() as session:
        result = await session.execute(select(WebhookEvent).where(WebhookEvent.event_id == evt_id))
        assert result.scalar_one_or_none() is None


# TEST 6: Missing signature does not create a database record
@pytest.mark.asyncio
async def test_missing_signature_does_not_persist(async_client_with_db):
    client, session_factory = async_client_with_db
    evt_id = f"evt_missing_{uuid.uuid4().hex[:8]}"
    payload = {"event_id": evt_id, "event": "payment.failed"}
    payload_bytes = json.dumps(payload).encode("utf-8")

    response = await client.post(
        "/webhooks/razorpay",
        content=payload_bytes,
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400

    async with session_factory() as session:
        result = await session.execute(select(WebhookEvent).where(WebhookEvent.event_id == evt_id))
        assert result.scalar_one_or_none() is None


# TEST 7: Malformed JSON does not create a database record
@pytest.mark.asyncio
async def test_malformed_json_does_not_persist(async_client_with_db):
    client, session_factory = async_client_with_db
    malformed_bytes = b"{\"event\": \"payment.failed\", invalid json..."
    sig = compute_signature(malformed_bytes)

    response = await client.post(
        "/webhooks/razorpay",
        content=malformed_bytes,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    )
    assert response.status_code == 400


# TEST 8: Optional missing fields do not crash processing
@pytest.mark.asyncio
async def test_optional_missing_fields_handled_safely(async_client_with_db):
    client, session_factory = async_client_with_db
    minimal_payload = {
        "event": "invoice.paid"
        # Missing event_id, account_id, created_at, payload container
    }
    payload_bytes = json.dumps(minimal_payload).encode("utf-8")
    sig = compute_signature(payload_bytes)

    response = await client.post(
        "/webhooks/razorpay",
        content=payload_bytes,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    )
    assert response.status_code == 200
    assert response.json()["event"] == "invoice.paid"
    assert response.json()["duplicate"] is False


# TEST 9: Database rollback handling
@pytest.mark.asyncio
async def test_database_rollback_on_session_error(async_client_with_db):
    client, session_factory = async_client_with_db
    # Payload missing event field -> raises HTTP 400 before DB commit
    payload = {"event_id": "evt_no_event_name"}
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_signature(payload_bytes)

    response = await client.post(
        "/webhooks/razorpay",
        content=payload_bytes,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    )
    assert response.status_code == 400
