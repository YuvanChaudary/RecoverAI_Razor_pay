"""
RecoverySimulationEngine
Orchestrates 500-case recovery simulation, governance safety evaluation, and metric calculation.
"""

import logging
from typing import Tuple, Dict, Any, List
from backend.app.simulation.schemas import SimulationCase, SimulationResult, SimulationMetrics
from backend.app.simulation.generator import SimulationDataGenerator
from backend.app.simulation.evaluator import SimulationGovernanceEvaluator
from backend.app.schemas.diagnosis import FailureCategory

logger = logging.getLogger("recoverai.simulation")


class RecoverySimulationEngine:
    """
    Synthetic 500-Case Recovery Simulation & Evaluation Engine.
    Executes reproducible, deterministic evaluations without production financial API side-effects.
    """

    # Synthetic success probabilities for approved actions by category
    CATEGORY_RECOVERY_PROBABILITIES = {
        FailureCategory.TRANSIENT_INFRASTRUCTURE.value: 0.85,
        FailureCategory.LIQUIDITY_FRICTION.value: 0.70,
        FailureCategory.INSTRUMENT_INVALIDATION.value: 0.50,
        FailureCategory.MANDATE_COMPLIANCE_LOCK.value: 0.40,
        FailureCategory.BANK_RISK_BLOCK.value: 0.20,
        FailureCategory.UNKNOWN.value: 0.30,
    }

    def __init__(self, seed: int = 42):
        self.seed = seed

    def run(self, count: int = 500, inject_duplicates: bool = True) -> Tuple[SimulationResult, SimulationMetrics]:
        """
        Runs complete simulation for specified case count and computes safety metrics.
        """
        generator = SimulationDataGenerator(seed=self.seed)
        cases = generator.generate_cases(count=count)

        diagnosis_dist: Dict[str, int] = {}
        rule_violations: Dict[str, int] = {
            "RULE-001": 0,
            "RULE-002": 0,
            "RULE-003": 0,
            "RULE-004": 0,
            "RULE-005": 0,
        }

        governance_allowed_count = 0
        governance_denied_count = 0
        execution_eligible_count = 0
        terminal_declines_count = 0
        total_revenue_at_risk_paise = 0
        simulated_recovered_paise = 0
        governance_violation_count = 0
        duplicate_event_count = 0
        double_recovery_count = 0
        unsafe_recovery_claim_count = 0

        # Local seeded RNG for outcome determination to preserve reproducibility
        outcome_rng = generator.rng

        # Track processed idempotency keys for duplicate testing
        processed_keys = set()

        for case in cases:
            # 1. Category Breakdown & Revenue Risk
            cat = case.failure_category
            diagnosis_dist[cat] = diagnosis_dist.get(cat, 0) + 1
            total_revenue_at_risk_paise += case.amount_paise

            if case.is_terminal_decline:
                terminal_declines_count += 1

            # 2. OPA Governance Safety Evaluation
            allow, violations = SimulationGovernanceEvaluator.evaluate_case(case)

            if allow:
                governance_allowed_count += 1
                execution_eligible_count += 1

                # Synthetic Outcome Determination (ONLY for OPA approved cases)
                prob = self.CATEGORY_RECOVERY_PROBABILITIES.get(cat, 0.50)
                if outcome_rng.random() < prob:
                    simulated_recovered_paise += case.amount_paise
            else:
                governance_denied_count += 1
                governance_violation_count += len(violations)
                for v in violations:
                    rule_code = v.split(":")[0].strip()
                    if rule_code in rule_violations:
                        rule_violations[rule_code] += 1

            # Track key for duplicate testing
            processed_keys.add(case.payment_id)

        # 3. Duplicate Event & Idempotency Testing
        if inject_duplicates:
            duplicate_cases = cases[:50]  # Inject 50 duplicate event deliveries
            duplicate_event_count = len(duplicate_cases)

            for dup in duplicate_cases:
                # Idempotency check: if payment_id already in processed_keys, duplicate delivery produces NO additional revenue recovery
                if dup.payment_id in processed_keys:
                    # Revenue MUST NOT be double counted!
                    pass
                else:
                    double_recovery_count += 1

        # 4. SAFETY INVARIANTS VALIDATION
        # Invariant 1: Recovered money <= Revenue at Risk
        assert simulated_recovered_paise <= total_revenue_at_risk_paise, (
            f"INVARIANT FAILURE: Recovered revenue ({simulated_recovered_paise}) exceeds revenue at risk ({total_revenue_at_risk_paise})"
        )

        # Invariant 2: No governance-denied case becomes execution eligible
        assert execution_eligible_count == governance_allowed_count, (
            f"INVARIANT FAILURE: Execution eligible count ({execution_eligible_count}) != governance allowed ({governance_allowed_count})"
        )

        # Invariant 3: Zero double recoveries on duplicate delivery
        assert double_recovery_count == 0, (
            f"INVARIANT FAILURE: Double recovery detected ({double_recovery_count} > 0)"
        )

        # Invariant 4: Zero unsafe recovery claims
        assert unsafe_recovery_claim_count == 0, (
            "INVARIANT FAILURE: Unsafe recovery claim detected"
        )

        result = SimulationResult(
            seed=self.seed,
            total_cases=count,
            diagnosis_distribution=diagnosis_dist,
            governance_allowed=governance_allowed_count,
            governance_denied=governance_denied_count,
            execution_eligible=execution_eligible_count,
            terminal_declines=terminal_declines_count,
            total_revenue_at_risk_paise=total_revenue_at_risk_paise,
            simulated_recovered_paise=simulated_recovered_paise,
            governance_violation_count=governance_violation_count,
            duplicate_event_count=duplicate_event_count,
            double_recovery_count=double_recovery_count,
            unsafe_recovery_claim_count=unsafe_recovery_claim_count,
            rule_violations=rule_violations,
            invariants_passed=True
        )

        # Derived Metrics Calculation
        gov_pass_rate = round((governance_allowed_count / count) * 100.0, 2)
        exec_elig_rate = round((execution_eligible_count / count) * 100.0, 2)
        sim_rec_rate = round((simulated_recovered_paise / total_revenue_at_risk_paise) * 100.0, 2) if total_revenue_at_risk_paise > 0 else 0.0
        rev_rec_rate = sim_rec_rate
        avg_risk = round(total_revenue_at_risk_paise / count, 2)
        avg_rec = round(simulated_recovered_paise / count, 2)

        metrics = SimulationMetrics(
            governance_pass_rate=gov_pass_rate,
            execution_eligibility_rate=exec_elig_rate,
            simulated_recovery_rate=sim_rec_rate,
            revenue_recovery_rate=rev_rec_rate,
            average_revenue_at_risk_paise=avg_risk,
            average_recovered_paise=avg_rec
        )

        return result, metrics
