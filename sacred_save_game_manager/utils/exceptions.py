"""Custom exception classes for Sacred Save Game Manager."""


class SacredManagerError(Exception):
    """Base exception class for Sacred Save Game Manager."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class ConfigurationError(SacredManagerError):
    """Raised when there are configuration file issues."""
    pass


class GameDirectoryError(SacredManagerError):
    """Raised when there are game directory validation problems."""
    pass


class SymlinkError(SacredManagerError):
    """Raised when symlink operations fail."""
    pass


class PermissionError(SacredManagerError):
    """Raised when file permission issues occur."""
    pass


class DiskSpaceError(SacredManagerError):
    """Raised when there's insufficient disk space."""
    pass


class ValidationError(SacredManagerError):
    """Raised when input validation fails."""
    pass


class FileOperationError(SacredManagerError):
    """Raised when file operations fail."""
    pass


class CorruptedDataError(SacredManagerError):
    """Raised when data corruption is detected."""
    pass


class NetworkError(SacredManagerError):
    """Raised when network-related operations fail."""
    pass


class SystemLimitError(SacredManagerError):
    """Raised when system limits are exceeded (e.g., path length)."""
    pass
