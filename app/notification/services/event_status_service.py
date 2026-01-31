"""
Event status tracking service.

This service maintains the lifecycle state of notification
events for status polling via API.
"""

import threading
from enum import Enum
from typing import Dict, Optional

class EventStatus(str, Enum):
    """
    Lifecycle states of a notification event.
    """

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EventStatusService:
    """
    Thread-safe in-memory service for tracking event status.

    This service is ephemeral:
    - Data is stored in memory
    - State is lost on application restart
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._statuses: Dict[str, EventStatus] = {}

    def mark_pending(self, event_id: str) -> None:
        with self._lock:
            self._statuses[event_id] = EventStatus.PENDING

    def mark_completed(self, event_id: str) -> None:
        with self._lock:
            self._statuses[event_id] = EventStatus.COMPLETED

    def mark_failed(self, event_id: str) -> None:
        with self._lock:
            self._statuses[event_id] = EventStatus.FAILED

    def get_status(self, event_id: str) -> Optional[EventStatus]:
        with self._lock:
            return self._statuses.get(event_id)
