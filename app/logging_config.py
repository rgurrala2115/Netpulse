"""Standard logging and structlog JSON configuration."""

import logging
import sys
from collections.abc import MutableMapping
from typing import Any

import structlog


SENSITIVE_FIELDS = {"password", "token", "api_key", "authorization", "secret"}


def redact_sensitive_fields(_logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    def redact(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: "***" if str(key).lower() in SENSITIVE_FIELDS else redact(child)
                for key, child in value.items()
            }
        if isinstance(value, list):
            return [redact(child) for child in value]
        return value

    return redact(event_dict)


def configure_logging() -> None:
    netpulse_logger = logging.getLogger("netpulse")
    netpulse_logger.setLevel(logging.INFO)
    netpulse_logger.propagate = False
    if not netpulse_logger.handlers:
        netpulse_logger.addHandler(logging.StreamHandler(sys.stdout))

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            redact_sensitive_fields,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
