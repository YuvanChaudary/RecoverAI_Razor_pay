"""
Repository Pattern for Case Management, Decisions, Policies, Actions, and Outcomes
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.app.db.models import (
    RecoveryCase,
    RecoveryDecision,
    PolicyDecision,
    RecoveryAction,
    RecoveryOutcome,
    AuditReference,
)


class CaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_case(self, case: RecoveryCase) -> RecoveryCase:
        self.session.add(case)
        await self.session.flush()
        return case

    async def get_case(self, case_id: str) -> Optional[RecoveryCase]:
        result = await self.session.execute(
            select(RecoveryCase)
            .where(RecoveryCase.case_id == case_id)
            .options(
                selectinload(RecoveryCase.decisions),
                selectinload(RecoveryCase.policy_decisions),
                selectinload(RecoveryCase.actions),
                selectinload(RecoveryCase.outcome),
                selectinload(RecoveryCase.audit_references),
            )
        )
        return result.scalar_one_or_none()

    async def get_case_by_payment(self, payment_id: str) -> Optional[RecoveryCase]:
        result = await self.session.execute(
            select(RecoveryCase)
            .where(RecoveryCase.payment_id == payment_id)
            .options(
                selectinload(RecoveryCase.decisions),
                selectinload(RecoveryCase.policy_decisions),
                selectinload(RecoveryCase.actions),
                selectinload(RecoveryCase.outcome),
                selectinload(RecoveryCase.audit_references),
            )
        )
        return result.scalar_one_or_none()

    async def update_case_state(self, case_id: str, new_status: str) -> Optional[RecoveryCase]:
        case = await self.get_case(case_id)
        if case:
            case.status = new_status
            await self.session.flush()
        return case

    async def increment_retry_count(self, case_id: str) -> Optional[RecoveryCase]:
        case = await self.get_case(case_id)
        if case:
            case.current_retry_count += 1
            await self.session.flush()
        return case

    async def create_decision(self, decision: RecoveryDecision) -> RecoveryDecision:
        self.session.add(decision)
        await self.session.flush()
        return decision

    async def create_policy_decision(self, policy_decision: PolicyDecision) -> PolicyDecision:
        self.session.add(policy_decision)
        await self.session.flush()
        return policy_decision

    async def create_action(self, action: RecoveryAction) -> RecoveryAction:
        self.session.add(action)
        await self.session.flush()
        return action

    async def create_outcome(self, outcome: RecoveryOutcome) -> RecoveryOutcome:
        self.session.add(outcome)
        await self.session.flush()
        return outcome

    async def create_audit_reference(self, audit: AuditReference) -> AuditReference:
        self.session.add(audit)
        await self.session.flush()
        return audit

    async def list_cases(self, limit: int = 100, offset: int = 0) -> List[RecoveryCase]:
        result = await self.session.execute(
            select(RecoveryCase)
            .order_by(RecoveryCase.created_at.desc())
            .offset(offset)
            .limit(limit)
            .options(
                selectinload(RecoveryCase.decisions),
                selectinload(RecoveryCase.policy_decisions),
                selectinload(RecoveryCase.actions),
                selectinload(RecoveryCase.outcome),
            )
        )
        return result.scalars().all()
