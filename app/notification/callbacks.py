"""
Callback dispatching for notification events.

This module is responsible for notifying external systems
about the final status of an event via HTTP callbacks.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.notification.models import Event, EventType


class CallbackDispatcher:
    """
    Sends callback notifications for completed or failed events.

    This class:
    - Builds callback payloads
    - Sends HTTP POST requests to client-provided URLs
    - Logs outcomes without interrupting worker execution
    """

    def __init__(self, timeout_seconds: int = 5) -> None:
        self._timeout = timeout_seconds
        self._logger = logging.getLogger("app.notification.callbacks")

    def notify_success(self, event: Event) -> None:
        """
        Send a success callback for a processed event.
        """
        payload = self._build_success_payload(event)
        self._send_callback(event.callback_url, payload)

    def notify_failure(self, event: Event, error_message: str) -> None:
        """
        Send a failure callback for a failed event.
        """
        payload = self._build_failure_payload(event, error_message)
        self._send_callback(event.callback_url, payload)

    def _build_success_payload(self, event: Event) -> dict:
        return {
            "eventId": event.event_id,
            "status": "COMPLETED",
            "eventType": event.event_type.value,
            "processedAt": self._utc_now(),
        }

    def _build_failure_payload(self, event: Event, error_message: str) -> dict:
        return {
            "eventId": event.event_id,
            "status": "FAILED",
            "eventType": event.event_type.value,
            "errorMessage": error_message,
            "processedAt": self._utc_now(),
        }

    def _send_callback(self, url: str, payload: dict) -> None:
        """
        Send the callback HTTP request.

        Errors are logged but never raised, ensuring
        worker threads continue running.
        """
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(str(url), json=payload)
                response.raise_for_status()

                self._logger.info(
                    f"Callback sent successfully to {url} "
                    f"(eventId={payload.get('eventId')})"
                )

        except Exception as exc:
            self._logger.error(
                f"Failed to send callback to {url}: {exc}"
            )


    @staticmethod
    def _utc_now() -> str:
        """
        Return the current UTC time in ISO 8601 format.
        """
        return datetime.now(timezone.utc).isoformat()
