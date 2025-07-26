"""Models package for Sacred Save Game Manager."""

from typing import Dict, Any, NotRequired, TypedDict

# Type definitions
GameData = TypedDict(
    "GameData",
    {
        "name": str,
        "path": str,
        "save": NotRequired[str],
        "save_backup": NotRequired[str],
        "valid": NotRequired[bool],
    },
)

__all__ = ['GameData']
