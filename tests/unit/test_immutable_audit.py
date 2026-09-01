"""
Phase 8 Unit & Adversarial Tests: immudb Cryptographic Immutable Audit Trail
"""

import pytest
from unittest.mock import MagicMock, patch
from backend.app.schemas.audit import AuditEvent, AuditVerificationResult
from backend.app.services.immutable_audit_service import ImmutableAuditService


# TEST 1 — EVENT PERSISTENCE & SHA-256 HASHING
@pytest.mark.asyncio
async def test_audit_event_persistence_and_hashing():
    service = ImmutableAuditService(client=MagicMock())
    event = AuditEvent(
        event_id="audit_evt_p8_001",
        event_type="GOVERNANCE_DECISION",
        recovery_case_id="case_p8_001",
        payment_id="pay_p8_001",
        failure_category="LIQUIDITY_FRICTION",
        risk_tier="HIGH",
        priority_score=85.5,
        recommended_action="RETRY_SCHEDULED",
        governance_allowed=True,
        idempotency_key="rec_idemp_p8_1",
        execution_status="EXECUTED"
    )

    res = await service.record_event(event)

    assert res["status"] == "CREATED"
    assert res["persisted"] is True
    assert res["created"] is True
    assert res["key"] == "recoverai/audit/audit_evt_p8_001"
    assert len(res["payload_hash"]) == 64  # SHA-256 hex string is 64 characters


# TEST 2 — DETERMINISTIC CANONICAL HASHING
def test_deterministic_canonical_hashing():
    # Two audit events with identical values & timestamp, but differing metadata dict order
    fixed_ts = "2026-08-29T12:00:00Z"
    event1 = AuditEvent(
        event_id="evt_det_100",
        event_type="RISK_ASSESSED",
        occurred_at=fixed_ts,
        recovery_case_id="case_100",
        payment_id="pay_100",
        priority_score=75.0,
        metadata={"b": 2, "a": 1}  # Dict keys order 1
    )

    event2 = AuditEvent(
        event_id="evt_det_100",
        event_type="RISK_ASSESSED",
        occurred_at=fixed_ts,
        recovery_case_id="case_100",
        payment_id="pay_100",
        priority_score=75.0,
        metadata={"a": 1, "b": 2}  # Dict keys order 2
    )

    hash1 = event1.compute_hash()
    hash2 = event2.compute_hash()

    assert hash1 == hash2


# TEST 3 — DUPLICATE EVENT (APPEND-ONLY ENFORCEMENT)
@pytest.mark.asyncio
async def test_append_only_duplicate_rejection():
    service = ImmutableAuditService(client=MagicMock())
    event = AuditEvent(
        event_id="evt_dup_001",
        event_type="FAILURE_DIAGNOSED",
        recovery_case_id="case_dup",
        payment_id="pay_dup",
        failure_category="TRANSIENT_INFRASTRUCTURE"
    )

    # First write -> CREATED
    res1 = await service.record_event(event)
    assert res1["status"] == "CREATED"
    assert res1["created"] is True

    # Second write with same event_id -> DUPLICATE (Retains original record under append-only rules)
    res2 = await service.record_event(event)
    assert res2["status"] == "DUPLICATE"
    assert res2["created"] is False
    assert res2["persisted"] is True


# TEST 4 — TAMPER DETECTION (CRITICAL MANDATORY TEST)
@pytest.mark.asyncio
async def test_tamper_detection_adversarial():
    service = ImmutableAuditService(client=MagicMock())
    event = AuditEvent(
        event_id="evt_tamper_001",
        event_type="AI_RECOMMENDATION",
        recovery_case_id="case_tamp",
        payment_id="pay_tamp",
        recommended_action="CUSTOMER_REMINDER",
        priority_score=45.0
    )

    res = await service.record_event(event)
    original_hash = res["payload_hash"]

    # Retrieve valid event -> Verify success
    verif_valid = await service.verify_event("evt_tamper_001")
    assert verif_valid.valid is True
    assert verif_valid.stored_hash == original_hash

    # Simulate tampered record in DB (e.g. attacker modified priority_score or recommended_action)
    raw_stored_dict = service._local_audit_store["recoverai/audit/evt_tamper_001"].copy()
    raw_stored_dict["priority_score"] = 99.0  # Tampered priority!
    raw_stored_dict["recommended_action"] = "RETRY_SCHEDULED"  # Tampered action!

    # Verify tampered payload -> Must fail verification with hash mismatch!
    verif_tampered = await service.verify_event("evt_tamper_001", tampered_record=raw_stored_dict)
    assert verif_tampered.valid is False
    assert verif_tampered.stored_hash == original_hash
    assert verif_tampered.calculated_hash != original_hash
    assert "TAMPER DETECTED" in verif_tampered.details


# TEST 5 — VALID VERIFICATION
@pytest.mark.asyncio
async def test_valid_event_verification():
    service = ImmutableAuditService(client=MagicMock())
    event = AuditEvent(
        event_id="evt_valid_001",
        event_type="OUTBOUND_ACTION_RESULT",
        recovery_case_id="case_val",
        payment_id="pay_val",
        execution_status="EXECUTED"
    )

    await service.record_event(event)
    verif = await service.verify_event("evt_valid_001")

    assert verif.valid is True
    assert "Integrity verified" in verif.details


# TEST 6 — IMMUDB UNAVAILABLE / CONNECTION FAILURE
@pytest.mark.asyncio
async def test_immudb_unavailable_failure_handling():
    # Mock ImmudbClient login throwing connection refusal exception
    mock_client = MagicMock()
    mock_client.set.side_effect = Exception("gRPC Connection Refused: localhost:3322")
    mock_client.verifiedSet.side_effect = Exception("gRPC Connection Refused: localhost:3322")

    service = ImmutableAuditService(client=mock_client)
    event = AuditEvent(
        event_id="evt_unavail_001",
        event_type="GOVERNANCE_DECISION",
        recovery_case_id="case_unavail",
        payment_id="pay_unavail"
    )

    res = await service.record_event(event)

    # Must report persisted = False (never falsely claim persistence success)
    assert res["status"] == "ERROR"
    assert res["persisted"] is False
    assert "Connection Refused" in res["error"]


# TEST 7 — NO RECOVERY STATE MUTATION / FORBIDDEN 'RECOVERED' AUDIT STATUS
def test_no_false_recovery_claim_validation():
    # Attempting to create an AuditEvent with execution_status='RECOVERED' must raise ValueError
    with pytest.raises(ValueError, match="must never be set to 'RECOVERED'"):
        AuditEvent(
            event_id="evt_invalid_rec_01",
            event_type="OUTBOUND_ACTION_RESULT",
            recovery_case_id="case_inv",
            payment_id="pay_inv",
            execution_status="RECOVERED"
        )


# TEST 8 — GOVERNANCE DECISION AUDIT PRESERVES OPA DENIAL
@pytest.mark.asyncio
async def test_governance_decision_audit_preserves_denial():
    service = ImmutableAuditService(client=MagicMock())
    event = AuditEvent(
        event_id="evt_opa_deny_01",
        event_type="GOVERNANCE_DECISION",
        recovery_case_id="case_opa",
        payment_id="pay_opa",
        recommended_action="RETRY_SCHEDULED",
        governance_allowed=False,
        metadata={"violations": ["RULE-001: Retry count limit exceeded"]}
    )

    res = await service.record_event(event)
    assert res["status"] == "CREATED"

    verif = await service.verify_event("evt_opa_deny_01")
    assert verif.valid is True
    stored_dict = service._local_audit_store["recoverai/audit/evt_opa_deny_01"]
    assert stored_dict["governance_allowed"] is False


# TEST 9 — HIGH AI CONFIDENCE CANNOT BECOME AUTHORITATIVE IN AUDIT
@pytest.mark.asyncio
async def test_ai_confidence_cannot_override_opa_in_audit():
    service = ImmutableAuditService(client=MagicMock())
    event = AuditEvent(
        event_id="evt_ai_override_01",
        event_type="AI_RECOMMENDATION",
        recovery_case_id="case_ai",
        payment_id="pay_ai",
        recommended_action="RETRY_SCHEDULED",
        governance_allowed=False,
        priority_score=99.0,
        metadata={"ai_confidence": 0.99}
    )

    res = await service.record_event(event)
    assert res["status"] == "CREATED"

    stored_dict = service._local_audit_store["recoverai/audit/evt_ai_override_01"]
    assert stored_dict["governance_allowed"] is False
    assert stored_dict["metadata"]["ai_confidence"] == 0.99
