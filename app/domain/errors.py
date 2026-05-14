class DomainError(Exception):
    """Base exception for all domain/business errors.

    Intentionally framework-agnostic (no HTTP, no DB details).
    """


class NotFoundError(DomainError):
    """A domain error for 'not found' cases so Presentation can map to 404."""
