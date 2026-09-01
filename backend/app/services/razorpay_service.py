"""
Outbound Razorpay REST API Client Service
Handles financial mutations (Payment Links, Invoice Retries) with idempotency headers.
"""

import logging
from typing import Dict, Any, Optional
import httpx
from backend.app.core.config import get_settings

logger = logging.getLogger("recoverai.razorpay_service")


class RazorpayService:
    """
    Async Outbound Razorpay Service.
    Enforces monetary integrity (integer paise), HTTP idempotency headers,
    and safe exception propagation.
    """

    BASE_URL = "https://api.razorpay.com/v1"
    DEFAULT_TIMEOUT_SECONDS = 10.0

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None
    ):
        settings = get_settings()
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET

    def _get_auth(self) -> tuple:
        return (self.key_id, self.key_secret)

    async def create_payment_link(
        self,
        amount_paise: int,
        customer: Dict[str, Any],
        description: str,
        idempotency_key: str
    ) -> Dict[str, Any]:
        """
        Creates a Razorpay Payment Link for unpaid invoices or instrument updates.
        Injects idempotency key via X-Razorpay-Comment header and payload notes.
        """
        if amount_paise <= 0:
            raise ValueError(f"Invalid monetary value: amount_paise={amount_paise} must be strictly positive.")
        if not idempotency_key:
            raise ValueError("Idempotency key is required for outbound financial mutations.")

        url = f"{self.BASE_URL}/payment_links"
        headers = {
            "Content-Type": "application/json",
            "X-Razorpay-Comment": idempotency_key,
            "X-Razorpay-Idempotency-Key": idempotency_key,
        }

        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "accept_partial": False,
            "description": description or "RecoverAI Revenue Recovery Payment Link",
            "customer": {
                "name": customer.get("name", "Customer"),
                "email": customer.get("email", "customer@example.com"),
                "contact": customer.get("contact", "+919999999999"),
            },
            "notify": {
                "sms": True,
                "email": True
            },
            "reminder_enable": True,
            "notes": {
                "idempotency_key": idempotency_key
            }
        }

        logger.info(
            f"Creating Razorpay Payment Link: amount_paise={amount_paise}, idempotency_key='{idempotency_key}'"
        )

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                auth=self._get_auth()
            )

        if response.status_code not in (200, 201):
            logger.error(
                f"Razorpay Payment Link creation failed: HTTP {response.status_code} - {response.text[:200]}"
            )
            response.raise_for_status()

        return response.json()

    async def retry_payment(
        self,
        payment_id: str,
        idempotency_key: str,
        invoice_id: Optional[str] = None,
        subscription_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes outbound retry request for a failed invoice or subscription payment.
        """
        if not idempotency_key:
            raise ValueError("Idempotency key is required for outbound payment retry.")

        headers = {
            "Content-Type": "application/json",
            "X-Razorpay-Comment": idempotency_key,
            "X-Razorpay-Idempotency-Key": idempotency_key,
        }

        if invoice_id:
            url = f"{self.BASE_URL}/invoices/{invoice_id}/retry"
        elif subscription_id:
            url = f"{self.BASE_URL}/subscriptions/{subscription_id}/retry"
        else:
            raise ValueError(
                f"Razorpay payment retry requires an associated invoice_id or subscription_id resource (payment_id={payment_id})."
            )

        logger.info(
            f"Executing Razorpay Retry: payment_id='{payment_id}', idempotency_key='{idempotency_key}'"
        )

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url,
                json={"payment_id": payment_id, "notes": {"idempotency_key": idempotency_key}},
                headers=headers,
                auth=self._get_auth()
            )

        if response.status_code not in (200, 201):
            logger.error(
                f"Razorpay Payment retry failed: HTTP {response.status_code} - {response.text[:200]}"
            )
            response.raise_for_status()

        return response.json()
