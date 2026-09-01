"""
Temporal Client Infrastructure Integration
"""

import logging
from typing import Optional
from temporalio.client import Client
from backend.app.core.config import get_settings

logger = logging.getLogger("recoverai.temporal_client")


async def get_temporal_client(
    host: Optional[str] = None,
    namespace: Optional[str] = None
) -> Client:
    """
    Asynchronously initializes and connects to the Temporal server.
    Fail-fast: Raises ConnectionError if Temporal service is unreachable.
    """
    settings = get_settings()
    target_host = host or settings.TEMPORAL_HOST or "localhost:7233"
    target_namespace = namespace or settings.TEMPORAL_NAMESPACE or "default"

    try:
        logger.info(f"Connecting to Temporal server at {target_host} (namespace={target_namespace})...")
        client = await Client.connect(
            target_host,
            namespace=target_namespace
        )
        logger.info("Successfully connected to Temporal server.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Temporal server at {target_host}: {e}")
        raise ConnectionError(f"Temporal server at {target_host} is unavailable: {e}") from e
