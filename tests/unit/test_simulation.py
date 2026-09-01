"""
Phase 10 Unit & Evaluation Tests: 500-Case Recovery Simulator Engine
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.app.simulation.schemas import SimulationCase, SimulationResult, SimulationMetrics
from backend.app.simulation.generator import SimulationDataGenerator
from backend.app.simulation.evaluator import SimulationGovernanceEvaluator
from backend.app.simulation.engine import RecoverySimulationEngine


# TEST 1 — EXACTLY 500 CASES GENERATED
def test_simulation_generates_exact_case_count():
    engine = RecoverySimulationEngine(seed=42)
    result, metrics = engine.run(count=500)

    assert result.total_cases == 500
    assert sum(result.diagnosis_distribution.values()) == 500


# TEST 2 — DETERMINISTIC REPRODUCIBILITY
def test_simulation_reproducibility_same_seed():
    engine1 = RecoverySimulationEngine(seed=42)
    result1, metrics1 = engine1.run(count=500)

    engine2 = RecoverySimulationEngine(seed=42)
    result2, metrics2 = engine2.run(count=500)

    assert result1.model_dump() == result2.model_dump()
    assert metrics1.model_dump() == metrics2.model_dump()


# TEST 3 — DIFFERENT SEEDS PRODUCE DIFFERENT DATASETS
def test_simulation_different_seeds_produce_different_results():
    engine1 = RecoverySimulationEngine(seed=42)
    result1, _ = engine1.run(count=500)

    engine2 = RecoverySimulationEngine(seed=999)
    result2, _ = engine2.run(count=500)

    assert result1.total_revenue_at_risk_paise != result2.total_revenue_at_risk_paise
    assert result1.simulated_recovered_paise != result2.simulated_recovered_paise


# TEST 4 — ALL SIX FAILURE CATEGORIES REPRESENTED
def test_simulation_covers_all_failure_categories():
    engine = RecoverySimulationEngine(seed=42)
    result, _ = engine.run(count=500)

    expected_categories = {
        "LIQUIDITY_FRICTION",
        "TRANSIENT_INFRASTRUCTURE",
        "INSTRUMENT_INVALIDATION",
        "MANDATE_COMPLIANCE_LOCK",
        "BANK_RISK_BLOCK",
        "UNKNOWN",
    }

    assert set(result.diagnosis_distribution.keys()) == expected_categories
    for cat, count in result.diagnosis_distribution.items():
        assert count > 0


# TEST 5 — GOVERNANCE SAFETY & COMBINED ADVERSARIAL CASE
def test_governance_denies_combined_adversarial_case():
    adv_case = SimulationCase(
        case_id="sim_adv_01",
        payment_id="pay_adv_01",
        customer_id="cust_adv_01",
        amount_paise=100000,
        failure_category="LIQUIDITY_FRICTION",
        retry_count=5,  # Exceeds max retries
        cooldown_hours=1.0,  # Cooldown violation
        is_terminal_decline=True,  # Terminal decline
        confidence=0.99,  # High AI confidence
        proposed_action="RETRY_SCHEDULED"
    )

    allow, violations = SimulationGovernanceEvaluator.evaluate_case(adv_case)

    assert allow is False
    assert any("RULE-001" in v for v in violations)
    assert any("RULE-002" in v for v in violations)
    assert any("RULE-003" in v for v in violations)


# TEST 6 — LOW AI CONFIDENCE DENIED
def test_governance_denies_low_ai_confidence():
    case = SimulationCase(
        case_id="sim_low_conf",
        payment_id="pay_low_conf",
        customer_id="cust_low_conf",
        amount_paise=50000,
        failure_category="LIQUIDITY_FRICTION",
        retry_count=0,
        cooldown_hours=48.0,
        is_terminal_decline=False,
        confidence=0.50,  # Below 0.80 floor
        proposed_action="RETRY_SCHEDULED"
    )

    allow, violations = SimulationGovernanceEvaluator.evaluate_case(case)

    assert allow is False
    assert any("RULE-004" in v for v in violations)


# TEST 7 — TERMINAL DECLINE PROHIBITED FROM AUTOMATIC RETRY
def test_governance_prohibits_terminal_decline_retry():
    case = SimulationCase(
        case_id="sim_term",
        payment_id="pay_term",
        customer_id="cust_term",
        amount_paise=50000,
        failure_category="INSTRUMENT_INVALIDATION",
        retry_count=0,
        cooldown_hours=48.0,
        is_terminal_decline=True,
        confidence=0.95,
        proposed_action="RETRY_SCHEDULED"
    )

    allow, violations = SimulationGovernanceEvaluator.evaluate_case(case)

    assert allow is False
    assert any("RULE-003" in v for v in violations)


# TEST 8 — DUPLICATE IDEMPOTENCY & ZERO DOUBLE RECOVERIES
def test_simulation_prevents_double_recoveries():
    engine = RecoverySimulationEngine(seed=42)
    result, _ = engine.run(count=500, inject_duplicates=True)

    assert result.duplicate_event_count > 0
    assert result.double_recovery_count == 0


# TEST 9 — MONETARY SAFETY INVARIANT
def test_simulation_monetary_safety_invariant():
    engine = RecoverySimulationEngine(seed=42)
    result, _ = engine.run(count=500)

    assert result.simulated_recovered_paise <= result.total_revenue_at_risk_paise
    assert result.simulated_recovered_paise >= 0


# TEST 10 — NO REAL RECOVERED MUTATIONS
def test_simulation_does_not_mutate_real_db_cases():
    engine = RecoverySimulationEngine(seed=42)
    result, _ = engine.run(count=500)

    assert result.unsafe_recovery_claim_count == 0


# TEST 11 — ZERO PRODUCTION OUTBOUND API CALLS
@patch("httpx.AsyncClient.post")
def test_simulation_makes_zero_external_api_calls(mock_post):
    engine = RecoverySimulationEngine(seed=42)
    engine.run(count=500)

    assert not mock_post.called


# TEST 12 — DETERMINISTIC METRICS VERIFICATION
def test_simulation_metrics_reproducibility():
    engine = RecoverySimulationEngine(seed=42)
    result1, metrics1 = engine.run(count=500)
    result2, metrics2 = engine.run(count=500)

    assert metrics1.governance_pass_rate == metrics2.governance_pass_rate
    assert metrics1.simulated_recovery_rate == metrics2.simulated_recovery_rate
    assert metrics1.revenue_recovery_rate == metrics2.revenue_recovery_rate
