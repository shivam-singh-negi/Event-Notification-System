import pytest

from app.notification.queues import EventQueueManager
from app.notification.models import Event, EventType
from app.notification.exceptions import UnsupportedEventTypeError


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def make_event(event_type: EventType) -> Event:
    """
    Create a valid event payload per event type.
    Payload correctness is required due to strict validation.
    """
    payloads = {
        EventType.EMAIL: {
            "recipient": "user@example.com",
            "message": "Hello",
        },
        EventType.SMS: {
            "phoneNumber": "+1234567890",
            "message": "Hello",
        },
        EventType.PUSH: {
            "deviceId": "device-123",
            "message": "Hello",
        },
    }

    return Event.create(
        event_type=event_type,
        payload=payloads[event_type],
        callback_url="http://example.com",
    )


# -------------------------------------------------------------------
# Core behavior
# -------------------------------------------------------------------

def test_fifo_order_is_preserved_per_event_type():
    """
    Events must be dequeued in the same order they are enqueued
    for a given event type (FIFO guarantee).
    """
    qm = EventQueueManager()

    e1 = make_event(EventType.EMAIL)
    e2 = make_event(EventType.EMAIL)

    qm.enqueue(e1)
    qm.enqueue(e2)

    assert qm.dequeue(EventType.EMAIL) == e1
    assert qm.dequeue(EventType.EMAIL) == e2


def test_event_is_enqueued_into_correct_queue_by_event_type():
    """
    Events must be enqueued only into the queue that matches their event type.
    """

    qm = EventQueueManager()

    email_event = make_event(EventType.EMAIL)
    sms_event = make_event(EventType.SMS)
    push_event = make_event(EventType.PUSH)

    qm.enqueue(email_event)
    qm.enqueue(sms_event)
    qm.enqueue(push_event)

    assert qm.dequeue(EventType.EMAIL) == email_event
    assert qm.dequeue(EventType.SMS) == sms_event
    assert qm.dequeue(EventType.PUSH) == push_event


# -------------------------------------------------------------------
# Queue state inspection
# -------------------------------------------------------------------

def test_queue_size_reflects_enqueue_and_dequeue():
    """
    Queue size should accurately reflect enqueue/dequeue operations.
    """
    qm = EventQueueManager()
    event = make_event(EventType.PUSH)

    assert qm.size(EventType.PUSH) == 0

    qm.enqueue(event)
    assert qm.size(EventType.PUSH) == 1

    qm.dequeue(EventType.PUSH)
    assert qm.size(EventType.PUSH) == 0


# -------------------------------------------------------------------
# Empty queue behavior
# -------------------------------------------------------------------

def test_dequeue_returns_none_when_queue_is_empty():
    """
    Dequeue should return None (not raise) when the queue is empty,
    allowing worker threads to poll safely.
    """
    qm = EventQueueManager()

    result = qm.dequeue(EventType.EMAIL, timeout=0.1)

    assert result is None


# -------------------------------------------------------------------
# Error handling
# -------------------------------------------------------------------

def test_unsupported_event_type_raises_error():
    """
    Dequeuing an unsupported event type must fail fast.
    """
    qm = EventQueueManager()

    with pytest.raises(UnsupportedEventTypeError):
        qm.dequeue("UNKNOWN")  # type: ignore


# -------------------------------------------------------------------
# Mixed usage patterns
# -------------------------------------------------------------------

def test_interleaved_enqueue_and_dequeue_behaves_correctly():
    """
    Queue behavior must remain correct when enqueue and dequeue
    calls are interleaved.
    """
    qm = EventQueueManager()

    e1 = make_event(EventType.EMAIL)
    e2 = make_event(EventType.EMAIL)

    qm.enqueue(e1)
    assert qm.dequeue(EventType.EMAIL) == e1

    qm.enqueue(e2)
    assert qm.dequeue(EventType.EMAIL) == e2
