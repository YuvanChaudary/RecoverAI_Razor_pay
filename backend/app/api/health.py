"""
System Health & Readiness Diagnostic Endpoints
"""

import httpx
from fastapi import APIRouter, Response, status
from typing import Dict, Any

from backend.app.core.config import get_settings
from backend.app.policy.engine import OPAGovernanceEngine
from backend.app.services.immutable_audit_service import ImmutableAuditService
from backend.app.db.database import get_db

router = APIRouter(tags=["System"])
settings = get_settings()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Liveness probe endpoint verifying basic application web server uptime.
    Preserves exact backward compatibility with Phase 1-12 contract.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
    }


@router.get("/ready")
async def readiness_check(response: Response) -> Dict[str, Any]:
    """
    Readiness probe endpoint checking downstream service connectivity.
    Exposes safe statuses without leaking credentials or secrets.
    """
    import asyncio
    import socket

    readiness: Dict[str, str] = {
        "postgres": "UNKNOWN",
        "opa": "UNKNOWN",
        "temporal": "UNKNOWN",
        "immudb": "UNKNOWN",
    }

    # Helper for fast TCP port check
    async def check_tcp(host: str, port: int) -> bool:
        try:
            _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=0.1)
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    import os
    from urllib.parse import urlparse

    pg_host = os.getenv("POSTGRES_HOST", getattr(settings, "POSTGRES_HOST", "127.0.0.1"))
    opa_url = os.getenv("OPA_URL", getattr(settings, "OPA_URL", "http://127.0.0.1:8181"))
    opa_host = urlparse(opa_url).hostname or "127.0.0.1"
    temporal_host = os.getenv("TEMPORAL_HOST", getattr(settings, "TEMPORAL_HOST", "127.0.0.1")).split(":")[0]
    immudb_host = os.getenv("IMMUDB_HOST", getattr(settings, "IMMUDB_HOST", "127.0.0.1"))

    async def check_service(host: str, port: int) -> bool:
        if await check_tcp(host, port):
            return True
        if host not in ("127.0.0.1", "localhost") and await check_tcp("127.0.0.1", port):
            return True
        return False

    from sqlalchemy import text

    # 1. PostgreSQL Check (Port 5432)
    try:
        pg_open = await check_service(pg_host, 5432)
        if pg_open:
            async for session in get_db():
                await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=0.5)
                readiness["postgres"] = "HEALTHY"
                break
        else:
            readiness["postgres"] = "DEGRADED"
    except Exception as e:
        readiness["postgres"] = "DEGRADED"

    # 2. OPA Check (Port 8181)
    try:
        opa_open = await check_service(opa_host, 8181)
        readiness["opa"] = "HEALTHY" if opa_open else "DEGRADED"
    except Exception:
        readiness["opa"] = "DEGRADED"

    # 3. Temporal Check (Port 7233)
    try:
        temporal_open = await check_service(temporal_host, 7233)
        readiness["temporal"] = "HEALTHY" if temporal_open else "DEGRADED"
    except Exception:
        readiness["temporal"] = "DEGRADED"

    # 4. immudb Check (Port 3322)
    try:
        immudb_open = await check_service(immudb_host, 3322)
        readiness["immudb"] = "HEALTHY" if immudb_open else "DEGRADED"
    except Exception:
        readiness["immudb"] = "DEGRADED"

    is_ready = all(v == "HEALTHY" for v in readiness.values())
    overall_status = "READY" if is_ready else "PARTIALLY_DEGRADED"

    return {
        "status": overall_status,
        "service": settings.APP_NAME,
        "components": readiness
    }


@router.post("/demo/reset_metrics", status_code=status.HTTP_200_OK)
async def demo_reset_metrics() -> Dict[str, Any]:
    """
    Demo Reset Endpoint: Clears diagnostic counters and resets live presentation state.
    Allows judges and hiring managers to reset state and observe fresh live transaction processing.
    """
    from datetime import datetime
    from backend.app.services.demo_service import InteractiveDemoService
    demo_service = InteractiveDemoService()
    return await demo_service.reset_state_async()

