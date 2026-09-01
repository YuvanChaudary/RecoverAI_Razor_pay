"""
Pydantic Schemas for Authoritative Recovery Case State Machine
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field


class CaseStateEnum(str, Enum):
    """
    Authoritative RecoveryCase Lifecycle States
    """
    DETECTED = "DETECTED"
    DIAGNOSED = "DIAGNOSED"
    GOVERNANCE_APPROVED = "GOVERNANCE_APPROVED"
    ACTION_SCHEDULED = "ACTION_SCHEDULED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    AWAITING_SETTLEMENT = "AWAITING_SETTLEMENT"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class CaseEventEnum(str, Enum):
    """
    State Transition Trigger Events
    """
    FAILURE_DIAGNOSED = "FAILURE_DIAGNOSED"
    GOVERNANCE_ALLOWED = "GOVERNANCE_ALLOWED"
    GOVERNANCE_DENIED = "GOVERNANCE_DENIED"
    ACTION_SCHEDULED = "ACTION_SCHEDULED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    SETTLEMENT_AWAITING = "SETTLEMENT_AWAITING"
    PAYMENT_CAPTURED = "PAYMENT_CAPTURED"
    PAYMENT_FAILED = "PAYMENT_FAILED"


class StateTransitionRequest(BaseModel):
    """
    Request payload for executing a state transition.
    """
    case_id: str = Field(..., description="RecoveryCase identifier")
    event: CaseEventEnum = Field(..., description="Triggering transition event")
    evidence: Optional[Dict[str, Any]] = Field(None, description="Authoritative settlement evidence or execution payload")
    ai_confidence: Optional[float] = Field(None, description="AI recommendation confidence score")
    opa_allowed: Optional[bool] = Field(None, description="OPA governance permission status")


class StateTransitionResult(BaseModel):
    """
    Strongly-typed result returned by RecoveryStateMachine.
    """
    success: bool = Field(..., description="True if state transition was valid and applied")
    case_id: str = Field(..., description="RecoveryCase identifier")
    previous_state: str = Field(..., description="State before transition attempt")
    new_state: str = Field(..., description="State after transition attempt")
    event: str = Field(..., description="Triggering event name")
    reason: str = Field(default="", description="Transition explanation or error message")
    idempotent: bool = Field(default=False, description="True if no-op duplicate delivery")
    recovered_amount_paise: int = Field(default=0, description="Amount recovered in integer paise if RECOVERED")
