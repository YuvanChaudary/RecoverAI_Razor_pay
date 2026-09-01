"""
Deterministic Synthetic Data Generator for 500-Case Recovery Simulation
"""

import random
from typing import List
from backend.app.simulation.schemas import SimulationCase
from backend.app.schemas.diagnosis import FailureCategory


class SimulationDataGenerator:
    """
    Local Seeded Random Generator for RecoverAI Simulation.
    Guarantees 100% deterministic reproducibility for any given seed + count pair.
    """

    CATEGORIES = [
        FailureCategory.LIQUIDITY_FRICTION.value,
        FailureCategory.TRANSIENT_INFRASTRUCTURE.value,
        FailureCategory.INSTRUMENT_INVALIDATION.value,
        FailureCategory.MANDATE_COMPLIANCE_LOCK.value,
        FailureCategory.BANK_RISK_BLOCK.value,
        FailureCategory.UNKNOWN.value,
    ]

    CATEGORY_WEIGHTS = [0.40, 0.20, 0.15, 0.10, 0.10, 0.05]
    CUSTOMER_TIERS = ["STANDARD", "PREMIUM", "VIP"]
    PROPOSED_ACTIONS = ["RETRY_SCHEDULED", "SEND_PAYMENT_LINK", "CUSTOMER_REMINDER", "NO_AUTOMATED_ACTION"]

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_cases(self, count: int = 500) -> List[SimulationCase]:
        """
        Generates synthetic failed payment cases with controlled adversarial distribution.
        """
        cases = []

        for i in range(1, count + 1):
            case_id = f"sim_case_{i:04d}"
            payment_id = f"pay_sim_{i:04d}"
            customer_id = f"cust_sim_{self.rng.randint(100, 250):03d}"

            # Amount in integer paise (₹500 to ₹100,000)
            amount_paise = self.rng.randint(50000, 10000000)

            # Category selection based on weights
            category = self.rng.choices(self.CATEGORIES, weights=self.CATEGORY_WEIGHTS, k=1)[0]

            # Scenario selection: 60% valid happy path, 40% adversarial/governance-violating
            scenario_type = self.rng.random()

            if scenario_type < 0.60:
                # Normal Valid Case
                retry_count = self.rng.randint(0, 2)
                cooldown_hours = self.rng.uniform(24.5, 72.0)
                is_terminal_decline = False
                confidence = round(self.rng.uniform(0.82, 0.98), 2)
                pre_debit_required = False
                pre_debit_sent = False
                proposed_action = self.rng.choice(["RETRY_SCHEDULED", "SEND_PAYMENT_LINK", "CUSTOMER_REMINDER"])
            elif scenario_type < 0.70:
                # Retry Limit Violation
                retry_count = self.rng.randint(3, 6)
                cooldown_hours = self.rng.uniform(25.0, 48.0)
                is_terminal_decline = False
                confidence = round(self.rng.uniform(0.80, 0.95), 2)
                pre_debit_required = False
                pre_debit_sent = False
                proposed_action = "RETRY_SCHEDULED"
            elif scenario_type < 0.80:
                # Cooldown Window Violation
                retry_count = self.rng.randint(0, 2)
                cooldown_hours = round(self.rng.uniform(1.0, 23.5), 1)
                is_terminal_decline = False
                confidence = round(self.rng.uniform(0.80, 0.95), 2)
                pre_debit_required = False
                pre_debit_sent = False
                proposed_action = "RETRY_SCHEDULED"
            elif scenario_type < 0.88:
                # Terminal Decline Violation
                retry_count = self.rng.randint(0, 2)
                cooldown_hours = 48.0
                is_terminal_decline = True
                confidence = round(self.rng.uniform(0.80, 0.99), 2)
                pre_debit_required = False
                pre_debit_sent = False
                proposed_action = "RETRY_SCHEDULED"
            elif scenario_type < 0.94:
                # Low AI Confidence
                retry_count = 0
                cooldown_hours = 48.0
                is_terminal_decline = False
                confidence = round(self.rng.uniform(0.30, 0.78), 2)
                pre_debit_required = False
                pre_debit_sent = False
                proposed_action = "RETRY_SCHEDULED"
            else:
                # Pre-debit Notice Missing
                retry_count = 0
                cooldown_hours = 48.0
                is_terminal_decline = False
                confidence = round(self.rng.uniform(0.85, 0.95), 2)
                pre_debit_required = True
                pre_debit_sent = False
                proposed_action = "RETRY_SCHEDULED"

            customer_tier = self.rng.choice(self.CUSTOMER_TIERS)
            payday_day = self.rng.randint(1, 28)

            case = SimulationCase(
                case_id=case_id,
                payment_id=payment_id,
                customer_id=customer_id,
                amount_paise=amount_paise,
                failure_category=category,
                retry_count=retry_count,
                cooldown_hours=cooldown_hours,
                is_terminal_decline=is_terminal_decline,
                confidence=confidence,
                customer_tier=customer_tier,
                payday_day_of_month=payday_day,
                pre_debit_notice_required=pre_debit_required,
                pre_debit_notice_sent=pre_debit_sent,
                proposed_action=proposed_action
            )
            cases.append(case)

        return cases
