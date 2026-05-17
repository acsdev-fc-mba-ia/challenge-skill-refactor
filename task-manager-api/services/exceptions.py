class ConflictError(ValueError):
    """Raised when a resource conflict occurs (e.g., duplicate email)."""
    pass


class AuthenticationError(Exception):
    """Raised when authentication credentials are invalid."""
    pass
