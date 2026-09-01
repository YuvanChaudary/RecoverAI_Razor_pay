"""
Authoritative RecoveryCase State Machine Service
Enforces deterministic lifecycle transitions, OPA governance checks, and authoritative settlement rules.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.state_machine import (
    CaseStateEnum,
    CaseEventEnum,
    StateTransitionRequest,
    StateTransitionResult,
)
from backend.app.db.models import RecoveryCase, RecoveryOutcome
from backend.app.db.repositories.case_repository import CaseRepository
from backend.app.services.immutable_audit_service import ImmutableAuditService
from backend.app.schemas.audit import AuditEvent

logger = logging.getLogger("recoverai.state_machine")


class RecoveryStateMachine:
    """
    Authoritative State Machine for RecoverAI.
    Controls RecoveryCase status transitions deterministically.
    Guarantee: RECOVERED status requires authoritative settlement evidence.
    """

    AUTHORITATIVE_SETTLEMENT_EVENTS = {
        "payment.captured",
        "invoice.paid",
        "subscription.charged",
        "payment.authorized"
    }

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.repo = CaseRepository(session) if session else None
        self.audit_service = ImmutableAuditService()

    async def transition(
        self,
        case_id: str,
        event: CaseEventEnum,
        current_state: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
        ai_confidence: Optional[float] = None,
        opa_allowed: Optional[bool] = None,
    ) -> StateTransitionResult:
        """
        Executes a deterministic state transition on a RecoveryCase.
        Validates state rules, OPA governance permissions, and authoritative settlement evidence.
        """
        evidence = evidence or {}
        case_model = None

        if self.session and self.repo:
            case_model = await self.repo.get_case(case_id)
            if case_model:
                current_state = case_model.status

        if not current_state:
            current_state = CaseStateEnum.DETECTED.value

        # Normalize state strings
        curr_state_str = str(current_state).upper()
        event_str = str(event.value if isinstance(event, CaseEventEnum) else event).upper()

        logger.info(
            f"State transition request for case '{case_id}': "
            f"current_state='{curr_state_str}', event='{event_str}', opa_allowed={opa_allowed}"
        )

        # 1. IDEMPOTENT SETTLEMENT DELIVERY CHECK
        if curr_state_str == CaseStateEnum.RECOVERED.value and event_str == CaseEventEnum.PAYMENT_CAPTURED.value:
            logger.info(f"Duplicate settlement event for case '{case_id}' already RECOVERED -> Idempotent no-op")
            return StateTransitionResult(
                success=True,
                case_id=case_id,
                previous_state=curr_state_str,
                new_state=CaseStateEnum.RECOVERED.value,
                event=event_str,
                reason="Duplicate settlement webhook delivery received. Case already in authoritative RECOVERED state.",
                idempotent=True,
                recovered_amount_paise=0  # Avoid double-counting revenue
            )

        # 2. TERMINAL STATE BLOCKS
        if curr_state_str == CaseStateEnum.BLOCKED.value:
            return StateTransitionResult(
                success=False,
                case_id=case_id,
                previous_state=curr_state_str,
                new_state=curr_state_str,
                event=event_str,
                reason="Rejected: Case is in terminal BLOCKED state due to OPA governance denial."
            )

        if curr_state_str == CaseStateEnum.RECOVERED.value and event_str != CaseEventEnum.PAYMENT_CAPTURED.value:
            return StateTransitionResult(
                success=False,
                case_id=case_id,
                previous_state=curr_state_str,
                new_state=curr_state_str,
                event=event_str,
                reason=f"Rejected: Terminal state RECOVERED cannot transition via event '{event_str}'."
            )

        # 3. OPA GOVERNANCE HARD BRAKE CHECK
        if opa_allowed is False or event_str == CaseEventEnum.GOVERNANCE_DENIED.value:
            if event_str in (
                CaseEventEnum.GOVERNANCE_ALLOWED.value,
                CaseEventEnum.ACTION_SCHEDULED.value,
                CaseEventEnum.ACTION_EXECUTED.value,
                CaseEventEnum.SETTLEMENT_AWAITING.value,
                CaseEventEnum.GOVERNANCE_DENIED.value,
            ):
                logger.warning(
                    f"State transition blocked for case '{case_id}': OPA Governance allowed=False. "
                    f"AI confidence ({ai_confidence}) cannot bypass OPA hard brake."
                )
                new_target_state = CaseStateEnum.BLOCKED.value
                await self._persist_state_change(case_id, case_model, new_target_state, event_str)
                return StateTransitionResult(
                    success=False,
                    case_id=case_id,
                    previous_state=curr_state_str,
                    new_state=new_target_state,
                    event=event_str,
                    reason="Transition rejected: OPA governance denial blocks executable recovery state."
                )

        # 4. AUTHORITATIVE RECOVERY TRANSITION CHECK
        if event_str == CaseEventEnum.PAYMENT_CAPTURED.value:
            is_authoritative = (
                evidence.get("authoritative") is True or
                evidence.get("event_type") in self.AUTHORITATIVE_SETTLEMENT_EVENTS or
                evidence.get("event") in self.AUTHORITATIVE_SETTLEMENT_EVENTS or
                evidence.get("signature_verified") is True
            )

            if not is_authoritative:
                return StateTransitionResult(
                    success=False,
                    case_id=case_id,
                    previous_state=curr_state_str,
                    new_state=curr_state_str,
                    event=event_str,
                    reason="Rejected: RECOVERED status requires verified authoritative payment settlement evidence."
                )

            # Valid authoritative settlement transition -> RECOVERED
            amount_paise = int(evidence.get("amount_paise") or evidence.get("recovered_amount_paise") or (case_model.revenue_at_risk_paise if case_model else 0))
            new_target_state = CaseStateEnum.RECOVERED.value

            await self._persist_state_change(case_id, case_model, new_target_state, event_str)
            await self._record_outcome(case_id, case_model, amount_paise, evidence.get("payment_id"))

            return StateTransitionResult(
                success=True,
                case_id=case_id,
                previous_state=curr_state_str,
                new_state=new_target_state,
                event=event_str,
                reason="Authoritative settlement confirmed via Razorpay webhook evidence.",
                recovered_amount_paise=amount_paise
            )

        # 5. DISPATCH STANDARD VALID TRANSITIONS
        next_state_map = {
            (CaseStateEnum.DETECTED.value, CaseEventEnum.FAILURE_DIAGNOSED.value): CaseStateEnum.DIAGNOSED.value,
            (CaseStateEnum.DIAGNOSED.value, CaseEventEnum.GOVERNANCE_ALLOWED.value): CaseStateEnum.GOVERNANCE_APPROVED.value,
            (CaseStateEnum.DIAGNOSED.value, CaseEventEnum.GOVERNANCE_DENIED.value): CaseStateEnum.BLOCKED.value,
            (CaseStateEnum.GOVERNANCE_APPROVED.value, CaseEventEnum.ACTION_SCHEDULED.value): CaseStateEnum.ACTION_SCHEDULED.value,
            (CaseStateEnum.GOVERNANCE_APPROVED.value, CaseEventEnum.ACTION_EXECUTED.value): CaseStateEnum.ACTION_EXECUTED.value,
            (CaseStateEnum.ACTION_SCHEDULED.value, CaseEventEnum.ACTION_EXECUTED.value): CaseStateEnum.ACTION_EXECUTED.value,
            (CaseStateEnum.ACTION_SCHEDULED.value, CaseEventEnum.SETTLEMENT_AWAITING.value): CaseStateEnum.AWAITING_SETTLEMENT.value,
            (CaseStateEnum.ACTION_EXECUTED.value, CaseEventEnum.SETTLEMENT_AWAITING.value): CaseStateEnum.AWAITING_SETTLEMENT.value,
            (CaseStateEnum.AWAITING_SETTLEMENT.value, CaseEventEnum.PAYMENT_FAILED.value): CaseStateEnum.FAILED.value,
            (CaseStateEnum.ACTION_EXECUTED.value, CaseEventEnum.PAYMENT_FAILED.value): CaseStateEnum.FAILED.value,
        }

        # Attempt to find valid transition
        key_pair = (curr_state_str, event_str)
        target_state = next_state_map.get(key_pair)

        if not target_state:
            # Special check for direct illegal attempts to jump to RECOVERED without settlement
            if event_str == CaseEventEnum.ACTION_EXECUTED.value and evidence.get("target_state") == CaseStateEnum.RECOVERED.value:
                return StateTransitionResult(
                    success=False,
                    case_id=case_id,
                    previous_state=curr_state_str,
                    new_state=curr_state_str,
                    event=event_str,
                    reason="Rejected: Outbound API execution alone cannot produce RECOVERED state without settlement evidence."
                )

            return StateTransitionResult(
                success=False,
                case_id=case_id,
                previous_state=curr_state_str,
                new_state=curr_state_str,
                event=event_str,
                reason=f"Illegal transition: State '{curr_state_str}' cannot transition via event '{event_str}'."
            )

        # Apply state transition
        await self._persist_state_change(case_id, case_model, target_state, event_str)

        return StateTransitionResult(
            success=True,
            case_id=case_id,
            previous_state=curr_state_str,
            new_state=target_state,
            event=event_str,
            reason=f"Transitioned from {curr_state_str} to {target_state} via {event_str}."
        )

    async def _persist_state_change(
        self,
        case_id: str,
        case_model: Optional[RecoveryCase],
        new_state: str,
        event: str
    ):
        prev_state = case_model.status if case_model else "UNKNOWN"
        if case_model and self.session:
            case_model.status = new_state
            await self.session.flush()

        # Phase 8 immudb Audit Integration
        try:
            audit_evt = AuditEvent(
                event_id=f"evt_trans_{case_id}_{event}_{new_state}",
                event_type=f"STATE_TRANSITION_{event}",
                recovery_case_id=case_id,
                payment_id=case_model.payment_id if case_model else "pay_unknown",
                execution_status=new_state if new_state != "RECOVERED" else "EXECUTED",
                metadata={"previous_state": prev_state, "new_state": new_state, "event": event}
            )
            await self.audit_service.record_event(audit_evt)
        except Exception as err:
            logger.warning(f"Failed to record audit event for state transition: {err}")

    async def _record_outcome(
        self,
        case_id: str,
        case_model: Optional[RecoveryCase],
        amount_paise: int,
        settled_payment_id: Optional[str]
    ):
        if self.session and self.repo:
            existing_outcome = getattr(case_model, "outcome", None)
            if not existing_outcome:
                outcome = RecoveryOutcome(
                    case_id=case_id,
                    final_status="RECOVERED",
                    recovered_amount_paise=amount_paise,
                    settled_payment_id=settled_payment_id or (case_model.payment_id if case_model else None)
                )
                await self.repo.create_outcome(outcome)
            else:
                existing_outcome.final_status = "RECOVERED"
                existing_outcome.recovered_amount_paise = amount_paise
                await self.session.flush()
