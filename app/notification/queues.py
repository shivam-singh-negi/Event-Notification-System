"""
In-memory FIFO queue management for notification events.

This module provides thread-safe queues for each supported
event type and acts as the handoff point between the API
layer and background worker threads.
"""

from queue import Queue, Empty
from typing import Optional
from typing import Dict

from app.notification.models import Event, EventType
from app.notification.exceptions import (
    UnsupportedEventTypeError,
    QueueOperationError,
)



class EventQueueManager:
    """
    Manages in-memory FIFO queues for notification events.

    Responsibilities:
    - Maintain a separate queue for each event type
    - Ensure FIFO ordering within each event type
    - Provide a thread-safe interface for enqueuing and dequeuing events

    This class does NOT:
    - Process events
    - Spawn threads
    - Apply business logic
    """

    def __init__(self) -> None:
        """
        Initialize FIFO queues for each supported event type.
        """
        self._queues: Dict[EventType, Queue[Event]] = {
            EventType.EMAIL: Queue(),
            EventType.SMS: Queue(),
            EventType.PUSH: Queue(),
        }

    def enqueue(self, event: Event) -> None:
        """
        Add an event to the appropriate FIFO queue.

        Args:
            event (Event): A validated event instance

        Raises:
            UnsupportedEventTypeError: If no queue exists for the event type
            QueueOperationError: If the enqueue operation fails
        """
        queue = self._queues.get(event.event_type)
        if queue is None:
            raise UnsupportedEventTypeError(
                f"No queue configured for event type: {event.event_type}"
            )

        try:
            queue.put(event)
        except Exception as exc:  # extremely rare, but defensive
            raise QueueOperationError(
                f"Failed to enqueue event {event.event_id}"
            ) from exc


    def dequeue(
        self,
        event_type: EventType,
        timeout: float = 1.0,
    ) -> Optional[Event]:
        """
        Attempt to remove and return the next event from the specified queue.

        This method:
        - Blocks for at most `timeout` seconds
        - Returns None if no event is available
        - Allows worker threads to periodically check shutdown signals

        Args:
            event_type (EventType): The queue to consume from
            timeout (float): Maximum time to block (seconds)

        Returns:
            Optional[Event]: The next event in FIFO order, or None if empty

        Raises:
            UnsupportedEventTypeError: If no queue exists for the event type
            QueueOperationError: If an unexpected queue error occurs
        """
        queue = self._queues.get(event_type)
        if queue is None:
            raise UnsupportedEventTypeError(
                f"No queue configured for event type: {event_type}"
            )

        try:
            return queue.get(timeout=timeout)
        except Empty:
            # Normal case: no event available within timeout
            return None
        except Exception as exc:
            raise QueueOperationError(
                f"Failed to dequeue event for type {event_type}"
            ) from exc


    def size(self, event_type: EventType) -> int:
        """
        Return the current size of the specified queue.

        Intended for monitoring and debugging purposes.

        Raises:
            UnsupportedEventTypeError: If no queue exists for the event type
        """
        queue = self._queues.get(event_type)
        if queue is None:
            raise UnsupportedEventTypeError(
                f"No queue configured for event type: {event_type}"
            )

        return queue.qsize()

    def __repr__(self) -> str:
        """
        Developer-friendly representation showing queue sizes.
        """
        sizes = {
            event_type.value: queue.qsize()
            for event_type, queue in self._queues.items()
        }
        return f"EventQueueManager(queues={sizes})"
