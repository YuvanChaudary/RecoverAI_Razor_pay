"""
Phase 14 Production Integration Suite: Full Synthetic Recovery Lifecycle & Adversarial Safety Boundaries
Exercises end-to-end orchestration without real financial transactions or live customer charges.
"""

import pytest
from unittest.mock import patch, MagicMock
import httpx
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

from backend.app.schemas.state_machine import CaseStateEnum, CaseEventEnum
from backend.app.services.recovery_state_machine import RecoveryStateMachine
from backend.app.policy.engine import OPAGovernanceEngine
from backend.app.services.razorpay_service import RazorpayService
from backend.app.services.immutable_audit_service import ImmutableAuditService
from backend.app.schemas.audit import AuditEvent


# 1. FULL SYNTHETIC RECOVERY LIFECYCLE
@pytest.mark.asyncio
async def test_full_synthetic_recovery_lifecycle():
    sm = RecoveryStateMachine()
    case_id = "case_p14_lifecycle_001"

    # Step 1: Webhook Payment Failure Received -> DETECTED -> DIAGNOSED
    res1 = await sm.transition(case_id=case_id, event=CaseEventEnum.FAILURE_DIAGNOSED, current_state="DETECTED")
    assert res1.success is True
    assert res1.new_state == "DIAGNOSED"

    # Step 2: OPA Governance Allowed -> GOVERNANCE_APPROVED
    res2 = await sm.transition(case_id=case_id, event=CaseEventEnum.GOVERNANCE_ALLOWED, current_state="DIAGNOSED", opa_allowed=True)
    assert res2.success is True
    assert res2.new_state == "GOVERNANCE_APPROVED"

    # Step 3: Outbound Payment Link Executed -> ACTION_EXECUTED (Not RECOVERED!)
    api_evidence = {"status_code": 200, "payment_link_id": "plink_p14_test"}
    res3 = await sm.transition(case_id=case_id, event=CaseEventEnum.ACTION_EXECUTED, current_state="GOVERNANCE_APPROVED", opa_allowed=True, evidence=api_evidence)
    assert res3.success is True
    assert res3.new_state == "ACTION_EXECUTED"
    assert res3.new_state != "RECOVERED"
    assert res3.recovered_amount_paise == 0

    # Step 4: Scheduled Sleep / Durable Waiting -> AWAITING_SETTLEMENT
    res4 = await sm.transition(case_id=case_id, event=CaseEventEnum.SETTLEMENT_AWAITING, current_state="ACTION_EXECUTED")
    assert res4.success is True
    assert res4.new_state == "AWAITING_SETTLEMENT"
    assert res4.new_state != "RECOVERED"

    # Step 5: Verified Authoritative Settlement Webhook -> RECOVERED
    settlement_evidence = {
        "authoritative": True,
        "event_type": "payment.captured",
        "payment_id": "pay_p14_captured_99",
        "amount_paise": 150000,
        "signature_verified": True
    }
    res5 = await sm.transition(case_id=case_id, event=CaseEventEnum.PAYMENT_CAPTURED, current_state="AWAITING_SETTLEMENT", evidence=settlement_evidence)
    assert res5.success is True
    assert res5.new_state == "RECOVERED"
    assert res5.recovered_amount_paise == 150000


# 2. ADVERSARIAL TEST A: OUTBOUND HTTP 200 CANNOT PRODUCE 'RECOVERED'
@pytest.mark.asyncio
async def test_adversarial_outbound_http_200_is_not_recovered():
    sm = RecoveryStateMachine()
    res = await sm.transition(
        case_id="case_p14_http200",
        event=CaseEventEnum.ACTION_EXECUTED,
        current_state="GOVERNANCE_APPROVED",
        opa_allowed=True,
        evidence={"http_code": 200, "action": "PAYMENT_LINK_CREATED"}
    )
    assert res.success is True
    assert res.new_state == "ACTION_EXECUTED"
    assert res.new_state != "RECOVERED"
    assert res.recovered_amount_paise == 0


# 3. ADVERSARIAL TEST B: AI CONFIDENCE 0.99 + OPA DENY -> BLOCKED
@pytest.mark.asyncio
async def test_adversarial_high_ai_confidence_with_opa_deny_transitions_to_blocked():
    sm = RecoveryStateMachine()
    res = await sm.transition(
        case_id="case_p14_adv_ai",
        event=CaseEventEnum.GOVERNANCE_ALLOWED,
        current_state="DIAGNOSED",
        ai_confidence=0.99,
        opa_allowed=False
    )
    assert res.success is False
    assert res.new_state == "BLOCKED"
    assert "OPA governance denial" in res.reason


# 4. ADVERSARIAL TEST C: DUPLICATE SETTLEMENT WEBHOOK IDEMPOTENCY
@pytest.mark.asyncio
async def test_adversarial_duplicate_settlement_webhook_zero_double_recovery():
    sm = RecoveryStateMachine()
    evidence = {
        "authoritative": True,
        "event_type": "payment.captured",
        "payment_id": "pay_p14_dup",
        "amount_paise": 250000,
        "signature_verified": True
    }

    # Delivery 1 -> RECOVERED (250000 paise)
    r1 = await sm.transition(case_id="case_p14_dup_test", event=CaseEventEnum.PAYMENT_CAPTURED, current_state="AWAITING_SETTLEMENT", evidence=evidence)
    assert r1.success is True
    assert r1.new_state == "RECOVERED"
    assert r1.recovered_amount_paise == 250000

    # Delivery 2 (Duplicate) -> Idempotent no-op (0 paise recovered)
    r2 = await sm.transition(case_id="case_p14_dup_test", event=CaseEventEnum.PAYMENT_CAPTURED, current_state="RECOVERED", evidence=evidence)
    assert r2.success is True
    assert r2.new_state == "RECOVERED"
    assert r2.idempotent is True
    assert r2.recovered_amount_paise == 0


# 5. ADVERSARIAL TEST D: INVALID SETTLEMENT WEBHOOK SIGNATURE REJECTED
@pytest.mark.asyncio
async def test_adversarial_invalid_webhook_signature_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"event": "payment.captured", "payload": {"payment": {"entity": {"id": "pay_fake_123", "amount": 50000}}}}
        headers = {"X-Razorpay-Signature": "invalid_fake_signature_hash_12345"}
        res = await ac.post("/webhooks/razorpay", json=payload, headers=headers)
        assert res.status_code == 401
        assert "Invalid Razorpay webhook signature" in res.text


# 6. ADVERSARIAL TEST E: DIRECT ILLEGAL 'RECOVERED' TRANSITION REJECTED
@pytest.mark.asyncio
async def test_adversarial_direct_illegal_recovered_transition_rejected():
    sm = RecoveryStateMachine()
    res = await sm.transition(case_id="case_p14_direct_illegal", event=CaseEventEnum.ACTION_EXECUTED, current_state="DETECTED")
    assert res.success is False
    assert res.new_state != "RECOVERED"


# 7. DEPENDENCY FAILURE: OPA UNAVAILABLE FAILS CLOSED
@pytest.mark.asyncio
async def test_dependency_failure_opa_unavailable_fails_closed():
    """When OPA HTTP is unreachable, the local Rego engine runs and enforces policy.
    Empty input causes RULE violations (cooldown=0 < 24h) -> DENY.
    This verifies the fail-closed local evaluation path works correctly.
    """
    engine = OPAGovernanceEngine(opa_url="http://non_existent_opa_host:9999/v1/data")
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("OPA server down")):
        decision = await engine.evaluate_policy({"action": "RETRY_SCHEDULED"})
        assert decision.allow is False, "Local Rego should deny request with missing cooldown_hours"
        assert len(decision.violations) > 0, f"Expected RULE violations from local Rego, got none"


# 8. IDEMPOTENCY KEY PRESERVED ACROSS RETRIES
@pytest.mark.asyncio
async def test_idempotency_key_preserved_across_retries():
    service = RazorpayService(key_id="rzp_test_mock", key_secret="secret_mock")
    req = httpx.Request("POST", "https://api.razorpay.com/v1/payment_links")
    mock_resp = httpx.Response(status_code=200, json={"id": "plink_retry_123"}, request=req)

    with patch("httpx.AsyncClient.post", return_value=mock_resp) as mock_post:
        key = "idemp_p14_retry_key"
        res1 = await service.create_payment_link(amount_paise=99000, customer={"email": "retry@example.com"}, description="Retry test", idempotency_key=key)
        res2 = await service.create_payment_link(amount_paise=99000, customer={"email": "retry@example.com"}, description="Retry test", idempotency_key=key)

        assert res1["id"] == "plink_retry_123"
        assert res2["id"] == "plink_retry_123"
        # Confirm header key was preserved across both requests
        assert mock_post.call_args_list[0][1]["headers"]["X-Razorpay-Idempotency-Key"] == key
        assert mock_post.call_args_list[1][1]["headers"]["X-Razorpay-Idempotency-Key"] == key


# 9. IMMUDB TAMPER DETECTION VERIFICATION
@pytest.mark.asyncio
async def test_immudb_tamper_detection_verification():
    audit_service = ImmutableAuditService(client=MagicMock())
    event = AuditEvent(
        event_id="evt_p14_audit_01",
        event_type="STATE_TRANSITION",
        recovery_case_id="case_p14_audit",
        payment_id="pay_p14_audit",
        governance_allowed=True,
        execution_status="EXECUTED"
    )

    res = await audit_service.record_event(event)
    assert res["status"] == "CREATED"

    # Verify original
    v1 = await audit_service.verify_event("evt_p14_audit_01")
    assert v1.valid is True

    # Tamper payload
    tampered_dict = event.model_dump(mode="json")
    tampered_dict["governance_allowed"] = False
    v2 = await audit_service.verify_event("evt_p14_audit_01", tampered_record=tampered_dict)
    assert v2.valid is False
    assert "TAMPER DETECTED" in v2.details
