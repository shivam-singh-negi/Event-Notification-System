"""
Event processing logic for notification events.

This module defines:
- A common processing contract for all event types
- Concrete processors for EMAIL, SMS, and PUSH events

Processors encapsulate business behavior such as:
- Simulated processing delay
- Random failure handling
- Logging of processing lifecycle
"""

import time
import random
import logging
from abc import ABC, abstractmethod

from app.notification.models import Event
from app.notification.exceptions import EventProcessingError
from app.config import FAILURE_RATE



class EventProcessor(ABC):
    """
    Abstract base class for event processors.

    Each processor implementation must:
    - Handle exactly one event type
    - Process events synchronously
    - Raise EventProcessingError on failure
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
        Simulate processing delay and random failure.
        """
        self._logger.info("Processing started")
        time.sleep(self._processing_time)

        if random.random() < FAILURE_RATE:
            raise EventProcessingError("Simulated processing failure")

        self._logger.info("Processing completed successfully")



class EmailProcessor(EventProcessor):
    """
    Processor for EMAIL notification events.
    """

    def __init__(self) -> None:
        super().__init__(
            processing_time_seconds=5,
            logger_name="app.notification.processor.email",
        )

    def process(self, event: Event) -> None:
        self._logger.info(
            f"EMAIL event {event.event_id} processing started"
        )
        self._simulate_processing()



class SmsProcessor(EventProcessor):
    """
    Processor for SMS notification events.
    """

    def __init__(self) -> None:
        super().__init__(
            processing_time_seconds=3,
            logger_name="app.notification.processor.sms",
        )

    def process(self, event: Event) -> None:
        self._logger.info(
            f"SMS event {event.event_id} processing started"
        )
        self._simulate_processing()



class PushProcessor(EventProcessor):
    """
    Processor for PUSH notification events.
    """

    def __init__(self) -> None:
        super().__init__(
            processing_time_seconds=2,
            logger_name="app.notification.processor.push",
        )

    def process(self, event: Event) -> None:
        self._logger.info(
            f"PUSH event {event.event_id} processing started"
        )
        self._simulate_processing()
