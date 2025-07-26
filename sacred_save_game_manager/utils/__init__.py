"""Utilities package for Sacred Save Game Manager."""

from .logger import get_logger, log_operation, log_error, log_warning, log_user_action, app_logger
from .exceptions import (
    SacredManagerError, ConfigurationError, GameDirectoryError, SymlinkError,
    PermissionError, DiskSpaceError, ValidationError, FileOperationError,
    CorruptedDataError, NetworkError, SystemLimitError
)
from .validators import (
    validate_game_path, validate_save_path, sanitize_name, check_system_requirements,
    PathValidator, NameValidator, GameValidator, SystemValidator
)

__all__ = [
    # Logger
    'get_logger', 'log_operation', 'log_error', 'log_warning', 'log_user_action', 'app_logger',
    # Exceptions
    'SacredManagerError', 'ConfigurationError', 'GameDirectoryError', 'SymlinkError',
    'PermissionError', 'DiskSpaceError', 'ValidationError', 'FileOperationError',
    'CorruptedDataError', 'NetworkError', 'SystemLimitError',
    # Validators
    'validate_game_path', 'validate_save_path', 'sanitize_name', 'check_system_requirements',
    'PathValidator', 'NameValidator', 'GameValidator', 'SystemValidator'
]
