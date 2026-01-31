"""
Graceful shutdown coordination.

This module provides utilities to signal worker threads
to stop and optionally wait for them to exit cleanly.
"""

import threading
import logging
from typing import Iterable

logger = logging.getLogger("app.lifecycle.shutdown")


class ShutdownManager:
    """
    Coordinates graceful shutdown of background workers.

    Responsibilities:
    - Signal shutdown intent
    - Wait for worker threads to exit
    """

    def __init__(self) -> None:
        self._shutdown_event = threading.Event()

    @property
    def shutdown_event(self) -> threading.Event:
        """
        Expose the shutdown event to workers.
        """
        return self._shutdown_event

    def initiate_shutdown(self) -> None:
        """
        Signal all workers to begin shutdown.
        """
        logger.info("Shutdown initiated")
        self._shutdown_event.set()

    def wait_for_workers(
        self,
        workers: Iterable[threading.Thread],
        timeout_seconds: float | None = None,
    ) -> None:
        """
        Wait for worker threads to exit.

        Args:
            workers: Iterable of worker threads
            timeout_seconds: Optional join timeout
        """
        for worker in workers:
            logger.info(f"Waiting for {worker.name} to shut down")
            worker.join(timeout=timeout_seconds)

        logger.info("All workers shut down")
