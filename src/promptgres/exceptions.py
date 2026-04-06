"""Package exceptions."""


class PromptgresError(Exception):
    """Base class for package errors."""


class ConfigError(PromptgresError):
    """Raised when configuration is invalid."""


class DatabaseError(PromptgresError):
    """Raised when database operations fail."""


class InputFileError(PromptgresError):
    """Raised when an input file cannot be parsed."""
