"""
Phase 7 Unit & Adversarial Tests: Outbound Razorpay Actions & Novu Communications
"""

import pytest
import respx
from httpx import Response, HTTPStatusError
from backend.app.services.razorpay_service import RazorpayService
from backend.app.services.notification_service import NotificationService
from backend.app.workflows.activities import execute_recovery_action_activity


# TEST 1 — PAYMENT LINK PAYLOAD VERIFICATION
@pytest.mark.asyncio
@respx.mock
async def test_razorpay_payment_link_payload_and_idempotency():
    service = RazorpayService(key_id="rzp_test_mock", key_secret="mock_secret")
    idemp_key = "rec_idemp_evt100_1"
    customer = {"name": "Alice Developer", "email": "alice@example.com", "contact": "+919876543210"}

    mock_route = respx.post("https://api.razorpay.com/v1/payment_links").mock(
        return_value=Response(200, json={
            "id": "plink_test_999",
            "short_url": "https://rzp.io/i/test999",
            "status": "created"
        })
    )

    res = await service.create_payment_link(
        amount_paise=49900,
        customer=customer,
        description="RecoverAI Invoice Recovery",
        idempotency_key=idemp_key
    )

    assert mock_route.called
    req = mock_route.calls.last.request

    # Verify HTTP Method, URL & Headers
    assert req.method == "POST"
    assert req.url == "https://api.razorpay.com/v1/payment_links"
    assert req.headers["X-Razorpay-Comment"] == idemp_key
    assert req.headers["X-Razorpay-Idempotency-Key"] == idemp_key
    assert "Authorization" in req.headers
    assert "mock_secret" not in req.headers["Authorization"]  # Secret is base64 encoded, not plain text

    # Verify Body
    import json
    body = json.loads(req.content)
    assert body["amount"] == 49900
    assert body["currency"] == "INR"
    assert body["notes"]["idempotency_key"] == idemp_key
    assert body["customer"]["email"] == "alice@example.com"
    assert res["id"] == "plink_test_999"


# TEST 2 — RETRY OPERATION VERIFICATION & SAFE HANDLING
@pytest.mark.asyncio
@respx.mock
async def test_razorpay_retry_operation_invoice():
    service = RazorpayService(key_id="rzp_test_mock", key_secret="mock_secret")
    idemp_key = "rec_idemp_evt200_1"

    mock_route = respx.post("https://api.razorpay.com/v1/invoices/inv_123/retry").mock(
        return_value=Response(200, json={"status": "retry_scheduled", "invoice_id": "inv_123"})
    )

    res = await service.retry_payment(
        payment_id="pay_failed_123",
        idempotency_key=idemp_key,
        invoice_id="inv_123"
    )

    assert mock_route.called
    assert res["status"] == "retry_scheduled"

    # Verify unsupported standalone payment retry without invoice/subscription raises ValueError safely
    with pytest.raises(ValueError, match="requires an associated invoice_id or subscription_id"):
        await service.retry_payment(payment_id="pay_failed_123", idempotency_key=idemp_key)


# TEST 3 — HTTP 500/504 ADVERSARIAL FAILURE PROPAGATION
@pytest.mark.asyncio
@respx.mock
async def test_razorpay_http_500_propagates_exception():
    service = RazorpayService(key_id="rzp_test_mock", key_secret="mock_secret")
    idemp_key = "rec_idemp_evt500_1"

    respx.post("https://api.razorpay.com/v1/payment_links").mock(
        return_value=Response(500, json={"error": {"code": "SERVER_ERROR", "description": "Internal error"}})
    )

    # Asserts that HTTP 500 error raises HTTPStatusError (NOT swallowed!)
    with pytest.raises(HTTPStatusError) as exc_info:
        await service.create_payment_link(
            amount_paise=49900,
            customer={"name": "Bob"},
            description="Test",
            idempotency_key=idemp_key
        )
    assert exc_info.value.response.status_code == 500


# TEST 4 — IDEMPOTENCY KEY REUSED ON RETRY
@pytest.mark.asyncio
@respx.mock
async def test_idempotency_key_reused_on_retries():
    service = RazorpayService(key_id="rzp_test_mock", key_secret="mock_secret")
    same_idemp_key = "rec_idemp_same_key_999"

    mock_route = respx.post("https://api.razorpay.com/v1/payment_links").mock(
        return_value=Response(200, json={"id": "plink_retry_1"})
    )

    # Attempt 1
    await service.create_payment_link(10000, {"name": "Test"}, "Desc", same_idemp_key)
    # Attempt 2 (Simulated Temporal retry with same key)
    await service.create_payment_link(10000, {"name": "Test"}, "Desc", same_idemp_key)

    assert mock_route.call_count == 2
    # Verify BOTH requests used the EXACT SAME idempotency key
    req1 = mock_route.calls[0].request
    req2 = mock_route.calls[1].request
    assert req1.headers["X-Razorpay-Idempotency-Key"] == same_idemp_key
    assert req2.headers["X-Razorpay-Idempotency-Key"] == same_idemp_key


# TEST 5 — OPA DENIAL BLOCKS OUTBOUND EXECUTION
@pytest.mark.asyncio
@respx.mock
async def test_opa_denial_blocks_outbound_execution():
    rzp_route = respx.post("https://api.razorpay.com/v1/payment_links").mock(return_value=Response(200))
    novu_route = respx.post("https://api.novu.co/v1/events/trigger").mock(return_value=Response(200))

    denied_governance = {
        "allow": False,
        "violations": ["RULE-001: Exceeded maximum retry limit (5 >= 3)"]
    }
    proposal = {"recommended_action": "SEND_PAYMENT_LINK", "delay_hours": 0}

    res = await execute_recovery_action_activity(
        case_id="case_denied_01",
        payment_id="pay_denied_01",
        amount_paise=49900,
        proposal_dict=proposal,
        governance_decision=denied_governance,
        idempotency_key="rec_idemp_denied_1"
    )

    assert res["status"] == "DENIED_BY_OPA"
    assert res["executed"] is False

    # Assert ZERO outbound HTTP calls were executed!
    assert not rzp_route.called
    assert not novu_route.called


# TEST 6 — HIGH AI CONFIDENCE CANNOT BYPASS OPA
@pytest.mark.asyncio
@respx.mock
async def test_high_ai_confidence_cannot_bypass_opa_denial():
    rzp_route = respx.post("https://api.razorpay.com/v1/payment_links").mock(return_value=Response(200))

    denied_governance = {
        "allow": False,
        "violations": ["RULE-003: Terminal decline prohibited"]
    }
    # High AI confidence (0.99)
    proposal = {
        "recommended_action": "RETRY_SCHEDULED",
        "confidence": 0.99,
        "reasoning_summary": "Extremely confident proposal"
    }

    res = await execute_recovery_action_activity(
        case_id="case_bypass_01",
        payment_id="pay_bypass_01",
        amount_paise=100000,
        proposal_dict=proposal,
        governance_decision=denied_governance,
        idempotency_key="rec_idemp_bypass_1"
    )

    assert res["status"] == "DENIED_BY_OPA"
    assert res["executed"] is False
    assert not rzp_route.called


# TEST 7 — NOVU MISSING KEY FALLBACK
@pytest.mark.asyncio
async def test_novu_missing_key_safe_fallback():
    # Instantiates NotificationService with empty/mock API key
    noti_svc = NotificationService(api_key="mock_novu_key")

    res = await noti_svc.send_dunning_message(
        customer_id="cust_novu_01",
        message_strategy="HINGLISH",
        message_body="Aapka payment pending hai."
    )

    assert res["status"] == "SKIPPED_LOCAL"
    assert res["delivered"] is False
    assert "missing or placeholder" in res["reason"]
