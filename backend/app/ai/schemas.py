"""
Pydantic Schemas & Enums for NVIDIA NIM AI Decision Engine
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ActionEnum(str, Enum):
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    SEND_PAYMENT_LINK = "SEND_PAYMENT_LINK"
    CUSTOMER_REMINDER = "CUSTOMER_REMINDER"
    NO_AUTOMATED_ACTION = "NO_AUTOMATED_ACTION"


class TimingEnum(str, Enum):
    IMMEDIATE = "IMMEDIATE"
    AFTER_PAYDAY = "AFTER_PAYDAY"
    DELAYED = "DELAYED"
    NONE = "NONE"


class MessageStrategyEnum(str, Enum):
    FORMAL = "FORMAL"
    CONCISE = "CONCISE"
    HINGLISH = "HINGLISH"
    NONE = "NONE"


class RecoveryContext(BaseModel):
    amount_paise: int = Field(..., description="Face value revenue at risk in integer paise")
    failure_category: str = Field(..., description="Diagnosed failure category (e.g. LIQUIDITY_FRICTION)")
    priority_tier: str = Field(..., description="Priority tier (HIGH, MEDIUM, LOW)")
    priority_score: float = Field(..., description="Priority score (0-100)")
    retry_count: int = Field(default=0, description="Current retry count")
    customer_tier: str = Field(default="STANDARD", description="Customer tier")
    payday_day_of_month: int = Field(default=1, description="Payday day of month (1-31)")
    untrusted_customer_note: Optional[str] = Field(default=None, description="Untrusted customer note or memo")


class ProposedRecoveryPlan(BaseModel):
    recommended_action: ActionEnum = Field(..., description="Proposed candidate recovery action")
    delay_hours: int = Field(default=0, ge=0, le=168, description="Proposed delay in hours (0 to 168)")
    timing: TimingEnum = Field(..., description="Timing strategy")
    message_strategy: MessageStrategyEnum = Field(..., description="Messaging tone & style strategy")
    dunning_message: Optional[str] = Field(default=None, description="Generated dunning message text if applicable")
    reasoning_summary: str = Field(..., description="Contextual reasoning summary supporting proposal")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence score (0.0 to 1.0)")
    is_fallback: bool = Field(default=False, description="Flag indicating if proposal is a deterministic fallback")

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0.")
        return round(v, 4)
