from app.notification.services.event_status_service import (
    EventStatusService,
    EventStatus,
)
import threading


def test_status_transitions():
    service = EventStatusService()

    service.mark_pending("1")
    assert service.get_status("1") == EventStatus.PENDING

    service.mark_completed("1")
    assert service.get_status("1") == EventStatus.COMPLETED

    service.mark_failed("2")
    assert service.get_status("2") == EventStatus.FAILED

def test_get_status_unknown_event_returns_none():
    service = EventStatusService()

    assert service.get_status("does-not-exist") is None


def test_status_overwrite_last_write_wins():
    service = EventStatusService()

    service.mark_pending("1")
    service.mark_failed("1")

    assert service.get_status("1") == EventStatus.FAILED


def test_multiple_events_are_isolated():
    service = EventStatusService()

    service.mark_pending("1")
    service.mark_completed("2")

    assert service.get_status("1") == EventStatus.PENDING
    assert service.get_status("2") == EventStatus.COMPLETED


def test_status_updates_are_idempotent():
    service = EventStatusService()

    service.mark_pending("1")
    service.mark_pending("1")

    assert service.get_status("1") == EventStatus.PENDING



def test_thread_safety_under_concurrent_updates():
    service = EventStatusService()

    def mark_status():
        for _ in range(100):
            service.mark_pending("1")
            service.mark_completed("1")

    threads = [threading.Thread(target=mark_status) for _ in range(5)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Final state must be one of the valid states, never corrupted
    assert service.get_status("1") in {
        EventStatus.PENDING,
        EventStatus.COMPLETED,
    }
