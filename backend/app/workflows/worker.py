"""
Temporal Standalone Worker Entrypoint
Runs a worker listening on the recoverai-recovery task queue.
"""

import asyncio
import logging
from temporalio.worker import Worker
from backend.app.integrations.temporal_client import get_temporal_client
from backend.app.workflows.recovery_workflow import RecoverySagaWorkflow
from backend.app.workflows.activities import (
    diagnose_failure_activity,
    calculate_risk_activity,
    get_ai_recommendation_activity,
    evaluate_governance_activity,
    prepare_recovery_action_activity,
    execute_recovery_action_activity,
)
from backend.app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recoverai.worker")


async def run_worker():
    """
    Connects to Temporal server and starts worker processing tasks.
    """
    settings = get_settings()
    client = await get_temporal_client()
    task_queue = settings.TEMPORAL_TASK_QUEUE or "recoverai-recovery"

    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[RecoverySagaWorkflow],
        activities=[
            diagnose_failure_activity,
            calculate_risk_activity,
            get_ai_recommendation_activity,
            evaluate_governance_activity,
            prepare_recovery_action_activity,
            execute_recovery_action_activity,
        ],
    )

    logger.info(f"Starting RecoverAI Temporal Worker on task queue: '{task_queue}'")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
