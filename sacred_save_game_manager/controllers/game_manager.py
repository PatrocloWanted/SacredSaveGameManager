"""Game management for Sacred Save Game Manager."""

import os
import pathlib
from tkinter import messagebox
from typing import Dict, Any, Optional
from .config_manager import ConfigManager
from ..models import GameData


class GameManager:
    """Handles game directory validation and symlink operations."""
    
    SAVE_DIR = "save"
    BACKUP_SAVE_DIR = "save_backup"
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
    
    def validate_game_directory(self, game: GameData) -> GameData:
        """Validate and setup game directory with proper save/backup structure."""
        game["valid"] = False
        save_dir = self._match_target_in_directory(
            directory=game["path"], target=self.SAVE_DIR, case_insensitive=True
        ) or pathlib.Path(game["path"], self.SAVE_DIR)
        backup_save_dir = self._match_target_in_directory(
            directory=game["path"], target=self.BACKUP_SAVE_DIR, case_insensitive=True
        ) or pathlib.Path(game["path"], self.BACKUP_SAVE_DIR)
        
        # The save directory either does not exist or it is a directory/symlink to a directory.
        if save_dir.exists(follow_symlinks=False):
            if not save_dir.is_symlink() and not save_dir.is_dir(follow_symlinks=True):
                messagebox.showerror(
                    "Unexpected Error", f"{save_dir} is not a directory."
                )
                return game
        
        # The backup save directory either does not exist or it is a directory.
        if backup_save_dir.exists(follow_symlinks=False) and not backup_save_dir.is_dir(
            follow_symlinks=False
        ):
            messagebox.showerror(
                "Unexpected Error", f"{backup_save_dir} is not a directory."
            )
            return game
        
        # Fail when there already is a backup save directory and the save directory is a non-empty directory.
        if (
            backup_save_dir.exists(follow_symlinks=False)
            and save_dir.exists(follow_symlinks=False)
            and save_dir.is_dir(follow_symlinks=False)
        ):
            if len(list(save_dir.iterdir())) > 0:
                messagebox.showerror("Unexpected Error", f"{save_dir} is not empty.")
                return game
            else:
                # Remove the save directory, so that it can be replaced by a symlink.
                save_dir.rmdir()
        
        # Create the backup save directory when it does not exist. Transfer content of save directory when it is not a symlink.
        if not backup_save_dir.exists(follow_symlinks=False):
            if not save_dir.exists(follow_symlinks=False) or save_dir.is_symlink():
                backup_save_dir.mkdir(parents=False, exist_ok=True)
            else:
                save_dir.replace(target=backup_save_dir)
        
        # Create the save directory symlink when it does not exist.
        if not save_dir.exists(follow_symlinks=False):
            save_dir.symlink_to(target=backup_save_dir, target_is_directory=True)
        
        # Update & return
        game["save"] = str(save_dir)
        game["save_backup"] = str(backup_save_dir)
        game["valid"] = True
        return game
    
    def _match_target_in_directory(
        self, directory: str, target: str, case_insensitive: bool = True
    ) -> Optional[pathlib.Path]:
        """Find a target file/directory in the given directory."""
        target = target.casefold() if case_insensitive else target
        for item in pathlib.Path(directory).rglob("*"):
            if (case_insensitive and item.name.casefold() == target) or (
                not case_insensitive and item.name == target
            ):
                return item
        return None
    
    def rebind_symlink(self, link: pathlib.Path, target: pathlib.Path) -> bool:
        """Rebind a symlink to point to a new target."""
        assert target.exists(follow_symlinks=False) and target.is_dir()
        try:
            if link.exists(follow_symlinks=False):
                assert link.is_symlink()
                link.unlink(missing_ok=True)
            link.symlink_to(target=target, target_is_directory=True)
            return True
        except OSError as e:
            messagebox.showerror("Error", f"Failed to rebind symlink: {e}")
        return False
    
    def get_game_symlink_target(self, game: GameData) -> str:
        """Get the target path of the game's save symlink."""
        game = self.validate_game_directory(game=game)
        if game["valid"]:
            target_path = pathlib.Path(game["save"]).resolve()
            if target_path == pathlib.Path(game["save_backup"]):
                return "default"
            else:
                return str(target_path)
        else:
            return "invalid"
    
    def is_valid_game_directory(self, path: str) -> bool:
        """Check if a directory is a valid Sacred Gold installation."""
        if os.path.islink(path):
            return False
        if not os.path.isdir(path):
            return False
        if not os.path.isfile(os.path.join(path, "Sacred.exe")):
            return False
        return True
    
    def validate_all_games(self) -> None:
        """Validate all games in configuration and update them."""
        config = self.config_manager.get_config()
        validated_games = [
            self.validate_game_directory(game=game) for game in config["games"]
        ]
        self.config_manager.update_games(validated_games)
