"""
Repository Pattern for Webhook Events, Customers, Payments, Payment Attempts, and Subscriptions
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from backend.app.db.models import (
    WebhookEvent,
    Customer,
    Payment,
    PaymentAttempt,
    Subscription,
)


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_webhook_event(self, event: WebhookEvent) -> WebhookEvent:
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_webhook_event_by_id(self, event_id: str) -> Optional[WebhookEvent]:
        result = await self.session.execute(
            select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        )
        return result.scalar_one_or_none()

    async def create_or_get_customer(self, customer_data: dict) -> Customer:
        customer_id = customer_data.get("customer_id")
        result = await self.session.execute(
            select(Customer).where(Customer.customer_id == customer_id)
        )
        customer = result.scalar_one_or_none()

        if not customer:
            customer = Customer(**customer_data)
            self.session.add(customer)
            await self.session.flush()

        return customer

    async def create_payment(self, payment: Payment) -> Payment:
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_by_razorpay_id(self, payment_id: str) -> Optional[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.payment_id == payment_id)
        )
        return result.scalar_one_or_none()

    async def create_attempt(self, attempt: PaymentAttempt) -> PaymentAttempt:
        self.session.add(attempt)
        await self.session.flush()
        return attempt

    async def get_attempt_count(self, payment_id: str) -> int:
        result = await self.session.execute(
            select(func.count(PaymentAttempt.attempt_id)).where(PaymentAttempt.payment_id == payment_id)
        )
        return result.scalar() or 0

    async def create_or_get_subscription(self, sub_data: dict) -> Subscription:
        sub_id = sub_data.get("subscription_id")
        result = await self.session.execute(
            select(Subscription).where(Subscription.subscription_id == sub_id)
        )
        sub = result.scalar_one_or_none()

        if not sub:
            sub = Subscription(**sub_data)
            self.session.add(sub)
            await self.session.flush()

        return sub
