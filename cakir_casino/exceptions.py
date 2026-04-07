class CasinoError(Exception):
    """Base exception for the casino application."""


class ValidationError(CasinoError):
    """Raised when user input or state is invalid."""


class AuthenticationError(CasinoError):
    """Raised when authentication fails."""


class AuthorizationError(CasinoError):
    """Raised when a user lacks permission."""


class NotFoundError(CasinoError):
    """Raised when a required record does not exist."""
