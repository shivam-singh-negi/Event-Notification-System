import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.logging.logger import setup_logging
from app.notification.api import (
    router as notification_router,
    queue_manager,
    status_service,
)
from app.notification.workers import create_workers
from app.lifecycle.shutdown import ShutdownManager

logger = logging.getLogger("app.main")

shutdown_manager = ShutdownManager()
workers = {}

# -------------------------------------------------------------------
# Lifespan ( non-blocking, deterministic)
# -------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---------------- STARTUP ----------------
    setup_logging()
    logger.info("Application startup initiated")

    global workers
    workers = create_workers(
        queue_manager=queue_manager,
        status_service=status_service,
        shutdown_event=shutdown_manager.shutdown_event,
    )

    for worker in workers.values():
        logger.info("Starting worker %s", worker.name)
        worker.start()

    logger.info("Application startup complete")

    yield  #  Application is running

    # ---------------- SHUTDOWN ----------------
    logger.info("Application shutdown initiated")

    # Signal shutdown FIRST
    shutdown_manager.initiate_shutdown()

    #  Freeze worker list to avoid mutation bugs
    workers_snapshot = list(workers.values())

    # Never block the event loop
    await asyncio.to_thread(
        shutdown_manager.wait_for_workers,
        workers_snapshot,
        None,  # wait until queues drain
    )

    logger.info("Application shutdown complete")


# -------------------------------------------------------------------
# App
# -------------------------------------------------------------------

app = FastAPI(
    title="Event Notification System",
    lifespan=lifespan,
)

# -------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------

@app.middleware("http")
async def block_requests_during_shutdown(request: Request, call_next):
    """
    Prevent new requests once shutdown has started.
    """
    if shutdown_manager.shutdown_event.is_set():
        return JSONResponse(
            status_code=503,
            content={"detail": "Service is shutting down"},
        )
    return await call_next(request)

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------

app.include_router(notification_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
