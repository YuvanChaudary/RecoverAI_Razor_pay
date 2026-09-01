"""
Pydantic Schemas for 500-Case Recovery Simulation & Evaluation Engine
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class SimulationCase(BaseModel):
    """
    Synthetic Failed Payment Case for Simulation.
    Monetary amounts strictly stored in integer paise.
    """
    case_id: str = Field(..., description="Synthetic case identifier")
    payment_id: str = Field(..., description="Synthetic payment identifier")
    customer_id: str = Field(..., description="Synthetic customer identifier")
    amount_paise: int = Field(..., description="Payment amount in integer paise")
    failure_category: str = Field(..., description="Diagnosed failure category")
    retry_count: int = Field(..., description="Current retry attempt count")
    cooldown_hours: float = Field(..., description="Hours elapsed since last attempt")
    is_terminal_decline: bool = Field(..., description="Flag indicating hard/terminal decline")
    confidence: float = Field(..., description="Simulated AI model confidence score")
    customer_tier: str = Field(default="STANDARD", description="Customer tier")
    payday_day_of_month: int = Field(default=1, description="Payday day of month")
    pre_debit_notice_required: bool = Field(default=False, description="Flag for pre-debit notice requirement")
    pre_debit_notice_sent: bool = Field(default=False, description="Flag for pre-debit notice sent")
    proposed_action: str = Field(default="RETRY_SCHEDULED", description="Proposed AI recommendation")


class SimulationResult(BaseModel):
    """
    Aggregated Output Payload of a Simulation Run.
    """
    seed: int = Field(..., description="Random seed used for generation")
    total_cases: int = Field(..., description="Total synthetic cases evaluated")
    diagnosis_distribution: Dict[str, int] = Field(..., description="Category breakdown count")
    governance_allowed: int = Field(..., description="Cases approved by OPA governance")
    governance_denied: int = Field(..., description="Cases blocked by OPA governance")
    execution_eligible: int = Field(..., description="Cases eligible for automated action")
    terminal_declines: int = Field(..., description="Cases identified as terminal declines")
    total_revenue_at_risk_paise: int = Field(..., description="Total revenue at risk in integer paise")
    simulated_recovered_paise: int = Field(..., description="Simulated recovered revenue in integer paise")
    governance_violation_count: int = Field(..., description="Total rule violation instances")
    duplicate_event_count: int = Field(default=0, description="Total duplicate events tested")
    double_recovery_count: int = Field(default=0, description="Total double recoveries detected (must be 0)")
    unsafe_recovery_claim_count: int = Field(default=0, description="Total unsafe recovery claims (must be 0)")
    rule_violations: Dict[str, int] = Field(default_factory=dict, description="Breakdown by OPA rule ID")
    invariants_passed: bool = Field(default=True, description="True if all safety invariants passed")


class SimulationMetrics(BaseModel):
    """
    Derived Performance & Safety Metrics for Evaluation.
    """
    governance_pass_rate: float = Field(..., description="Percentage of cases passing OPA governance")
    execution_eligibility_rate: float = Field(..., description="Percentage of cases eligible for execution")
    simulated_recovery_rate: float = Field(..., description="Percentage of approved cases synthetically recovered")
    revenue_recovery_rate: float = Field(..., description="Percentage of total revenue at risk synthetically recovered")
    average_revenue_at_risk_paise: float = Field(..., description="Average revenue at risk per case in paise")
    average_recovered_paise: float = Field(..., description="Average recovered amount per case in paise")
