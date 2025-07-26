"""Configuration management for Sacred Save Game Manager."""

import json
import os
import pathlib
from typing import Dict, List, Any


class ConfigManager:
    """Handles configuration loading, saving, and validation."""
    
    def __init__(self):
        self.config_file = (
            "sacred_save_game_manager/config.json"
            if pathlib.Path("sacred_save_game_manager").is_dir()
            else "config.json"
        )
        self._config = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file, creating default if it doesn't exist."""
        if not os.path.exists(self.config_file):
            self._create_default_config()
        
        with open(self.config_file, "r") as f:
            config = json.load(f)
            # Ensure save_dirs is sorted
            config["save_dirs"].sort()
            self._config = config
            return config
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        # Sort save_dirs before saving
        config["save_dirs"].sort()
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=4)
        self._config = config
    
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        default_config = {"games": [], "save_dirs": []}
        with open(self.config_file, "w") as f:
            json.dump(default_config, f, indent=4)
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration, loading if necessary."""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def update_games(self, games: List[Dict[str, Any]]) -> None:
        """Update games list in configuration."""
        if self._config is None:
            self.load_config()
        self._config["games"] = games
        self.save_config(self._config)
    
    def add_game(self, game: Dict[str, Any]) -> None:
        """Add a game to the configuration."""
        if self._config is None:
            self.load_config()
        self._config["games"].append(game)
        self.save_config(self._config)
    
    def remove_game(self, game: Dict[str, Any]) -> None:
        """Remove a game from the configuration."""
        if self._config is None:
            self.load_config()
        if game in self._config["games"]:
            self._config["games"].remove(game)
            self.save_config(self._config)
    
    def add_save_dirs(self, save_dirs: List[str]) -> None:
        """Add save directories to the configuration."""
        if self._config is None:
            self.load_config()
        for save_dir in save_dirs:
            if save_dir not in self._config["save_dirs"]:
                self._config["save_dirs"].append(save_dir)
        self.save_config(self._config)
    
    def remove_save_dirs(self, save_dirs: List[str]) -> None:
        """Remove save directories from the configuration."""
        if self._config is None:
            self.load_config()
        for save_dir in save_dirs:
            if save_dir in self._config["save_dirs"]:
                self._config["save_dirs"].remove(save_dir)
        self.save_config(self._config)
