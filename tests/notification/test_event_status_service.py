import threading

from app.notification.services.event_status_service import (
    EventStatusService,
    EventStatus,
)


def test_status_lifecycle_transitions():
    """
    An event should transition cleanly through valid lifecycle states.
    """
    service = EventStatusService()

    service.mark_pending("event-1")
    assert service.get_status("event-1") == EventStatus.PENDING

    service.mark_completed("event-1")
    assert service.get_status("event-1") == EventStatus.COMPLETED


def test_failed_status_is_recorded_correctly():
    service = EventStatusService()

    service.mark_failed("event-2")
    assert service.get_status("event-2") == EventStatus.FAILED


def test_unknown_event_returns_none():
    """
    Querying an unknown event must not raise.
    """
    service = EventStatusService()

    assert service.get_status("unknown-id") is None


def test_last_status_write_wins():
    """
    Status updates are overwrite-based.
    """
    service = EventStatusService()

    service.mark_pending("event-1")
    service.mark_failed("event-1")

    assert service.get_status("event-1") == EventStatus.FAILED


def test_multiple_events_are_tracked_independently():
    service = EventStatusService()

    service.mark_pending("event-1")
    service.mark_completed("event-2")

    assert service.get_status("event-1") == EventStatus.PENDING
    assert service.get_status("event-2") == EventStatus.COMPLETED


def test_status_updates_are_idempotent():
    """
    Re-applying the same status must not cause issues.
    """
    service = EventStatusService()

    service.mark_pending("event-1")
    service.mark_pending("event-1")

    assert service.get_status("event-1") == EventStatus.PENDING


def test_thread_safety_under_concurrent_updates():
    """
    Concurrent updates must never corrupt state.
    """
    service = EventStatusService()

    def update_status_repeatedly():
        for _ in range(100):
            service.mark_pending("event-1")
            service.mark_completed("event-1")

    threads = [
        threading.Thread(target=update_status_repeatedly)
        for _ in range(5)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert service.get_status("event-1") in {
        EventStatus.PENDING,
        EventStatus.COMPLETED,
    }
