from app.notification.callbacks import CallbackDispatcher
from app.notification.models import Event, EventType


def test_callback_payload_building():
    dispatcher = CallbackDispatcher()

    event = Event.create(
        EventType.EMAIL,
        {},
        "http://example.com",
    )

    payload = dispatcher._build_success_payload(event)

    assert payload["status"] == "COMPLETED"
    assert payload["eventId"] == event.event_id


def test_failure_callback_payload_building():
    dispatcher = CallbackDispatcher()

    event = Event.create(
        EventType.EMAIL,
        {},
        "http://example.com",
    )

    payload = dispatcher._build_failure_payload(event, "some error")

    assert payload["status"] == "FAILED"
    assert payload["eventId"] == event.event_id
    assert payload["errorMessage"] == "some error"


def test_callback_payload_contains_common_fields():
    dispatcher = CallbackDispatcher()

    event = Event.create(
        EventType.PUSH,
        {},
        "http://example.com",
    )

    payload = dispatcher._build_success_payload(event)

    assert "eventId" in payload
    assert "status" in payload
    assert "eventType" in payload
    assert "processedAt" in payload


def test_callback_payload_timestamp_format():
    dispatcher = CallbackDispatcher()

    event = Event.create(
        EventType.SMS,
        {},
        "http://example.com",
    )

    payload = dispatcher._build_success_payload(event)

    assert isinstance(payload["processedAt"], str)
    assert "T" in payload["processedAt"]  # ISO-8601 shape check


def test_send_callback_does_not_raise_on_http_failure(monkeypatch):
    dispatcher = CallbackDispatcher()

    event = Event.create(
        EventType.EMAIL,
        {},
        "http://example.com",
    )

    def fake_post(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr("httpx.Client.post", fake_post)

    # Should NOT raise
    dispatcher.notify_success(event)


def test_callback_accepts_pydantic_url_type():
    dispatcher = CallbackDispatcher()

    event = Event.create(
        EventType.EMAIL,
        {},
        "http://example.com",
    )

    payload = dispatcher._build_success_payload(event)

    # Should not raise even if URL is not a raw str
    dispatcher._send_callback(event.callback_url, payload)
