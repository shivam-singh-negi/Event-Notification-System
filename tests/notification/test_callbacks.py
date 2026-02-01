import pytest

from app.notification.callbacks import CallbackDispatcher
from app.notification.models import Event, EventType


def _create_event(event_type=EventType.EMAIL):
    """
    Test helper to reduce duplication and ensure
    consistent event construction.
    """
    return Event.create(
        event_type=event_type,
        payload={},
        callback_url="http://example.com",
    )


# ------------------------------------------------------------------
# Payload construction
# ------------------------------------------------------------------

def test_build_success_callback_payload():
    dispatcher = CallbackDispatcher()
    event = _create_event(EventType.EMAIL)

    payload = dispatcher._build_success_payload(event)

    assert payload["eventId"] == event.event_id
    assert payload["eventType"] == EventType.EMAIL.value
    assert payload["status"] == "COMPLETED"
    assert "processedAt" in payload


def test_build_failure_callback_payload():
    dispatcher = CallbackDispatcher()
    event = _create_event(EventType.EMAIL)

    payload = dispatcher._build_failure_payload(event, "some error")

    assert payload["eventId"] == event.event_id
    assert payload["eventType"] == EventType.EMAIL.value
    assert payload["status"] == "FAILED"
    assert payload["errorMessage"] == "some error"
    assert "processedAt" in payload


# ------------------------------------------------------------------
# Schema consistency
# ------------------------------------------------------------------

def test_callback_payload_contains_common_fields_for_all_event_types():
    dispatcher = CallbackDispatcher()

    for event_type in EventType:
        event = _create_event(event_type)
        payload = dispatcher._build_success_payload(event)

        assert set(payload.keys()) >= {
            "eventId",
            "eventType",
            "status",
            "processedAt",
        }


def test_callback_timestamp_is_iso8601_string():
    dispatcher = CallbackDispatcher()
    event = _create_event(EventType.SMS)

    payload = dispatcher._build_success_payload(event)

    assert isinstance(payload["processedAt"], str)
    assert "T" in payload["processedAt"]  # ISO-8601 shape check


# ------------------------------------------------------------------
# Network resilience
# ------------------------------------------------------------------

def test_notify_success_swallows_network_errors(monkeypatch):
    """
    Callback failures must never crash worker threads.
    """
    dispatcher = CallbackDispatcher()
    event = _create_event(EventType.EMAIL)

    def fake_post(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr("httpx.Client.post", fake_post)

    # Must not raise
    dispatcher.notify_success(event)


def test_send_callback_accepts_pydantic_httpurl():
    """
    Ensure HttpUrl values from Pydantic models
    are handled correctly by the HTTP client.
    """
    dispatcher = CallbackDispatcher()
    event = _create_event(EventType.PUSH)

    payload = dispatcher._build_success_payload(event)

    # Must not raise
    dispatcher._send_callback(event.callback_url, payload)
