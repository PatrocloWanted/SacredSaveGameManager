"""Operation history management for undo/redo functionality."""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from ..utils import get_logger, log_error
from ..utils.exceptions import ConfigurationError, FileOperationError


@dataclass
class LinkOperation:
    """Represents a single link operation that can be undone/redone."""
    operation_id: str
    timestamp: str
    operation_type: str  # "override" or "reset"
    game_id: str  # Unique identifier based on game path
    game_name: str
    previous_target: str
    new_target: str
    is_valid: bool = True
    validation_reason: str = ""


class OperationHistoryManager:
    """Manages operation history for undo/redo functionality."""
    
    def __init__(self, config_manager, game_manager, history_file: str = None):
        self.config_manager = config_manager
        self.game_manager = game_manager
        self.logger = get_logger("operation_history")
        
        # History file location
        if history_file is None:
            config_dir = Path(self.config_manager.config_file).parent
            self.history_file = config_dir / "operation_history.json"
        else:
            self.history_file = Path(history_file)
        
        # Operation history
        self.history: List[LinkOperation] = []
        self.current_position: int = -1
        self.max_history: int = 50
        
        # Start with clean history for each session
        self.history = []
        self.current_position = -1
        
        # Clean up any existing history file to prevent accumulation
        self._clear_history_file()
    
    def _load_history(self) -> None:
        """Load operation history from file."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.history = [LinkOperation(**item) for item in data.get('history', [])]
                    self.current_position = data.get('current_position', -1)
                    self.logger.info(f"Loaded {len(self.history)} operations from history")
        except Exception as e:
            self.logger.warning(f"Failed to load operation history: {e}")
            self.history = []
            self.current_position = -1
    
    def _save_history(self) -> None:
        """Save operation history to file."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'history': [asdict(op) for op in self.history],
                'current_position': self.current_position
            }
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.debug("Saved operation history")
        except Exception as e:
            self.logger.error(f"Failed to save operation history: {e}")
    
    def record_operation(self, operation: LinkOperation) -> None:
        """Record a new operation in history."""
        # Remove any operations after current position (redo history)
        self.history = self.history[:self.current_position + 1]
        
        # Add new operation
        self.history.append(operation)
        self.current_position = len(self.history) - 1
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
            self.current_position = len(self.history) - 1
        
        self._save_history()
        self.logger.debug(f"Recorded operation: {operation.operation_type} for {operation.game_name}")
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return self.current_position >= 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return self.current_position < len(self.history) - 1
    
    def validate_operation(self, operation: LinkOperation) -> bool:
        """Validate if an operation can still be performed."""
        try:
            # Check if game still exists
            config = self.config_manager.get_config()
            games = config.get("games", [])
            
            game_exists = any(
                game["path"] == operation.game_id 
                for game in games
            )
            
            if not game_exists:
                operation.is_valid = False
                operation.validation_reason = "Game no longer exists"
                return False
            
            # Check if target directories exist
            previous_exists = Path(operation.previous_target).exists()
            new_exists = Path(operation.new_target).exists()
            
            if not previous_exists and not new_exists:
                operation.is_valid = False
                operation.validation_reason = "Both target directories no longer exist"
                return False
            
            if not previous_exists:
                operation.is_valid = False
                operation.validation_reason = "Previous target directory no longer exists"
                return False
            
            if not new_exists:
                operation.is_valid = False
                operation.validation_reason = "New target directory no longer exists"
                return False
            
            # Check if game configuration is compatible
            game = next(
                (g for g in games if g["path"] == operation.game_id),
                None
            )
            
            if game and game["name"] != operation.game_name:
                # Game renamed, but still valid
                operation.game_name = game["name"]
            
            operation.is_valid = True
            operation.validation_reason = ""
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating operation: {e}")
            return False
    
    def undo(self) -> Optional[LinkOperation]:
        """Undo the last operation."""
        if not self.can_undo():
            return None
        
        operation = self.history[self.current_position]
        
        # Validate operation
        if not self.validate_operation(operation):
            self.logger.warning(f"Cannot undo invalid operation: {operation.validation_reason}")
            return None
        
        try:
            # Perform the undo
            game = next(
                g for g in self.config_manager.get_config().get("games", [])
                if g["path"] == operation.game_id
            )
            
            success = self.game_manager.rebind_symlink(
                link=Path(game["save"]),
                target=Path(operation.previous_target)
            )
            
            if success:
                self.current_position -= 1
                self._save_history()
                self.logger.info(f"Undid operation: {operation.operation_type} for {operation.game_name}")
                return operation
            
        except Exception as e:
            self.logger.error(f"Error undoing operation: {e}")
            return None
    
    def redo(self) -> Optional[LinkOperation]:
        """Redo the next operation."""
        if not self.can_redo():
            return None
        
        operation = self.history[self.current_position + 1]
        
        # Validate operation
        if not self.validate_operation(operation):
            self.logger.warning(f"Cannot redo invalid operation: {operation.validation_reason}")
            return None
        
        try:
            # Perform the redo
            game = next(
                g for g in self.config_manager.get_config().get("games", [])
                if g["path"] == operation.game_id
            )
            
            success = self.game_manager.rebind_symlink(
                link=Path(game["save"]),
                target=Path(operation.new_target)
            )
            
            if success:
                self.current_position += 1
                self._save_history()
                self.logger.info(f"Redid operation: {operation.operation_type} for {operation.game_name}")
                return operation
            
        except Exception as e:
            self.logger.error(f"Error redoing operation: {e}")
            return None
    
    def cleanup_invalid_operations(self) -> int:
        """Clean up invalid operations from history."""
        cleaned_count = 0
        valid_operations = []
        
        for operation in self.history:
            if self.validate_operation(operation):
                valid_operations.append(operation)
            else:
                cleaned_count += 1
        
        self.history = valid_operations
        self.current_position = min(self.current_position, len(self.history) - 1)
        
        if cleaned_count > 0:
            self._save_history()
            self.logger.info(f"Cleaned up {cleaned_count} invalid operations")
        
        return cleaned_count
    
    def get_operation_summary(self) -> Dict[str, Any]:
        """Get summary of current history state."""
        return {
            "total_operations": len(self.history),
            "current_position": self.current_position,
            "can_undo": self.can_undo(),
            "can_redo": self.can_redo(),
            "valid_operations": sum(1 for op in self.history if op.is_valid),
            "invalid_operations": sum(1 for op in self.history if not op.is_valid)
        }
    
    def clear_history(self) -> None:
        """Clear all operation history."""
        self.history.clear()
        self.current_position = -1
        self._save_history()
        self.logger.info("Cleared operation history")
    
    def _clear_history_file(self) -> None:
        """Clear the history file on startup to ensure clean sessions."""
        try:
            if self.history_file.exists():
                self.history_file.unlink()
                self.logger.debug("Cleared existing history file for clean session")
        except Exception as e:
            self.logger.warning(f"Failed to clear history file: {e}")
