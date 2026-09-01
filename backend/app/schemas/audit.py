"""
Pydantic Schemas for immudb Immutable Audit Trail Events & Verifications
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator


class AuditEvent(BaseModel):
    """
    Strongly-typed Audit Event for RecoverAI.
    Distinguishes proposed actions and execution attempts from final settlement.
    Never determines financial recovery state.
    """
    event_id: str = Field(..., description="Unique audit event identifier")
    event_type: str = Field(..., description="Type of audit event (e.g. FAILURE_DIAGNOSED, GOVERNANCE_DECISION)")
    occurred_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp"
    )
    recovery_case_id: str = Field(..., description="Associated RecoveryCase identifier")
    payment_id: str = Field(..., description="Associated Razorpay payment identifier")
    failure_category: Optional[str] = Field(None, description="Diagnosed failure category")
    risk_tier: Optional[str] = Field(None, description="Assessed risk tier")
    priority_score: Optional[float] = Field(None, description="Assessed priority score")
    recommended_action: Optional[str] = Field(None, description="Proposed AI recommendation")
    governance_allowed: Optional[bool] = Field(None, description="OPA governance policy decision")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key")
    actor: str = Field(default="RecoverAI Engine", description="Audit event source/actor")
    execution_status: Optional[str] = Field(None, description="Neutral action execution status (e.g. ATTEMPTED, EXECUTED, DENIED)")
    payload_hash: Optional[str] = Field(None, description="SHA-256 hash of canonical payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional audit metadata")

    @model_validator(mode="after")
    def validate_no_false_recovery(self) -> "AuditEvent":
        """
        Fintech Safety Enforcement:
        Audit layer records observed actions/decisions but NEVER claims financial recovery.
        """
        if self.execution_status and self.execution_status.upper() == "RECOVERED":
            raise ValueError("Audit execution_status must never be set to 'RECOVERED'. Authoritative recovery occurs only via settlement webhooks.")
        return self

    def to_canonical_json(self) -> str:
        """
        Computes deterministic JSON string representation for SHA-256 hashing.
        Excludes payload_hash itself.
        """
        data = self.model_dump(exclude={"payload_hash"}, mode="json")
        return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def compute_hash(self) -> str:
        """
        Computes SHA-256 hash of the canonical JSON string.
        """
        canonical = self.to_canonical_json()
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class AuditVerificationResult(BaseModel):
    """
    Result payload for audit event cryptographic verification.
    """
    valid: bool = Field(..., description="True if calculated hash matches stored payload_hash")
    event_id: str = Field(..., description="Audit event identifier")
    stored_hash: str = Field(..., description="SHA-256 hash retrieved from immudb")
    calculated_hash: str = Field(..., description="SHA-256 hash recalculated from canonical JSON")
    details: Optional[str] = Field(None, description="Verification detail message")
