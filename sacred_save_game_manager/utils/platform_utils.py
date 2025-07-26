"""Cross-platform utilities for Sacred Save Game Manager."""

import os
import sys
import platform
import subprocess
import ctypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .logger import get_logger
from .exceptions import SystemLimitError, PermissionError

logger = get_logger("platform_utils")


class PlatformInfo:
    """Platform detection and information utilities."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.version = platform.version()
        self.machine = platform.machine()
        self.is_windows = self.system == 'windows'
        self.is_macos = self.system == 'darwin'
        self.is_linux = self.system == 'linux'
        
        # Windows-specific detection
        self.windows_version = None
        self.is_windows_10_or_later = False
        self.has_developer_mode = False
        self.is_admin = False
        
        if self.is_windows:
            self._detect_windows_specifics()
        
        logger.info(f"Platform detected: {self.system} {self.version} on {self.machine}")
    
    def _detect_windows_specifics(self) -> None:
        """Detect Windows-specific capabilities."""
        try:
            # Get Windows version
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            self.windows_version = winreg.QueryValueEx(key, "CurrentVersion")[0]
            winreg.CloseKey(key)
            
            # Check if Windows 10 or later (version 10.0+)
            version_parts = self.windows_version.split('.')
            if len(version_parts) >= 2:
                major = int(version_parts[0])
                minor = int(version_parts[1])
                self.is_windows_10_or_later = major >= 10
            
            # Check for administrator privileges
            self.is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            
            # Check for Developer Mode (Windows 10+)
            if self.is_windows_10_or_later:
                self.has_developer_mode = self._check_windows_developer_mode()
                
        except Exception as e:
            logger.warning(f"Failed to detect Windows specifics: {e}")
    
    def _check_windows_developer_mode(self) -> bool:
        """Check if Windows Developer Mode is enabled."""
        try:
            import winreg
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            value, _ = winreg.QueryValueEx(key, "AllowDevelopmentWithoutDevLicense")
            winreg.CloseKey(key)
            return value == 1
        except (FileNotFoundError, OSError):
            return False
        except Exception as e:
            logger.debug(f"Error checking Developer Mode: {e}")
            return False
    
    def can_create_symlinks(self) -> bool:
        """Check if the current user can create symbolic links."""
        if self.is_windows:
            return self.is_admin or self.has_developer_mode
        else:
            # Unix systems generally allow symlinks for regular users
            return True
    
    def get_symlink_capability_info(self) -> Dict[str, any]:
        """Get detailed information about symlink capabilities."""
        info = {
            'can_create_symlinks': self.can_create_symlinks(),
            'platform': self.system,
            'requires_admin': False,
            'has_junction_support': False,
            'recommendations': []
        }
        
        if self.is_windows:
            info['requires_admin'] = not self.has_developer_mode
            info['has_junction_support'] = True
            info['is_admin'] = self.is_admin
            info['has_developer_mode'] = self.has_developer_mode
            
            if not self.can_create_symlinks():
                info['recommendations'].extend([
                    "Enable Windows Developer Mode in Settings > Update & Security > For developers",
                    "Or run the application as Administrator"
                ])
        
        return info


class CrossPlatformPaths:
    """Cross-platform path handling utilities."""
    
    # Maximum path lengths by platform
    MAX_PATH_LENGTHS = {
        'windows': 260,  # Traditional limit, can be 32767 with long path support
        'darwin': 1024,  # macOS HFS+ limit
        'linux': 4096    # Most Linux filesystems
    }
    
    # Reserved names on Windows
    WINDOWS_RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    # Invalid characters by platform
    INVALID_CHARS = {
        'windows': r'<>:"/\|?*\x00-\x1f',
        'darwin': r':\x00',
        'linux': r'/\x00'
    }
    
    def __init__(self, platform_info: PlatformInfo):
        self.platform_info = platform_info
        self.system = platform_info.system
    
    def normalize_path(self, path: str) -> str:
        """Normalize a path for the current platform."""
        path_obj = Path(path)
        
        # Resolve to absolute path
        try:
            normalized = path_obj.resolve()
        except (OSError, ValueError) as e:
            raise SystemLimitError(f"Invalid path: {path}", {"error": str(e)})
        
        return str(normalized)
    
    def validate_path_length(self, path: str) -> None:
        """Validate path length for the current platform."""
        max_length = self.MAX_PATH_LENGTHS.get(self.system, 4096)
        
        if len(path) > max_length:
            raise SystemLimitError(
                f"Path length ({len(path)}) exceeds platform limit ({max_length})",
                {"path": path, "length": len(path), "limit": max_length, "platform": self.system}
            )
    
    def validate_filename(self, filename: str) -> None:
        """Validate filename for the current platform."""
        if self.system == 'windows':
            # Check reserved names
            name_upper = filename.upper()
            if name_upper in self.WINDOWS_RESERVED_NAMES:
                raise SystemLimitError(f"'{filename}' is a reserved name on Windows")
            
            # Check for reserved names with extensions
            name_base = name_upper.split('.')[0]
            if name_base in self.WINDOWS_RESERVED_NAMES:
                raise SystemLimitError(f"'{filename}' uses a reserved name on Windows")
        
        # Check invalid characters
        invalid_chars = self.INVALID_CHARS.get(self.system, '')
        for char in filename:
            if char in invalid_chars:
                raise SystemLimitError(f"Character '{char}' is not allowed in filenames on {self.system}")
    
    def is_case_sensitive_filesystem(self, path: str) -> bool:
        """Check if the filesystem at the given path is case-sensitive."""
        try:
            test_path = Path(path)
            if not test_path.exists():
                test_path = test_path.parent
            
            # Create test files with different cases
            test_lower = test_path / "case_test_file.tmp"
            test_upper = test_path / "CASE_TEST_FILE.tmp"
            
            try:
                test_lower.touch()
                # If filesystem is case-insensitive, both paths refer to the same file
                is_case_sensitive = not test_upper.exists()
                
                # Clean up
                if test_lower.exists():
                    test_lower.unlink()
                if test_upper.exists() and is_case_sensitive:
                    test_upper.unlink()
                
                return is_case_sensitive
                
            except (OSError, PermissionError):
                # Fall back to platform defaults
                return self.system == 'linux'
                
        except Exception as e:
            logger.warning(f"Failed to test case sensitivity: {e}")
            # Default assumptions
            return self.system == 'linux'


class GameExecutables:
    """Platform-specific game executable detection."""
    
    # Game executables by platform
    # Note: Sacred Gold is a Windows game that runs through Wine/Proton on Linux/macOS
    # so the executable is always Sacred.exe regardless of platform
    SACRED_EXECUTABLES = {
        'windows': ['Sacred.exe', 'Sacred Gold.exe', 'sacred.exe'],
        'darwin': ['Sacred.exe', 'Sacred Gold.exe', 'sacred.exe'],  # Wine/Proton on macOS
        'linux': ['Sacred.exe', 'Sacred Gold.exe', 'sacred.exe']    # Wine/Proton on Linux
    }
    
    def __init__(self, platform_info: PlatformInfo):
        self.platform_info = platform_info
        self.system = platform_info.system
    
    def get_executable_names(self) -> List[str]:
        """Get list of possible executable names for the current platform."""
        return self.SACRED_EXECUTABLES.get(self.system, ['Sacred.exe'])
    
    def find_game_executable(self, game_directory: str) -> Optional[str]:
        """Find the game executable in the given directory."""
        game_path = Path(game_directory)
        
        if not game_path.exists() or not game_path.is_dir():
            return None
        
        executable_names = self.get_executable_names()
        
        # Check for case-sensitive vs case-insensitive matching
        paths = CrossPlatformPaths(self.platform_info)
        is_case_sensitive = paths.is_case_sensitive_filesystem(game_directory)
        
        for exe_name in executable_names:
            if is_case_sensitive:
                # Exact match
                exe_path = game_path / exe_name
                if exe_path.exists():
                    return str(exe_path)
            else:
                # Case-insensitive search
                for item in game_path.iterdir():
                    if item.name.lower() == exe_name.lower():
                        return str(item)
        
        return None
    
    def is_valid_game_directory(self, game_directory: str) -> bool:
        """Check if directory contains a valid Sacred Gold installation."""
        return self.find_game_executable(game_directory) is not None


# Global instances
platform_info = PlatformInfo()
cross_platform_paths = CrossPlatformPaths(platform_info)
game_executables = GameExecutables(platform_info)


def get_platform_info() -> PlatformInfo:
    """Get platform information instance."""
    return platform_info


def get_cross_platform_paths() -> CrossPlatformPaths:
    """Get cross-platform paths utility instance."""
    return cross_platform_paths


def get_game_executables() -> GameExecutables:
    """Get game executables utility instance."""
    return game_executables


def log_platform_info() -> None:
    """Log detailed platform information."""
    info = platform_info
    logger.info(f"Platform: {info.system} {info.version}")
    logger.info(f"Machine: {info.machine}")
    
    if info.is_windows:
        logger.info(f"Windows version: {info.windows_version}")
        logger.info(f"Is Windows 10+: {info.is_windows_10_or_later}")
        logger.info(f"Is Administrator: {info.is_admin}")
        logger.info(f"Has Developer Mode: {info.has_developer_mode}")
    
    symlink_info = info.get_symlink_capability_info()
    logger.info(f"Can create symlinks: {symlink_info['can_create_symlinks']}")
    
    if symlink_info['recommendations']:
        logger.info(f"Recommendations: {'; '.join(symlink_info['recommendations'])}")
