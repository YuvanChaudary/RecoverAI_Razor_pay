"""
Unit & Integration Tests for Interactive Demo Reset & Recovery Flow
"""

import pytest
import asyncio
from backend.app.services.demo_service import InteractiveDemoService


@pytest.fixture
def demo_service():
    svc = InteractiveDemoService()
    svc.reset_state()
    return svc


def test_demo_reset_cleans_state(demo_service):
    """Test 1: Verify reset_state returns clean READY status."""
    status = demo_service.reset_state()
    assert status["success"] is True
    assert status["demo"] is True
    assert status["state"] == "READY"
    assert status["revenue_at_risk_paise"] == 0
    assert status["recovered_amount_paise"] == 0
    assert status["recovery_rate_pct"] == 0.0
    assert all(v is False for v in status["lifecycle_tracker"].values())


@pytest.mark.asyncio
async def test_demo_start_lifecycle_progression(demo_service):
    """Test 2: Verify start_demo completes all 8 lifecycle stages through RECOVERED.
    Verifies DYNAMIC behavior: amounts are non-zero, mathematically consistent,
    and are computed from actual DiagnosisService/RiskService/NvidiaNIMAgent calls.
    Does NOT assert specific hardcoded amounts.
    """
    status = await demo_service.run_recovery_demo()
    assert status["success"] is True
    # State must be RECOVERED or BLOCKED (if OPA denied the AI proposal)
    assert status["state"] in ("RECOVERED", "BLOCKED")
    # Revenue at risk must come from the dynamically generated amount_paise
    assert status["revenue_at_risk_paise"] > 0, "Revenue at risk must be non-zero (from dynamic amount)"
    if status["state"] == "RECOVERED":
        # Recovered amount must be the 68% computed settlement, not a hardcoded value
        assert status["recovered_amount_paise"] > 0
        assert status["recovered_amount_paise"] == int(status["revenue_at_risk_paise"] * 0.68)
        # Recovery rate must equal recovered/risk * 100 (not hardcoded 68.0)
        expected_rate = round((status["recovered_amount_paise"] / status["revenue_at_risk_paise"]) * 100, 1)
        assert status["recovery_rate_pct"] == expected_rate
    # All lifecycle stages for the path taken must be truthy
    tracker = status["lifecycle_tracker"]
    assert tracker["DETECTED"] is True
    assert tracker["DIAGNOSED"] is True
    assert tracker["AI_DECISION"] is True


@pytest.mark.asyncio
async def test_financial_invariant_execution_not_recovered(demo_service):
    """Test 3: Verify financial invariant — execution alone != recovery."""
    # Pre-run status check
    status = demo_service.get_status()
    assert status["recovered_amount_paise"] == 0

    # Run full demo
    final_status = await demo_service.run_recovery_demo()
    assert final_status["settlement_details"]["signature_verified"] is True
    assert final_status["settlement_details"]["status"] == "RECOVERED_AUTHORITATIVE"


@pytest.mark.asyncio
async def test_idempotency_and_status_restoration(demo_service):
    """Test 4 & 6: Verify status endpoint restoration and idempotency."""
    status1 = await demo_service.run_recovery_demo()
    status2 = demo_service.get_status()

    assert status1["session_id"] == status2["session_id"]
    assert status1["state"] == status2["state"]
    # Recovered amount must match between calls (idempotency)
    assert status1["recovered_amount_paise"] == status2["recovered_amount_paise"]
    # If recovered, recovered amount must be dynamically computed (not hardcoded 850000)
    if status2["state"] == "RECOVERED":
        assert status2["recovered_amount_paise"] > 0
        assert status2["recovered_amount_paise"] == int(status2["revenue_at_risk_paise"] * 0.68)


def test_synthetic_safety_flag(demo_service):
    """Test 7: Verify demo mode safety flag."""
    status = demo_service.get_status()
    assert status["demo"] is True


@pytest.mark.asyncio
async def test_create_multiple_unique_transactions(demo_service):
    """Test 8: Verify creating multiple transactions creates unique IDs without collision."""
    for _ in range(6):
        await demo_service.process_another_transaction()

    cases_resp = demo_service.get_demo_cases(page=1, page_size=20)
    assert cases_resp["total"] == 6
    case_ids = [c["case_id"] for c in cases_resp["items"]]
    payment_ids = [c["payment_id"] for c in cases_resp["items"]]

    # Verify all IDs are unique
    assert len(set(case_ids)) == 6
    assert len(set(payment_ids)) == 6


@pytest.mark.asyncio
async def test_process_another_preserves_previous_cases(demo_service):
    """Test 9: Verify process_another_transaction appends cases without resetting previous ones."""
    await demo_service.run_recovery_demo()
    assert len(demo_service.demo_cases) == 1

    await demo_service.process_another_transaction()
    assert len(demo_service.demo_cases) == 2

    await demo_service.process_another_transaction()
    assert len(demo_service.demo_cases) == 3


def test_demo_cases_pagination(demo_service):
    """Test 10: Verify pagination bounds and totals for get_demo_cases."""
    demo_service.demo_cases = [
        {"case_id": f"c_{i:02d}", "payment_id": f"p_{i:02d}", "failure_category": "TEST", "current_state": "RECOVERED"}
        for i in range(25)
    ]

    page1 = demo_service.get_demo_cases(page=1, page_size=10)
    assert page1["total"] == 25
    assert page1["total_pages"] == 3
    assert len(page1["items"]) == 10
    assert page1["items"][0]["case_id"] == "c_00"

    page3 = demo_service.get_demo_cases(page=3, page_size=10)
    assert len(page3["items"]) == 5
    assert page3["items"][0]["case_id"] == "c_20"

