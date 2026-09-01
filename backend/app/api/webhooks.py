"""
Razorpay Webhook Endpoint Implementation with Database Persistence & Idempotency.
Handles raw-body HMAC-SHA256 signature verification, event persistence, and duplicate protection.
"""

import hmac
import hashlib
import json
import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, status, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.db.database import get_db
from backend.app.schemas.webhook import WebhookResponse, NormalizedEvent
from backend.app.services.webhook_service import WebhookService

logger = logging.getLogger("recoverai.webhooks")
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post(
    "/razorpay",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest Razorpay Webhooks",
    description="Receives real-time Razorpay webhook events, validates HMAC-SHA256 signature over raw request body, persists event to PostgreSQL, and enforces database-backed idempotency."
)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Razorpay Webhook Ingestion Endpoint with PostgreSQL Event Persistence.
    1. Reads raw request body bytes BEFORE any JSON parsing.
    2. Verifies HMAC-SHA256 signature against RAZORPAY_WEBHOOK_SECRET using hmac.compare_digest().
    3. Parses JSON payload.
    4. Persists WebhookEvent to PostgreSQL via WebhookService.
    5. Checks database-backed event_id idempotency (returns duplicate=true for repeat dispatches).
    6. Logs event telemetry safely without exposing secrets.
    7. Returns HTTP 200 OK.
    """
    settings = get_settings()
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

    # Step 1: Verify presence of signature header
    if not x_razorpay_signature:
        logger.warning("Rejected webhook attempt: Missing X-Razorpay-Signature header.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Razorpay-Signature header"
        )

    # Step 2: Read exact raw request body bytes BEFORE any JSON parsing
    try:
        raw_body = await request.body()
    except Exception as e:
        logger.error(f"Failed to read raw request body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to read request body"
        )

    if not webhook_secret:
        logger.error("RAZORPAY_WEBHOOK_SECRET is not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret configuration error"
        )

    # Step 3: Compute expected HMAC-SHA256 signature over exact raw bytes
    expected_signature = hmac.new(
        key=webhook_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    # Step 4: Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(expected_signature, x_razorpay_signature):
        logger.warning("Rejected webhook attempt: Signature verification failed (X-Razorpay-Signature mismatch).")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Razorpay webhook signature"
        )

    # Step 5: Signature verified successfully! Parse JSON payload.
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        logger.warning(f"Rejected webhook attempt: Malformed JSON body after valid signature: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON payload"
        )

    if not isinstance(payload, dict):
        logger.warning("Rejected webhook attempt: JSON payload is not a dictionary.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unexpected payload structure"
        )

    event_name = payload.get("event")
    if not event_name:
        logger.warning("Webhook payload missing 'event' field.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'event' field in payload"
        )

    # Step 6: Persist Event & Perform Database-backed Idempotency Check
    webhook_service = WebhookService(db)
    saved_event, is_duplicate = await webhook_service.process_webhook_event(
        payload=payload,
        signature_verified=True
    )

    # Extract metadata safely for telemetry logging
    event_payload_container = payload.get("payload", {})
    if not isinstance(event_payload_container, dict):
        event_payload_container = {}

    payment_entity = event_payload_container.get("payment", {}).get("entity", {}) if isinstance(event_payload_container.get("payment"), dict) else {}
    payment_id = payment_entity.get("id")
    amount_paise = payment_entity.get("amount")

    # Step 7: Safe structured logging (NO secrets, NO credentials, NO sensitive card data)
    if is_duplicate:
        logger.info(
            f"🔁 Duplicate Razorpay Webhook Event Received & Handled: "
            f"event_id='{saved_event.event_id}', event='{event_name}', payment_id='{payment_id or 'N/A'}'"
        )
    else:
        logger.info(
            f"✅ Razorpay Webhook Verified & Persisted to DB: "
            f"event_id='{saved_event.event_id}', event='{event_name}', payment_id='{payment_id or 'N/A'}', amount_paise={amount_paise or 'N/A'}"
        )

    return WebhookResponse(
        status="accepted",
        event=event_name,
        duplicate=is_duplicate
    )
