import pathlib
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import json
import os
import sys
import uuid
from datetime import datetime

from .controllers import ConfigManager, GameManager, SaveManager, UIManager, StatusBarManager, OperationHistoryManager
from .controllers.operation_history_manager import LinkOperation
from .models import GameData
from .utils import (
    get_logger, log_user_action, log_error, app_logger,
    validate_game_path, sanitize_name, ValidationError,
    ConfigurationError, GameDirectoryError, FileOperationError,
    log_platform_info, get_platform_info
)


class App:
    """Main application coordinator."""
    
    def __init__(self, root):
        self.root = root
        self.logger = get_logger("app")
        
        try:
            # Log application startup
            from .utils import get_version
            app_logger.log_startup(get_version())
            
            # Log platform information
            log_platform_info()
            
            # Initialize managers
            self.logger.info("Initializing application managers...")
            self.config_manager = ConfigManager()
            self.game_manager = GameManager(self.config_manager)
            self.save_manager = SaveManager(self.config_manager)
            self.ui_manager = UIManager(root, self.config_manager, self.game_manager, self.save_manager)
            
            # Initialize status bar and operation history
            self.status_bar_manager = StatusBarManager(root)
            self.operation_history_manager = OperationHistoryManager(
                self.config_manager, self.game_manager
            )
            
            # Wire up event handlers
            self.ui_manager.add_game_handler = self.add_game_handler
            self.ui_manager.remove_game_handler = self.remove_game_handler
            self.ui_manager.reset_game_handler = self.reset_game_handler
            self.ui_manager.add_save_dir_handler = self.add_save_dir_handler
            self.ui_manager.remove_save_dir_handler = self.remove_save_dir_handler
            self.ui_manager.override_save_dir_handler = self.override_save_dir_handler
            self.ui_manager.undo_handler = self.undo_handler
            self.ui_manager.redo_handler = self.redo_handler
            
            # Initialize UI
            self.logger.info("Setting up user interface...")
            self.ui_manager.setup_main_window()
            self.ui_manager.populate_games()
            
            # Initialize save directories listbox
            try:
                # Try to find the save directories listbox with a more flexible approach
                for widget in self.root.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, ttk.Frame):
                                for grandchild in child.winfo_children():
                                    if hasattr(grandchild, 'winfo_name') and grandchild.winfo_name() == "save_dirs_listbox":
                                        self.ui_manager.refresh_listbox(grandchild)
                                        break
            except Exception as e:
                self.logger.warning(f"Could not find save directories listbox widget: {e}")
            
            # Set up keyboard shortcuts
            self._setup_keyboard_shortcuts()
            
            # Initialize status bar and undo/redo counts
            self.status_bar_manager.set_status("Ready")
            self._update_undo_redo_counts()
            
            # Set up shutdown handler
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            self.logger.info("Application initialization completed successfully")
            
        except Exception as e:
            log_error("app", e, "initialization")
            messagebox.showerror(
                "Initialization Error",
                f"Failed to initialize application: {str(e)}\n\nCheck the log files for more details."
            )
            sys.exit(1)
    
    def _on_closing(self):
        """Handle application shutdown."""
        try:
            self.logger.info("Application shutdown initiated")
            app_logger.log_shutdown()
            self.root.destroy()
        except Exception as e:
            log_error("app", e, "shutdown")
            self.root.destroy()

    # === Undo/Redo Handlers ===
    
    def undo_handler(self):
        """Handle undo operation."""
        try:
            self.status_bar_manager.set_status("Performing undo...")
            operation = self.operation_history_manager.undo()
            
            if operation:
                self.status_bar_manager.show_undo_redo_result(operation, "Undo", success=True)
                # Clear selected frame before refreshing UI to prevent stale references
                self.ui_manager.selected_frame = None
                self.ui_manager.populate_games()  # Refresh UI
                self._update_undo_redo_counts()
                self.logger.info(f"Undo successful: {operation.operation_type} for {operation.game_name}")
            else:
                self.status_bar_manager.show_warning("Nothing to undo")
                
        except Exception as e:
            log_error("app", e, "undo_operation")
            self.status_bar_manager.show_error(f"Undo failed: {str(e)}")
    
    def redo_handler(self):
        """Handle redo operation."""
        try:
            self.status_bar_manager.set_status("Performing redo...")
            operation = self.operation_history_manager.redo()
            
            if operation:
                self.status_bar_manager.show_undo_redo_result(operation, "Redo", success=True)
                # Clear selected frame before refreshing UI to prevent stale references
                self.ui_manager.selected_frame = None
                self.ui_manager.populate_games()  # Refresh UI
                self._update_undo_redo_counts()
                self.logger.info(f"Redo successful: {operation.operation_type} for {operation.game_name}")
            else:
                self.status_bar_manager.show_warning("Nothing to redo")
                
        except Exception as e:
            log_error("app", e, "redo_operation")
            self.status_bar_manager.show_error(f"Redo failed: {str(e)}")
    
    def _update_undo_redo_counts(self):
        """Update the status bar with current undo/redo counts and button states."""
        # Count only valid operations
        valid_undo_count = 0
        valid_redo_count = 0
        
        for i, op in enumerate(self.operation_history_manager.history):
            if self.operation_history_manager.validate_operation(op):
                if i <= self.operation_history_manager.current_position:
                    valid_undo_count += 1
                else:
                    valid_redo_count += 1
        
        self.status_bar_manager.update_operation_count(valid_undo_count, valid_redo_count)
        
        # Update button states
        can_undo = self.operation_history_manager.can_undo()
        can_redo = self.operation_history_manager.can_redo()
        self.ui_manager.update_undo_redo_button_states(can_undo, can_redo)
    
    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for undo/redo operations."""
        # Undo: Ctrl+Z
        self.root.bind('<Control-z>', lambda event: self.undo_handler())
        self.root.bind('<Control-Z>', lambda event: self.undo_handler())
        
        # Redo: Ctrl+Y
        self.root.bind('<Control-y>', lambda event: self.redo_handler())
        self.root.bind('<Control-Y>', lambda event: self.redo_handler())
        
        # Alternative Redo: Ctrl+Shift+Z (common in some applications)
        self.root.bind('<Control-Shift-z>', lambda event: self.redo_handler())
        self.root.bind('<Control-Shift-Z>', lambda event: self.redo_handler())
        
        self.logger.debug("Keyboard shortcuts configured: Ctrl+Z (undo), Ctrl+Y (redo)")

    # === Game Tab Handlers ===

    def add_game_handler(self) -> None:
        try:
            log_user_action("add_game_initiated")
            self.status_bar_manager.set_status("Selecting game directory...")
            selected_path = filedialog.askdirectory(title="Select Sacred Gold installation")
            
            if not selected_path:
                self.logger.debug("User cancelled game directory selection")
                self.status_bar_manager.set_status("Ready")
                return
            
            self.logger.info(f"User selected game directory: {selected_path}")
            self.status_bar_manager.set_status("Validating game directory...")
            
            # Validate the selected path using our validators
            try:
                validated_path = validate_game_path(selected_path)
                self.logger.info(f"Game directory validation successful: {validated_path}")
            except ValidationError as e:
                self.logger.warning(f"Game directory validation failed: {str(e)}")
                messagebox.showerror("Invalid Directory", str(e))
                return
            except Exception as e:
                log_error("app", e, "game_path_validation", {"path": selected_path})
                messagebox.showerror("Validation Error", f"Failed to validate directory: {str(e)}")
                return
            
            # Check if game already exists
            try:
                config = self.config_manager.get_config()
                for game in config["games"]:
                    if game["path"] == validated_path:
                        self.logger.info(f"Game already exists: {game['name']}")
                        messagebox.showinfo(
                            "Game already added",
                            f"This directory has already been added as '{game['name']}'.",
                        )
                        return
            except (ConfigurationError, FileOperationError) as e:
                log_error("app", e, "get_config_for_duplicate_check")
                messagebox.showerror("Configuration Error", f"Failed to check for duplicates: {str(e)}")
                return

            # Get and validate game name
            name = simpledialog.askstring(
                "Name", "Provide a name for this Sacred Gold installation:"
            )
            if not name:
                name = "Sacred Gold"
            
            try:
                sanitized_name = sanitize_name(name)
                if sanitized_name != name:
                    self.logger.info(f"Game name sanitized: '{name}' -> '{sanitized_name}'")
                name = sanitized_name
            except ValidationError as e:
                self.logger.warning(f"Game name validation failed: {str(e)}")
                messagebox.showerror("Invalid Name", str(e))
                return
            
            # Create and validate game
            self.status_bar_manager.set_status(f"Setting up game '{name}'...")
            game = {"name": name, "path": validated_path}
            try:
                game = self.game_manager.validate_game_directory(game=game)
                if game["valid"]:
                    self.config_manager.add_game(game)
                    self.ui_manager.populate_games()
                    log_user_action("add_game_success", {"name": name, "path": validated_path})
                    self.logger.info(f"Game added successfully: {name} at {validated_path}")
                    self.status_bar_manager.show_info(f"Game '{name}' added successfully")
                else:
                    self.logger.error(f"Game validation failed for: {validated_path}")
                    self.status_bar_manager.show_error("Game validation failed")
                    messagebox.showerror("Game Validation Failed", "The selected directory could not be set up as a valid game directory.")
            except (GameDirectoryError, FileOperationError) as e:
                log_error("app", e, "add_game_validation", {"name": name, "path": validated_path})
                self.status_bar_manager.show_error(f"Game setup failed: {str(e)}")
                messagebox.showerror("Game Setup Error", f"Failed to set up game directory: {str(e)}")
                return
            except Exception as e:
                log_error("app", e, "add_game_unexpected", {"name": name, "path": validated_path})
                self.status_bar_manager.show_error(f"Unexpected error: {str(e)}")
                messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {str(e)}")
                return
                
        except Exception as e:
            log_error("app", e, "add_game_handler")
            messagebox.showerror("Error", f"Failed to add game: {str(e)}")

    def reset_game_handler(self):
        if self.ui_manager.selected_frame:
            frame, game = self.ui_manager.selected_frame
            game = self.game_manager.validate_game_directory(game=game)
            
            if game["valid"]:
                try:
                    # Get current target before reset
                    current_target = self.game_manager.get_game_symlink_target(game=game)
                    
                    # Update status
                    self.status_bar_manager.set_status(f"Resetting {game['name']}...")
                    
                    # Perform reset
                    success = self.game_manager.rebind_symlink(
                        link=pathlib.Path(game["save"]),
                        target=pathlib.Path(game["save_backup"]),
                    )
                    
                    if success:
                        # Record operation for undo/redo
                        operation = LinkOperation(
                            operation_id=str(uuid.uuid4()),
                            timestamp=datetime.now().isoformat(),
                            operation_type="reset",
                            game_id=game["path"],
                            game_name=game["name"],
                            previous_target=current_target,
                            new_target=game["save_backup"]
                        )
                        self.operation_history_manager.record_operation(operation)
                        
                        # Update UI
                        save_dir_path = frame.nametowidget("save_dir_path")
                        if save_dir_path:
                            save_dir_path.config(text="default")
                        
                        # Update status bar
                        self.status_bar_manager.show_operation_result(
                            "Reset", game["name"], "default", success=True
                        )
                        self._update_undo_redo_counts()
                        
                        self.logger.info(f"Reset successful for {game['name']}")
                    else:
                        self.status_bar_manager.show_error(f"Failed to reset {game['name']}")
                        
                except Exception as e:
                    log_error("app", e, "reset_game", {"game": game["name"]})
                    self.status_bar_manager.show_error(f"Reset failed: {str(e)}")
        else:
            messagebox.showinfo(
                "No Game Selected", "Please select a Sacred Gold entry to reset."
            )

    def remove_game_handler(self) -> None:
        if self.ui_manager.selected_frame:
            frame, game = self.ui_manager.selected_frame
            if messagebox.askyesno(
                "Remove Game",
                f"Are you sure you want to remove '{game['name']}'?",
            ):
                try:
                    self.status_bar_manager.set_status(f"Removing game '{game['name']}'...")
                    self.ui_manager.selected_frame = None
                    frame.destroy()
                    self.config_manager.remove_game(game)
                    # Refresh the UI
                    self.ui_manager.populate_games()
                    self.status_bar_manager.show_info(f"Game '{game['name']}' removed successfully")
                    self.logger.info(f"Game removed: {game['name']}")
                except Exception as e:
                    log_error("app", e, "remove_game", {"game": game["name"]})
                    self.status_bar_manager.show_error(f"Failed to remove game: {str(e)}")
        else:
            self.status_bar_manager.show_warning("No game selected")
            messagebox.showinfo(
                "No Game Selected", "Please select a Sacred Gold entry to remove."
            )
        return

    # === Save Dir Tab Handlers ===

    def add_save_dir_handler(self):
        self.status_bar_manager.set_status("Selecting save directory...")
        selected_path = filedialog.askdirectory(title="Select save archive.")
        
        # Find the listbox widget
        listbox = None
        try:
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Frame):
                            for grandchild in child.winfo_children():
                                if hasattr(grandchild, 'winfo_name') and grandchild.winfo_name() == "save_dirs_listbox":
                                    listbox = grandchild
                                    break
        except Exception as e:
            self.logger.warning(f"Could not find save directories listbox: {e}")
        
        if not selected_path:
            self.status_bar_manager.set_status("Ready")
            return
            
        if selected_path and listbox:
            try:
                add_recursively = messagebox.askyesno(
                    "Add recursively",
                    f"Do you want to recursively add every terminal directories contained in {selected_path}?",
                )
                
                self.status_bar_manager.set_status("Adding save directories...")
                
                # Use SaveManager to add directories
                new_dirs = self.save_manager.add_save_directory(selected_path, recursive=add_recursively)
                
                # Update UI
                for new_dir in new_dirs:
                    listbox.insert(tk.END, new_dir)
                
                # Refresh config
                self.config = self.config_manager.get_config()
                
                # Show success message
                count = len(new_dirs)
                if count > 0:
                    self.status_bar_manager.show_info(f"Added {count} save director{'y' if count == 1 else 'ies'}")
                    self.logger.info(f"Added {count} save directories")
                else:
                    self.status_bar_manager.show_warning("No new directories were added")
                    
            except Exception as e:
                log_error("app", e, "add_save_dir", {"path": selected_path})
                self.status_bar_manager.show_error(f"Failed to add save directories: {str(e)}")
        return

    def remove_save_dir_handler(self):
        # Find the listbox widget
        listbox = None
        try:
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Frame):
                            for grandchild in child.winfo_children():
                                if hasattr(grandchild, 'winfo_name') and grandchild.winfo_name() == "save_dirs_listbox":
                                    listbox = grandchild
                                    break
        except Exception as e:
            self.logger.warning(f"Could not find save directories listbox: {e}")
        
        if listbox:
            selected = listbox.curselection()
            if selected:
                confirm = messagebox.askyesno(
                    "Confirm Removal",
                    f"Are you sure you want to remove {len(selected)} selected directory(ies)?",
                )
                if not confirm:
                    return
                
                try:
                    count = len(selected)
                    self.status_bar_manager.set_status(f"Removing {count} save director{'y' if count == 1 else 'ies'}...")
                    
                    # Get paths to remove
                    paths_to_remove = []
                    for index in reversed(selected):
                        path = listbox.get(index)
                        paths_to_remove.append(path)
                        listbox.delete(index)
                    
                    # Use SaveManager to remove directories
                    self.save_manager.remove_save_directories(paths_to_remove)
                    
                    # Refresh config
                    self.config = self.config_manager.get_config()
                    
                    # Show success message
                    self.status_bar_manager.show_info(f"Removed {count} save director{'y' if count == 1 else 'ies'}")
                    self.logger.info(f"Removed {count} save directories")
                    
                except Exception as e:
                    log_error("app", e, "remove_save_dir", {"count": len(selected)})
                    self.status_bar_manager.show_error(f"Failed to remove save directories: {str(e)}")
            else:
                self.status_bar_manager.show_warning("No save directories selected")
        return

    def override_save_dir_handler(self, listbox: tk.Listbox):
        # get target save dir
        selected = listbox.curselection()
        assert len(selected) == 1
        target = pathlib.Path(listbox.get(selected[0]))
        
        # Use SaveManager to validate directory
        if not self.save_manager.validate_save_directory(str(target)):
            self.status_bar_manager.show_error(f"{target} is not a directory")
            messagebox.showerror("Invalid Path", f"{target} is not a directory.")
            listbox.selection_clear(0, tk.END)
            return
        
        # override
        if self.ui_manager.selected_frame:
            frame, game = self.ui_manager.selected_frame
            game = self.game_manager.validate_game_directory(game=game)
            
            if game["valid"]:
                try:
                    # Get current target before override
                    current_target = self.game_manager.get_game_symlink_target(game=game)
                    
                    # Update status
                    self.status_bar_manager.set_status(f"Overriding {game['name']}...")
                    
                    # Perform override
                    success = self.game_manager.rebind_symlink(
                        link=pathlib.Path(game["save"]), 
                        target=pathlib.Path(target)
                    )
                    
                    if success:
                        # Record operation for undo/redo
                        operation = LinkOperation(
                            operation_id=str(uuid.uuid4()),
                            timestamp=datetime.now().isoformat(),
                            operation_type="override",
                            game_id=game["path"],
                            game_name=game["name"],
                            previous_target=current_target,
                            new_target=str(target)
                        )
                        self.operation_history_manager.record_operation(operation)
                        
                        # Update UI
                        save_dir_path = frame.nametowidget("save_dir_path")
                        if save_dir_path:
                            save_dir_path.config(text=str(target))
                        
                        # Update status bar
                        self.status_bar_manager.show_operation_result(
                            "Override", game["name"], str(target), success=True
                        )
                        self._update_undo_redo_counts()
                        
                        # Clear listbox selection
                        listbox.selection_clear(0, tk.END)
                        
                        self.logger.info(f"Override successful for {game['name']} → {target}")
                    else:
                        self.status_bar_manager.show_error(f"Failed to override {game['name']}")
                        
                except Exception as e:
                    log_error("app", e, "override_save_dir", {"game": game["name"], "target": str(target)})
                    self.status_bar_manager.show_error(f"Override failed: {str(e)}")
        else:
            self.status_bar_manager.show_warning("No game selected")
            messagebox.showinfo("No Game Selected", "Please select a game first.")
        return


def main():
    """Main entry point for the Sacred Save Game Manager application."""
    root = tk.Tk()
    root.minsize(800, 700)
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
