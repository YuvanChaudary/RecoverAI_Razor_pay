"""
Phase 12 Integration Test Suite: End-to-End Recovery Pipeline & Safety Scenarios
Exercises multi-service boundaries using synthetic/test data without real financial transactions.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from backend.app.schemas.state_machine import CaseStateEnum, CaseEventEnum
from backend.app.services.recovery_state_machine import RecoveryStateMachine
from backend.app.policy.engine import OPAGovernanceEngine, PolicyDecision
from backend.app.services.razorpay_service import RazorpayService
from backend.app.services.immutable_audit_service import ImmutableAuditService
from backend.app.schemas.audit import AuditEvent
from backend.app.simulation.schemas import SimulationCase
from backend.app.simulation.evaluator import SimulationGovernanceEvaluator


# TEST 1 — E2E HAPPY PATH PIPELINE: EXECUTION IS NOT RECOVERY
@pytest.mark.asyncio
async def test_e2e_happy_path_execution_is_not_recovery():
    sm = RecoveryStateMachine()

    # Step 1: Webhook Payment Failure Received -> DETECTED
    res1 = await sm.transition(case_id="e2e_case_01", event=CaseEventEnum.FAILURE_DIAGNOSED, current_state="DETECTED")
    assert res1.success is True
    assert res1.new_state == "DIAGNOSED"

    # Step 2: Governance Allowed -> GOVERNANCE_APPROVED
    res2 = await sm.transition(case_id="e2e_case_01", event=CaseEventEnum.GOVERNANCE_ALLOWED, current_state="DIAGNOSED", opa_allowed=True)
    assert res2.success is True
    assert res2.new_state == "GOVERNANCE_APPROVED"

    # Step 3: Action Executed -> ACTION_EXECUTED
    res3 = await sm.transition(case_id="e2e_case_01", event=CaseEventEnum.ACTION_EXECUTED, current_state="GOVERNANCE_APPROVED", opa_allowed=True)
    assert res3.success is True
    assert res3.new_state == "ACTION_EXECUTED"

    # CRITICAL FINTECH INVARIANT: Outbound execution does NOT equal RECOVERED
    assert res3.new_state != "RECOVERED"
    assert res3.recovered_amount_paise == 0

    # Step 4: Awaiting Settlement
    res4 = await sm.transition(case_id="e2e_case_01", event=CaseEventEnum.SETTLEMENT_AWAITING, current_state="ACTION_EXECUTED")
    assert res4.success is True
    assert res4.new_state == "AWAITING_SETTLEMENT"
    assert res4.new_state != "RECOVERED"


# TEST 2 — OPA ADVERSARIAL DENIAL STOPS OUTBOUND EXECUTION
@pytest.mark.asyncio
async def test_e2e_opa_denial_blocks_financial_execution():
    sm = RecoveryStateMachine()

    # Adversarial case: high AI confidence (0.99) with OPA denial
    res = await sm.transition(
        case_id="e2e_adv_01",
        event=CaseEventEnum.GOVERNANCE_ALLOWED,
        current_state="DIAGNOSED",
        ai_confidence=0.99,
        opa_allowed=False
    )

    assert res.success is False
    assert res.new_state == "BLOCKED"
    assert "OPA governance denial" in res.reason


# TEST 3 — OPA UNAVAILABLE FAIL-CLOSED SECURITY BOUNDARY
@pytest.mark.asyncio
async def test_e2e_opa_unavailable_fails_closed():
    """When OPA HTTP is unreachable, the local Rego engine runs and still enforces policy rules.
    Empty input (missing cooldown_hours defaults to 0) triggers RULE-002 denial.
    Verify: policy is still enforced even without the OPA HTTP server.
    """
    engine = OPAGovernanceEngine(opa_url="http://non_existent_opa_host:9999/v1/data")

    # Mock httpx failure
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
        decision = await engine.evaluate_policy({"action": "RETRY_SCHEDULED"})

        # Local Rego engine must still deny — missing cooldown_hours defaults to 0 < 24h
        assert decision.allow is False, f"Expected DENY from local Rego, got allow=True"
        # Violations must contain at least one RULE violation from local engine
        assert len(decision.violations) > 0, "Expected at least one RULE violation from local Rego"


# TEST 4 — RAZORPAY HTTP 500 ERROR PROPAGATION
@pytest.mark.asyncio
async def test_e2e_razorpay_http_500_error_propagated():
    service = RazorpayService(key_id="rzp_test_mock", key_secret="secret_mock")

    req = httpx.Request("POST", "https://api.razorpay.com/v1/payment_links")
    mock_response = httpx.Response(status_code=500, text="Internal Server Error from Gateway", request=req)

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(httpx.HTTPStatusError):
            await service.create_payment_link(
                amount_paise=49900,
                customer={"email": "cust@example.com"},
                description="Test payment link",
                idempotency_key="idemp_500_test"
            )


# TEST 5 — RAZORPAY IDEMPOTENCY KEY REUSE
@pytest.mark.asyncio
async def test_e2e_razorpay_idempotency_key_preserved():
    service = RazorpayService(key_id="rzp_test_mock", key_secret="secret_mock")
    req = httpx.Request("POST", "https://api.razorpay.com/v1/payment_links")
    mock_success = httpx.Response(status_code=200, json={"id": "plink_123", "status": "created"}, request=req)

    with patch("httpx.AsyncClient.post", return_value=mock_success) as mock_post:
        res1 = await service.create_payment_link(
            amount_paise=50000,
            customer={"email": "idemp@example.com"},
            description="Idempotency test",
            idempotency_key="idemp_key_999"
        )
        assert res1["id"] == "plink_123"

        # Verify idempotency key header was passed
        headers = mock_post.call_args[1]["headers"]
        assert headers["X-Razorpay-Idempotency-Key"] == "idemp_key_999"
        assert headers["X-Razorpay-Comment"] == "idemp_key_999"


# TEST 6 — DUPLICATE SETTLEMENT WEBHOOK IDEMPOTENCY
@pytest.mark.asyncio
async def test_e2e_duplicate_settlement_webhook_idempotent():
    sm = RecoveryStateMachine()
    settlement_evidence = {
        "authoritative": True,
        "event_type": "payment.captured",
        "payment_id": "pay_e2e_settle",
        "amount_paise": 75000,
        "signature_verified": True
    }

    # Delivery 1 -> RECOVERED
    res1 = await sm.transition(
        case_id="case_e2e_dup",
        event=CaseEventEnum.PAYMENT_CAPTURED,
        current_state="AWAITING_SETTLEMENT",
        evidence=settlement_evidence
    )
    assert res1.success is True
    assert res1.new_state == "RECOVERED"
    assert res1.recovered_amount_paise == 75000

    # Delivery 2 (Duplicate Settlement Webhook Delivery) -> Idempotent no-op
    res2 = await sm.transition(
        case_id="case_e2e_dup",
        event=CaseEventEnum.PAYMENT_CAPTURED,
        current_state="RECOVERED",
        evidence=settlement_evidence
    )
    assert res2.success is True
    assert res2.new_state == "RECOVERED"
    assert res2.idempotent is True
    # Zero recovered amount on duplicate to prevent double-counting!
    assert res2.recovered_amount_paise == 0


# TEST 7 — API SUCCESS IS NOT RECOVERY
@pytest.mark.asyncio
async def test_e2e_api_success_does_not_mutate_case_to_recovered():
    sm = RecoveryStateMachine()

    # Outbound API HTTP 200 response
    api_evidence = {"api_status_code": 200, "payment_link_id": "plink_abc"}

    res = await sm.transition(
        case_id="case_api_200",
        event=CaseEventEnum.ACTION_EXECUTED,
        current_state="GOVERNANCE_APPROVED",
        opa_allowed=True,
        evidence=api_evidence
    )

    assert res.success is True
    assert res.new_state == "ACTION_EXECUTED"
    assert res.new_state != "RECOVERED"


# TEST 8 — IMMUDB CRYPTOGRAPHIC AUDIT VERIFICATION & TAMPER DETECTION
@pytest.mark.asyncio
async def test_e2e_immudb_audit_verification_and_tamper_detection():
    audit_service = ImmutableAuditService(client=MagicMock())

    event = AuditEvent(
        event_id="evt_e2e_audit_01",
        event_type="STATE_TRANSITION",
        recovery_case_id="case_e2e_audit",
        payment_id="pay_e2e_audit",
        governance_allowed=True,
        execution_status="EXECUTED"
    )

    # 1. Record event into audit trail
    record_result = await audit_service.record_event(event)
    assert record_result["status"] == "CREATED"
    assert record_result["persisted"] is True

    # 2. Verify untampered event -> Valid
    verify_valid = await audit_service.verify_event("evt_e2e_audit_01")
    assert verify_valid.valid is True

    # 3. Verify tampered payload -> Detected
    tampered_payload = event.model_dump(mode="json")
    tampered_payload["governance_allowed"] = False  # Alter payload after recording

    verify_tampered = await audit_service.verify_event("evt_e2e_audit_01", tampered_record=tampered_payload)
    assert verify_tampered.valid is False
    assert "TAMPER DETECTED" in verify_tampered.details
