"""
Operational Metrics Collector for RecoverAI Architecture
Provides thread-safe in-memory counters for system events and decision metrics.
"""

import threading
from typing import Dict, Any


class MetricsCollector:
    """
    Lightweight, thread-safe operational metrics collector.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = {
            "webhooks_received": 0,
            "webhook_signature_failures": 0,
            "duplicate_webhooks": 0,
            "recovery_actions_attempted": 0,
            "recovery_actions_executed": 0,
            "recovery_actions_failed": 0,
            "opa_allow_decisions": 0,
            "opa_deny_decisions": 0,
            "razorpay_outbound_failures": 0,
            "novu_notification_failures": 0,
            "state_transitions_succeeded": 0,
            "state_transitions_failed": 0,
            "idempotency_duplicates_detected": 0,
        }

    def increment(self, metric_name: str, amount: int = 1):
        """
        Increments metric counter by amount.
        """
        with self._lock:
            if metric_name in self._counters:
                self._counters[metric_name] += amount
            else:
                self._counters[metric_name] = amount

    def get_metrics(self) -> Dict[str, int]:
        """
        Returns copy of all current metric counters.
        """
        with self._lock:
            return dict(self._counters)

    def reset(self):
        """
        Resets all counters to zero (useful for tests).
        """
        with self._lock:
            for k in self._counters:
                self._counters[k] = 0


# Global singleton metrics instance
metrics = MetricsCollector()
