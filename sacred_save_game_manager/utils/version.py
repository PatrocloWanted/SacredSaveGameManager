"""
Version utilities for Sacred Save Game Manager.

This module provides utilities for accessing version information consistently
throughout the application.
"""

from .. import __version__, __author__, __email__, __description__


def get_version() -> str:
    """Get the current version of Sacred Save Game Manager.
    
    Returns:
        str: The version string (e.g., "1.0.0")
    """
    return __version__


def get_version_info() -> dict:
    """Get comprehensive version and package information.
    
    Returns:
        dict: Dictionary containing version, author, email, and description
    """
    return {
        "version": __version__,
        "author": __author__,
        "email": __email__,
        "description": __description__,
    }


def get_full_version_string() -> str:
    """Get a formatted version string with package name.
    
    Returns:
        str: Formatted string like "Sacred Save Game Manager v1.0.0"
    """
    return f"Sacred Save Game Manager v{__version__}"


# Make version easily accessible at module level
VERSION = __version__
