"""
Deterministic Revenue-at-Risk & Priority Scoring Engine
Calculates monetary risk in integer paise and evaluates priority tiers.
"""

import logging
from backend.app.schemas.diagnosis import FailureCategory, PriorityTier, RiskAssessment

logger = logging.getLogger("recoverai.risk_service")


class RiskService:
    """
    Deterministic Revenue-at-Risk Engine.
    Ensures 100% integer paise monetary integrity and reproducible priority scoring.
    """

    HIGH_THRESHOLD_PAISE = 500000    # ₹5,000.00
    MEDIUM_THRESHOLD_PAISE = 100000  # ₹1,000.00

    HIGH_SCORE_CUTOFF = 70.0
    MEDIUM_SCORE_CUTOFF = 40.0

    @staticmethod
    def format_inr(amount_paise: int) -> str:
        """Formats integer paise into standard INR currency string."""
        inr_val = amount_paise / 100.0
        return f"₹{inr_val:,.2f}"

    @classmethod
    def calculate_priority_score(
        cls,
        amount_paise: int,
        category: FailureCategory,
        retry_count: int = 0
    ) -> float:
        """
        Calculates a deterministic priority score between 0.0 and 100.0 based on:
        1. Monetary Component (max 50 pts)
        2. Failure Recovery Component (max 30 pts)
        3. Retry Recency Component (max 20 pts)
        """
        # 1. Monetary Component
        if amount_paise >= cls.HIGH_THRESHOLD_PAISE:
            monetary_score = 50.0
        elif amount_paise >= cls.MEDIUM_THRESHOLD_PAISE:
            monetary_score = 30.0
        else:
            monetary_score = 10.0

        # 2. Failure Category Component
        if category in (FailureCategory.LIQUIDITY_FRICTION, FailureCategory.TRANSIENT_INFRASTRUCTURE):
            category_score = 30.0
        elif category == FailureCategory.MANDATE_COMPLIANCE_LOCK:
            category_score = 20.0
        elif category in (FailureCategory.BANK_RISK_BLOCK, FailureCategory.INSTRUMENT_INVALIDATION):
            category_score = 10.0
        else:
            category_score = 0.0

        # 3. Retry History Component
        if retry_count == 0:
            retry_score = 20.0
        elif retry_count in (1, 2):
            retry_score = 10.0
        else:
            retry_score = 0.0

        total_score = min(100.0, max(0.0, monetary_score + category_score + retry_score))
        return total_score

    @classmethod
    def assess_risk(
        cls,
        amount_paise: int,
        category: FailureCategory,
        retry_count: int = 0
    ) -> RiskAssessment:
        """
        Performs Revenue-at-Risk assessment and assigns deterministic PriorityTier.
        """
        if amount_paise < 0:
            raise ValueError(f"Invalid monetary value: amount_paise={amount_paise} cannot be negative.")

        score = cls.calculate_priority_score(amount_paise, category, retry_count)

        if score >= cls.HIGH_SCORE_CUTOFF:
            tier = PriorityTier.HIGH
        elif score >= cls.MEDIUM_SCORE_CUTOFF:
            tier = PriorityTier.MEDIUM
        else:
            tier = PriorityTier.LOW

        inr_str = cls.format_inr(amount_paise)

        logger.info(
            f"Risk Assessment Calculated: amount_paise={amount_paise} ({inr_str}), "
            f"category='{category.value}', priority_tier='{tier.value}', priority_score={score}"
        )

        return RiskAssessment(
            revenue_at_risk_paise=amount_paise,
            amount_inr_formatted=inr_str,
            priority_tier=tier,
            priority_score=score,
        )
