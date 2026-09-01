"""
Pydantic Schemas for Razorpay Webhook Events & Internal Representations.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class WebhookResponse(BaseModel):
    status: str = Field(default="accepted", description="Status of webhook processing")
    event: Optional[str] = Field(default=None, description="Extracted Razorpay event name")
    duplicate: bool = Field(default=False, description="Indicates if event was already processed (idempotent)")


class NormalizedEvent(BaseModel):
    event_type: str = Field(..., description="Razorpay event type, e.g. payment.failed")
    event_id: Optional[str] = Field(None, description="Top-level event ID if provided by Razorpay")
    created_at: Optional[int] = Field(None, description="Event timestamp in epoch seconds")
    account_id: Optional[str] = Field(None, description="Razorpay merchant account ID")
    entity_ids: Dict[str, Optional[str]] = Field(default_factory=dict, description="Extracted entity IDs")
    payment_details: Optional[Dict[str, Any]] = Field(None, description="Extracted payment details if available")
