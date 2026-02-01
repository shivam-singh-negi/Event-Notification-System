"""
Event processing logic for notification events.

This module defines:
- A common processing contract for all event types
- Concrete processors for EMAIL, SMS, and PUSH events

Processing behavior is fully driven by environment configuration.
"""

import time
import random
import logging
from abc import ABC, abstractmethod

from app.notification.models import Event
from app.notification.exceptions import EventProcessingError
from app.config import (
    FAILURE_RATE,
    EMAIL_PROCESSING_TIME,
    SMS_PROCESSING_TIME,
    PUSH_PROCESSING_TIME,
)


# -------------------------------------------------------------------
# Base Processor
# -------------------------------------------------------------------

class EventProcessor(ABC):
    """
    Abstract base class for all event processors.

    Responsibilities:
    - Provide a common processing contract
    - Simulate processing delay
    - Simulate controlled failure
    """

    def __init__(self, processing_time_seconds: int, logger_name: str) -> None:
        self._processing_time = processing_time_seconds
        self._logger = logging.getLogger(logger_name)

    @abstractmethod
    def process(self, event: Event) -> None:
        """
        Process a single event.

        Args:
            event (Event): Event to process

        Raises:
            EventProcessingError: If processing fails
        """
        raise NotImplementedError

    def _simulate_processing(self) -> None:
        """
        Simulate processing delay and probabilistic failure.
        """
        self._logger.info(
            f"Processing started (sleep={self._processing_time}s, failureRate={FAILURE_RATE})"
        )

        time.sleep(self._processing_time)

        if random.random() < FAILURE_RATE:
            raise EventProcessingError("Simulated processing failure")

        self._logger.info("Processing completed successfully")


# -------------------------------------------------------------------
# EMAIL Processor
# -------------------------------------------------------------------

class EmailProcessor(EventProcessor):
    """
    Processor for EMAIL notification events.

    Processing time is controlled via:
    EMAIL_PROCESSING_TIME
    """

    def __init__(self) -> None:
        super().__init__(
            processing_time_seconds=EMAIL_PROCESSING_TIME,
            logger_name="app.notification.processor.email",
        )

    def process(self, event: Event) -> None:
        self._logger.info(
            f"EMAIL event {event.event_id} processing started"
        )
        self._simulate_processing()


# -------------------------------------------------------------------
# SMS Processor
# -------------------------------------------------------------------

class SmsProcessor(EventProcessor):
    """
    Processor for SMS notification events.

    Processing time is controlled via:
    SMS_PROCESSING_TIME
    """

    def __init__(self) -> None:
        super().__init__(
            processing_time_seconds=SMS_PROCESSING_TIME,
            logger_name="app.notification.processor.sms",
        )

    def process(self, event: Event) -> None:
        self._logger.info(
            f"SMS event {event.event_id} processing started"
        )
        self._simulate_processing()


# -------------------------------------------------------------------
# PUSH Processor
# -------------------------------------------------------------------

class PushProcessor(EventProcessor):
    """
    Processor for PUSH notification events.

    Processing time is controlled via:
    PUSH_PROCESSING_TIME
    """

    def __init__(self) -> None:
        super().__init__(
            processing_time_seconds=PUSH_PROCESSING_TIME,
            logger_name="app.notification.processor.push",
        )

    def process(self, event: Event) -> None:
        self._logger.info(
            f"PUSH event {event.event_id} processing started"
        )
        self._simulate_processing()
