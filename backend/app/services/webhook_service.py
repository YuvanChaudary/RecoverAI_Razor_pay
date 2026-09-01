"""
Webhook Ingestion & Database Event Persistence Service
"""
import hashlib
import json
import logging
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from backend.app.db.models import WebhookEvent
from backend.app.db.repositories.payment_repository import PaymentRepository

logger = logging.getLogger("recoverai.webhook_service")


class WebhookService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PaymentRepository(session)

    @staticmethod
    def extract_event_id(payload: Dict[str, Any]) -> str:
        """
        Safely extracts or deterministically computes the Razorpay event ID.
        """
        if payload.get("event_id"):
            return str(payload["event_id"])
        if payload.get("id"):
            return str(payload["id"])

        # Fallback deterministic event ID for payloads missing explicit event_id
        raw_repr = f"{payload.get('event')}_{payload.get('account_id')}_{payload.get('created_at')}_{json.dumps(payload.get('payload', {}), sort_keys=True)}"
        derived_hash = hashlib.sha256(raw_repr.encode("utf-8")).hexdigest()[:16]
        return f"evt_derived_{derived_hash}"

    async def process_webhook_event(
        self,
        payload: Dict[str, Any],
        signature_verified: bool = True
    ) -> Tuple[WebhookEvent, bool]:
        """
        Persists a verified Razorpay webhook event in PostgreSQL.
        Enforces database-backed idempotency using WebhookEvent.event_id.

        Returns:
            Tuple[WebhookEvent, bool]: (WebhookEvent instance, is_duplicate flag)
        """
        event_id = self.extract_event_id(payload)
        event_type = payload.get("event", "unknown")

        logger.info(f"Processing webhook event_id='{event_id}', event_type='{event_type}'")

        # 1. Database-backed Idempotency Check
        existing_event = await self.repo.get_webhook_event_by_id(event_id)
        if existing_event:
            logger.info(f"Duplicate webhook event detected: event_id='{event_id}' already processed.")
            return existing_event, True

        # 2. Construct New WebhookEvent Model
        new_event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            signature_verified=signature_verified,
            processed=False,
            payload=payload,
        )

        try:
            saved_event = await self.repo.create_webhook_event(new_event)
            await self.session.commit()
            logger.info(f"Successfully persisted new webhook event: event_id='{event_id}'")

            # Phase 9: Webhook -> Authoritative State Transition Integration
            if signature_verified and event_type in ("payment.captured", "invoice.paid"):
                await self._process_settlement_transition(payload)

            return saved_event, False
        except IntegrityError:
            await self.session.rollback()
            logger.warning(f"Race condition detected: duplicate event_id='{event_id}' during concurrent write.")
            fetched = await self.repo.get_webhook_event_by_id(event_id)
            if fetched:
                return fetched, True
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to persist webhook event '{event_id}': {e}")
            raise

    async def _process_settlement_transition(self, payload: Dict[str, Any]):
        """
        Extracts settlement details from payment.captured / invoice.paid webhook and triggers state machine transition.
        """
        try:
            entity = payload.get("payload", {}).get("payment", {}).get("entity", {}) or payload.get("payload", {}).get("invoice", {}).get("entity", {})
            payment_id = entity.get("id") or entity.get("payment_id")
            if not payment_id:
                return

            case = await self.repo.get_case_by_payment(payment_id)
            if case:
                amount_paise = entity.get("amount", case.revenue_at_risk_paise)
                evidence = {
                    "authoritative": True,
                    "event_type": payload.get("event", "payment.captured"),
                    "payment_id": payment_id,
                    "amount_paise": amount_paise,
                    "signature_verified": True
                }
                from backend.app.services.recovery_state_machine import RecoveryStateMachine
                from backend.app.schemas.state_machine import CaseEventEnum

                state_machine = RecoveryStateMachine(session=self.session)
                res = await state_machine.transition(
                    case_id=case.case_id,
                    event=CaseEventEnum.PAYMENT_CAPTURED,
                    evidence=evidence
                )
                logger.info(f"Authoritative settlement state transition result for case '{case.case_id}': {res.model_dump()}")
                await self.session.commit()
        except Exception as err:
            logger.error(f"Failed to process settlement transition for webhook: {err}")
