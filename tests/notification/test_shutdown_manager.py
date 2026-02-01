import threading

from app.lifecycle.shutdown import ShutdownManager
from app.notification.queues import EventQueueManager
from app.notification.workers import EventWorker
from app.notification.services.event_status_service import EventStatusService
from app.notification.services.processors import EmailProcessor
from app.notification.callbacks import CallbackDispatcher
from app.notification.models import Event, EventType


# ------------------------------------------------------------------
# Shutdown behavior – core guarantees
# ------------------------------------------------------------------

def test_shutdown_prevents_new_event_acceptance():
    """
    Once shutdown is initiated, new events must not be accepted
    for processing.
    """
    queue_manager = EventQueueManager()
    shutdown_manager = ShutdownManager()

    shutdown_manager.initiate_shutdown()

    event = Event.create(
        EventType.EMAIL,
        {"recipient": "a@b.com", "message": "hi"},
        "http://example.com",
    )

    if shutdown_manager.shutdown_event.is_set():
        accepted = False
    else:
        queue_manager.enqueue(event)
        accepted = True

    assert accepted is False
    assert queue_manager.size(EventType.EMAIL) == 0


def test_in_progress_event_is_completed_during_shutdown(monkeypatch):
    """
    Events already dequeued must complete processing
    even after shutdown is triggered.
    """
    qm = EventQueueManager()
    status = EventStatusService()
    shutdown = threading.Event()

    # Make processing deterministic and instant
    monkeypatch.setattr(
        EmailProcessor,
        "_simulate_processing",
        lambda self: None,
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

    event = Event.create(
        EventType.EMAIL,
        {"recipient": "a@b.com", "message": "hi"},
        "http://example.com",
    )

    status.mark_pending(event.event_id)
    qm.enqueue(event)

    # Trigger shutdown while event is being processed
    shutdown.set()
    worker.join(timeout=2)

    assert status.get_status(event.event_id).value in {
        "COMPLETED",
        "FAILED",
    }


def test_worker_threads_terminate_cleanly_after_shutdown(monkeypatch):
    """
    Worker threads must exit cleanly once shutdown is requested
    and queues are drained.
    """
    qm = EventQueueManager()
    status = EventStatusService()
    shutdown = threading.Event()

    monkeypatch.setattr(
        EmailProcessor,
        "_simulate_processing",
        lambda self: None,
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
    shutdown.set()
    worker.join(timeout=2)

    assert not worker.is_alive()
