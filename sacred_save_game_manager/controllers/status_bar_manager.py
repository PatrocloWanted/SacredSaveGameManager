"""Status bar management for displaying operation feedback and progress."""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any
from datetime import datetime

from ..utils import get_logger


class StatusBarManager:
    """Manages the status bar at the bottom of the application window."""
    
    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.logger = get_logger("status_bar")
        
        # Create status bar widgets
        self.status_bar = None
        self.status_label = None
        self.operation_label = None
        self.system_label = None
        
        self._create_status_bar()
        
        # Default status
        self.set_status("Ready")
    
    def _create_status_bar(self) -> None:
        """Create the status bar widgets."""
        # Main status bar frame
        self.status_bar = ttk.Frame(self.parent, relief=tk.SUNKEN, borderwidth=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=2, pady=2)
        
        # Status message (left)
        self.status_label = ttk.Label(
            self.status_bar,
            text="Ready",
            anchor=tk.W,
            font=("Arial", 9)
        )
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Operation info (center)
        self.operation_label = ttk.Label(
            self.status_bar,
            text="",
            anchor=tk.CENTER,
            font=("Arial", 9),
            foreground="blue"
        )
        self.operation_label.pack(side=tk.LEFT, padx=5, pady=2, expand=True)
        
        # System info (right)
        self.system_label = ttk.Label(
            self.status_bar,
            text="",
            anchor=tk.E,
            font=("Arial", 9),
            foreground="gray"
        )
        self.system_label.pack(side=tk.RIGHT, padx=5, pady=2)
    
    def set_status(self, message: str, duration: Optional[int] = None) -> None:
        """Set the main status message."""
        self.status_label.config(text=message)
        self.logger.debug(f"Status: {message}")
        
        if duration:
            # Clear message after duration (in milliseconds)
            self.status_label.after(duration, lambda: self.set_status("Ready"))
    
    def set_operation(self, message: str, duration: Optional[int] = 3000) -> None:
        """Set the operation message (temporary)."""
        self.operation_label.config(text=message)
        self.logger.info(f"Operation: {message}")
        
        if duration:
            # Clear message after duration
            self.operation_label.after(duration, lambda: self.operation_label.config(text=""))
    
    def set_system_info(self, message: str) -> None:
        """Set the system information message."""
        self.system_label.config(text=message)
    
    def show_operation_result(self, operation: str, game_name: str, 
                            target: str, success: bool = True) -> None:
        """Show the result of an operation."""
        if success:
            message = f"{operation} successful for '{game_name}' → {target}"
            self.set_operation(message)
        else:
            message = f"{operation} failed for '{game_name}'"
            self.set_operation(message, duration=5000)
    
    def show_undo_redo_result(self, operation, 
                            action: str, success: bool = True) -> None:
        """Show the result of an undo/redo operation."""
        if success:
            message = f"{action}: {operation.operation_type} for '{operation.game_name}'"
            self.set_operation(message)
        else:
            message = f"{action} failed: {operation.validation_reason}"
            self.set_operation(message, duration=5000)
    
    def show_error(self, message: str) -> None:
        """Show an error message."""
        self.set_operation(f"Error: {message}", duration=5000)
    
    def show_warning(self, message: str) -> None:
        """Show a warning message."""
        self.set_operation(f"Warning: {message}", duration=4000)
    
    def show_info(self, message: str) -> None:
        """Show an informational message."""
        self.set_operation(message, duration=3000)
    
    def update_game_selection(self, game_name: Optional[str] = None) -> None:
        """Update status when a game is selected."""
        if game_name:
            self.set_status(f"Game selected: {game_name}")
        else:
            self.set_status("Ready")
    
    def update_operation_count(self, undo_count: int, redo_count: int) -> None:
        """Update system info with undo/redo counts."""
        info_parts = []
        if undo_count > 0:
            info_parts.append(f"Undo: {undo_count}")
        if redo_count > 0:
            info_parts.append(f"Redo: {redo_count}")
        
        if info_parts:
            self.set_system_info(" | ".join(info_parts))
        else:
            self.set_system_info("")
    
    def clear_operation(self) -> None:
        """Clear the operation message."""
        self.operation_label.config(text="")
    
    def get_status(self) -> Dict[str, str]:
        """Get current status bar content."""
        return {
            "status": self.status_label.cget("text"),
            "operation": self.operation_label.cget("text"),
            "system": self.system_label.cget("text")
        }
