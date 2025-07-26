import pathlib
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import json
import os
import sys

from .controllers import ConfigManager, GameManager, SaveManager, UIManager
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
            
            # Wire up event handlers
            self.ui_manager.add_game_handler = self.add_game_handler
            self.ui_manager.remove_game_handler = self.remove_game_handler
            self.ui_manager.reset_game_handler = self.reset_game_handler
            self.ui_manager.add_save_dir_handler = self.add_save_dir_handler
            self.ui_manager.remove_save_dir_handler = self.remove_save_dir_handler
            self.ui_manager.override_save_dir_handler = self.override_save_dir_handler
            
            # Initialize UI
            self.logger.info("Setting up user interface...")
            self.ui_manager.setup_main_window()
            self.ui_manager.populate_games()
            
            # Initialize save directories listbox
            try:
                listbox = self.root.nametowidget("!frame.!frame2.save_dirs_listbox")
                if listbox:
                    self.ui_manager.refresh_listbox(listbox)
            except tk.TclError:
                self.logger.warning("Could not find save directories listbox widget")
            
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

    # === Game Tab Handlers ===

    def add_game_handler(self) -> None:
        try:
            log_user_action("add_game_initiated")
            selected_path = filedialog.askdirectory(title="Select Sacred Gold installation")
            
            if not selected_path:
                self.logger.debug("User cancelled game directory selection")
                return
            
            self.logger.info(f"User selected game directory: {selected_path}")
            
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
            game = {"name": name, "path": validated_path}
            try:
                game = self.game_manager.validate_game_directory(game=game)
                if game["valid"]:
                    self.config_manager.add_game(game)
                    self.ui_manager.populate_games()
                    log_user_action("add_game_success", {"name": name, "path": validated_path})
                    self.logger.info(f"Game added successfully: {name} at {validated_path}")
                else:
                    self.logger.error(f"Game validation failed for: {validated_path}")
                    messagebox.showerror("Game Validation Failed", "The selected directory could not be set up as a valid game directory.")
            except (GameDirectoryError, FileOperationError) as e:
                log_error("app", e, "add_game_validation", {"name": name, "path": validated_path})
                messagebox.showerror("Game Setup Error", f"Failed to set up game directory: {str(e)}")
                return
            except Exception as e:
                log_error("app", e, "add_game_unexpected", {"name": name, "path": validated_path})
                messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {str(e)}")
                return
                
        except Exception as e:
            log_error("app", e, "add_game_handler")
            messagebox.showerror("Error", f"Failed to add game: {str(e)}")

    def reset_game_handler(self):
        if self.ui_manager.selected_frame:
            frame, game = self.ui_manager.selected_frame
            game = self.game_manager.validate_game_directory(game=game)
            if game["valid"] and self.game_manager.rebind_symlink(
                link=pathlib.Path(game["save"]),
                target=pathlib.Path(game["save_backup"]),
            ):
                save_dir_path = frame.nametowidget("save_dir_path")
                if save_dir_path:
                    save_dir_path.config(text="default")
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
                self.ui_manager.selected_frame = None
                frame.destroy()
                self.config_manager.remove_game(game)
                # Refresh the UI
                self.ui_manager.populate_games()
        else:
            messagebox.showinfo(
                "No Game Selected", "Please select a Sacred Gold entry to remove."
            )
        return

    # === Save Dir Tab Handlers ===

    def add_save_dir_handler(self):
        selected_path = filedialog.askdirectory(title="Select save archive.")
        listbox = self.root.nametowidget("!frame.!frame2.save_dirs_listbox")
        if selected_path and listbox:
            add_recursively = messagebox.askyesno(
                "Add recursively",
                f"Do you want to recursively add every terminal directories contained in {selected_path}?",
            )
            
            # Use SaveManager to add directories
            new_dirs = self.save_manager.add_save_directory(selected_path, recursive=add_recursively)
            
            # Update UI
            for new_dir in new_dirs:
                listbox.insert(tk.END, new_dir)
            
            # Refresh config
            self.config = self.config_manager.get_config()
        return

    def remove_save_dir_handler(self):
        listbox = self.root.nametowidget("!frame.!frame2.save_dirs_listbox")
        if listbox:
            selected = listbox.curselection()
            if selected:
                confirm = messagebox.askyesno(
                    "Confirm Removal",
                    f"Are you sure you want to remove {len(selected)} selected directory(ies)?",
                )
                if not confirm:
                    return
                
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
        return

    def override_save_dir_handler(self, listbox: tk.Listbox):
        # get target save dir
        selected = listbox.curselection()
        assert len(selected) == 1
        target = pathlib.Path(listbox.get(selected[0]))
        
        # Use SaveManager to validate directory
        if not self.save_manager.validate_save_directory(str(target)):
            messagebox.showerror("Invalid Path", f"{target} is not a directory.")
            listbox.select_clear()
            return
        
        # override
        if self.ui_manager.selected_frame:
            frame, game = self.ui_manager.selected_frame
            game = self.game_manager.validate_game_directory(game=game)
            if game["valid"] and self.game_manager.rebind_symlink(
                link=pathlib.Path(game["save"]), target=pathlib.Path(target)
            ):
                save_dir_path = frame.nametowidget("save_dir_path")
                if save_dir_path:
                    save_dir_path.config(text=str(target))
        else:
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
