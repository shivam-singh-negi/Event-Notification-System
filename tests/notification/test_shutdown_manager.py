import threading
import time

from app.lifecycle.shutdown import ShutdownManager


class DummyWorker(threading.Thread):
    def __init__(self, shutdown_event):
        super().__init__(daemon=True)
        self.shutdown_event = shutdown_event
        self.stopped = False

    def run(self):
        while not self.shutdown_event.is_set():
            time.sleep(0.01)
        self.stopped = True


def test_shutdown_manager():
    manager = ShutdownManager()
    worker = DummyWorker(manager.shutdown_event)

    worker.start()
    time.sleep(0.05)

    manager.initiate_shutdown()
    manager.wait_for_workers([worker], timeout_seconds=1)

    assert worker.stopped is True
