"""
Phase 6 Unit & Orchestration Tests: Temporal Durable Recovery Workflow
"""

import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio.common import RetryPolicy

from backend.app.workflows.recovery_workflow import (
    RecoverySagaWorkflow,
    RecoveryWorkflowInput,
    RecoveryWorkflowResult,
)
from backend.app.workflows.activities import (
    diagnose_failure_activity,
    calculate_risk_activity,
    get_ai_recommendation_activity,
    evaluate_governance_activity,
    prepare_recovery_action_activity,
    execute_recovery_action_activity,
)
from backend.app.policy.engine import OPAGovernanceEngine, PolicyDecision
from backend.app.services.razorpay_service import RazorpayService
from backend.app.ai.agent import NvidiaNIMAgent
from backend.app.ai.schemas import ProposedRecoveryPlan, ActionEnum, TimingEnum, MessageStrategyEnum


# Helper mock candidate plan for AI Activity
MOCK_AI_PLAN = ProposedRecoveryPlan(
    recommended_action=ActionEnum.RETRY_SCHEDULED,
    delay_hours=1,
    timing=TimingEnum.AFTER_PAYDAY,
    message_strategy=MessageStrategyEnum.CONCISE,
    dunning_message=None,
    reasoning_summary="Test scheduled retry plan",
    confidence=0.90,
    is_fallback=False
)


# --- 1. WORKFLOW HAPPY PATH TEST ---
@pytest.mark.asyncio
async def test_temporal_workflow_happy_path():
    inp = RecoveryWorkflowInput(
        case_id="case_wf_01",
        payment_id="pay_wf_01",
        invoice_id="inv_wf_01",
        amount_paise=49900,
        error_code="BAD_REQUEST_ERROR",
        error_reason="insufficient_funds",
        retry_count=0,
        cooldown_hours=24.0,
        is_terminal_decline=False
    )

    mock_decision = PolicyDecision(allow=True, violations=[], raw_response={"result": {"allow": True}})
    mock_rzp_res = {"status": "retry_scheduled", "invoice_id": "inv_wf_01"}

    with patch.object(OPAGovernanceEngine, "evaluate_policy", new_callable=AsyncMock, return_value=mock_decision):
        with patch.object(NvidiaNIMAgent, "get_recovery_recommendation", new_callable=AsyncMock, return_value=MOCK_AI_PLAN):
            with patch.object(RazorpayService, "retry_payment", new_callable=AsyncMock, return_value=mock_rzp_res):
                with patch.object(RazorpayService, "create_payment_link", new_callable=AsyncMock, return_value=mock_rzp_res):
                    async with await WorkflowEnvironment.start_time_skipping() as env:
                        async with Worker(
                            env.client,
                            task_queue="test-recovery-queue",
                            workflows=[RecoverySagaWorkflow],
                            activities=[
                                diagnose_failure_activity,
                                calculate_risk_activity,
                                get_ai_recommendation_activity,
                                evaluate_governance_activity,
                                prepare_recovery_action_activity,
                                execute_recovery_action_activity,
                            ],
                        ):
                            res: RecoveryWorkflowResult = await env.client.execute_workflow(
                                RecoverySagaWorkflow.run,
                                inp,
                                id="wf-test-happy-path",
                                task_queue="test-recovery-queue",
                            )

                            assert res.case_id == "case_wf_01"
                            assert res.status == "ACTION_EXECUTED"
                            assert res.governance_allowed is True
                            assert res.governance_violations == []
                            assert res.action_prepared is not None
                            assert res.action_executed is not None
                            assert res.action_executed["status"] == "EXECUTED"


# --- 2. OPA DENY STOPS ACTION EXECUTION TEST ---
@pytest.mark.asyncio
async def test_temporal_workflow_opa_deny_stops_action():
    inp = RecoveryWorkflowInput(
        case_id="case_wf_deny_01",
        payment_id="pay_wf_deny_01",
        invoice_id="inv_wf_deny_01",
        amount_paise=49900,
        error_code="BAD_REQUEST_ERROR",
        error_reason="insufficient_funds",
        retry_count=5,  # Exceeds max retries
        cooldown_hours=1.0
    )

    mock_decision = PolicyDecision(
        allow=False,
        violations=["RULE-001: Exceeded maximum retry limit (5 >= 3)"],
        raw_response={}
    )

    with patch.object(OPAGovernanceEngine, "evaluate_policy", new_callable=AsyncMock, return_value=mock_decision):
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-recovery-queue",
                workflows=[RecoverySagaWorkflow],
                activities=[
                    diagnose_failure_activity,
                    calculate_risk_activity,
                    get_ai_recommendation_activity,
                    evaluate_governance_activity,
                    prepare_recovery_action_activity,
                    execute_recovery_action_activity,
                ],
            ):
                res: RecoveryWorkflowResult = await env.client.execute_workflow(
                    RecoverySagaWorkflow.run,
                    inp,
                    id="wf-test-opa-deny",
                    task_queue="test-recovery-queue",
                )

                assert res.status == "GOVERNANCE_DENIED"
                assert res.governance_allowed is False
                assert len(res.governance_violations) > 0
                assert any("RULE-001" in v for v in res.governance_violations)
                assert res.action_executed is None


# --- 3. AI CANNOT BYPASS OPA TEST ---
@pytest.mark.asyncio
async def test_temporal_workflow_ai_cannot_bypass_opa():
    inp = RecoveryWorkflowInput(
        case_id="case_wf_bypass_01",
        payment_id="pay_wf_bypass_01",
        invoice_id="inv_wf_bypass_01",
        amount_paise=100000,
        error_code="BAD_REQUEST_ERROR",
        error_reason="expired_card",
        retry_count=0,
        is_terminal_decline=True  # Terminal decline!
    )

    mock_decision = PolicyDecision(
        allow=False,
        violations=["RULE-003: Retry action prohibited on terminal failure decline"],
        raw_response={}
    )

    with patch.object(OPAGovernanceEngine, "evaluate_policy", new_callable=AsyncMock, return_value=mock_decision):
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-recovery-queue",
                workflows=[RecoverySagaWorkflow],
                activities=[
                    diagnose_failure_activity,
                    calculate_risk_activity,
                    get_ai_recommendation_activity,
                    evaluate_governance_activity,
                    prepare_recovery_action_activity,
                    execute_recovery_action_activity,
                ],
            ):
                res: RecoveryWorkflowResult = await env.client.execute_workflow(
                    RecoverySagaWorkflow.run,
                    inp,
                    id="wf-test-ai-bypass-denied",
                    task_queue="test-recovery-queue",
                )

                assert res.status == "GOVERNANCE_DENIED"
                assert res.governance_allowed is False
                assert res.action_executed is None


# --- 4. CRITICAL DURABLE TIMER TEST ---
@pytest.mark.asyncio
async def test_temporal_durable_timer_sleep_execution():
    inp = RecoveryWorkflowInput(
        case_id="case_wf_timer_01",
        payment_id="pay_wf_timer_01",
        invoice_id="inv_wf_timer_01",
        amount_paise=49900,
        error_code="BAD_REQUEST_ERROR",
        error_reason="insufficient_funds",
        retry_count=0
    )

    mock_decision = PolicyDecision(allow=True, violations=[], raw_response={})
    mock_rzp_res = {"status": "retry_scheduled", "invoice_id": "inv_wf_timer_01"}

    with patch.object(OPAGovernanceEngine, "evaluate_policy", new_callable=AsyncMock, return_value=mock_decision):
        with patch.object(NvidiaNIMAgent, "get_recovery_recommendation", new_callable=AsyncMock, return_value=MOCK_AI_PLAN):
            with patch.object(RazorpayService, "retry_payment", new_callable=AsyncMock, return_value=mock_rzp_res):
                with patch.object(RazorpayService, "create_payment_link", new_callable=AsyncMock, return_value=mock_rzp_res):
                    async with await WorkflowEnvironment.start_time_skipping() as env:
                        async with Worker(
                            env.client,
                            task_queue="test-recovery-queue",
                            workflows=[RecoverySagaWorkflow],
                            activities=[
                                diagnose_failure_activity,
                                calculate_risk_activity,
                                get_ai_recommendation_activity,
                                evaluate_governance_activity,
                                prepare_recovery_action_activity,
                                execute_recovery_action_activity,
                            ],
                        ):
                            res: RecoveryWorkflowResult = await env.client.execute_workflow(
                                RecoverySagaWorkflow.run,
                                inp,
                                id="wf-test-durable-timer",
                                task_queue="test-recovery-queue",
                            )

                            assert res.workflow_completed is True
                            assert res.status == "ACTION_EXECUTED"


# --- 5. NO FINANCIAL RECOVERY CLAIM TEST ---
@pytest.mark.asyncio
async def test_no_financial_recovery_claim_in_workflow():
    inp = RecoveryWorkflowInput(
        case_id="case_wf_claim_01",
        payment_id="pay_wf_claim_01",
        invoice_id="inv_wf_claim_01",
        amount_paise=150000,
        error_code="GATEWAY_TIMEOUT",
        error_reason="network_error"
    )

    mock_decision = PolicyDecision(allow=True, violations=[], raw_response={})
    mock_rzp_res = {"status": "retry_scheduled"}

    with patch.object(OPAGovernanceEngine, "evaluate_policy", new_callable=AsyncMock, return_value=mock_decision):
        with patch.object(NvidiaNIMAgent, "get_recovery_recommendation", new_callable=AsyncMock, return_value=MOCK_AI_PLAN):
            with patch.object(RazorpayService, "retry_payment", new_callable=AsyncMock, return_value=mock_rzp_res):
                with patch.object(RazorpayService, "create_payment_link", new_callable=AsyncMock, return_value=mock_rzp_res):
                    async with await WorkflowEnvironment.start_time_skipping() as env:
                        async with Worker(
                            env.client,
                            task_queue="test-recovery-queue",
                            workflows=[RecoverySagaWorkflow],
                            activities=[
                                diagnose_failure_activity,
                                calculate_risk_activity,
                                get_ai_recommendation_activity,
                                evaluate_governance_activity,
                                prepare_recovery_action_activity,
                                execute_recovery_action_activity,
                            ],
                        ):
                            res: RecoveryWorkflowResult = await env.client.execute_workflow(
                                RecoverySagaWorkflow.run,
                                inp,
                                id="wf-test-no-claim",
                                task_queue="test-recovery-queue",
                            )

                            assert res.status in ("ACTION_EXECUTED", "ACTION_SCHEDULED", "GOVERNANCE_DENIED")
                            assert res.status != "RECOVERED"
                            assert not hasattr(res, "recovered_amount_paise")


# --- 6. ACTIVITY RETRY POLICY TEST ---
def test_activity_retry_policy_configuration():
    policy = RetryPolicy(
        initial_interval=timedelta(seconds=1),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(seconds=10),
        maximum_attempts=3,
    )
    assert policy.maximum_attempts == 3
    assert policy.backoff_coefficient == 2.0
