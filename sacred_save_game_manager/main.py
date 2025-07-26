import pathlib
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import json
import os

from .controllers import ConfigManager, GameManager, SaveManager, UIManager
from .models import GameData


class App:
    """Main application coordinator."""
    
    def __init__(self, root):
        self.root = root
        
        # Initialize managers
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
        self.ui_manager.setup_main_window()
        self.ui_manager.populate_games()
        
        # Initialize save directories listbox
        listbox = self.root.nametowidget("!frame.!frame2.save_dirs_listbox")
        if listbox:
            self.ui_manager.refresh_listbox(listbox)

    # === Game Tab Handlers ===

    def add_game_handler(self) -> None:
        selected_path = filedialog.askdirectory(title="Select Sacred Gold installation")
        if selected_path:
            # Use GameManager for validation
            if not self.game_manager.is_valid_game_directory(selected_path):
                if os.path.islink(selected_path):
                    messagebox.showerror(
                        "Invalid Directory", "Symbolic links are not supported."
                    )
                elif not os.path.isdir(selected_path):
                    messagebox.showerror(
                        "Invalid Directory", "Selected path is not a directory."
                    )
                else:
                    messagebox.showerror(
                        "Invalid Directory", "Sacred.exe not found in selected directory."
                    )
                return
            
            # Check if game already exists
            config = self.config_manager.get_config()
            for game in config["games"]:
                if game["path"] == selected_path:
                    messagebox.showinfo(
                        "Game already added",
                        f"This directory has already been added as '{game['name']}'.",
                    )
                    return

            name = simpledialog.askstring(
                "Name", "Provide a name for this Sacred Gold installation:"
            )
            if not name:
                name = "Sacred Gold"
            
            game = {"name": name, "path": selected_path}
            game = self.game_manager.validate_game_directory(game=game)
            if game["valid"]:
                self.config_manager.add_game(game)
                # Refresh the UI
                self.ui_manager.populate_games()
        return

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


if __name__ == "__main__":
    root = tk.Tk()
    root.minsize(800, 700)
    app = App(root)
    root.mainloop()
