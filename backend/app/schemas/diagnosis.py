"""
Pydantic Schemas & Enums for Failure Diagnosis & Revenue-at-Risk Engine
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class FailureCategory(str, Enum):
    LIQUIDITY_FRICTION = "LIQUIDITY_FRICTION"
    TRANSIENT_INFRASTRUCTURE = "TRANSIENT_INFRASTRUCTURE"
    INSTRUMENT_INVALIDATION = "INSTRUMENT_INVALIDATION"
    MANDATE_COMPLIANCE_LOCK = "MANDATE_COMPLIANCE_LOCK"
    BANK_RISK_BLOCK = "BANK_RISK_BLOCK"
    UNKNOWN = "UNKNOWN"


class PriorityTier(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DiagnosisResult(BaseModel):
    category: FailureCategory = Field(..., description="Deterministic failure taxonomy category")
    normalized_code: str = Field(..., description="Normalized error code string")
    reason: Optional[str] = Field(None, description="Granular error reason")
    source: Optional[str] = Field(None, description="Error source (e.g. bank, gateway, customer)")
    step: Optional[str] = Field(None, description="Processing step where failure occurred")
    confidence: float = Field(default=1.0, description="Classification confidence (1.0 for deterministic rules)")


class RiskAssessment(BaseModel):
    revenue_at_risk_paise: int = Field(..., description="Face value revenue at risk in integer paise")
    amount_inr_formatted: str = Field(..., description="Formatted INR currency string for UI display")
    priority_tier: PriorityTier = Field(..., description="Deterministic priority assignment (HIGH, MEDIUM, LOW)")
    priority_score: float = Field(..., description="Calculated composite risk score (0 - 100)")

    @field_validator("revenue_at_risk_paise")
    @classmethod
    def validate_non_negative_paise(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Revenue at risk paise cannot be negative.")
        return value
