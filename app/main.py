from fastapi import FastAPI

from app.logging.logger import setup_logging
from app.notification.api import (
    router as notification_router,
    queue_manager,
    status_service,
)
from app.notification.workers import create_workers
from app.lifecycle.shutdown import ShutdownManager

app = FastAPI(title="Event Notification System")

shutdown_manager = ShutdownManager()
workers = {}


@app.on_event("startup")
def startup_event():
    setup_logging()

    global workers
    workers = create_workers(
        queue_manager=queue_manager,
        status_service=status_service,
        shutdown_event=shutdown_manager.shutdown_event,
    )

    for worker in workers.values():
        worker.start()


@app.on_event("shutdown")
def shutdown_event_handler():
    shutdown_manager.initiate_shutdown()
    shutdown_manager.wait_for_workers(workers.values(), timeout_seconds=5)


app.include_router(notification_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
