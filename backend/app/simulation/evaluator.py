"""
Governance Safety Evaluator for Simulation Engine
Evaluates OPA Rego Rules (RULE-001 through RULE-005) against synthetic cases.
"""

from typing import Tuple, List
from backend.app.simulation.schemas import SimulationCase


class SimulationGovernanceEvaluator:
    """
    Evaluates OPA governance rules deterministically for simulation evaluation.
    Matches backend/policies/governance.rego rules.
    """

    MAX_RETRIES = 3
    MIN_COOLDOWN_HOURS = 24.0
    MIN_CONFIDENCE_FLOOR = 0.80

    @classmethod
    def evaluate_case(cls, case: SimulationCase) -> Tuple[bool, List[str]]:
        """
        Evaluates a synthetic simulation case against OPA governance rules.
        Returns:
            Tuple[bool, List[str]]: (allow: bool, violations: List[str])
        """
        violations = []
        action = case.proposed_action

        # Non-retry actions (SEND_PAYMENT_LINK, CUSTOMER_REMINDER) bypass retry limits, cooldown & terminal decline rules
        if action == "RETRY_SCHEDULED":
            # RULE-001: Maximum Retry Attempts Exceeded
            if case.retry_count >= cls.MAX_RETRIES:
                violations.append(f"RULE-001: Maximum retries exceeded ({case.retry_count} >= {cls.MAX_RETRIES})")

            # RULE-002: Insufficient Cooldown Window
            if case.cooldown_hours < cls.MIN_COOLDOWN_HOURS:
                violations.append(f"RULE-002: Cooldown violation ({case.cooldown_hours:.1f}h < {cls.MIN_COOLDOWN_HOURS}h)")

            # RULE-003: Terminal Failure Decline
            if case.is_terminal_decline:
                violations.append("RULE-003: Terminal decline prohibited from retry execution")

            # RULE-004: AI Confidence Floor Violation
            if case.confidence < cls.MIN_CONFIDENCE_FLOOR:
                violations.append(f"RULE-004: Low AI confidence ({case.confidence} < {cls.MIN_CONFIDENCE_FLOOR})")

            # RULE-005: Missing Pre-Debit Notice
            if case.pre_debit_notice_required and not case.pre_debit_notice_sent:
                violations.append("RULE-005: Pre-debit notice required but not sent")

        # Default fail-closed: allow = True ONLY if zero violations exist
        allow = len(violations) == 0
        return allow, violations
