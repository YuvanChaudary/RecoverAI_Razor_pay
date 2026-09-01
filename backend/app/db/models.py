"""
SQLAlchemy Domain Models for RecoverAI Operational Data Store
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    BigInteger,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from backend.app.db.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class WebhookEvent(Base):
    """Raw & Normalized Razorpay Webhook Ingestion Records"""
    __tablename__ = "webhook_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(100), unique=True, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    signature_verified = Column(Boolean, default=True, nullable=False)
    processed = Column(Boolean, default=False, nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_webhook_events_type_processed", "event_type", "processed"),
    )


class Customer(Base):
    """Merchant Customer Profile & Historical Payday Performance"""
    __tablename__ = "customers"

    customer_id = Column(String(100), primary_key=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    name = Column(String(255), nullable=True)
    customer_tier = Column(String(50), default="STANDARD", nullable=False)
    payday_day_of_month = Column(BigInteger, default=1, nullable=False)
    total_subscriptions_count = Column(BigInteger, default=0, nullable=False)
    historical_successful_recoveries = Column(BigInteger, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    payments = relationship("Payment", back_populates="customer")
    cases = relationship("RecoveryCase", back_populates="customer")


class Payment(Base):
    """Razorpay Gateway Payment Attempt Transactions"""
    __tablename__ = "payments"

    payment_id = Column(String(100), primary_key=True)
    customer_id = Column(String(100), ForeignKey("customers.customer_id"), nullable=True, index=True)
    subscription_id = Column(String(100), nullable=True, index=True)
    invoice_id = Column(String(100), nullable=True, index=True)
    amount_paise = Column(BigInteger, nullable=False)  # Integer paise (e.g., ₹499.00 -> 49900)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(50), nullable=False, index=True)
    method = Column(String(50), nullable=True)
    error_code = Column(String(100), nullable=True, index=True)
    error_reason = Column(String(255), nullable=True)
    error_source = Column(String(100), nullable=True)
    error_step = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    customer = relationship("Customer", back_populates="payments")
    cases = relationship("RecoveryCase", back_populates="payment")
    attempts = relationship("PaymentAttempt", back_populates="payment")


class PaymentAttempt(Base):
    """Granular Retries and Execution Attempt Audit Log per Payment"""
    __tablename__ = "payment_attempts"

    attempt_id = Column(String(100), primary_key=True, default=lambda: f"att_{uuid.uuid4().hex[:12]}")
    payment_id = Column(String(100), ForeignKey("payments.payment_id"), nullable=False, index=True)
    attempt_number = Column(BigInteger, nullable=False)
    action_type = Column(String(100), nullable=False)
    provider_response = Column(JSON, nullable=True)
    provider_reference = Column(String(100), nullable=True)
    outcome = Column(String(50), nullable=False)
    attempted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    payment = relationship("Payment", back_populates="attempts")


class Subscription(Base):
    """Razorpay Recurring Subscription Metadata"""
    __tablename__ = "subscriptions"

    subscription_id = Column(String(100), primary_key=True)
    customer_id = Column(String(100), ForeignKey("customers.customer_id"), nullable=True)
    plan_id = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False)
    paid_count = Column(BigInteger, default=0, nullable=False)
    total_count = Column(BigInteger, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class RecoveryCase(Base):
    """Master Revenue Recovery Case State Machine Record"""
    __tablename__ = "recovery_cases"

    case_id = Column(String(100), primary_key=True, default=lambda: f"case_{uuid.uuid4().hex[:12]}")
    payment_id = Column(String(100), ForeignKey("payments.payment_id"), nullable=False, index=True)
    subscription_id = Column(String(100), nullable=True, index=True)
    customer_id = Column(String(100), ForeignKey("customers.customer_id"), nullable=True, index=True)
    revenue_at_risk_paise = Column(BigInteger, nullable=False)  # Integer paise (e.g., ₹2999.00 -> 299900)
    risk_tier = Column(String(50), default="MEDIUM_RISK", nullable=False, index=True)
    priority_score = Column(Float, default=50.0, nullable=False)
    diagnosed_cause = Column(String(100), nullable=True, index=True)
    status = Column(
        String(50),
        default="DETECTED",
        nullable=False,
        index=True
    )
    current_retry_count = Column(BigInteger, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    payment = relationship("Payment", back_populates="cases")
    customer = relationship("Customer", back_populates="cases")
    decisions = relationship("RecoveryDecision", back_populates="case")
    policy_decisions = relationship("PolicyDecision", back_populates="case")
    actions = relationship("RecoveryAction", back_populates="case")
    outcome = relationship("RecoveryOutcome", back_populates="case", uselist=False)
    audit_references = relationship("AuditReference", back_populates="case")


class RecoveryDecision(Base):
    """NVIDIA NIM LLM Contextual Recovery Recommendations"""
    __tablename__ = "recovery_decisions"

    decision_id = Column(String(100), primary_key=True, default=lambda: f"dec_{uuid.uuid4().hex[:12]}")
    case_id = Column(String(100), ForeignKey("recovery_cases.case_id"), nullable=False, index=True)
    recommended_action = Column(String(100), nullable=False)
    delay_hours = Column(BigInteger, default=0, nullable=False)
    channel = Column(String(50), default="EMAIL", nullable=False)
    dunning_message = Column(Text, nullable=True)
    reasoning_summary = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    langfuse_trace_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    case = relationship("RecoveryCase", back_populates="decisions")
    policy_decisions = relationship("PolicyDecision", back_populates="decision")


class PolicyDecision(Base):
    """Open Policy Agent (OPA) Governance Hard Brake Evaluation Proofs"""
    __tablename__ = "policy_decisions"

    policy_decision_id = Column(String(100), primary_key=True, default=lambda: f"pol_{uuid.uuid4().hex[:12]}")
    case_id = Column(String(100), ForeignKey("recovery_cases.case_id"), nullable=False, index=True)
    decision_id = Column(String(100), ForeignKey("recovery_decisions.decision_id"), nullable=False, index=True)
    opa_approved = Column(Boolean, nullable=False, index=True)
    enforced_rule_id = Column(String(100), nullable=True)
    veto_reason = Column(Text, nullable=True)
    verification_token = Column(String(128), nullable=False)
    policy_hash = Column(String(64), nullable=False)
    evaluated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    case = relationship("RecoveryCase", back_populates="policy_decisions")
    decision = relationship("RecoveryDecision", back_populates="policy_decisions")


class RecoveryAction(Base):
    """Executed API Recovery Operations (Razorpay & Novu)"""
    __tablename__ = "recovery_actions"

    action_id = Column(String(100), primary_key=True, default=lambda: f"act_{uuid.uuid4().hex[:12]}")
    case_id = Column(String(100), ForeignKey("recovery_cases.case_id"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    razorpay_invoice_id = Column(String(100), nullable=True)
    razorpay_payment_id = Column(String(100), nullable=True)
    razorpay_payment_link_id = Column(String(100), nullable=True)
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)
    status = Column(String(50), default="EXECUTED", nullable=False)
    api_response = Column(JSON, nullable=True)
    executed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    case = relationship("RecoveryCase", back_populates="actions")


class RecoveryOutcome(Base):
    """Authoritative Razorpay Settlement & Recovery Outcomes"""
    __tablename__ = "recovery_outcomes"

    outcome_id = Column(String(100), primary_key=True, default=lambda: f"out_{uuid.uuid4().hex[:12]}")
    case_id = Column(String(100), ForeignKey("recovery_cases.case_id"), unique=True, nullable=False, index=True)
    final_status = Column(String(50), nullable=False, index=True)
    recovered_amount_paise = Column(BigInteger, default=0, nullable=False)  # Integer paise
    settled_payment_id = Column(String(100), nullable=True)
    settled_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    case = relationship("RecoveryCase", back_populates="outcome")


class WorkflowExecution(Base):
    """Temporal Durable Workflow State Machine Trace Logs"""
    __tablename__ = "workflow_executions"

    workflow_id = Column(String(100), primary_key=True)
    run_id = Column(String(100), nullable=False)
    case_id = Column(String(100), ForeignKey("recovery_cases.case_id"), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class AuditReference(Base):
    """Cryptographic Ledger Verification References (immudb Merkle Receipts)"""
    __tablename__ = "audit_references"

    audit_id = Column(String(100), primary_key=True, default=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    case_id = Column(String(100), ForeignKey("recovery_cases.case_id"), nullable=False, index=True)
    event_name = Column(String(100), nullable=False)
    previous_state = Column(String(50), nullable=True)
    new_state = Column(String(50), nullable=False)
    payload_sha256 = Column(String(64), nullable=False)
    immudb_tx_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    case = relationship("RecoveryCase", back_populates="audit_references")
