"""
NVIDIA NIM AI Decision Agent with Langfuse Observability & Deterministic Fallbacks
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Optional, Dict, Any

import httpx
from backend.app.core.config import get_settings
from backend.app.ai.schemas import (
    ActionEnum,
    TimingEnum,
    MessageStrategyEnum,
    ProposedRecoveryPlan,
    RecoveryContext,
)
from backend.app.ai.prompts import SYSTEM_RECOVERY_PROMPT, build_recovery_user_prompt

logger = logging.getLogger("recoverai.ai_agent")


class NvidiaNIMAgent:
    """
    NVIDIA NIM AI Recovery Decision Agent.
    Interacts with NVIDIA NIM foundation models via OpenAI-compatible REST API.
    Enforces structured Pydantic output, 3.0s SLA timeouts, and deterministic fallbacks.
    """

    CONFIDENCE_THRESHOLD = 0.80
    TIMEOUT_SECONDS = 3.0

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.NVIDIA_API_KEY
        self.model = self.settings.NVIDIA_MODEL
        self.base_url = self.settings.NVIDIA_BASE_URL.rstrip("/")

        # Initialize Langfuse client safely if credentials present
        self.langfuse = None
        if self.settings.LANGFUSE_PUBLIC_KEY and self.settings.LANGFUSE_SECRET_KEY:
            try:
                from langfuse import Langfuse
                self.langfuse = Langfuse(
                    public_key=self.settings.LANGFUSE_PUBLIC_KEY,
                    secret_key=self.settings.LANGFUSE_SECRET_KEY,
                    host=self.settings.LANGFUSE_HOST
                )
                logger.info("Langfuse observability client initialized.")
            except Exception as e:
                logger.warning(f"Langfuse initialization notice: {e}")

    @classmethod
    def get_deterministic_fallback(cls, reason: str = "Fallback engaged") -> ProposedRecoveryPlan:
        """
        Returns a safe, low-risk deterministic fallback proposal.
        Guarantees: Zero financial state mutation & Zero recovery claim.
        """
        logger.warning(f"Engaging deterministic fallback plan: reason='{reason}'")
        return ProposedRecoveryPlan(
            recommended_action=ActionEnum.NO_AUTOMATED_ACTION,
            delay_hours=24,
            timing=TimingEnum.DELAYED,
            message_strategy=MessageStrategyEnum.CONCISE,
            dunning_message=None,
            reasoning_summary=f"Deterministic fallback engaged: {reason}",
            confidence=0.50,
            is_fallback=True,
        )

    def _log_langfuse_trace(
        self,
        trace_id: str,
        context: RecoveryContext,
        plan: ProposedRecoveryPlan,
        latency_ms: float,
        error_msg: Optional[str] = None
    ):
        """Safely logs execution telemetry to Langfuse without blocking core flow or exposing secrets."""
        if not self.langfuse:
            return
        try:
            trace = self.langfuse.trace(
                id=trace_id,
                name="nvidia_nim_recovery_recommendation",
                metadata={
                    "model": self.model,
                    "failure_category": context.failure_category,
                    "priority_tier": context.priority_tier,
                    "amount_paise": context.amount_paise,
                    "retry_count": context.retry_count,
                    "latency_ms": latency_ms,
                    "is_fallback": plan.is_fallback,
                }
            )
            trace.generation(
                name="recommend_strategy",
                model=self.model,
                output=plan.model_dump(),
                metadata={"confidence": plan.confidence, "error": error_msg}
            )
        except Exception as e:
            logger.warning(f"Non-blocking Langfuse logging notice: {e}")

    async def get_recovery_recommendation(
        self,
        context: RecoveryContext
    ) -> ProposedRecoveryPlan:
        """
        Queries NVIDIA NIM for a structured recovery recommendation.
        Enforces 3.0s timeout, Pydantic validation, confidence threshold (>= 0.80), and fallback logic.
        """
        trace_id = f"trc_{uuid.uuid4().hex[:12]}"
        start_time = time.perf_counter()

        user_prompt = build_recovery_user_prompt(
            amount_paise=context.amount_paise,
            failure_category=context.failure_category,
            priority_tier=context.priority_tier,
            priority_score=context.priority_score,
            retry_count=context.retry_count,
            customer_tier=context.customer_tier,
            payday_day_of_month=context.payday_day_of_month,
            untrusted_customer_note=context.untrusted_customer_note
        )

        if not self.api_key or "YOUR_NVIDIA" in self.api_key or "mock" in self.api_key:
            logger.info("NVIDIA_API_KEY missing or placeholder -> Returning deterministic rule-based proposal.")
            fallback = self._generate_rule_based_recommendation(context)
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._log_langfuse_trace(trace_id, context, fallback, latency_ms)
            return fallback

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_RECOVERY_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": 512,
        }

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                url = f"{self.base_url}/chat/completions"
                response = await asyncio.wait_for(
                    client.post(url, headers=headers, json=payload),
                    timeout=self.TIMEOUT_SECONDS
                )

            latency_ms = (time.perf_counter() - start_time) * 1000

            if response.status_code != 200:
                logger.warning(f"NVIDIA NIM API HTTP {response.status_code}: {response.text[:200]}")
                fallback = self.get_deterministic_fallback(f"NVIDIA API HTTP {response.status_code}")
                self._log_langfuse_trace(trace_id, context, fallback, latency_ms, error_msg=response.text[:100])
                return fallback

            res_json = response.json()
            content_str = res_json["choices"][0]["message"]["content"].strip()

            # Clean potential markdown block wrapping
            if content_str.startswith("```"):
                content_str = content_str.split("```")[1]
                if content_str.startswith("json"):
                    content_str = content_str[4:]
                content_str = content_str.strip()

            plan_dict = json.loads(content_str)
            plan = ProposedRecoveryPlan(**plan_dict)

            # Enforce Confidence Floor Threshold
            if plan.confidence < self.CONFIDENCE_THRESHOLD:
                logger.info(
                    f"Low AI confidence ({plan.confidence} < {self.CONFIDENCE_THRESHOLD}) -> Triggering fallback plan."
                )
                fallback = self.get_deterministic_fallback(f"Low AI confidence ({plan.confidence:.2f})")
                self._log_langfuse_trace(trace_id, context, fallback, latency_ms)
                return fallback

            logger.info(
                f"NVIDIA NIM Recommendation Received: action='{plan.recommended_action.value}', "
                f"confidence={plan.confidence}, latency={latency_ms:.1f}ms"
            )
            self._log_langfuse_trace(trace_id, context, plan, latency_ms)
            return plan

        except asyncio.TimeoutError:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(f"NVIDIA NIM request timed out after {self.TIMEOUT_SECONDS}s.")
            fallback = self.get_deterministic_fallback("NVIDIA NIM Request SLA Timeout (>3.0s)")
            self._log_langfuse_trace(trace_id, context, fallback, latency_ms, error_msg="Timeout")
            return fallback
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"NVIDIA NIM agent execution exception: {e}")
            fallback = self.get_deterministic_fallback(f"NVIDIA Agent Exception: {type(e).__name__}")
            self._log_langfuse_trace(trace_id, context, fallback, latency_ms, error_msg=str(e))
            return fallback

    def _generate_rule_based_recommendation(self, context: RecoveryContext) -> ProposedRecoveryPlan:
        """
        Rule-based recommendation generator used when offline or testing without cloud API keys.
        """
        cat = context.failure_category
        retries = context.retry_count

        if retries >= 3:
            return ProposedRecoveryPlan(
                recommended_action=ActionEnum.NO_AUTOMATED_ACTION,
                delay_hours=0,
                timing=TimingEnum.NONE,
                message_strategy=MessageStrategyEnum.NONE,
                reasoning_summary="Maximum retry limit reached (3 attempts). Halting automated actions.",
                confidence=0.95,
                is_fallback=False
            )

        if cat == "LIQUIDITY_FRICTION":
            return ProposedRecoveryPlan(
                recommended_action=ActionEnum.RETRY_SCHEDULED,
                delay_hours=48,
                timing=TimingEnum.AFTER_PAYDAY,
                message_strategy=MessageStrategyEnum.HINGLISH,
                dunning_message="Aapka payment retry scheduled hai. Kripya account balance check karein.",
                reasoning_summary="Liquidity friction detected. Scheduling retry after payday alignment window.",
                confidence=0.88,
                is_fallback=False
            )
        elif cat == "TRANSIENT_INFRASTRUCTURE":
            return ProposedRecoveryPlan(
                recommended_action=ActionEnum.RETRY_SCHEDULED,
                delay_hours=2,
                timing=TimingEnum.IMMEDIATE,
                message_strategy=MessageStrategyEnum.CONCISE,
                dunning_message=None,
                reasoning_summary="Transient bank timeout. Immediate short-delay retry recommended.",
                confidence=0.92,
                is_fallback=False
            )
        elif cat == "INSTRUMENT_INVALIDATION":
            return ProposedRecoveryPlan(
                recommended_action=ActionEnum.SEND_PAYMENT_LINK,
                delay_hours=12,
                timing=TimingEnum.DELAYED,
                message_strategy=MessageStrategyEnum.FORMAL,
                dunning_message="Your card has expired. Please update your payment method via the link below.",
                reasoning_summary="Expired card detected. Direct retry will fail; sending payment link.",
                confidence=0.90,
                is_fallback=False
            )
        else:
            return ProposedRecoveryPlan(
                recommended_action=ActionEnum.CUSTOMER_REMINDER,
                delay_hours=24,
                timing=TimingEnum.DELAYED,
                message_strategy=MessageStrategyEnum.CONCISE,
                dunning_message="Friendly reminder regarding your subscription payment.",
                reasoning_summary="Unclassified failure. Sending polite customer reminder notice.",
                confidence=0.82,
                is_fallback=False
            )
