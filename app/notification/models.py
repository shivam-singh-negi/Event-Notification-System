"""
Core domain models for the Event Notification System.

This module defines:
- Supported notification event types
- Strictly validated API request schema
- Internal event domain representation

These models form the contract between the API layer and
the asynchronous processing pipeline.
"""

from enum import Enum
from typing import Dict, Any
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, model_validator

from app.notification.exceptions import InvalidEventPayloadError


class EventType(str, Enum):
    """
    Supported notification event types.

    This enum:
    - Restricts the system to known event categories
    - Eliminates magic strings
    - Enables automatic request validation
    """

    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"

    def __str__(self) -> str:
        """Return the raw string value of the enum."""
        return self.value


class CreateEventRequest(BaseModel):
    """
    API request model for creating a notification event.

    Responsibilities:
    - Validate request structure
    - Enforce event-type-specific payload requirements
    - Reject invalid input early at the API boundary

    All validation errors raised by this model are
    treated as client errors (HTTP 400).
    """

    eventType: EventType = Field(..., description="Notification event type")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    callbackUrl: HttpUrl = Field(..., description="Callback endpoint")

    @model_validator(mode="after")
    def validate_payload_by_event_type(self):
        """
        Validate payload contents based on event type.

        Ensures that all required fields for the given
        event type are present before the request is accepted.

        Raises:
            InvalidEventPayloadError: If validation fails
        """
        payload = self.payload
        event_type = self.eventType

        if not payload:
            raise InvalidEventPayloadError("Payload must not be empty")

        if event_type == EventType.EMAIL:
            required_fields = {"recipient", "message"}
        elif event_type == EventType.SMS:
            required_fields = {"phoneNumber", "message"}
        elif event_type == EventType.PUSH:
            required_fields = {"deviceId", "message"}
        else:
            raise InvalidEventPayloadError(
                f"Unsupported event type: {event_type}"
            )

        missing_fields = required_fields - payload.keys()
        if missing_fields:
            raise InvalidEventPayloadError(
                f"Missing required payload fields: {', '.join(missing_fields)}"
            )

        return self

    def __repr__(self) -> str:
        """Compact representation for debugging and logs."""
        return (
            f"CreateEventRequest(eventType={self.eventType}, "
            f"callbackUrl={self.callbackUrl})"
        )



class Event(BaseModel):
    """
    Internal representation of an accepted notification event.

    An Event instance represents a validated request that has been
    assigned a unique identifier and is ready for asynchronous
    processing by worker threads.
    """

    event_id: str
    event_type: EventType
    payload: Dict[str, Any]
    callback_url: HttpUrl
    created_at: datetime

    @classmethod
    def create(
        cls,
        event_type: EventType,
        payload: Dict[str, Any],
        callback_url: HttpUrl,
    ) -> "Event":
        """
        Create a new Event with a generated ID and timestamp.

        This factory method guarantees:
        - Unique event identity
        - Consistent initialization
        - Immutable creation metadata
        """
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            payload=payload,
            callback_url=callback_url,
            created_at=datetime.utcnow(),
        )

    def __repr__(self) -> str:
        """Concise, log-friendly representation."""
        return (
            f"Event(event_id={self.event_id}, "
            f"event_type={self.event_type}, "
            f"created_at={self.created_at.isoformat()})"
        )

    def __eq__(self, other: object) -> bool:
        """
        Compare events by identifier.

        Two events are considered equal if they share the same event_id.
        """
        if not isinstance(other, Event):
            return False
        return self.event_id == other.event_id

