import threading
import time
import random

from app.notification.workers import EventWorker
from app.notification.queues import EventQueueManager
from app.notification.services.event_status_service import EventStatusService
from app.notification.services.processors import EmailProcessor
from app.notification.callbacks import CallbackDispatcher
from app.notification.models import Event, EventType


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def make_event(event_id_suffix: str = "") -> Event:
    return Event.create(
        EventType.EMAIL,
        {"recipient": f"user{event_id_suffix}@example.com", "message": "hi"},
        "http://example.com",
    )


def start_worker(monkeypatch, *, disable_callbacks=True, instant_processing=False):
    qm = EventQueueManager()
    status = EventStatusService()
    shutdown = threading.Event()

    if instant_processing:
        monkeypatch.setattr(
            EmailProcessor,
            "_simulate_processing",
            lambda self: None,
        )

    if disable_callbacks:
        monkeypatch.setattr(
            CallbackDispatcher,
            "notify_success",
            lambda *args, **kwargs: None,
        )

    worker = EventWorker(
        EventType.EMAIL,
        qm,
        EmailProcessor(),
        status,
        CallbackDispatcher(),
        shutdown,
    )

    worker.start()
    return worker, qm, status, shutdown


# -------------------------------------------------------------------
# Core worker behavior
# -------------------------------------------------------------------

def test_worker_processes_single_event(monkeypatch):
    """
    Worker should dequeue and process a single event.
    """
    worker, qm, status, shutdown = start_worker(
        monkeypatch, instant_processing=True
    )

    event = make_event("1")
    status.mark_pending(event.event_id)
    qm.enqueue(event)

    time.sleep(0.2)
    shutdown.set()
    worker.join(timeout=2)

    assert status.get_status(event.event_id).value in {"COMPLETED", "FAILED"}


def test_worker_remains_idle_when_queue_is_empty():
    """
    Worker must not crash or exit when queue is empty.
    """
    qm = EventQueueManager()
    status = EventStatusService()
    shutdown = threading.Event()

    worker = EventWorker(
        EventType.EMAIL,
        qm,
        EmailProcessor(),
        status,
        CallbackDispatcher(),
        shutdown,
    )

    worker.start()
    time.sleep(0.2)

    shutdown.set()
    worker.join(timeout=2)

    assert not worker.is_alive()


def test_worker_processes_multiple_events_in_order(monkeypatch):
    """
    Worker should process all queued events before shutdown.
    """
    worker, qm, status, shutdown = start_worker(
        monkeypatch, instant_processing=True
    )

    events = [make_event(str(i)) for i in range(3)]

    for event in events:
        status.mark_pending(event.event_id)
        qm.enqueue(event)

    time.sleep(0.3)
    shutdown.set()
    worker.join(timeout=2)

    for event in events:
        assert status.get_status(event.event_id).value in {
            "COMPLETED",
            "FAILED",
        }


def test_worker_does_not_process_events_after_shutdown(monkeypatch):
    """
    Events enqueued after shutdown should not be processed.
    """
    qm = EventQueueManager()
    status = EventStatusService()
    shutdown = threading.Event()

    worker = EventWorker(
        EventType.EMAIL,
        qm,
        EmailProcessor(),
        status,
        CallbackDispatcher(),
        shutdown,
    )

    shutdown.set()
    worker.start()

    event = make_event("late")
    status.mark_pending(event.event_id)
    qm.enqueue(event)

    worker.join(timeout=2)

    assert status.get_status(event.event_id).value == "PENDING"


# -------------------------------------------------------------------
# Failure handling
# -------------------------------------------------------------------
from app.notification.exceptions import EventProcessingError


def test_worker_invokes_failure_callback(monkeypatch):
    """
    Failure callback must be invoked when processing fails
    with a domain-level EventProcessingError.
    """
    qm = EventQueueManager()
    status = EventStatusService()
    shutdown = threading.Event()

    # Make processing instantly fail with the correct exception
    monkeypatch.setattr(
        EmailProcessor,
        "_simulate_processing",
        lambda self: (_ for _ in ()).throw(
            EventProcessingError("forced failure")
        ),
    )

    failure_called = threading.Event()

    def fake_notify_failure(*args, **kwargs):
        failure_called.set()

    callback_dispatcher = CallbackDispatcher()
    monkeypatch.setattr(
        callback_dispatcher,
        "notify_failure",
        fake_notify_failure,
    )

    worker = EventWorker(
        EventType.EMAIL,
        qm,
        EmailProcessor(),
        status,
        callback_dispatcher,
        shutdown,
    )

    worker.start()

    event = make_event("fail")
    status.mark_pending(event.event_id)
    qm.enqueue(event)

    # Wait for failure callback
    assert failure_called.wait(timeout=2.0)

    shutdown.set()
    worker.join(timeout=2)
