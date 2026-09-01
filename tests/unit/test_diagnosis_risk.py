"""
Phase 3 Unit & Integration Tests: Failure Diagnosis & Revenue-at-Risk Engine
"""

import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from backend.app.db.database import Base
from backend.app.db.models import Payment, RecoveryCase, Customer
from backend.app.db.repositories.case_repository import CaseRepository
from backend.app.db.repositories.payment_repository import PaymentRepository
from backend.app.schemas.diagnosis import FailureCategory, PriorityTier
from backend.app.services.diagnosis_service import DiagnosisService
from backend.app.services.risk_service import RiskService
from backend.app.core.config import get_settings

settings = get_settings()


@pytest_asyncio.fixture
async def phase3_db_session():
    """Isolated async database session fixture for Phase 3 tests."""
    engine = create_async_engine(settings.async_database_url, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()


# --- DIAGNOSIS TESTS ---

def test_diagnose_insufficient_funds():
    res = DiagnosisService.diagnose_failure(code="BAD_REQUEST_ERROR", reason="insufficient_funds")
    assert res.category == FailureCategory.LIQUIDITY_FRICTION
    assert res.confidence == 1.0


def test_diagnose_expired_card():
    res = DiagnosisService.diagnose_failure(code="BAD_REQUEST_ERROR", reason="EXPIRED_CARD ")
    assert res.category == FailureCategory.INSTRUMENT_INVALIDATION


def test_diagnose_gateway_timeout():
    res = DiagnosisService.diagnose_failure(code="GATEWAY_TIMEOUT", reason="network_error")
    assert res.category == FailureCategory.TRANSIENT_INFRASTRUCTURE


def test_diagnose_mandate_expired():
    res = DiagnosisService.diagnose_failure(code="MANDATE_EXPIRED", reason="mandate_expired")
    assert res.category == FailureCategory.MANDATE_COMPLIANCE_LOCK


def test_diagnose_bank_risk_decline():
    res = DiagnosisService.diagnose_failure(code="BAD_REQUEST_ERROR", reason="bank/risk decline")
    assert res.category == FailureCategory.BANK_RISK_BLOCK


def test_diagnose_unknown_error():
    res = DiagnosisService.diagnose_failure(code="SOME_UNSEEN_CODE", reason="some_random_reason")
    assert res.category == FailureCategory.UNKNOWN


def test_diagnose_normalization_and_whitespace():
    res = DiagnosisService.diagnose_failure(code="  INSUFFICIENT_FUNDS  ", reason="   Low_Balance  ")
    assert res.category == FailureCategory.LIQUIDITY_FRICTION
    assert res.normalized_code == "insufficient_funds"


def test_diagnose_missing_fields_safely():
    res = DiagnosisService.diagnose_failure(code=None, reason=None)
    assert res.category == FailureCategory.UNKNOWN


def test_diagnose_raw_payload():
    payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_reason": "insufficient_funds"
                }
            }
        }
    }
    res = DiagnosisService.diagnose_failure(raw_payload=payload)
    assert res.category == FailureCategory.LIQUIDITY_FRICTION


# --- REVENUE-AT-RISK TESTS ---

def test_risk_valid_paise():
    assessment = RiskService.assess_risk(amount_paise=49900, category=FailureCategory.LIQUIDITY_FRICTION)
    assert assessment.revenue_at_risk_paise == 49900
    assert assessment.amount_inr_formatted == "₹499.00"
    assert isinstance(assessment.revenue_at_risk_paise, int)


def test_risk_high_value_paise():
    assessment = RiskService.assess_risk(amount_paise=1000000, category=FailureCategory.TRANSIENT_INFRASTRUCTURE)
    assert assessment.revenue_at_risk_paise == 1000000
    assert assessment.amount_inr_formatted == "₹10,000.00"


def test_risk_zero_paise():
    assessment = RiskService.assess_risk(amount_paise=0, category=FailureCategory.UNKNOWN)
    assert assessment.revenue_at_risk_paise == 0
    assert assessment.amount_inr_formatted == "₹0.00"
    assert assessment.priority_tier == PriorityTier.LOW


def test_risk_negative_paise_rejected():
    with pytest.raises(ValueError, match="cannot be negative"):
        RiskService.assess_risk(amount_paise=-1000, category=FailureCategory.LIQUIDITY_FRICTION)


# --- PRIORITY TESTS ---

def test_priority_high_tier():
    # Large amount + high recovery category + 0 retries -> High Score -> HIGH
    assessment = RiskService.assess_risk(
        amount_paise=600000,  # ₹6,000 (50 pts)
        category=FailureCategory.LIQUIDITY_FRICTION,  # (30 pts)
        retry_count=0  # (20 pts) -> Total = 100 pts -> HIGH
    )
    assert assessment.priority_score == 100.0
    assert assessment.priority_tier == PriorityTier.HIGH


def test_priority_medium_tier():
    # Medium amount + medium category + 1 retry -> Medium score -> MEDIUM
    assessment = RiskService.assess_risk(
        amount_paise=200000,  # ₹2,000 (30 pts)
        category=FailureCategory.MANDATE_COMPLIANCE_LOCK,  # (20 pts)
        retry_count=1  # (10 pts) -> Total = 60 pts -> MEDIUM
    )
    assert assessment.priority_score == 60.0
    assert assessment.priority_tier == PriorityTier.MEDIUM


def test_priority_low_tier():
    # Small amount + unknown category + multiple retries -> Low score -> LOW
    assessment = RiskService.assess_risk(
        amount_paise=50000,  # ₹500 (10 pts)
        category=FailureCategory.UNKNOWN,  # (0 pts)
        retry_count=5  # (0 pts) -> Total = 10 pts -> LOW
    )
    assert assessment.priority_score == 10.0
    assert assessment.priority_tier == PriorityTier.LOW


def test_priority_reproducibility():
    a1 = RiskService.assess_risk(amount_paise=300000, category=FailureCategory.LIQUIDITY_FRICTION, retry_count=1)
    a2 = RiskService.assess_risk(amount_paise=300000, category=FailureCategory.LIQUIDITY_FRICTION, retry_count=1)
    assert a1.priority_score == a2.priority_score
    assert a1.priority_tier == a2.priority_tier


# --- RECOVERY CASE INTEGRATION TEST ---

@pytest.mark.asyncio
async def test_recovery_case_creation_from_diagnosis_and_risk(phase3_db_session):
    pay_repo = PaymentRepository(phase3_db_session)
    case_repo = CaseRepository(phase3_db_session)

    # 1. Create Payment
    pay_id = f"pay_failed_{uuid.uuid4().hex[:8]}"
    payment = await pay_repo.create_payment(Payment(
        payment_id=pay_id,
        amount_paise=299900,  # ₹2,999.00
        currency="INR",
        status="failed",
        error_code="BAD_REQUEST_ERROR",
        error_reason="insufficient_funds"
    ))

    # 2. Run Phase 3 Diagnosis & Risk Engine
    diagnosis = DiagnosisService.diagnose_failure(code=payment.error_code, reason=payment.error_reason)
    risk = RiskService.assess_risk(amount_paise=payment.amount_paise, category=diagnosis.category, retry_count=0)

    # 3. Create RecoveryCase
    case = RecoveryCase(
        payment_id=payment.payment_id,
        revenue_at_risk_paise=risk.revenue_at_risk_paise,
        diagnosed_cause=diagnosis.category.value,
        risk_tier=risk.priority_tier.value,
        priority_score=risk.priority_score,
        status="DETECTED"  # Status is DETECTED, NOT RECOVERED
    )
    saved_case = await case_repo.create_case(case)
    await phase3_db_session.commit()

    # 4. Assert RecoveryCase properties
    assert saved_case.case_id.startswith("case_")
    assert saved_case.revenue_at_risk_paise == 299900
    assert saved_case.diagnosed_cause == "LIQUIDITY_FRICTION"
    assert saved_case.risk_tier == "HIGH"
    assert saved_case.status == "DETECTED"
    assert saved_case.status != "RECOVERED"  # NEVER CLAIM RECOVERY IN PHASE 3
