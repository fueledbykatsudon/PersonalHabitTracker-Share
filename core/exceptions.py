"""Purpose-built exceptions shared across application layers."""


class DatabaseError(RuntimeError):
    """A database operation could not be completed."""


class AuthenticationError(RuntimeError):
    """Authentication failed without exposing which credential was incorrect."""


class AuthorizationError(RuntimeError):
    """The current account does not have permission for an operation."""


class ValidationError(ValueError):
    """Input data failed application validation."""
