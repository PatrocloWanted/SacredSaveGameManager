"""Input validation and sanitization utilities for Sacred Save Game Manager."""

import os
import pathlib
import re
import shutil
from typing import Optional, List
from .exceptions import ValidationError, PermissionError, DiskSpaceError, SystemLimitError
from .logger import get_logger

logger = get_logger("validators")


class PathValidator:
    """Validates and sanitizes file paths."""
    
    # Maximum path length for different systems
    MAX_PATH_LENGTH = {
        'windows': 260,
        'posix': 4096
    }
    
    # Invalid characters for file names
    INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1f]'
    
    @staticmethod
    def validate_directory_path(path: str, must_exist: bool = True) -> str:
        """Validate a directory path."""
        if not path or not isinstance(path, str):
            raise ValidationError("Path cannot be empty or non-string")
        
        # Remove leading/trailing whitespace
        path = path.strip()
        
        if not path:
            raise ValidationError("Path cannot be empty after trimming whitespace")
        
        # Convert to Path object for validation
        try:
            path_obj = pathlib.Path(path).resolve()
        except (OSError, ValueError) as e:
            raise ValidationError(f"Invalid path format: {path}", {"error": str(e)})
        
        # Check path length
        PathValidator._check_path_length(str(path_obj))
        
        # Check for directory traversal attempts
        PathValidator._check_directory_traversal(path)
        
        # Check if path exists (if required)
        if must_exist and not path_obj.exists():
            raise ValidationError(f"Directory does not exist: {path}")
        
        # Check if it's actually a directory (if it exists)
        if path_obj.exists() and not path_obj.is_dir():
            raise ValidationError(f"Path is not a directory: {path}")
        
        # Check permissions
        if path_obj.exists():
            PathValidator._check_directory_permissions(path_obj)
        
        logger.debug(f"Path validation successful: {path}")
        return str(path_obj)
    
    @staticmethod
    def validate_file_path(path: str, must_exist: bool = True) -> str:
        """Validate a file path."""
        if not path or not isinstance(path, str):
            raise ValidationError("File path cannot be empty or non-string")
        
        path = path.strip()
        if not path:
            raise ValidationError("File path cannot be empty after trimming whitespace")
        
        try:
            path_obj = pathlib.Path(path).resolve()
        except (OSError, ValueError) as e:
            raise ValidationError(f"Invalid file path format: {path}", {"error": str(e)})
        
        # Check path length
        PathValidator._check_path_length(str(path_obj))
        
        # Check for directory traversal
        PathValidator._check_directory_traversal(path)
        
        # Check if file exists (if required)
        if must_exist and not path_obj.exists():
            raise ValidationError(f"File does not exist: {path}")
        
        # Check if it's actually a file (if it exists)
        if path_obj.exists() and not path_obj.is_file():
            raise ValidationError(f"Path is not a file: {path}")
        
        # Check parent directory permissions
        if path_obj.parent.exists():
            PathValidator._check_directory_permissions(path_obj.parent)
        
        logger.debug(f"File path validation successful: {path}")
        return str(path_obj)
    
    @staticmethod
    def _check_path_length(path: str) -> None:
        """Check if path length exceeds system limits."""
        system = 'windows' if os.name == 'nt' else 'posix'
        max_length = PathValidator.MAX_PATH_LENGTH[system]
        
        if len(path) > max_length:
            raise SystemLimitError(
                f"Path length ({len(path)}) exceeds system limit ({max_length})",
                {"path": path, "length": len(path), "limit": max_length}
            )
    
    @staticmethod
    def _check_directory_traversal(path: str) -> None:
        """Check for directory traversal attempts."""
        # Look for suspicious patterns
        suspicious_patterns = ['../', '..\\', '../', '..\\\\']
        path_lower = path.lower()
        
        for pattern in suspicious_patterns:
            if pattern in path_lower:
                raise ValidationError(
                    f"Directory traversal attempt detected in path: {path}",
                    {"pattern": pattern}
                )
    
    @staticmethod
    def _check_directory_permissions(path: pathlib.Path) -> None:
        """Check directory permissions."""
        try:
            # Check read permission
            if not os.access(path, os.R_OK):
                raise PermissionError(f"No read permission for directory: {path}")
            
            # Check write permission
            if not os.access(path, os.W_OK):
                raise PermissionError(f"No write permission for directory: {path}")
            
        except OSError as e:
            raise PermissionError(f"Permission check failed for {path}: {str(e)}")


class NameValidator:
    """Validates and sanitizes names (game names, etc.)."""
    
    MIN_NAME_LENGTH = 1
    MAX_NAME_LENGTH = 100
    
    @staticmethod
    def sanitize_game_name(name: str) -> str:
        """Sanitize and validate a game name."""
        if not name or not isinstance(name, str):
            raise ValidationError("Game name cannot be empty or non-string")
        
        # Remove leading/trailing whitespace
        name = name.strip()
        
        if not name:
            raise ValidationError("Game name cannot be empty after trimming whitespace")
        
        # Check length
        if len(name) < NameValidator.MIN_NAME_LENGTH:
            raise ValidationError(f"Game name too short (minimum {NameValidator.MIN_NAME_LENGTH} characters)")
        
        if len(name) > NameValidator.MAX_NAME_LENGTH:
            raise ValidationError(f"Game name too long (maximum {NameValidator.MAX_NAME_LENGTH} characters)")
        
        # Remove invalid characters
        sanitized = re.sub(PathValidator.INVALID_CHARS, '', name)
        
        # Replace multiple spaces with single space
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        if not sanitized:
            raise ValidationError("Game name contains only invalid characters")
        
        if sanitized != name:
            logger.warning(f"Game name sanitized: '{name}' -> '{sanitized}'")
        
        return sanitized


class GameValidator:
    """Validates game directories and installations."""
    
    REQUIRED_FILES = ['Sacred.exe']
    FORBIDDEN_SYMLINKS = True
    
    @staticmethod
    def validate_game_directory(path: str) -> str:
        """Validate a Sacred Gold game directory."""
        # First validate the path itself
        validated_path = PathValidator.validate_directory_path(path, must_exist=True)
        path_obj = pathlib.Path(validated_path)
        
        # Check if it's a symlink (not allowed for game directories)
        if GameValidator.FORBIDDEN_SYMLINKS and path_obj.is_symlink():
            raise ValidationError("Symbolic links are not supported for game directories")
        
        # Check for required files
        missing_files = []
        for required_file in GameValidator.REQUIRED_FILES:
            file_path = path_obj / required_file
            if not file_path.exists():
                missing_files.append(required_file)
        
        if missing_files:
            raise ValidationError(
                f"Required files missing from game directory: {', '.join(missing_files)}",
                {"missing_files": missing_files, "path": validated_path}
            )
        
        logger.info(f"Game directory validation successful: {validated_path}")
        return validated_path


class SystemValidator:
    """Validates system resources and capabilities."""
    
    MIN_FREE_SPACE_MB = 100  # Minimum 100MB free space
    
    @staticmethod
    def check_disk_space(path: str, required_mb: int = None) -> None:
        """Check available disk space."""
        if required_mb is None:
            required_mb = SystemValidator.MIN_FREE_SPACE_MB
        
        try:
            path_obj = pathlib.Path(path)
            if not path_obj.exists():
                path_obj = path_obj.parent
            
            # Get disk usage
            total, used, free = shutil.disk_usage(path_obj)
            free_mb = free // (1024 * 1024)  # Convert to MB
            
            if free_mb < required_mb:
                raise DiskSpaceError(
                    f"Insufficient disk space. Required: {required_mb}MB, Available: {free_mb}MB",
                    {"required_mb": required_mb, "available_mb": free_mb, "path": str(path_obj)}
                )
            
            logger.debug(f"Disk space check passed: {free_mb}MB available at {path_obj}")
            
        except OSError as e:
            raise DiskSpaceError(f"Failed to check disk space for {path}: {str(e)}")
    
    @staticmethod
    def check_symlink_support(path: str) -> bool:
        """Check if the filesystem supports symlinks."""
        try:
            path_obj = pathlib.Path(path)
            if not path_obj.exists():
                path_obj = path_obj.parent
            
            # Try to create a test symlink
            test_target = path_obj / "test_symlink_target"
            test_link = path_obj / "test_symlink"
            
            try:
                test_target.mkdir(exist_ok=True)
                test_link.symlink_to(test_target, target_is_directory=True)
                
                # Check if symlink was created successfully
                supports_symlinks = test_link.is_symlink()
                
                # Clean up
                if test_link.exists():
                    test_link.unlink()
                if test_target.exists():
                    test_target.rmdir()
                
                return supports_symlinks
                
            except (OSError, NotImplementedError):
                return False
                
        except Exception as e:
            logger.warning(f"Failed to check symlink support: {str(e)}")
            return False


# Convenience functions
def validate_game_path(path: str) -> str:
    """Validate a game directory path."""
    return GameValidator.validate_game_directory(path)


def validate_save_path(path: str) -> str:
    """Validate a save directory path."""
    return PathValidator.validate_directory_path(path, must_exist=True)


def sanitize_name(name: str) -> str:
    """Sanitize a game name."""
    return NameValidator.sanitize_game_name(name)


def check_system_requirements(path: str) -> None:
    """Check system requirements for the given path."""
    SystemValidator.check_disk_space(path)
    if not SystemValidator.check_symlink_support(path):
        logger.warning(f"Symlink support not available at {path}")
