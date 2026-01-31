import threading
import time

from app.notification.workers import EventWorker
from app.notification.queues import EventQueueManager
from app.notification.services.event_status_service import EventStatusService
from app.notification.services.processors import EmailProcessor
from app.notification.callbacks import CallbackDispatcher
from app.notification.models import Event, EventType


def test_worker_processes_event(monkeypatch):
    qm = EventQueueManager()
    status = EventStatusService()
    shutdown = threading.Event()

    # Disable callbacks
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

    event = Event.create(
        EventType.EMAIL,
        {"recipient": "a@b.com", "message": "hi"},
        "http://example.com",
    )

    status.mark_pending(event.event_id)
    qm.enqueue(event)

    time.sleep(6)
    shutdown.set()
    worker.join()

    assert status.get_status(event.event_id).value in {"COMPLETED", "FAILED"}


import threading
import time

from app.notification.workers import EventWorker
from app.notification.queues import EventQueueManager
from app.notification.services.event_status_service import EventStatusService
from app.notification.services.processors import EmailProcessor
from app.notification.callbacks import CallbackDispatcher
from app.notification.models import Event, EventType


def test_worker_processes_event(monkeypatch):
    qm = EventQueueManager()
    status = EventStatusService()
    shutdown = threading.Event()

    # Disable callbacks
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

    event = Event.create(
        EventType.EMAIL,
        {"recipient": "a@b.com", "message": "hi"},
        "http://example.com",
    )

    status.mark_pending(event.event_id)
    qm.enqueue(event)

    time.sleep(6)
    shutdown.set()
    worker.join()

    assert status.get_status(event.event_id).value in {"COMPLETED", "FAILED"}


def test_worker_idle_when_queue_empty():
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
    time.sleep(1)

    shutdown.set()
    worker.join(timeout=2)

    assert not worker.is_alive()


def test_worker_processes_multiple_events(monkeypatch):
    qm = EventQueueManager()
    status = EventStatusService()
    shutdown = threading.Event()

    # Make processing instant
    monkeypatch.setattr(
        EmailProcessor,
        "_simulate_processing",
        lambda self: None,
    )

    # Disable callbacks
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

    events = [
        Event.create(
            EventType.EMAIL,
            {"recipient": f"user{i}@b.com", "message": "hi"},
            "http://example.com",
        )
        for i in range(3)
    ]

    for e in events:
        status.mark_pending(e.event_id)
        qm.enqueue(e)

    # Give worker a short moment
    time.sleep(0.5)

    shutdown.set()
    worker.join(timeout=2)

    for e in events:
        assert status.get_status(e.event_id).value in {
            "COMPLETED",
            "FAILED",
        }


def test_worker_does_not_process_after_shutdown(monkeypatch):
    qm = EventQueueManager()
    status = EventStatusService()
    shutdown = threading.Event()

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

    shutdown.set()
    worker.start()

    event = Event.create(
        EventType.EMAIL,
        {"recipient": "a@b.com", "message": "hi"},
        "http://example.com",
    )

    status.mark_pending(event.event_id)
    qm.enqueue(event)

    time.sleep(1)
    worker.join(timeout=2)

    # Event should remain pending because worker never processed it
    assert status.get_status(event.event_id).value == "PENDING"


def test_worker_invokes_failure_callback(monkeypatch):
    qm = EventQueueManager()
    status = EventStatusService()
    shutdown = threading.Event()

    monkeypatch.setattr("random.random", lambda: 0.0)

    called = {"value": False}

    def fake_notify_failure(*args, **kwargs):
        called["value"] = True

    monkeypatch.setattr(
        CallbackDispatcher,
        "notify_failure",
        fake_notify_failure,
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

    time.sleep(6)
    shutdown.set()
    worker.join(timeout=3)

    assert called["value"] is True
