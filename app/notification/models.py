"""
Core domain models for the Event Notification System.

This module defines:
- Supported notification event types
- Strict API request validation schemas
- Internal event domain representation

These models form the contract between the API layer
and the asynchronous processing pipeline.
"""

from enum import Enum
from typing import Dict, Any
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, model_validator

from app.notification.exceptions import InvalidEventPayloadError


# -------------------------------------------------------------------
# Event Type
# -------------------------------------------------------------------

class EventType(str, Enum):
    """
    Supported notification event types.
    """

    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"

    def __str__(self) -> str:
        return self.value


# -------------------------------------------------------------------
# Strict payload schemas (SPEC ENFORCED)
# -------------------------------------------------------------------

class EmailPayload(BaseModel):
    recipient: str
    message: str

    class Config:
        extra = "forbid"


class SmsPayload(BaseModel):
    phoneNumber: str
    message: str

    class Config:
        extra = "forbid"


class PushPayload(BaseModel):
    deviceId: str
    message: str

    class Config:
        extra = "forbid"


# -------------------------------------------------------------------
# API Request Model
# -------------------------------------------------------------------

class CreateEventRequest(BaseModel):
    """
    API request model for creating a notification event.

    Responsibilities:
    - Validate request structure
    - Enforce event-type-specific payload schema
    - Reject invalid or non-spec-compliant input early
    """

    eventType: EventType = Field(..., description="Notification event type")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    callbackUrl: HttpUrl = Field(..., description="Callback endpoint")

    @model_validator(mode="after")
    def validate_payload_by_event_type(self):
        """
        Enforce strict payload schema per event type with
        clear, human-readable validation errors including data types.
        """
        payload = self.payload or {}

        if self.eventType == EventType.EMAIL:
            schema = {
                "recipient": str,
                "message": str,
            }
            event_name = "EMAIL"

        elif self.eventType == EventType.SMS:
            schema = {
                "phoneNumber": str,
                "message": str,
            }
            event_name = "SMS"

        elif self.eventType == EventType.PUSH:
            schema = {
                "deviceId": str,
                "message": str,
            }
            event_name = "PUSH"

        else:
            raise InvalidEventPayloadError(
                f"Unsupported event type: {self.eventType}"
            )

        required_fields = set(schema.keys())
        provided_fields = set(payload.keys())

        # ---- Missing fields ----
        missing = required_fields - provided_fields
        if missing:
            raise InvalidEventPayloadError(
                f"{event_name} payload is missing required field(s): "
                f"{', '.join(sorted(missing))}"
            )

        # ---- Extra fields ----
        extra = provided_fields - required_fields
        if extra:
            raise InvalidEventPayloadError(
                f"{event_name} payload contains unsupported field(s): "
                f"{', '.join(sorted(extra))}. "
                f"Allowed fields are: {', '.join(sorted(required_fields))}"
            )

        # ---- Type validation ----
        for field, expected_type in schema.items():
            value = payload[field]
            if not isinstance(value, expected_type):
                raise InvalidEventPayloadError(
                    f"{event_name} payload field '{field}' must be of type "
                    f"{expected_type.__name__}, got {type(value).__name__}"
                )

        return self


# -------------------------------------------------------------------
# Internal Domain Event
# -------------------------------------------------------------------

class Event(BaseModel):
    """
    Internal representation of an accepted notification event.

    Represents a validated request that is ready for
    asynchronous processing.
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
        Factory method to create a new Event.
        """
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            payload=payload,
            callback_url=callback_url,
            created_at=datetime.utcnow(),
        )

    def __repr__(self) -> str:
        return (
            f"Event(event_id={self.event_id}, "
            f"event_type={self.event_type}, "
            f"created_at={self.created_at.isoformat()})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Event):
            return False
        return self.event_id == other.event_id
