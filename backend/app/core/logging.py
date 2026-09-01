"""
Production Structured Logging & Secret Redaction Module
Formats logs in structured JSON/KV format and redacts sensitive credentials.
"""

import re
import json
import logging
from typing import Any, Dict

# Secret pattern matchers for redaction
SECRET_PATTERNS = [
    (re.compile(r"(RAZORPAY_KEY_SECRET|key_secret)\s*[:=]\s*['\"]?([^\s'\"]+)", re.IGNORECASE), r"\1=[REDACTED]"),
    (re.compile(r"(RAZORPAY_KEY_ID|key_id)\s*[:=]\s*['\"]?([^\s'\"]+)", re.IGNORECASE), r"\1=[REDACTED]"),
    (re.compile(r"(NOVU_API_KEY|api_key)\s*[:=]\s*['\"]?([^\s'\"]+)", re.IGNORECASE), r"\1=[REDACTED]"),
    (re.compile(r"(NVIDIA_API_KEY|NVIDIA_NIM_API_KEY)\s*[:=]\s*['\"]?([^\s'\"]+)", re.IGNORECASE), r"\1=[REDACTED]"),
    (re.compile(r"nvapi-[A-Za-z0-9_-]+", re.IGNORECASE), "[REDACTED]"),
    (re.compile(r"(POSTGRES_PASSWORD|IMMUDB_PASSWORD|password)\s*[:=]\s*['\"]?([^\s'\"]+)", re.IGNORECASE), r"\1=[REDACTED]"),
    (re.compile(r"(Authorization\s*[:=]?\s*)(Bearer|Basic)?\s*([^\s'\"]+)", re.IGNORECASE), r"\1\2 [REDACTED]"),
    (re.compile(r"(Bearer\s+)([^\s'\"]+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(X-Razorpay-Signature)\s*[:=]\s*['\"]?([^\s'\"]+)", re.IGNORECASE), r"\1=[REDACTED]"),
]


def redact_secrets(text: str) -> str:
    """
    Redacts sensitive keys, secrets, authorization tokens, and signatures from string content.
    """
    if not isinstance(text, str):
        text = str(text)

    redacted = text
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)

    return redacted


class RedactingFilter(logging.Filter):
    """
    Logging filter that automatically redacts secrets from log record messages and arguments.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: redact_secrets(str(v)) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_secrets(str(a)) if isinstance(a, str) else a for a in record.args)
        return True


class JSONLogFormatter(logging.Formatter):
    """
    Structured JSON log formatter including timestamps, levels, correlation IDs, and context metrics.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_secrets(record.getMessage()),
        }

        # Include correlation ID and extra context if present
        if hasattr(record, "correlation_id") and record.correlation_id:
            log_data["correlation_id"] = record.correlation_id
        if hasattr(record, "case_id") and record.case_id:
            log_data["case_id"] = record.case_id
        if hasattr(record, "payment_id") and record.payment_id:
            log_data["payment_id"] = record.payment_id
        if hasattr(record, "workflow_id") and record.workflow_id:
            log_data["workflow_id"] = record.workflow_id

        if record.exc_info:
            log_data["exception"] = redact_secrets(self.formatException(record.exc_info))

        return json.dumps(log_data)


def setup_structured_logging(log_level: int = logging.INFO):
    """
    Configures root logger with RedactingFilter and JSONLogFormatter.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(JSONLogFormatter())
    stream_handler.addFilter(RedactingFilter())

    root_logger.addHandler(stream_handler)
