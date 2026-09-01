"""
Phase 1 & 2 Integration Tests: Real Razorpay Webhook Ingestion & HMAC Verification.
"""

import hmac
import hashlib
import json
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import get_settings

client = TestClient(app)
settings = get_settings()
WEBHOOK_SECRET = settings.RAZORPAY_WEBHOOK_SECRET or "OLW4y-M67FEULeYEfNYN5S0wDsD8XxFP0m-Lda-WpZQ"


def compute_signature(payload_bytes: bytes, secret: str = WEBHOOK_SECRET) -> str:
    """Independently calculates HMAC-SHA256 signature for test verification."""
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()


def test_health_endpoint():
    """Verify /health returns HTTP 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": settings.APP_NAME,
    }


def test_valid_signature_returns_200():
    """TEST 1: Valid Razorpay signature -> HTTP 200."""
    payload = {
        "event_id": f"evt_wh_test_{uuid.uuid4().hex[:8]}",
        "entity": "event",
        "account_id": "acc_test_12345",
        "event": "payment.failed",
        "created_at": 1724180400,
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_{uuid.uuid4().hex[:8]}",
                    "amount": 299900,
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

    response = client.post(
        "/webhooks/razorpay",
        content=payload_bytes,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["event"] == "payment.failed"


def test_invalid_signature_rejected():
    """TEST 2: Invalid signature -> rejected (HTTP 401)."""
    payload = {"event": "payment.failed"}
    payload_bytes = json.dumps(payload).encode("utf-8")
    invalid_sig = "a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e"

    response = client.post(
        "/webhooks/razorpay",
        content=payload_bytes,
        headers={"X-Razorpay-Signature": invalid_sig, "Content-Type": "application/json"}
    )

    assert response.status_code in (400, 401)
    assert "signature" in response.json()["detail"].lower()


def test_missing_signature_rejected():
    """TEST 3: Missing signature -> rejected (HTTP 400)."""
    payload = {"event": "payment.failed"}
    payload_bytes = json.dumps(payload).encode("utf-8")

    response = client.post(
        "/webhooks/razorpay",
        content=payload_bytes,
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 400
    assert "Missing X-Razorpay-Signature" in response.json()["detail"]


def test_malformed_json_rejected():
    """TEST 4: Malformed JSON -> rejected (HTTP 400)."""
    malformed_bytes = b"{"  # Invalid JSON
    sig = compute_signature(malformed_bytes)

    response = client.post(
        "/webhooks/razorpay",
        content=malformed_bytes,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    )

    assert response.status_code == 400
    assert "Malformed JSON" in response.json()["detail"]


def test_valid_payment_failed_payload_extracted():
    """TEST 5: Valid payment.failed payload -> event is correctly extracted."""
    payload = {
        "event_id": f"evt_wh_failed_{uuid.uuid4().hex[:8]}",
        "entity": "event",
        "account_id": "acc_PZ000000000001",
        "event": "payment.failed",
        "created_at": 1724180400,
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_{uuid.uuid4().hex[:8]}",
                    "amount": 299900,
                    "currency": "INR",
                    "status": "failed",
                    "order_id": "order_PZ177a8B9cD0eF",
                    "invoice_id": "inv_PZ166x1Y2z3A4B",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_reason": "insufficient_funds"
                }
            },
            "subscription": {
                "entity": {
                    "id": "sub_PZ100s1T2u3V4W"
                }
            }
        }
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_signature(payload_bytes)

    response = client.post(
        "/webhooks/razorpay",
        content=payload_bytes,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "accepted"
    assert res_data["event"] == "payment.failed"


def test_valid_payment_captured_payload_extracted():
    """TEST 6: Different valid event such as payment.captured -> event is correctly extracted."""
    payload = {
        "event_id": f"evt_wh_captured_{uuid.uuid4().hex[:8]}",
        "entity": "event",
        "account_id": "acc_PZ000000000001",
        "event": "payment.captured",
        "created_at": 1724180450,
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_{uuid.uuid4().hex[:8]}",
                    "amount": 299900,
                    "currency": "INR",
                    "status": "captured"
                }
            }
        }
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_signature(payload_bytes)

    response = client.post(
        "/webhooks/razorpay",
        content=payload_bytes,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "accepted"
    assert res_data["event"] == "payment.captured"


def test_modified_payload_with_original_signature_rejected():
    """TEST 7: Modified payload with original signature -> rejected (HTTP 401)."""
    original_payload = {"event": "payment.failed", "amount": 1000}
    original_bytes = json.dumps(original_payload).encode("utf-8")
    original_sig = compute_signature(original_bytes)

    modified_payload = {"event": "payment.failed", "amount": 9999999}  # Tampered amount
    tampered_bytes = json.dumps(modified_payload).encode("utf-8")

    response = client.post(
        "/webhooks/razorpay",
        content=tampered_bytes,
        headers={"X-Razorpay-Signature": original_sig, "Content-Type": "application/json"}
    )

    assert response.status_code in (400, 401)
    assert "signature" in response.json()["detail"].lower()
