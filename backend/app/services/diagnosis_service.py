"""
Deterministic Failure Diagnosis Engine
Maps Razorpay error attributes into a strict, reproducible taxonomy.
"""

import logging
from typing import Optional, Dict, Any
from backend.app.schemas.diagnosis import FailureCategory, DiagnosisResult

logger = logging.getLogger("recoverai.diagnosis_service")


class DiagnosisService:
    """
    Deterministic Diagnosis Service.
    Applies pure rule-based evaluation over normalized error indicators.
    Guarantees: Same Input -> Same FailureCategory.
    """

    LIQUIDITY_KEYWORDS = {
        "insufficient_funds",
        "insufficient_balance",
        "low_balance",
        "balance_insufficient",
        "account_insufficient_funds",
    }

    INSTRUMENT_KEYWORDS = {
        "expired_card",
        "card_expired",
        "invalid_card",
        "invalid_card_details",
        "card_not_active",
        "invalid_account",
        "card_declined",
        "expired_instrument",
    }

    INFRASTRUCTURE_KEYWORDS = {
        "gateway_timeout",
        "network_error",
        "timed_out",
        "timeout",
        "system_error",
        "bank_offline",
        "technical_error",
        "gateway_error",
        "connection_failed",
    }

    MANDATE_KEYWORDS = {
        "mandate_expired",
        "mandate_invalid",
        "mandate_cancelled",
        "mandate_failed",
        "pre_debit_failed",
        "mandate_registration_failed",
    }

    RISK_KEYWORDS = {
        "bank_decline",
        "bank/risk decline",
        "risk_decline",
        "suspected_fraud",
        "blocked_by_bank",
        "security_violation",
        "risk_check_failed",
        "declined_by_issuer",
    }

    @classmethod
    def normalize_str(cls, val: Optional[str]) -> str:
        """Helper to trim whitespace and lowercase strings safely."""
        if not val:
            return ""
        return str(val).strip().lower()

    @classmethod
    def diagnose_failure(
        cls,
        code: Optional[str] = None,
        reason: Optional[str] = None,
        source: Optional[str] = None,
        step: Optional[str] = None,
        description: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> DiagnosisResult:
        """
        Diagnoses a payment failure deterministically.
        Inspects error code, reason, description, source, and step attributes.
        """
        # Extract fields from raw_payload if provided as container
        if raw_payload and isinstance(raw_payload, dict):
            payment_entity = raw_payload.get("payload", {}).get("payment", {}).get("entity", {}) if isinstance(raw_payload.get("payload"), dict) else {}
            code = code or payment_entity.get("error_code")
            reason = reason or payment_entity.get("error_reason")
            source = source or payment_entity.get("error_source")
            step = step or payment_entity.get("error_step")
            description = description or payment_entity.get("error_description")

        norm_code = cls.normalize_str(code)
        norm_reason = cls.normalize_str(reason)
        norm_desc = cls.normalize_str(description)
        combined_text = f"{norm_code} {norm_reason} {norm_desc}"

        # 1. Check Liquidity Friction
        if any(kw in combined_text for kw in cls.LIQUIDITY_KEYWORDS):
            return DiagnosisResult(
                category=FailureCategory.LIQUIDITY_FRICTION,
                normalized_code=norm_code or "insufficient_funds",
                reason=reason or "insufficient_funds",
                source=source,
                step=step,
                confidence=1.0,
            )

        # 2. Check Instrument Invalidation
        if any(kw in combined_text for kw in cls.INSTRUMENT_KEYWORDS):
            return DiagnosisResult(
                category=FailureCategory.INSTRUMENT_INVALIDATION,
                normalized_code=norm_code or "expired_card",
                reason=reason or "expired_card",
                source=source,
                step=step,
                confidence=1.0,
            )

        # 3. Check Transient Infrastructure
        if any(kw in combined_text for kw in cls.INFRASTRUCTURE_KEYWORDS):
            return DiagnosisResult(
                category=FailureCategory.TRANSIENT_INFRASTRUCTURE,
                normalized_code=norm_code or "gateway_timeout",
                reason=reason or "gateway_timeout",
                source=source,
                step=step,
                confidence=1.0,
            )

        # 4. Check Mandate Compliance Lock
        if any(kw in combined_text for kw in cls.MANDATE_KEYWORDS):
            return DiagnosisResult(
                category=FailureCategory.MANDATE_COMPLIANCE_LOCK,
                normalized_code=norm_code or "mandate_expired",
                reason=reason or "mandate_expired",
                source=source,
                step=step,
                confidence=1.0,
            )

        # 5. Check Bank Risk Block
        if any(kw in combined_text for kw in cls.RISK_KEYWORDS):
            return DiagnosisResult(
                category=FailureCategory.BANK_RISK_BLOCK,
                normalized_code=norm_code or "bank_decline",
                reason=reason or "bank_decline",
                source=source,
                step=step,
                confidence=1.0,
            )

        # Fallback Default -> UNKNOWN
        logger.info(f"Unrecognized error pattern: code='{code}', reason='{reason}' -> Categorized as UNKNOWN")
        return DiagnosisResult(
            category=FailureCategory.UNKNOWN,
            normalized_code=norm_code or "unknown",
            reason=reason or "unclassified_failure",
            source=source,
            step=step,
            confidence=1.0,
        )
