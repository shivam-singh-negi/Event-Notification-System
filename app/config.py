"""
Application configuration.

All environment-driven configuration values are loaded
and exposed through this module.
"""

import os
from dotenv import load_dotenv

# Load values from .env into environment variables
load_dotenv()


# Application
APP_NAME = os.getenv("APP_NAME", "event-notification-system")
APP_ENV = os.getenv("APP_ENV", "development")

# Server
APP_PORT = int(os.getenv("APP_PORT", 8000))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Processing
FAILURE_RATE = float(os.getenv("FAILURE_RATE", 0.1))
