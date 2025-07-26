"""Save directory management for Sacred Save Game Manager."""

import os
import pathlib
from typing import List
from .config_manager import ConfigManager


class SaveManager:
    """Handles save directory operations and validation."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
    
    def add_save_directory(self, path: str, recursive: bool = False) -> List[str]:
        """Add save directory(ies) to configuration."""
        added_dirs = []
        
        if recursive:
            # Add all terminal directories recursively
            for root, dirs, _ in os.walk(path):
                if not dirs:  # Terminal directory (no subdirectories)
                    if self._is_valid_save_directory(root):
                        added_dirs.append(root)
        else:
            # Add single directory
            if self._is_valid_save_directory(path):
                added_dirs.append(path)
        
        # Filter out directories that are already in config
        config = self.config_manager.get_config()
        new_dirs = [d for d in added_dirs if d not in config["save_dirs"]]
        
        if new_dirs:
            self.config_manager.add_save_dirs(new_dirs)
        
        return new_dirs
    
    def remove_save_directories(self, paths: List[str]) -> None:
        """Remove save directories from configuration."""
        self.config_manager.remove_save_dirs(paths)
    
    def get_save_directories(self) -> List[str]:
        """Get all save directories from configuration."""
        config = self.config_manager.get_config()
        return config["save_dirs"]
    
    def filter_save_directories(self, search_term: str) -> List[str]:
        """Filter save directories by search term."""
        save_dirs = self.get_save_directories()
        if not search_term:
            return save_dirs
        
        search_term = search_term.lower()
        return [path for path in save_dirs if search_term in path.lower()]
    
    def _is_valid_save_directory(self, path: str) -> bool:
        """Check if a path is a valid save directory."""
        return os.path.exists(path) and os.path.isdir(path)
    
    def validate_save_directory(self, path: str) -> bool:
        """Validate that a save directory exists and is accessible."""
        path_obj = pathlib.Path(path)
        return (
            path_obj.exists(follow_symlinks=False) and 
            path_obj.is_dir()
        )
