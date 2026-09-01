"""
Temporal Workflow Activities
Defines non-deterministic side-effect boundaries for RecoverAI workflows.
"""

from typing import Optional, Dict, Any
from temporalio import activity
from backend.app.services.diagnosis_service import DiagnosisService
from backend.app.services.risk_service import RiskService
from backend.app.ai.agent import NvidiaNIMAgent
from backend.app.ai.schemas import RecoveryContext
from backend.app.policy.engine import OPAGovernanceEngine
from backend.app.services.razorpay_service import RazorpayService
from backend.app.services.notification_service import NotificationService


@activity.defn
async def diagnose_failure_activity(
    error_code: Optional[str] = None,
    error_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Activity wrapping deterministic failure taxonomy classification.
    """
    res = DiagnosisService.diagnose_failure(code=error_code, reason=error_reason)
    return res.model_dump()


@activity.defn
async def calculate_risk_activity(
    amount_paise: int,
    category_str: str,
    retry_count: int = 0
) -> Dict[str, Any]:
    """
    Activity wrapping deterministic Revenue-at-Risk assessment & priority scoring.
    """
    from backend.app.schemas.diagnosis import FailureCategory
    cat_enum = FailureCategory(category_str)
    res = RiskService.assess_risk(amount_paise=amount_paise, category=cat_enum, retry_count=retry_count)
    return res.model_dump()


@activity.defn
async def get_ai_recommendation_activity(context_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Activity wrapping NVIDIA NIM AI recovery strategy proposal agent.
    """
    ctx = RecoveryContext(**context_dict)
    agent = NvidiaNIMAgent()
    plan = await agent.get_recovery_recommendation(ctx)
    return plan.model_dump()


@activity.defn
async def evaluate_governance_activity(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Activity wrapping Open Policy Agent Rego governance firewall.
    """
    engine = OPAGovernanceEngine()
    decision = await engine.evaluate_policy(input_data)
    return decision.model_dump()


@activity.defn
async def prepare_recovery_action_activity(
    proposal_dict: Dict[str, Any],
    case_id: str
) -> Dict[str, Any]:
    """
    Phase 6 Orchestration Action Boundary.
    Prepares candidate action payload metadata without executing financial transactions.
    """
    action_type = proposal_dict.get("recommended_action", "NO_AUTOMATED_ACTION")
    delay_hours = proposal_dict.get("delay_hours", 0)

    activity.logger.info(
        f"Phase 6 Action Prepared for case '{case_id}': action_type='{action_type}', delay_hours={delay_hours}"
    )

    return {
        "prepared_action_id": f"act_prep_{case_id}",
        "case_id": case_id,
        "action_type": action_type,
        "delay_hours": delay_hours,
        "execution_status": "PREPARED",
        "is_executed": False
    }


@activity.defn
async def execute_recovery_action_activity(
    case_id: str,
    payment_id: str,
    amount_paise: int,
    proposal_dict: Dict[str, Any],
    governance_decision: Dict[str, Any],
    idempotency_key: str,
    customer_info: Optional[Dict[str, Any]] = None,
    invoice_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Phase 7 Real Outbound Action Execution Boundary.
    Executes outbound Razorpay or Novu API operations ONLY if OPA governance allows it.
    """
    # 1. OPA SAFETY GATE: Never execute outbound actions if OPA decision is not allow=True
    if not governance_decision.get("allow", False):
        activity.logger.warning(
            f"OPA SAFETY GATE DENIED: Outbound execution blocked for case '{case_id}'. "
            f"Violations: {governance_decision.get('violations')}"
        )
        return {
            "status": "DENIED_BY_OPA",
            "executed": False,
            "violations": governance_decision.get("violations", []),
            "idempotency_key": idempotency_key
        }

    action_type = proposal_dict.get("recommended_action", "NO_AUTOMATED_ACTION")
    customer = customer_info or {"name": "Customer", "email": "customer@example.com", "contact": "+919999999999"}
    customer_id = customer.get("customer_id", f"cust_{case_id}")

    razorpay_svc = RazorpayService()
    noti_svc = NotificationService()

    external_response = {}

    if action_type == "SEND_PAYMENT_LINK":
        description = proposal_dict.get("reasoning_summary", "RecoverAI Revenue Recovery Payment Link")
        external_response = await razorpay_svc.create_payment_link(
            amount_paise=amount_paise,
            customer=customer,
            description=description,
            idempotency_key=idempotency_key
        )
    elif action_type == "RETRY_SCHEDULED":
        external_response = await razorpay_svc.retry_payment(
            payment_id=payment_id,
            idempotency_key=idempotency_key,
            invoice_id=invoice_id,
            subscription_id=subscription_id
        )
    elif action_type == "CUSTOMER_REMINDER":
        message_body = proposal_dict.get("dunning_message", "Friendly reminder regarding your subscription payment.")
        strategy = proposal_dict.get("message_strategy", "CONCISE")
        external_response = await noti_svc.send_dunning_message(
            customer_id=customer_id,
            message_strategy=strategy,
            message_body=message_body,
            subscriber_email=customer.get("email")
        )
    elif action_type == "NO_AUTOMATED_ACTION":
        return {
            "status": "NO_AUTOMATED_ACTION",
            "executed": True,
            "idempotency_key": idempotency_key,
            "response": {"info": "No automated action requested by policy."}
        }
    else:
        raise ValueError(f"Unsupported action type for execution: '{action_type}'")

    return {
        "status": "EXECUTED",
        "action_type": action_type,
        "executed": True,
        "idempotency_key": idempotency_key,
        "external_response": external_response
    }
