"""
Domain-specific exceptions for the notification service.
"""


class InvalidEventPayloadError(ValueError):
    """Raised when an event payload fails validation."""


class UnsupportedEventTypeError(ValueError):
    """
    Raised when an operation is attempted on an unsupported
    or unconfigured event type.
    """


class QueueOperationError(RuntimeError):
    """
    Raised when a queue operation fails unexpectedly.
    """


class EventProcessingError(RuntimeError):
    """
    Raised when an event fails during processing.
    """
