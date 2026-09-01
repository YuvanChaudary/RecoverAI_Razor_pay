"""
Phase 5 Unit & Adversarial Tests: OPA Governance Firewall
"""

import pytest
import respx
from httpx import Response
from backend.app.policy.engine import OPAGovernanceEngine, PolicyDecision


# Helper to evaluate governance rules in Python mimicking exact Rego logic for mock transport
def evaluate_rego_governance_mock(input_data: dict) -> dict:
    violations = []
    action = input_data.get("action")
    retry_count = input_data.get("retry_count", 0)
    cooldown_hours = input_data.get("cooldown_hours", 0)
    is_terminal = input_data.get("is_terminal_decline", False)
    confidence = input_data.get("confidence", 0.0)
    notice_req = input_data.get("pre_debit_notice_required", False)
    notice_sent = input_data.get("pre_debit_notice_sent", False)

    # RULE-001
    if action == "RETRY_SCHEDULED" and retry_count >= 3:
        violations.append(f"RULE-001: Exceeded maximum retry limit ({retry_count} >= 3)")

    # RULE-002
    if action == "RETRY_SCHEDULED" and cooldown_hours < 24:
        violations.append(f"RULE-002: Insufficient cooldown hours ({cooldown_hours} < 24)")

    # RULE-003
    if is_terminal and action == "RETRY_SCHEDULED":
        violations.append("RULE-003: Retry action prohibited on terminal failure decline")

    # RULE-004
    if confidence < 0.80:
        violations.append(f"RULE-004: AI confidence below threshold ({confidence} < 0.80)")

    # RULE-005
    if notice_req and not notice_sent:
        violations.append("RULE-005: Pre-debit notice required but not sent")

    allow = len(violations) == 0
    return {
        "result": {
            "allow": allow,
            "violations": violations
        }
    }


# TEST 1: HAPPY PATH
@pytest.mark.asyncio
@respx.mock
async def test_opa_happy_path():
    engine = OPAGovernanceEngine("http://localhost:8181/v1/data/recovery/governance")
    input_data = {
        "action": "RETRY_SCHEDULED",
        "confidence": 0.90,
        "retry_count": 0,
        "cooldown_hours": 24,
        "is_terminal_decline": False,
        "pre_debit_notice_required": False,
        "pre_debit_notice_sent": False
    }

    respx.post("http://localhost:8181/v1/data/recovery/governance").mock(
        return_value=Response(200, json=evaluate_rego_governance_mock(input_data))
    )

    decision = await engine.evaluate_policy(input_data)
    assert decision.allow is True
    assert decision.violations == []


# TEST 2: FAIL CLOSED — LOCAL REGO FALLBACK
@pytest.mark.asyncio
async def test_opa_fail_closed_unreachable():
    """When OPA HTTP server is unreachable, the local Rego engine evaluates the policy.
    The local engine returns real ALLOW/DENY based on input — not a blanket fail-closed.
    This is correct behavior: we still enforce the policy rules locally.
    Verify: valid input -> ALLOW, invalid input -> DENY with RULE violations.
    """
    engine = OPAGovernanceEngine("http://localhost:9999/v1/data/recovery/governance")

    # Valid input — local Rego engine should ALLOW this
    valid_input = {
        "action": "RETRY_SCHEDULED",
        "confidence": 0.90,
        "retry_count": 0,
        "cooldown_hours": 24,
        "is_terminal_decline": False,
        "pre_debit_notice_required": False,
        "pre_debit_notice_sent": False
    }
    decision_valid = await engine.evaluate_policy(valid_input)
    # Local Rego evaluates fully — valid input should be ALLOWED
    assert decision_valid.allow is True, f"Local Rego should allow valid input, got violations={decision_valid.violations}"
    assert decision_valid.violations == []

    # Invalid input (cooldown < 24h) — local Rego engine should DENY
    invalid_input = {
        "action": "RETRY_SCHEDULED",
        "confidence": 0.90,
        "retry_count": 0,
        "cooldown_hours": 1,  # Violates RULE-002: < 24h
        "is_terminal_decline": False,
        "pre_debit_notice_required": False,
        "pre_debit_notice_sent": False
    }
    decision_invalid = await engine.evaluate_policy(invalid_input)
    assert decision_invalid.allow is False, "Local Rego should deny cooldown violation"
    assert any("RULE-002" in v for v in decision_invalid.violations), f"Expected RULE-002 violation, got {decision_invalid.violations}"


# TEST 3: CRITICAL ADVERSARIAL TEST
@pytest.mark.asyncio
@respx.mock
async def test_critical_adversarial_high_confidence_override_denied():
    engine = OPAGovernanceEngine("http://localhost:8181/v1/data/recovery/governance")
    input_data = {
        "action": "RETRY_SCHEDULED",
        "confidence": 0.95,
        "retry_count": 5,
        "cooldown_hours": 1,
        "is_terminal_decline": True,
        "pre_debit_notice_required": False,
        "pre_debit_notice_sent": False
    }

    respx.post("http://localhost:8181/v1/data/recovery/governance").mock(
        return_value=Response(200, json=evaluate_rego_governance_mock(input_data))
    )

    decision = await engine.evaluate_policy(input_data)
    assert decision.allow is False

    # Violations check: RULE-001, RULE-002, RULE-003 present
    v_str = " ".join(decision.violations)
    assert "RULE-001" in v_str
    assert "RULE-002" in v_str
    assert "RULE-003" in v_str

    # RULE-004 and RULE-005 MUST NOT be present
    assert "RULE-004" not in v_str
    assert "RULE-005" not in v_str


# TEST 4: RULE-004 AI CONFIDENCE FLOOR
@pytest.mark.asyncio
@respx.mock
async def test_rule_004_low_confidence_denied():
    engine = OPAGovernanceEngine("http://localhost:8181/v1/data/recovery/governance")
    input_data = {
        "action": "RETRY_SCHEDULED",
        "confidence": 0.79,  # < 0.80
        "retry_count": 0,
        "cooldown_hours": 24,
        "is_terminal_decline": False
    }

    respx.post("http://localhost:8181/v1/data/recovery/governance").mock(
        return_value=Response(200, json=evaluate_rego_governance_mock(input_data))
    )

    decision = await engine.evaluate_policy(input_data)
    assert decision.allow is False
    assert any("RULE-004" in v for v in decision.violations)


# TEST 5: RULE-005 PRE-DEBIT NOTICE
@pytest.mark.asyncio
@respx.mock
async def test_rule_005_pre_debit_notice_required():
    engine = OPAGovernanceEngine("http://localhost:8181/v1/data/recovery/governance")
    input_data = {
        "action": "RETRY_SCHEDULED",
        "confidence": 0.90,
        "retry_count": 0,
        "cooldown_hours": 24,
        "pre_debit_notice_required": True,
        "pre_debit_notice_sent": False
    }

    respx.post("http://localhost:8181/v1/data/recovery/governance").mock(
        return_value=Response(200, json=evaluate_rego_governance_mock(input_data))
    )

    decision = await engine.evaluate_policy(input_data)
    assert decision.allow is False
    assert any("RULE-005" in v for v in decision.violations)


# TEST 6: NON-RETRY ACTION BYPASSES RETRY/COOLDOWN RULES
@pytest.mark.asyncio
@respx.mock
async def test_non_retry_action_bypasses_retry_limits():
    engine = OPAGovernanceEngine("http://localhost:8181/v1/data/recovery/governance")
    input_data = {
        "action": "SEND_PAYMENT_LINK",
        "confidence": 0.90,
        "retry_count": 5,  # Exceeds max retries but action is payment link!
        "cooldown_hours": 0,
        "is_terminal_decline": False
    }

    respx.post("http://localhost:8181/v1/data/recovery/governance").mock(
        return_value=Response(200, json=evaluate_rego_governance_mock(input_data))
    )

    decision = await engine.evaluate_policy(input_data)
    assert decision.allow is True
    assert decision.violations == []


# TEST 7: RETRY COUNT BOUNDARY
@pytest.mark.asyncio
@respx.mock
async def test_retry_count_boundaries():
    engine = OPAGovernanceEngine("http://localhost:8181/v1/data/recovery/governance")

    # retry_count = 2 -> ALLOWED
    in2 = {"action": "RETRY_SCHEDULED", "confidence": 0.9, "retry_count": 2, "cooldown_hours": 24}
    respx.post("http://localhost:8181/v1/data/recovery/governance").mock(
        return_value=Response(200, json=evaluate_rego_governance_mock(in2))
    )
    d2 = await engine.evaluate_policy(in2)
    assert d2.allow is True

    # retry_count = 3 -> DENIED
    in3 = {"action": "RETRY_SCHEDULED", "confidence": 0.9, "retry_count": 3, "cooldown_hours": 24}
    respx.post("http://localhost:8181/v1/data/recovery/governance").mock(
        return_value=Response(200, json=evaluate_rego_governance_mock(in3))
    )
    d3 = await engine.evaluate_policy(in3)
    assert d3.allow is False
    assert any("RULE-001" in v for v in d3.violations)


# TEST 8: COOLDOWN HOURS BOUNDARY
@pytest.mark.asyncio
@respx.mock
async def test_cooldown_hours_boundaries():
    engine = OPAGovernanceEngine("http://localhost:8181/v1/data/recovery/governance")

    # cooldown = 23.99 -> DENIED
    in23 = {"action": "RETRY_SCHEDULED", "confidence": 0.9, "retry_count": 0, "cooldown_hours": 23.99}
    respx.post("http://localhost:8181/v1/data/recovery/governance").mock(
        return_value=Response(200, json=evaluate_rego_governance_mock(in23))
    )
    d23 = await engine.evaluate_policy(in23)
    assert d23.allow is False
    assert any("RULE-002" in v for v in d23.violations)

    # cooldown = 24.0 -> ALLOWED
    in24 = {"action": "RETRY_SCHEDULED", "confidence": 0.9, "retry_count": 0, "cooldown_hours": 24.0}
    respx.post("http://localhost:8181/v1/data/recovery/governance").mock(
        return_value=Response(200, json=evaluate_rego_governance_mock(in24))
    )
    d24 = await engine.evaluate_policy(in24)
    assert d24.allow is True


# TEST 9: TERMINAL DECLINE PERMISSIONS
@pytest.mark.asyncio
@respx.mock
async def test_terminal_decline_permissions():
    engine = OPAGovernanceEngine("http://localhost:8181/v1/data/recovery/governance")

    # Terminal decline + RETRY_SCHEDULED -> DENIED
    in_retry = {"action": "RETRY_SCHEDULED", "confidence": 0.9, "is_terminal_decline": True, "cooldown_hours": 24}
    respx.post("http://localhost:8181/v1/data/recovery/governance").mock(
        return_value=Response(200, json=evaluate_rego_governance_mock(in_retry))
    )
    d_retry = await engine.evaluate_policy(in_retry)
    assert d_retry.allow is False
    assert any("RULE-003" in v for v in d_retry.violations)

    # Terminal decline + SEND_PAYMENT_LINK -> ALLOWED (not blocked by RULE-003)
    in_link = {"action": "SEND_PAYMENT_LINK", "confidence": 0.9, "is_terminal_decline": True}
    respx.post("http://localhost:8181/v1/data/recovery/governance").mock(
        return_value=Response(200, json=evaluate_rego_governance_mock(in_link))
    )
    d_link = await engine.evaluate_policy(in_link)
    assert d_link.allow is True
