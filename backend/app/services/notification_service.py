"""
Outbound Customer Communication Service (Novu Integration)
"""

import logging
from typing import Dict, Any, Optional
import httpx
from backend.app.core.config import get_settings

logger = logging.getLogger("recoverai.notification_service")


class NotificationService:
    """
    Novu Notification Service.
    Handles customer dunning notifications with safe local fallback when Novu key is absent.
    """

    NOVU_URL = "https://api.novu.co/v1/events/trigger"
    DEFAULT_TIMEOUT_SECONDS = 5.0

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.NOVU_API_KEY

    def is_configured(self) -> bool:
        return bool(self.api_key and "mock" not in self.api_key.lower() and "YOUR_" not in self.api_key)

    async def send_dunning_message(
        self,
        customer_id: str,
        message_strategy: str,
        message_body: str,
        subscriber_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Triggers a customer dunning notification event via Novu.
        Falls back safely to local logging if Novu API key is absent.
        """
        if not self.is_configured():
            logger.info(
                f"Novu API key not configured -> Skipped external delivery for customer '{customer_id}'. "
                f"Strategy: '{message_strategy}'"
            )
            return {
                "status": "SKIPPED_LOCAL",
                "delivered": False,
                "reason": "NOVU_API_KEY missing or placeholder",
                "customer_id": customer_id,
                "strategy": message_strategy,
            }

        headers = {
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "name": "recoverai-dunning-reminder",
            "to": {
                "subscriberId": customer_id,
                "email": subscriber_email or f"{customer_id}@example.com"
            },
            "payload": {
                "strategy": message_strategy,
                "message": message_body,
                "customer_id": customer_id
            }
        }

        logger.info(f"Triggering Novu notification for customer '{customer_id}' (strategy='{message_strategy}')")

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT_SECONDS) as client:
            response = await client.post(self.NOVU_URL, json=payload, headers=headers)

        if response.status_code not in (200, 201):
            logger.error(
                f"Novu notification delivery failed: HTTP {response.status_code} - {response.text[:200]}"
            )
            response.raise_for_status()

        res_data = response.json()
        res_data["delivered"] = True
        return res_data
