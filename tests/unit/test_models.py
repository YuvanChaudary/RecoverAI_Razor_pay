"""
Unit Tests for Phase 1 — Database Models & Repository Layer
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.db.database import Base
from backend.app.db.models import (
    WebhookEvent,
    Customer,
    Payment,
    PaymentAttempt,
    RecoveryCase,
    RecoveryDecision,
    PolicyDecision,
    RecoveryAction,
    RecoveryOutcome,
    AuditReference,
)
from backend.app.db.repositories.case_repository import CaseRepository
from backend.app.db.repositories.payment_repository import PaymentRepository
from backend.app.core.config import get_settings

settings = get_settings()


from sqlalchemy.pool import NullPool

@pytest_asyncio.fixture
async def db_session():
    """Provides a fresh, isolated async database session for testing."""
    engine = create_async_engine(settings.async_database_url, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.mark.asyncio
async def test_webhook_event_persistence(db_session):
    repo = PaymentRepository(db_session)
    event = WebhookEvent(
        event_id="evt_test_001",
        event_type="payment.failed",
        signature_verified=True,
        payload={"event": "payment.failed", "id": "pay_test_123"}
    )
    saved_event = await repo.create_webhook_event(event)
    assert saved_event.id is not None
    assert saved_event.event_id == "evt_test_001"

    fetched = await repo.get_webhook_event_by_id("evt_test_001")
    assert fetched is not None
    assert fetched.event_type == "payment.failed"


@pytest.mark.asyncio
async def test_recovery_case_lifecycle(db_session):
    pay_repo = PaymentRepository(db_session)
    case_repo = CaseRepository(db_session)

    # 1. Create Customer
    customer = await pay_repo.create_or_get_customer({
        "customer_id": "cust_test_99",
        "email": "test@recoverai.io",
        "customer_tier": "PREMIUM"
    })
    assert customer.customer_id == "cust_test_99"

    # 2. Create Payment
    payment = Payment(
        payment_id="pay_failed_999",
        customer_id=customer.customer_id,
        amount_paise=299900,  # Integer paise ₹2,999.00
        currency="INR",
        status="failed",
        error_code="BAD_REQUEST_ERROR",
        error_reason="insufficient_funds"
    )
    saved_payment = await pay_repo.create_payment(payment)
    assert saved_payment.payment_id == "pay_failed_999"

    # 3. Create Case
    case = RecoveryCase(
        payment_id=saved_payment.payment_id,
        customer_id=customer.customer_id,
        revenue_at_risk_paise=299900,
        risk_tier="HIGH_RISK",
        priority_score=85.5,
        diagnosed_cause="LIQUIDITY_FRICTION",
        status="DETECTED"
    )
    saved_case = await case_repo.create_case(case)
    assert saved_case.case_id.startswith("case_")
    assert saved_case.status == "DETECTED"

    # 4. Create Decision
    decision = RecoveryDecision(
        case_id=saved_case.case_id,
        recommended_action="RETRY_SCHEDULED",
        delay_hours=24,
        channel="WHATSAPP",
        reasoning_summary="Sufficient funds expected after payday",
        confidence=0.92
    )
    saved_decision = await case_repo.create_decision(decision)
    assert saved_decision.decision_id.startswith("dec_")

    # 5. Create Policy Decision
    policy_dec = PolicyDecision(
        case_id=saved_case.case_id,
        decision_id=saved_decision.decision_id,
        opa_approved=True,
        enforced_rule_id="RULE-001",
        verification_token="verify_tok_123",
        policy_hash="hash_sha256_mock"
    )
    saved_policy = await case_repo.create_policy_decision(policy_dec)
    assert saved_policy.opa_approved is True

    # 6. Create Action
    action = RecoveryAction(
        case_id=saved_case.case_id,
        action_type="SCHEDULED_RETRY",
        idempotency_key="idemp_key_001",
        status="EXECUTED"
    )
    saved_action = await case_repo.create_action(action)
    assert saved_action.action_id.startswith("act_")

    # 7. Create Outcome
    outcome = RecoveryOutcome(
        case_id=saved_case.case_id,
        final_status="RECOVERED",
        recovered_amount_paise=299900,
        settled_payment_id="pay_succ_100"
    )
    saved_outcome = await case_repo.create_outcome(outcome)
    assert saved_outcome.final_status == "RECOVERED"

    # 8. Create Audit Reference
    audit = AuditReference(
        case_id=saved_case.case_id,
        event_name="PAYMENT_RECOVERED",
        previous_state="ACTION_EXECUTED",
        new_state="RECOVERED",
        payload_sha256="0000000000000000000000000000000000000000000000000000000000000000",
        immudb_tx_id=101
    )
    await case_repo.create_audit_reference(audit)

    # 9. Verify Complete Full Object Hydration
    fetched_case = await case_repo.get_case(saved_case.case_id)
    assert fetched_case is not None
    assert len(fetched_case.decisions) == 1
    assert len(fetched_case.policy_decisions) == 1
    assert len(fetched_case.actions) == 1
    assert fetched_case.outcome.final_status == "RECOVERED"
    assert len(fetched_case.audit_references) == 1
