"""
Worker threads for asynchronous event processing.

This module defines long-running worker threads that:
- Consume events from FIFO queues
- Delegate processing to event processors
- Update event status
- Send success / failure callbacks
- Respect shutdown signals
"""

import threading
import logging
from typing import Dict

from app.notification.models import EventType, Event
from app.notification.queues import EventQueueManager
from app.notification.services.processors import (
    EventProcessor,
    EmailProcessor,
    SmsProcessor,
    PushProcessor,
)
from app.notification.services.event_status_service import EventStatusService
from app.notification.exceptions import EventProcessingError
from app.notification.callbacks import CallbackDispatcher


class EventWorker(threading.Thread):
    """
    Background worker thread responsible for processing
    events of a single EventType.

    Each worker:
    - Polls its queue using a timeout
    - Processes events sequentially (FIFO)
    - Updates event status
    - Never crashes on empty queues
    """

    def __init__(
        self,
        event_type: EventType,
        queue_manager: EventQueueManager,
        processor: EventProcessor,
        status_service: EventStatusService,
        callback_dispatcher: CallbackDispatcher,
        shutdown_event: threading.Event,
    ) -> None:
        super().__init__(name=f"{event_type.value}-Worker", daemon=True)

        self._event_type = event_type
        self._queue_manager = queue_manager
        self._processor = processor
        self._status_service = status_service
        self._callback_dispatcher = callback_dispatcher
        self._shutdown_event = shutdown_event

        self._logger = logging.getLogger(
            f"app.notification.worker.{event_type.value.lower()}"
        )

    def run(self) -> None:
        """
        Main worker loop.

        Polls the queue until shutdown is requested.
        Handles empty queues gracefully.
        """
        self._logger.info("Worker started")

        while not self._shutdown_event.is_set():
            try:
                event = self._queue_manager.dequeue(self._event_type)

                # Queue empty → retry after timeout
                if event is None:
                    continue

                self._logger.info(
                    f"Dequeued event {event.event_id} for processing"
                )

                self._processor.process(event)

                self._status_service.mark_completed(event.event_id)
                self._callback_dispatcher.notify_success(event)

            except EventProcessingError as exc:
                self._logger.error(
                    f"Event {event.event_id} failed during processing: {exc}"
                )

                self._status_service.mark_failed(event.event_id)
                self._callback_dispatcher.notify_failure(
                    event, str(exc)
                )

            except Exception as exc:
                # Defensive: worker must never die
                self._logger.exception(
                    f"Unexpected worker error: {exc}"
                )

        self._logger.info("Worker shutting down")


# ✅ FACTORY FUNCTION — MUST BE MODULE LEVEL
def create_workers(
    queue_manager: EventQueueManager,
    status_service: EventStatusService,
    shutdown_event: threading.Event,
) -> Dict[EventType, EventWorker]:
    """
    Create and configure one worker per event type.
    """
    callback_dispatcher = CallbackDispatcher()

    return {
        EventType.EMAIL: EventWorker(
            EventType.EMAIL,
            queue_manager,
            EmailProcessor(),
            status_service,
            callback_dispatcher,
            shutdown_event,
        ),
        EventType.SMS: EventWorker(
            EventType.SMS,
            queue_manager,
            SmsProcessor(),
            status_service,
            callback_dispatcher,
            shutdown_event,
        ),
        EventType.PUSH: EventWorker(
            EventType.PUSH,
            queue_manager,
            PushProcessor(),
            status_service,
            callback_dispatcher,
            shutdown_event,
        ),
    }
