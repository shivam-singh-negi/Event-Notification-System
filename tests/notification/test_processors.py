import pytest
import random

from app.notification.services.processors import EmailProcessor
from app.notification.models import Event, EventType
from app.notification.exceptions import EventProcessingError
from app.notification.services.processors import SmsProcessor
from app.notification.services.processors import PushProcessor


def test_processor_success(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 1.0)

    processor = EmailProcessor()
    event = Event.create(
        EventType.EMAIL,
        {"recipient": "a@b.com", "message": "hi"},
        "http://example.com",
    )

    processor.process(event)


def test_processor_failure(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 0.0)

    processor = EmailProcessor()
    event = Event.create(
        EventType.EMAIL,
        {"recipient": "a@b.com", "message": "hi"},
        "http://example.com",
    )

    with pytest.raises(EventProcessingError):
        processor.process(event)


def test_processor_does_not_mutate_event(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 1.0)

    processor = EmailProcessor()
    payload = {"recipient": "a@b.com", "message": "hi"}

    event = Event.create(
        EventType.EMAIL,
        payload.copy(),
        "http://example.com",
    )

    processor.process(event)

    assert event.payload == payload
    assert event.event_type == EventType.EMAIL


def test_processor_failure_exception_type(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 0.0)

    processor = EmailProcessor()
    event = Event.create(
        EventType.EMAIL,
        {"recipient": "a@b.com", "message": "hi"},
        "http://example.com",
    )

    with pytest.raises(EventProcessingError) as exc:
        processor.process(event)

    assert "failure" in str(exc.value).lower()


def test_processor_multiple_success_runs(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 1.0)

    processor = EmailProcessor()

    for _ in range(3):
        event = Event.create(
            EventType.EMAIL,
            {"recipient": "a@b.com", "message": "hi"},
            "http://example.com",
        )
        processor.process(event)



def test_sms_processor_success(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 1.0)

    processor = SmsProcessor()
    event = Event.create(
        EventType.SMS,
        {"phoneNumber": "+1234567890", "message": "hi"},
        "http://example.com",
    )

    processor.process(event)



def test_push_processor_failure(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 0.0)

    processor = PushProcessor()
    event = Event.create(
        EventType.PUSH,
        {"deviceId": "device-1", "message": "hi"},
        "http://example.com",
    )

    with pytest.raises(EventProcessingError):
        processor.process(event)
