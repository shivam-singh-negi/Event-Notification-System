"""
Application configuration.

All environment-driven configuration values are loaded
and exposed through this module.

This module is the SINGLE source of truth for runtime config.
"""

import os
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Load environment variables
# -------------------------------------------------------------------

load_dotenv()


# -------------------------------------------------------------------
# Helpers (fail fast on bad config)
# -------------------------------------------------------------------

def _get_int(name: str, default: int) -> int:
    value = os.getenv(name, default)
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid value for {name}: expected int, got '{value}'"
        ) from exc


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name, default)
    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid value for {name}: expected float, got '{value}'"
        ) from exc


# -------------------------------------------------------------------
# Application
# -------------------------------------------------------------------

APP_NAME = os.getenv("APP_NAME", "event-notification-system")
APP_ENV = os.getenv("APP_ENV", "development")

# -------------------------------------------------------------------
# Server
# -------------------------------------------------------------------

APP_PORT = _get_int("APP_PORT", 8080)

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# -------------------------------------------------------------------
# Event Processing
# -------------------------------------------------------------------

EMAIL_PROCESSING_TIME = _get_int("EMAIL_PROCESSING_TIME", 5)
SMS_PROCESSING_TIME = _get_int("SMS_PROCESSING_TIME", 3)
PUSH_PROCESSING_TIME = _get_int("PUSH_PROCESSING_TIME", 2)

FAILURE_RATE = _get_float("FAILURE_RATE", 0.1)
