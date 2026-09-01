"""
Phase 1 Master Unit & Integration Tests (10 Mandatory Requirements)
"""
import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import NullPool

from backend.app.db.database import Base
from backend.app.db.models import (
    WebhookEvent,
    Customer,
    Payment,
    PaymentAttempt,
    Subscription,
    RecoveryCase,
    RecoveryDecision,
    PolicyDecision,
    RecoveryAction,
    RecoveryOutcome,
    WorkflowExecution,
    AuditReference,
)
from backend.app.db.repositories.case_repository import CaseRepository
from backend.app.db.repositories.payment_repository import PaymentRepository
from backend.app.core.config import get_settings

settings = get_settings()


@pytest_asyncio.fixture
async def repo_db_session():
    """Isolated async database session fixture for repository tests."""
    engine = create_async_engine(settings.async_database_url, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()


# TEST 1: All domain models can be imported
def test_models_importable():
    models = [
        WebhookEvent,
        Customer,
        Payment,
        PaymentAttempt,
        Subscription,
        RecoveryCase,
        RecoveryDecision,
        PolicyDecision,
        RecoveryAction,
        RecoveryOutcome,
        WorkflowExecution,
        AuditReference,
    ]
    assert len(models) == 12
    for m in models:
        assert hasattr(m, "__tablename__")


# TEST 2: Database tables can be created
@pytest.mark.asyncio
async def test_database_tables_creatable(repo_db_session):
    assert repo_db_session is not None


# TEST 3: Relationships work
@pytest.mark.asyncio
async def test_relationships_work(repo_db_session):
    pay_repo = PaymentRepository(repo_db_session)
    case_repo = CaseRepository(repo_db_session)

    cust_id = f"cust_rel_{uuid.uuid4().hex[:6]}"
    pay_id = f"pay_rel_{uuid.uuid4().hex[:6]}"

    customer = await pay_repo.create_or_get_customer({
        "customer_id": cust_id,
        "email": "rel@recoverai.io"
    })
    payment = await pay_repo.create_payment(Payment(
        payment_id=pay_id,
        customer_id=customer.customer_id,
        amount_paise=150000,
        status="failed"
    ))
    case = await case_repo.create_case(RecoveryCase(
        payment_id=payment.payment_id,
        customer_id=customer.customer_id,
        revenue_at_risk_paise=150000,
        status="DETECTED"
    ))

    fetched_case = await case_repo.get_case(case.case_id)
    assert fetched_case.payment.payment_id == pay_id
    assert fetched_case.customer.customer_id == cust_id


# TEST 4: Monetary values remain integer paise
@pytest.mark.asyncio
async def test_monetary_values_integer_paise(repo_db_session):
    pay_repo = PaymentRepository(repo_db_session)
    pay_id = f"pay_paise_{uuid.uuid4().hex[:6]}"
    payment = await pay_repo.create_payment(Payment(
        payment_id=pay_id,
        amount_paise=49900,  # ₹499.00
        status="failed"
    ))
    assert isinstance(payment.amount_paise, int)
    assert payment.amount_paise == 49900


# TEST 5: Duplicate Razorpay payment IDs are rejected
@pytest.mark.asyncio
async def test_duplicate_payment_id_rejected(repo_db_session):
    pay_repo = PaymentRepository(repo_db_session)
    pay_id = f"pay_dup_{uuid.uuid4().hex[:6]}"
    await pay_repo.create_payment(Payment(
        payment_id=pay_id,
        amount_paise=10000,
        status="failed"
    ))
    await repo_db_session.commit()

    with pytest.raises(IntegrityError):
        try:
            await pay_repo.create_payment(Payment(
                payment_id=pay_id,
                amount_paise=20000,
                status="failed"
            ))
            await repo_db_session.commit()
        finally:
            await repo_db_session.rollback()


# TEST 6: Duplicate webhook event IDs are rejected
@pytest.mark.asyncio
async def test_duplicate_webhook_event_id_rejected(repo_db_session):
    pay_repo = PaymentRepository(repo_db_session)
    evt_id = f"evt_dup_{uuid.uuid4().hex[:6]}"
    await pay_repo.create_webhook_event(WebhookEvent(
        event_id=evt_id,
        event_type="payment.failed",
        payload={"id": evt_id}
    ))
    await repo_db_session.commit()

    with pytest.raises(IntegrityError):
        try:
            await pay_repo.create_webhook_event(WebhookEvent(
                event_id=evt_id,
                event_type="payment.failed",
                payload={"id": evt_id}
            ))
            await repo_db_session.commit()
        finally:
            await repo_db_session.rollback()


# TEST 7: Duplicate recovery idempotency keys are rejected
@pytest.mark.asyncio
async def test_duplicate_idempotency_key_rejected(repo_db_session):
    pay_repo = PaymentRepository(repo_db_session)
    case_repo = CaseRepository(repo_db_session)

    pay_id = f"pay_idemp_{uuid.uuid4().hex[:6]}"
    idemp_key = f"idemp_{uuid.uuid4().hex[:6]}"

    payment = await pay_repo.create_payment(Payment(
        payment_id=pay_id,
        amount_paise=50000,
        status="failed"
    ))
    case = await case_repo.create_case(RecoveryCase(
        payment_id=payment.payment_id,
        revenue_at_risk_paise=50000,
        status="DETECTED"
    ))

    await case_repo.create_action(RecoveryAction(
        case_id=case.case_id,
        action_type="RETRY",
        idempotency_key=idemp_key,
        status="EXECUTED"
    ))
    await repo_db_session.commit()

    with pytest.raises(IntegrityError):
        try:
            await case_repo.create_action(RecoveryAction(
                case_id=case.case_id,
                action_type="RETRY",
                idempotency_key=idemp_key,
                status="EXECUTED"
            ))
            await repo_db_session.commit()
        finally:
            await repo_db_session.rollback()


# TEST 8: Recovery case can be created and retrieved
@pytest.mark.asyncio
async def test_create_and_get_case(repo_db_session):
    pay_repo = PaymentRepository(repo_db_session)
    case_repo = CaseRepository(repo_db_session)

    pay_id = f"pay_case_{uuid.uuid4().hex[:6]}"
    payment = await pay_repo.create_payment(Payment(
        payment_id=pay_id,
        amount_paise=99900,
        status="failed"
    ))
    case = await case_repo.create_case(RecoveryCase(
        payment_id=payment.payment_id,
        revenue_at_risk_paise=99900,
        status="DETECTED"
    ))

    fetched = await case_repo.get_case(case.case_id)
    assert fetched is not None
    assert fetched.case_id == case.case_id
    assert fetched.revenue_at_risk_paise == 99900


# TEST 9: Payment attempts are correctly associated with a payment
@pytest.mark.asyncio
async def test_payment_attempts_association(repo_db_session):
    pay_repo = PaymentRepository(repo_db_session)
    pay_id = f"pay_att_{uuid.uuid4().hex[:6]}"
    payment = await pay_repo.create_payment(Payment(
        payment_id=pay_id,
        amount_paise=29900,
        status="failed"
    ))

    await pay_repo.create_attempt(PaymentAttempt(
        payment_id=payment.payment_id,
        attempt_number=1,
        action_type="INITIAL_DEBIT",
        outcome="FAILED"
    ))
    await pay_repo.create_attempt(PaymentAttempt(
        payment_id=payment.payment_id,
        attempt_number=2,
        action_type="SCHEDULED_RETRY",
        outcome="FAILED"
    ))

    count = await pay_repo.get_attempt_count(payment.payment_id)
    assert count == 2


# TEST 10: Recovery decision/action/outcome relationships work
@pytest.mark.asyncio
async def test_decision_action_outcome_relationships(repo_db_session):
    pay_repo = PaymentRepository(repo_db_session)
    case_repo = CaseRepository(repo_db_session)

    pay_id = f"pay_flow_{uuid.uuid4().hex[:6]}"
    idemp_key = f"idemp_flow_{uuid.uuid4().hex[:6]}"

    payment = await pay_repo.create_payment(Payment(
        payment_id=pay_id,
        amount_paise=100000,
        status="failed"
    ))
    case = await case_repo.create_case(RecoveryCase(
        payment_id=payment.payment_id,
        revenue_at_risk_paise=100000,
        status="DETECTED"
    ))

    decision = await case_repo.create_decision(RecoveryDecision(
        case_id=case.case_id,
        recommended_action="RETRY_SCHEDULED",
        reasoning_summary="Payday window active",
        confidence=0.88
    ))

    action = await case_repo.create_action(RecoveryAction(
        case_id=case.case_id,
        action_type="RETRY_SCHEDULED",
        idempotency_key=idemp_key,
        status="EXECUTED"
    ))

    outcome = await case_repo.create_outcome(RecoveryOutcome(
        case_id=case.case_id,
        final_status="RECOVERED",
        recovered_amount_paise=100000,
        settled_payment_id=f"pay_succ_{uuid.uuid4().hex[:6]}"
    ))

    fetched_case = await case_repo.get_case(case.case_id)
    assert fetched_case.decisions[0].decision_id == decision.decision_id
    assert fetched_case.actions[0].action_id == action.action_id
    assert fetched_case.outcome.outcome_id == outcome.outcome_id
    assert fetched_case.outcome.recovered_amount_paise == 100000
