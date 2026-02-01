"""
Worker threads for asynchronous event processing.

Responsibilities:
- Consume events from FIFO queues
- Process events sequentially per event type
- Drain all queued events during shutdown
- Update event status
- Send success / failure callbacks
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
        super().__init__(
            name=f"{event_type.value}-Worker",
            daemon=False,  # MUST be non-daemon for graceful shutdown
        )

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
        Worker loop.

        Exit condition:
        - Shutdown requested
        - AND queue is fully drained
        """
        self._logger.info(
            "Worker started (eventType=%s)",
            self._event_type.value,
        )

        while True:
            if (
                self._shutdown_event.is_set()
                and self._queue_manager.is_empty(self._event_type)
            ):
                break

            try:
                event = self._queue_manager.dequeue(
                    self._event_type,
                    timeout=1.0,
                )

                if event is None:
                    continue

                self._logger.info(
                    "Dequeued event_id=%s",
                    event.event_id,
                )

                self._processor.process(event)

                self._status_service.mark_completed(event.event_id)
                self._callback_dispatcher.notify_success(event)

                self._logger.info(
                    "Event processed successfully event_id=%s",
                    event.event_id,
                )

            except EventProcessingError as exc:
                self._logger.error(
                    "Processing failed event_id=%s error=%s",
                    event.event_id,
                    exc,
                )

                self._status_service.mark_failed(event.event_id)
                self._callback_dispatcher.notify_failure(
                    event,
                    str(exc),
                )

            except Exception:
                self._logger.exception(
                    "Unexpected worker error; continuing execution"
                )

        self._logger.info(
            "Worker shutdown complete (eventType=%s)",
            self._event_type.value,
        )


# ------------------------------------------------------------------
# Worker factory
# ------------------------------------------------------------------

def create_workers(
    queue_manager: EventQueueManager,
    status_service: EventStatusService,
    shutdown_event: threading.Event,
) -> Dict[EventType, EventWorker]:
    """
    Create one worker per event type.
    """
    callback_dispatcher = CallbackDispatcher()

    logging.getLogger("app.notification.worker").info(
        "Initializing worker threads"
    )

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
