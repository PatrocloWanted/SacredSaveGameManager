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
from .platform_utils import (
    get_platform_info, get_cross_platform_paths, get_game_executables, log_platform_info,
    PlatformInfo, CrossPlatformPaths, GameExecutables
)
from .cross_platform_symlinks import (
    get_symlink_manager, CrossPlatformSymlinkManager, LinkType
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
    'PathValidator', 'NameValidator', 'GameValidator', 'SystemValidator',
    # Platform utilities
    'get_platform_info', 'get_cross_platform_paths', 'get_game_executables', 'log_platform_info',
    'PlatformInfo', 'CrossPlatformPaths', 'GameExecutables',
    # Cross-platform symlinks
    'get_symlink_manager', 'CrossPlatformSymlinkManager', 'LinkType'
]
