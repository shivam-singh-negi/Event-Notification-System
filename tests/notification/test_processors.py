import random
import time
import pytest

from app.notification.models import Event, EventType
from app.notification.exceptions import EventProcessingError
from app.notification.services.processors import (
    EmailProcessor,
    SmsProcessor,
    PushProcessor,
)

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def make_event(event_type: EventType, payload: dict) -> Event:
    return Event.create(
        event_type=event_type,
        payload=payload,
        callback_url="http://example.com",
    )


def force_success(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 1.0)


def force_failure(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 0.0)


def capture_sleep(monkeypatch):
    """
    Capture calls to time.sleep to verify simulated processing delays
    without slowing down tests.
    """
    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(time, "sleep", fake_sleep)
    return sleep_calls


# -------------------------------------------------------------------
# EMAIL Processing (5 seconds)
# -------------------------------------------------------------------

def test_email_event_is_processed_successfully(monkeypatch):
    force_success(monkeypatch)

    processor = EmailProcessor()
    event = make_event(
        EventType.EMAIL,
        {"recipient": "a@b.com", "message": "hi"},
    )

    processor.process(event)


def test_email_event_processing_fails_on_simulated_failure(monkeypatch):
    force_failure(monkeypatch)

    processor = EmailProcessor()
    event = make_event(
        EventType.EMAIL,
        {"recipient": "a@b.com", "message": "hi"},
    )

    with pytest.raises(EventProcessingError):
        processor.process(event)


def test_email_processor_does_not_mutate_event_payload(monkeypatch):
    force_success(monkeypatch)

    processor = EmailProcessor()
    payload = {"recipient": "a@b.com", "message": "hi"}

    event = make_event(EventType.EMAIL, payload.copy())
    processor.process(event)

    assert event.payload == payload
    assert event.event_type == EventType.EMAIL


def test_email_processor_can_process_multiple_events_sequentially(monkeypatch):
    force_success(monkeypatch)

    processor = EmailProcessor()

    for _ in range(3):
        processor.process(
            make_event(
                EventType.EMAIL,
                {"recipient": "a@b.com", "message": "hi"},
            )
        )


def test_email_event_is_processed_with_5_second_delay(monkeypatch):
    force_success(monkeypatch)
    sleep_calls = capture_sleep(monkeypatch)

    processor = EmailProcessor()
    event = make_event(
        EventType.EMAIL,
        {"recipient": "a@b.com", "message": "hi"},
    )

    processor.process(event)

    assert sleep_calls == [5], "EMAIL events must simulate a 5-second delay"


# -------------------------------------------------------------------
# SMS Processing (3 seconds)
# -------------------------------------------------------------------

def test_sms_event_is_processed_successfully(monkeypatch):
    force_success(monkeypatch)

    processor = SmsProcessor()
    event = make_event(
        EventType.SMS,
        {"phoneNumber": "+1234567890", "message": "hi"},
    )

    processor.process(event)


def test_sms_event_processing_fails_on_simulated_failure(monkeypatch):
    force_failure(monkeypatch)

    processor = SmsProcessor()
    event = make_event(
        EventType.SMS,
        {"phoneNumber": "+1234567890", "message": "hi"},
    )

    with pytest.raises(EventProcessingError):
        processor.process(event)


def test_sms_processor_does_not_mutate_event_payload(monkeypatch):
    force_success(monkeypatch)

    processor = SmsProcessor()
    payload = {"phoneNumber": "+1234567890", "message": "hi"}

    event = make_event(EventType.SMS, payload.copy())
    processor.process(event)

    assert event.payload == payload
    assert event.event_type == EventType.SMS


def test_sms_event_is_processed_with_3_second_delay(monkeypatch):
    force_success(monkeypatch)
    sleep_calls = capture_sleep(monkeypatch)

    processor = SmsProcessor()
    event = make_event(
        EventType.SMS,
        {"phoneNumber": "+1234567890", "message": "hi"},
    )

    processor.process(event)

    assert sleep_calls == [3], "SMS events must simulate a 3-second delay"


# -------------------------------------------------------------------
# PUSH Processing (2 seconds)
# -------------------------------------------------------------------

def test_push_event_is_processed_successfully(monkeypatch):
    force_success(monkeypatch)

    processor = PushProcessor()
    event = make_event(
        EventType.PUSH,
        {"deviceId": "device-1", "message": "hi"},
    )

    processor.process(event)


def test_push_event_processing_fails_on_simulated_failure(monkeypatch):
    force_failure(monkeypatch)

    processor = PushProcessor()
    event = make_event(
        EventType.PUSH,
        {"deviceId": "device-1", "message": "hi"},
    )

    with pytest.raises(EventProcessingError):
        processor.process(event)


def test_push_processor_does_not_mutate_event_payload(monkeypatch):
    force_success(monkeypatch)

    processor = PushProcessor()
    payload = {"deviceId": "device-1", "message": "hi"}

    event = make_event(EventType.PUSH, payload.copy())
    processor.process(event)

    assert event.payload == payload
    assert event.event_type == EventType.PUSH


def test_push_event_is_processed_with_2_second_delay(monkeypatch):
    force_success(monkeypatch)
    sleep_calls = capture_sleep(monkeypatch)

    processor = PushProcessor()
    event = make_event(
        EventType.PUSH,
        {"deviceId": "device-1", "message": "hi"},
    )

    processor.process(event)

    assert sleep_calls == [2], "PUSH events must simulate a 2-second delay"
