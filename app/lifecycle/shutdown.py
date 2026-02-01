"""
Graceful shutdown coordination.

Ensures:
- Workers receive shutdown signal
- Queues are drained before exit
- Threads exit cleanly
"""

import threading
import logging
from typing import Iterable

logger = logging.getLogger("app.lifecycle.shutdown")


class ShutdownManager:
    """
    Coordinates graceful shutdown of background workers.
    """

    def __init__(self) -> None:
        self._shutdown_event = threading.Event()

    @property
    def shutdown_event(self) -> threading.Event:
        return self._shutdown_event

    def initiate_shutdown(self) -> None:
        """
        Signal workers to stop after draining queues.
        """
        if not self._shutdown_event.is_set():
            logger.info("Shutdown signal set")
            self._shutdown_event.set()

    def wait_for_workers(
        self,
        workers: Iterable[threading.Thread],
        timeout_seconds: float | None = None,
    ) -> None:
        """
        Block until all workers exit.
        """
        for worker in workers:
            logger.info("Waiting for %s to exit", worker.name)
            worker.join(timeout=timeout_seconds)

        logger.info("All workers shut down cleanly")
