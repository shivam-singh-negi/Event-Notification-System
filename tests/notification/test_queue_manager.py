from app.notification.queues import EventQueueManager
from app.notification.models import Event, EventType
import pytest
from app.notification.exceptions import UnsupportedEventTypeError


def test_queue_fifo_order():
    qm = EventQueueManager()

    e1 = Event.create(EventType.EMAIL, {}, "http://example.com")
    e2 = Event.create(EventType.EMAIL, {}, "http://example.com")

    qm.enqueue(e1)
    qm.enqueue(e2)

    assert qm.dequeue(EventType.EMAIL) == e1
    assert qm.dequeue(EventType.EMAIL) == e2

def test_queue_isolation_by_event_type():
    qm = EventQueueManager()

    email_event = Event.create(EventType.EMAIL, {}, "http://example.com")
    sms_event = Event.create(EventType.SMS, {}, "http://example.com")

    qm.enqueue(email_event)
    qm.enqueue(sms_event)

    assert qm.dequeue(EventType.EMAIL) == email_event
    assert qm.dequeue(EventType.SMS) == sms_event

def test_queue_size_tracking():
    qm = EventQueueManager()

    event = Event.create(EventType.PUSH, {}, "http://example.com")

    assert qm.size(EventType.PUSH) == 0

    qm.enqueue(event)
    assert qm.size(EventType.PUSH) == 1

    qm.dequeue(EventType.PUSH)
    assert qm.size(EventType.PUSH) == 0

def test_dequeue_timeout_returns_none():
    qm = EventQueueManager()

    result = qm.dequeue(EventType.EMAIL, timeout=0.1)

    assert result is None



def test_dequeue_unsupported_event_type_raises():
    qm = EventQueueManager()

    with pytest.raises(UnsupportedEventTypeError):
        qm.dequeue("UNKNOWN")  # type: ignore

def test_interleaved_enqueue_dequeue():
    qm = EventQueueManager()

    e1 = Event.create(EventType.EMAIL, {}, "http://example.com")
    e2 = Event.create(EventType.EMAIL, {}, "http://example.com")

    qm.enqueue(e1)
    assert qm.dequeue(EventType.EMAIL) == e1

    qm.enqueue(e2)
    assert qm.dequeue(EventType.EMAIL) == e2
