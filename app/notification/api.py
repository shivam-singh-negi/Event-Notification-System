"""
API endpoints for the Event Notification System.

This module exposes HTTP endpoints for clients to submit
notification events for asynchronous processing.
"""


import logging
from fastapi import APIRouter, HTTPException, status

from app.notification.models import CreateEventRequest, Event
from app.notification.queues import EventQueueManager
from app.notification.exceptions import UnsupportedEventTypeError
from app.notification.services.event_status_service import EventStatusService

router = APIRouter()
logger = logging.getLogger("app.notification.api")

# SHARED singletons (IMPORTANT)
queue_manager = EventQueueManager()
status_service = EventStatusService()


@router.post("/api/events", status_code=status.HTTP_202_ACCEPTED)
def create_event(request: CreateEventRequest):
    event = Event.create(
        event_type=request.eventType,
        payload=request.payload,
        callback_url=request.callbackUrl,
    )

    # Mark event as PENDING
    status_service.mark_pending(event.event_id)
    queue_manager.enqueue(event)

    logger.info(
        f"Accepted event {event.event_id} of type {event.event_type}"
    )

    return {
        "eventId": event.event_id,
        "message": "Event accepted for processing",
    }


@router.get("/api/events/{event_id}/status")
def get_event_status(event_id: str):
    status_value = status_service.get_status(event_id)

    if status_value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return {
        "eventId": event_id,
        "status": status_value.value,
    }
