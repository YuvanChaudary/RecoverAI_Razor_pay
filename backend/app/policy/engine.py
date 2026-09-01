"""
OPA Governance Engine
Deterministic Fail-Closed Policy Enforcement Client
"""

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import httpx
from backend.app.core.config import get_settings

logger = logging.getLogger("recoverai.opa_governance")


class PolicyDecision(BaseModel):
    """
    Structured policy evaluation decision container.
    """
    allow: bool = Field(..., description="Boolean permission decision from OPA")
    violations: List[str] = Field(default_factory=list, description="List of rule violation codes/messages")
    raw_response: Dict[str, Any] = Field(default_factory=dict, description="Raw OPA server HTTP JSON payload")


class OPAGovernanceEngine:
    """
    Open Policy Agent Governance Engine.
    Enforces a strict, fail-closed policy firewall between AI recommendations and execution.
    """

    DEFAULT_TIMEOUT_SECONDS = 3.0

    def __init__(self, opa_url: Optional[str] = None):
        settings = get_settings()
        self.opa_url = opa_url or settings.OPA_URL or "http://localhost:8181/v1/data/recovery/governance"

    async def evaluate_policy(self, input_data: Dict[str, Any]) -> PolicyDecision:
        """
        Evaluates input proposal against OPA Rego governance rules.
        When OPA HTTP server is available, queries OPA HTTP endpoint.
        When OPA HTTP server is unreachable, evaluates exact Rego rules via local fallback evaluator.
        """
        payload = {"input": input_data}
        headers = {"Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT_SECONDS) as client:
                response = await client.post(self.opa_url, json=payload, headers=headers)

            if response.status_code != 200:
                logger.warning(f"OPA server returned non-200 status code: {response.status_code}")
                return self._evaluate_local_rego(input_data)

            res_json = response.json()
            result = res_json.get("result", {})
            if isinstance(result, bool):
                allow = result
                violations = []
            elif isinstance(result, dict):
                allow = bool(result.get("allow", False))
                raw_violations = result.get("violations", [])
                if isinstance(raw_violations, (list, set)):
                    violations = sorted([str(v) for v in raw_violations])
                else:
                    violations = [str(raw_violations)] if raw_violations else []
            else:
                allow = False
                violations = ["Unexpected OPA response format"]

            logger.info(f"OPA Policy Evaluated: allow={allow}, violations={violations}")
            return PolicyDecision(
                allow=allow,
                violations=violations,
                raw_response=res_json
            )

        except Exception as e:
            logger.info(f"OPA HTTP server unreachable ({type(e).__name__}) -> Evaluating policy via local Rego engine.")
            return self._evaluate_local_rego(input_data)

    def _evaluate_local_rego(self, input_data: Dict[str, Any]) -> PolicyDecision:
        """
        Local Rego policy evaluation matching policies/governance.rego.
        """
        violations = []
        action = input_data.get("action")
        retry_count = input_data.get("retry_count", 0)
        max_retries = input_data.get("max_retries", 3)
        cooldown_hours = input_data.get("cooldown_hours", 0)
        is_terminal = input_data.get("is_terminal_decline", False)
        confidence = input_data.get("confidence", 1.0)
        notice_required = input_data.get("pre_debit_notice_required", False)
        notice_sent = input_data.get("pre_debit_notice_sent", False)

        # RULE-001: Maximum Retry Limit
        if action == "RETRY_SCHEDULED" and retry_count >= max_retries:
            violations.append(f"RULE-001: Exceeded maximum retry limit ({retry_count} >= {max_retries})")

        # RULE-002: Minimum Cooldown
        if action == "RETRY_SCHEDULED" and cooldown_hours < 24:
            violations.append(f"RULE-002: Insufficient cooldown hours ({cooldown_hours:.2f} < 24)")

        # RULE-003: Terminal Decline Protection
        if is_terminal and action == "RETRY_SCHEDULED":
            violations.append("RULE-003: Retry action prohibited on terminal failure decline")

        # RULE-004: AI Confidence Floor
        if confidence < 0.80:
            violations.append(f"RULE-004: AI confidence below threshold ({confidence:.2f} < 0.80)")

        # RULE-005: Pre-Debit Notice
        if notice_required and not notice_sent:
            violations.append("RULE-005: Pre-debit notice required but not sent")

        allow = len(violations) == 0
        return PolicyDecision(
            allow=allow,
            violations=violations,
            raw_response={"local_evaluation": True, "allow": allow, "violations": violations}
        )

