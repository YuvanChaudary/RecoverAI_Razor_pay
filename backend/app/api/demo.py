"""
Interactive Demo Endpoints Router for RecoverAI.
Exposes POST /api/demo/reset, POST /api/demo/start, and GET /api/demo/status.
"""

from fastapi import APIRouter, status, BackgroundTasks
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.app.services.demo_service import InteractiveDemoService

router = APIRouter(tags=["Interactive Demo"])
demo_service = InteractiveDemoService()


class DynamicTransactionRequest(BaseModel):
    amount_paise: Optional[int] = Field(None, description="Monetary value in integer paise")
    raw_gateway_code: Optional[str] = Field(None, description="Raw gateway error code (e.g., insufficient_funds, expired_card)")
    retry_count: Optional[int] = Field(None, description="Previous retry count for transaction")
    cooldown_hours: Optional[float] = Field(None, description="Cooldown window in hours")
    is_terminal_decline: Optional[bool] = Field(None, description="Terminal decline indicator")
    simulate_settlement: Optional[bool] = Field(None, description="Flag to simulate authoritative settlement webhook")
    captured_amount_paise: Optional[int] = Field(None, description="Settled recovery amount in integer paise")


@router.post("/demo/reset", status_code=status.HTTP_200_OK)
@router.post("/api/demo/reset", status_code=status.HTTP_200_OK)
async def reset_demo() -> Dict[str, Any]:
    """
    Resets the interactive demo state to READY state and clears database tables.
    """
    return await demo_service.reset_state_async()


@router.get("/demo/status", status_code=status.HTTP_200_OK)
@router.get("/api/demo/status", status_code=status.HTTP_200_OK)
async def get_demo_status() -> Dict[str, Any]:
    """
    Returns current interactive demo status (supports frontend F5 page refresh restoration).
    """
    return demo_service.get_status()


@router.post("/demo/start", status_code=status.HTTP_200_OK)
@router.post("/api/demo/start", status_code=status.HTTP_200_OK)
async def start_demo() -> Dict[str, Any]:
    """
    Triggers an interactive 8-stage synthetic recovery transaction.
    """
    return await demo_service.run_recovery_demo()


@router.post("/demo/transaction", status_code=status.HTTP_200_OK)
@router.post("/api/demo/transaction", status_code=status.HTTP_200_OK)
async def process_another_transaction(req: Optional[DynamicTransactionRequest] = None) -> Dict[str, Any]:
    """
    Dynamically creates and processes a new synthetic transaction from input event data without deleting previous demo cases.
    """
    payload = req.model_dump() if req else None
    return await demo_service.process_another_transaction(transaction_input=payload)



@router.get("/demo/cases", status_code=status.HTTP_200_OK)
@router.get("/api/demo/cases", status_code=status.HTTP_200_OK)
async def get_demo_cases(
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    status: str = "ALL"
) -> Dict[str, Any]:
    """
    Returns paginated interactive demo cases.
    """
    return demo_service.get_demo_cases(page=page, page_size=page_size, search=search, status=status)

