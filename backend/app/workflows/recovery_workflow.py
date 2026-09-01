"""
Temporal Durable Recovery Workflow
Deterministic Saga Orchestration Engine for RecoverAI
"""

from datetime import timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activity definitions for type hints in workflow execution
with workflow.unsafe.imports_passed_through():
    from backend.app.workflows.activities import (
        diagnose_failure_activity,
        calculate_risk_activity,
        get_ai_recommendation_activity,
        evaluate_governance_activity,
        prepare_recovery_action_activity,
        execute_recovery_action_activity,
    )


class RecoveryWorkflowInput(BaseModel):
    """
    Input payload for RecoverySagaWorkflow.
    """
    case_id: str = Field(..., description="RecoveryCase identifier")
    payment_id: str = Field(..., description="Razorpay payment identifier")
    amount_paise: int = Field(..., description="Payment amount in integer paise")
    error_code: Optional[str] = Field(None, description="Razorpay error code")
    error_reason: Optional[str] = Field(None, description="Razorpay error reason")
    retry_count: int = Field(default=0, description="Current retry attempt count")
    customer_tier: str = Field(default="STANDARD", description="Customer tier")
    payday_day_of_month: int = Field(default=1, description="Payday day of month")
    is_terminal_decline: bool = Field(default=False, description="Flag indicating terminal decline")
    cooldown_hours: float = Field(default=24.0, description="Hours since last attempt")
    pre_debit_notice_required: bool = Field(default=False, description="Flag indicating pre-debit notice requirement")
    pre_debit_notice_sent: bool = Field(default=False, description="Flag indicating pre-debit notice sent")
    untrusted_customer_note: Optional[str] = Field(None, description="Untrusted customer note")
    invoice_id: Optional[str] = Field(None, description="Associated Razorpay invoice identifier if available")
    subscription_id: Optional[str] = Field(None, description="Associated Razorpay subscription identifier if available")
    customer_info: Optional[Dict[str, Any]] = Field(None, description="Customer metadata for outbound actions")


class RecoveryWorkflowResult(BaseModel):
    """
    Orchestration result payload returned by RecoverySagaWorkflow.
    """
    case_id: str
    status: str
    diagnosis: Dict[str, Any]
    risk: Dict[str, Any]
    ai_recommendation: Dict[str, Any]
    governance_allowed: bool
    governance_violations: List[str] = Field(default_factory=list)
    action_prepared: Optional[Dict[str, Any]] = None
    action_executed: Optional[Dict[str, Any]] = None
    workflow_completed: bool = True


@workflow.defn(sandboxed=False)
class RecoverySagaWorkflow:
    """
    Durable Saga Workflow for RecoverAI.
    Orchestrates failure diagnosis, risk assessment, AI proposal, OPA governance,
    durable sleeping, and outbound action dispatch boundaries.
    """

    @workflow.run
    async def run(self, input_data: RecoveryWorkflowInput) -> RecoveryWorkflowResult:
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )

        # Generate deterministic idempotency key for application & external APIs
        idempotency_key = f"rec_idemp_{input_data.payment_id}_{input_data.retry_count + 1}"

        # 1. Execute Failure Diagnosis Activity
        diagnosis = await workflow.execute_activity(
            diagnose_failure_activity,
            args=[input_data.error_code, input_data.error_reason],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        # 2. Execute Revenue-at-Risk Assessment Activity
        risk = await workflow.execute_activity(
            calculate_risk_activity,
            args=[input_data.amount_paise, diagnosis["category"], input_data.retry_count],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        # 3. Execute AI Recommendation Activity
        ai_context = {
            "amount_paise": input_data.amount_paise,
            "failure_category": diagnosis["category"],
            "priority_tier": risk["priority_tier"],
            "priority_score": risk["priority_score"],
            "retry_count": input_data.retry_count,
            "customer_tier": input_data.customer_tier,
            "payday_day_of_month": input_data.payday_day_of_month,
            "untrusted_customer_note": input_data.untrusted_customer_note,
        }
        ai_recommendation = await workflow.execute_activity(
            get_ai_recommendation_activity,
            args=[ai_context],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        # 4. Execute OPA Governance Firewall Activity
        opa_input = {
            "action": ai_recommendation["recommended_action"],
            "confidence": ai_recommendation["confidence"],
            "retry_count": input_data.retry_count,
            "cooldown_hours": input_data.cooldown_hours,
            "is_terminal_decline": input_data.is_terminal_decline,
            "pre_debit_notice_required": input_data.pre_debit_notice_required,
            "pre_debit_notice_sent": input_data.pre_debit_notice_sent,
        }
        governance = await workflow.execute_activity(
            evaluate_governance_activity,
            args=[opa_input],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        # 5. OPA Governance Check: If DENIED, stop downstream action execution immediately
        if not governance.get("allow", False):
            workflow.logger.warning(
                f"Workflow for case '{input_data.case_id}' DENIED by OPA: {governance.get('violations')}"
            )
            return RecoveryWorkflowResult(
                case_id=input_data.case_id,
                status="GOVERNANCE_DENIED",
                diagnosis=diagnosis,
                risk=risk,
                ai_recommendation=ai_recommendation,
                governance_allowed=False,
                governance_violations=governance.get("violations", []),
                action_prepared=None,
                action_executed=None,
                workflow_completed=True,
            )

        # 6. Prepare Action Boundary Activity
        action_prepared = await workflow.execute_activity(
            prepare_recovery_action_activity,
            args=[ai_recommendation, input_data.case_id],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        # 7. Durable Timer Execution: Uses workflow.sleep() for O(1) memory waiting
        delay_hours = ai_recommendation.get("delay_hours", 0)
        if delay_hours > 0:
            workflow.logger.info(f"Durable sleep engaged: waiting {delay_hours} hours via Temporal durable timer...")
            await workflow.sleep(timedelta(hours=delay_hours))

        # 8. Execute Real Outbound Recovery Action Boundary Activity (Phase 7)
        action_executed = await workflow.execute_activity(
            execute_recovery_action_activity,
            args=[
                input_data.case_id,
                input_data.payment_id,
                input_data.amount_paise,
                ai_recommendation,
                governance,
                idempotency_key,
                input_data.customer_info,
                input_data.invoice_id,
                input_data.subscription_id,
            ],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        return RecoveryWorkflowResult(
            case_id=input_data.case_id,
            status="ACTION_EXECUTED" if action_executed.get("executed") else "ACTION_FAILED",
            diagnosis=diagnosis,
            risk=risk,
            ai_recommendation=ai_recommendation,
            governance_allowed=True,
            governance_violations=[],
            action_prepared=action_prepared,
            action_executed=action_executed,
            workflow_completed=True,
        )
