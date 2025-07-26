"""Configuration management for Sacred Save Game Manager."""

import json
import os
import pathlib
import shutil
from typing import Dict, List, Any
from ..utils import (
    get_logger, log_operation, log_error, log_warning,
    ConfigurationError, FileOperationError, PermissionError,
    CorruptedDataError, ValidationError
)


class ConfigManager:
    """Handles configuration loading, saving, and validation."""
    
    def __init__(self):
        self.logger = get_logger("config_manager")
        self.config_file = (
            "sacred_save_game_manager/config.json"
            if pathlib.Path("sacred_save_game_manager").is_dir()
            else "config.json"
        )
        self._config = None
        self.logger.debug(f"ConfigManager initialized with config file: {self.config_file}")
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file, creating default if it doesn't exist."""
        try:
            if not os.path.exists(self.config_file):
                self.logger.info(f"Config file not found, creating default: {self.config_file}")
                self._create_default_config()
            
            # Check file permissions
            if not os.access(self.config_file, os.R_OK):
                raise PermissionError(f"No read permission for config file: {self.config_file}")
            
            # Create backup before loading
            self._backup_config_file()
            
            with open(self.config_file, "r", encoding='utf-8') as f:
                try:
                    config = json.load(f)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Config file corrupted: {e}")
                    raise CorruptedDataError(
                        f"Configuration file is corrupted: {str(e)}",
                        {"file": self.config_file, "error": str(e)}
                    )
            
            # Validate configuration structure
            self._validate_config_structure(config)
            
            # Ensure save_dirs is sorted
            if "save_dirs" in config and isinstance(config["save_dirs"], list):
                config["save_dirs"].sort()
            
            self._config = config
            self.logger.info(f"Configuration loaded successfully from {self.config_file}")
            log_operation("config_manager", "load_config", {"games": len(config.get("games", [])), "save_dirs": len(config.get("save_dirs", []))})
            return config
            
        except (OSError, IOError) as e:
            log_error("config_manager", e, "load_config", {"file": self.config_file})
            raise FileOperationError(f"Failed to load configuration file: {str(e)}", {"file": self.config_file})
        except Exception as e:
            log_error("config_manager", e, "load_config", {"file": self.config_file})
            raise ConfigurationError(f"Unexpected error loading configuration: {str(e)}")
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            # Validate configuration before saving
            self._validate_config_structure(config)
            
            # Check write permissions
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.access(config_dir, os.W_OK):
                raise PermissionError(f"No write permission for config directory: {config_dir}")
            
            # Sort save_dirs before saving
            if "save_dirs" in config and isinstance(config["save_dirs"], list):
                config["save_dirs"].sort()
            
            # Create temporary file first for atomic write
            temp_file = f"{self.config_file}.tmp"
            
            with open(temp_file, "w", encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            # Atomic move to replace original file
            shutil.move(temp_file, self.config_file)
            
            self._config = config
            self.logger.info(f"Configuration saved successfully to {self.config_file}")
            log_operation("config_manager", "save_config", {"games": len(config.get("games", [])), "save_dirs": len(config.get("save_dirs", []))})
            
        except (OSError, IOError) as e:
            log_error("config_manager", e, "save_config", {"file": self.config_file})
            # Clean up temp file if it exists
            temp_file = f"{self.config_file}.tmp"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
            raise FileOperationError(f"Failed to save configuration file: {str(e)}", {"file": self.config_file})
        except Exception as e:
            log_error("config_manager", e, "save_config", {"file": self.config_file})
            raise ConfigurationError(f"Unexpected error saving configuration: {str(e)}")
    
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        try:
            default_config = {"games": [], "save_dirs": []}
            
            # Ensure directory exists
            config_dir = os.path.dirname(self.config_file)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_file, "w", encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            
            self.logger.info(f"Default configuration created: {self.config_file}")
            log_operation("config_manager", "create_default_config", {"file": self.config_file})
            
        except (OSError, IOError) as e:
            log_error("config_manager", e, "_create_default_config", {"file": self.config_file})
            raise FileOperationError(f"Failed to create default configuration: {str(e)}", {"file": self.config_file})
    
    def _validate_config_structure(self, config: Dict[str, Any]) -> None:
        """Validate the structure of the configuration."""
        if not isinstance(config, dict):
            raise ValidationError("Configuration must be a dictionary")
        
        # Check required keys
        required_keys = ["games", "save_dirs"]
        for key in required_keys:
            if key not in config:
                raise ValidationError(f"Missing required configuration key: {key}")
        
        # Validate games structure
        if not isinstance(config["games"], list):
            raise ValidationError("'games' must be a list")
        
        for i, game in enumerate(config["games"]):
            if not isinstance(game, dict):
                raise ValidationError(f"Game at index {i} must be a dictionary")
            
            required_game_keys = ["name", "path"]
            for key in required_game_keys:
                if key not in game:
                    raise ValidationError(f"Game at index {i} missing required key: {key}")
        
        # Validate save_dirs structure
        if not isinstance(config["save_dirs"], list):
            raise ValidationError("'save_dirs' must be a list")
        
        for i, save_dir in enumerate(config["save_dirs"]):
            if not isinstance(save_dir, str):
                raise ValidationError(f"Save directory at index {i} must be a string")
    
    def _backup_config_file(self) -> None:
        """Create a backup of the configuration file."""
        if not os.path.exists(self.config_file):
            return
        
        try:
            backup_file = f"{self.config_file}.backup"
            shutil.copy2(self.config_file, backup_file)
            self.logger.debug(f"Configuration backup created: {backup_file}")
        except (OSError, IOError) as e:
            log_warning("config_manager", f"Failed to create config backup: {str(e)}")
    
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
