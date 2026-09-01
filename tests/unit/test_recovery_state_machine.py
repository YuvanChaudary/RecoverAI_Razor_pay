"""
Phase 9 Unit & Adversarial Tests: Authoritative RecoveryCase State Machine
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.schemas.state_machine import CaseStateEnum, CaseEventEnum, StateTransitionResult
from backend.app.services.recovery_state_machine import RecoveryStateMachine


# TEST 1 — VALID DIAGNOSIS TRANSITION
@pytest.mark.asyncio
async def test_state_machine_valid_diagnosis():
    sm = RecoveryStateMachine()
    res = await sm.transition(
        case_id="case_sm_01",
        event=CaseEventEnum.FAILURE_DIAGNOSED,
        current_state="DETECTED"
    )
    assert res.success is True
    assert res.previous_state == "DETECTED"
    assert res.new_state == "DIAGNOSED"


# TEST 2 — VALID GOVERNANCE ALLOWED TRANSITION
@pytest.mark.asyncio
async def test_state_machine_governance_allowed():
    sm = RecoveryStateMachine()
    res = await sm.transition(
        case_id="case_sm_02",
        event=CaseEventEnum.GOVERNANCE_ALLOWED,
        current_state="DIAGNOSED",
        opa_allowed=True
    )
    assert res.success is True
    assert res.previous_state == "DIAGNOSED"
    assert res.new_state == "GOVERNANCE_APPROVED"


# TEST 3 — GOVERNANCE DENIAL TRANSITION
@pytest.mark.asyncio
async def test_state_machine_governance_denial_blocks_case():
    sm = RecoveryStateMachine()
    res = await sm.transition(
        case_id="case_sm_03",
        event=CaseEventEnum.GOVERNANCE_DENIED,
        current_state="DIAGNOSED",
        opa_allowed=False
    )
    assert res.success is False
    assert res.new_state == "BLOCKED"


# TEST 4 — VALID ACTION EXECUTION TRANSITION
@pytest.mark.asyncio
async def test_state_machine_action_execution():
    sm = RecoveryStateMachine()
    res = await sm.transition(
        case_id="case_sm_04",
        event=CaseEventEnum.ACTION_EXECUTED,
        current_state="GOVERNANCE_APPROVED",
        opa_allowed=True
    )
    assert res.success is True
    assert res.new_state == "ACTION_EXECUTED"


# TEST 5 — EXECUTION DOES NOT MEAN RECOVERY (CRITICAL MANDATORY TEST)
@pytest.mark.asyncio
async def test_action_execution_does_not_equal_recovery():
    sm = RecoveryStateMachine()
    # OPA ALLOW = True, Razorpay API = HTTP 200 (Action Executed)
    res = await sm.transition(
        case_id="case_sm_05",
        event=CaseEventEnum.ACTION_EXECUTED,
        current_state="GOVERNANCE_APPROVED",
        opa_allowed=True,
        ai_confidence=0.99,
        evidence={"api_status_code": 200, "payment_link_id": "plink_123"}
    )
    assert res.success is True
    assert res.new_state == "ACTION_EXECUTED"
    # CRITICAL INVARIANT: Status must NOT be RECOVERED
    assert res.new_state != "RECOVERED"
    assert res.recovered_amount_paise == 0


# TEST 6 — CRITICAL ADVERSARIAL DIRECT RECOVERY REJECTED
@pytest.mark.asyncio
async def test_direct_illegal_recovery_attempt_rejected():
    sm = RecoveryStateMachine()
    # Attempting to jump directly from ACTION_EXECUTED to RECOVERED without settlement evidence
    res = await sm.transition(
        case_id="case_sm_06",
        event=CaseEventEnum.ACTION_EXECUTED,
        current_state="ACTION_EXECUTED",
        evidence={"target_state": "RECOVERED"}  # Unverified claim
    )
    assert res.success is False
    assert res.new_state != "RECOVERED"
    assert "cannot produce RECOVERED state" in res.reason or "Illegal transition" in res.reason


# TEST 7 — AUTHORITATIVE WEBHOOK RECOVERY (SOLE VALID PATH)
@pytest.mark.asyncio
async def test_authoritative_webhook_establishes_recovery():
    sm = RecoveryStateMachine()
    authoritative_evidence = {
        "authoritative": True,
        "event_type": "payment.captured",
        "payment_id": "pay_settled_999",
        "amount_paise": 49900,
        "signature_verified": True
    }
    res = await sm.transition(
        case_id="case_sm_07",
        event=CaseEventEnum.PAYMENT_CAPTURED,
        current_state="AWAITING_SETTLEMENT",
        evidence=authoritative_evidence
    )
    assert res.success is True
    assert res.previous_state == "AWAITING_SETTLEMENT"
    assert res.new_state == "RECOVERED"
    assert res.recovered_amount_paise == 49900


# TEST 8 — DUPLICATE WEBHOOK IDEMPOTENCY (NO DOUBLE COUNTING)
@pytest.mark.asyncio
async def test_duplicate_webhook_delivery_idempotent():
    sm = RecoveryStateMachine()
    authoritative_evidence = {
        "authoritative": True,
        "event_type": "payment.captured",
        "payment_id": "pay_settled_dup",
        "amount_paise": 49900
    }

    # Delivery 1 -> RECOVERED
    res1 = await sm.transition(
        case_id="case_sm_08",
        event=CaseEventEnum.PAYMENT_CAPTURED,
        current_state="AWAITING_SETTLEMENT",
        evidence=authoritative_evidence
    )
    assert res1.success is True
    assert res1.new_state == "RECOVERED"
    assert res1.recovered_amount_paise == 49900

    # Delivery 2 (Duplicate Webhook Delivery) -> Idempotent no-op
    res2 = await sm.transition(
        case_id="case_sm_08",
        event=CaseEventEnum.PAYMENT_CAPTURED,
        current_state="RECOVERED",
        evidence=authoritative_evidence
    )
    assert res2.success is True
    assert res2.new_state == "RECOVERED"
    assert res2.idempotent is True
    # Zero recovered amount on duplicate delivery to prevent double-counting!
    assert res2.recovered_amount_paise == 0


# TEST 9 — ILLEGAL TRANSITION MATRIX REJECTIONS
@pytest.mark.asyncio
async def test_illegal_transition_rejections():
    sm = RecoveryStateMachine()
    illegal_cases = [
        ("DETECTED", CaseEventEnum.PAYMENT_CAPTURED, {}),  # Missing settlement evidence
        ("DIAGNOSED", CaseEventEnum.PAYMENT_CAPTURED, {}),
        ("BLOCKED", CaseEventEnum.GOVERNANCE_ALLOWED, {"opa_allowed": True}),
        ("ACTION_EXECUTED", CaseEventEnum.ACTION_SCHEDULED, {}),
        ("RECOVERED", CaseEventEnum.ACTION_SCHEDULED, {}),
        ("RECOVERED", CaseEventEnum.FAILURE_DIAGNOSED, {}),
    ]

    for curr_st, evt, kwargs in illegal_cases:
        res = await sm.transition(case_id="case_ill", event=evt, current_state=curr_st, **kwargs)
        assert res.success is False
        assert res.new_state == curr_st


# TEST 10 — ADVERSARIAL AI CONFIDENCE CANNOT OVERRIDE OPA GOVERNANCE
@pytest.mark.asyncio
async def test_ai_confidence_cannot_override_opa_governance_in_state_machine():
    sm = RecoveryStateMachine()
    # High AI Confidence (0.99) with OPA Denial (opa_allowed = False)
    res = await sm.transition(
        case_id="case_sm_10",
        event=CaseEventEnum.GOVERNANCE_ALLOWED,
        current_state="DIAGNOSED",
        ai_confidence=0.99,
        opa_allowed=False
    )
    assert res.success is False
    assert res.new_state == "BLOCKED"
    assert "OPA governance denial" in res.reason


# TEST 11 — PHASE 8 AUDIT INTEGRATION PRESERVES EVIDENCE
@pytest.mark.asyncio
async def test_state_transition_logs_phase_8_audit():
    sm = RecoveryStateMachine()
    authoritative_evidence = {
        "authoritative": True,
        "event_type": "payment.captured",
        "payment_id": "pay_audit_99",
        "amount_paise": 15000
    }
    with patch("backend.app.services.immutable_audit_service.ImmutableAuditService.record_event", new_callable=AsyncMock) as mock_audit:
        res = await sm.transition(
            case_id="case_audit_99",
            event=CaseEventEnum.PAYMENT_CAPTURED,
            current_state="AWAITING_SETTLEMENT",
            evidence=authoritative_evidence
        )
        assert res.success is True
        assert mock_audit.called
        recorded_event = mock_audit.call_args[0][0]
        assert recorded_event.recovery_case_id == "case_audit_99"
        assert recorded_event.metadata["new_state"] == "RECOVERED"
