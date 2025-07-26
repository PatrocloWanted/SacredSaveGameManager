"""Cross-platform symlink management for Sacred Save Game Manager."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from .logger import get_logger
from .exceptions import SymlinkError, PermissionError, SystemLimitError
from .platform_utils import get_platform_info, get_cross_platform_paths

logger = get_logger("cross_platform_symlinks")


class LinkType:
    """Constants for different link types."""
    SYMLINK = "symlink"
    JUNCTION = "junction"  # Windows junction point
    HARDLINK = "hardlink"
    COPY = "copy"  # Fallback: directory copy with sync


class CrossPlatformSymlinkManager:
    """Manages directory linking across different platforms."""
    
    def __init__(self):
        self.platform_info = get_platform_info()
        self.paths = get_cross_platform_paths()
        self.logger = get_logger("symlink_manager")
        
        # Determine preferred link types by platform
        self.preferred_link_types = self._get_preferred_link_types()
        
        self.logger.info(f"Symlink manager initialized for {self.platform_info.system}")
        self.logger.info(f"Preferred link types: {self.preferred_link_types}")
    
    def _get_preferred_link_types(self) -> list:
        """Get ordered list of preferred link types for the current platform."""
        if self.platform_info.is_windows:
            if self.platform_info.can_create_symlinks():
                return [LinkType.SYMLINK, LinkType.JUNCTION, LinkType.COPY]
            else:
                return [LinkType.JUNCTION, LinkType.COPY]
        else:
            # Unix systems (Linux, macOS)
            return [LinkType.SYMLINK, LinkType.COPY]
    
    def create_directory_link(self, link_path: str, target_path: str, 
                            force: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Create a directory link using the best available method.
        
        Returns:
            Tuple of (success, link_type_used, details)
        """
        link_path_obj = Path(link_path)
        target_path_obj = Path(target_path)
        
        # Validate inputs
        try:
            self._validate_link_creation(link_path_obj, target_path_obj, force)
        except Exception as e:
            return False, None, {"error": str(e), "stage": "validation"}
        
        # Try each link type in order of preference
        last_error = None
        for link_type in self.preferred_link_types:
            try:
                success, details = self._create_link_by_type(
                    link_path_obj, target_path_obj, link_type, force
                )
                if success:
                    self.logger.info(f"Successfully created {link_type} link: {link_path} -> {target_path}")
                    return True, link_type, details
                else:
                    self.logger.debug(f"Failed to create {link_type} link: {details.get('error', 'Unknown error')}")
                    last_error = details.get('error')
            except Exception as e:
                self.logger.debug(f"Exception creating {link_type} link: {str(e)}")
                last_error = str(e)
                continue
        
        # All methods failed
        error_msg = f"Failed to create directory link using any method. Last error: {last_error}"
        self.logger.error(error_msg)
        return False, None, {"error": error_msg, "last_error": last_error}
    
    def _validate_link_creation(self, link_path: Path, target_path: Path, force: bool) -> None:
        """Validate that link creation is possible."""
        # Check target exists and is a directory
        if not target_path.exists():
            raise SymlinkError(f"Target directory does not exist: {target_path}")
        
        if not target_path.is_dir():
            raise SymlinkError(f"Target is not a directory: {target_path}")
        
        # Check if link already exists
        if link_path.exists(follow_symlinks=False):
            if not force:
                raise SymlinkError(f"Link path already exists: {link_path}")
            else:
                # Remove existing link/directory
                self._remove_existing_link(link_path)
        
        # Check parent directory exists and is writable
        parent_dir = link_path.parent
        if not parent_dir.exists():
            raise SymlinkError(f"Parent directory does not exist: {parent_dir}")
        
        if not os.access(parent_dir, os.W_OK):
            raise PermissionError(f"No write permission to parent directory: {parent_dir}")
        
        # Validate path lengths
        self.paths.validate_path_length(str(link_path))
        self.paths.validate_path_length(str(target_path))
    
    def _create_link_by_type(self, link_path: Path, target_path: Path, 
                           link_type: str, force: bool) -> Tuple[bool, Dict[str, Any]]:
        """Create a link using the specified type."""
        if link_type == LinkType.SYMLINK:
            return self._create_symlink(link_path, target_path)
        elif link_type == LinkType.JUNCTION:
            return self._create_junction(link_path, target_path)
        elif link_type == LinkType.COPY:
            return self._create_copy_link(link_path, target_path)
        else:
            return False, {"error": f"Unknown link type: {link_type}"}
    
    def _create_symlink(self, link_path: Path, target_path: Path) -> Tuple[bool, Dict[str, Any]]:
        """Create a symbolic link."""
        try:
            link_path.symlink_to(target_path, target_is_directory=True)
            return True, {"method": "symlink", "link": str(link_path), "target": str(target_path)}
        except OSError as e:
            return False, {"error": f"Symlink creation failed: {str(e)}", "errno": e.errno}
        except Exception as e:
            return False, {"error": f"Unexpected error creating symlink: {str(e)}"}
    
    def _create_junction(self, link_path: Path, target_path: Path) -> Tuple[bool, Dict[str, Any]]:
        """Create a Windows junction point."""
        if not self.platform_info.is_windows:
            return False, {"error": "Junction points are only supported on Windows"}
        
        try:
            # Use mklink command to create junction
            cmd = ["mklink", "/J", str(link_path), str(target_path)]
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.returncode == 0:
                return True, {
                    "method": "junction", 
                    "link": str(link_path), 
                    "target": str(target_path),
                    "output": result.stdout.strip()
                }
            else:
                return False, {
                    "error": f"Junction creation failed: {result.stderr.strip()}",
                    "returncode": result.returncode,
                    "command": " ".join(cmd)
                }
        except Exception as e:
            return False, {"error": f"Exception creating junction: {str(e)}"}
    
    def _create_copy_link(self, link_path: Path, target_path: Path) -> Tuple[bool, Dict[str, Any]]:
        """Create a directory copy as fallback."""
        try:
            # Copy the directory
            shutil.copytree(target_path, link_path, dirs_exist_ok=False)
            
            # Create a marker file to indicate this is a "copy link"
            marker_file = link_path / ".sacred_copy_link"
            with open(marker_file, 'w') as f:
                f.write(f"target={target_path}\n")
                f.write(f"created_by=sacred_save_game_manager\n")
            
            # Make marker file hidden on Windows
            if self.platform_info.is_windows:
                try:
                    import ctypes
                    ctypes.windll.kernel32.SetFileAttributesW(str(marker_file), 2)  # FILE_ATTRIBUTE_HIDDEN
                except Exception:
                    pass  # Not critical if hiding fails
            
            return True, {
                "method": "copy", 
                "link": str(link_path), 
                "target": str(target_path),
                "marker_file": str(marker_file)
            }
        except Exception as e:
            return False, {"error": f"Directory copy failed: {str(e)}"}
    
    def _remove_existing_link(self, link_path: Path) -> None:
        """Remove existing link or directory."""
        try:
            if link_path.is_symlink():
                link_path.unlink()
            elif link_path.is_dir():
                # Check if it's a junction point on Windows
                if self.platform_info.is_windows and self._is_junction(link_path):
                    # Use rmdir for junction points
                    subprocess.run(["rmdir", str(link_path)], shell=True, check=True)
                else:
                    # Regular directory or copy link
                    shutil.rmtree(link_path)
            else:
                link_path.unlink()
        except Exception as e:
            raise SymlinkError(f"Failed to remove existing link: {str(e)}")
    
    def _is_junction(self, path: Path) -> bool:
        """Check if a path is a Windows junction point."""
        if not self.platform_info.is_windows:
            return False
        
        try:
            # Use dir command to check for junction
            result = subprocess.run(
                ["dir", str(path.parent), "/AL"],
                shell=True,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                # Look for junction indicator in output
                return "<JUNCTION>" in result.stdout and path.name in result.stdout
            
            return False
        except Exception:
            return False
    
    def get_link_info(self, link_path: str) -> Dict[str, Any]:
        """Get information about an existing link."""
        link_path_obj = Path(link_path)
        
        if not link_path_obj.exists(follow_symlinks=False):
            return {"exists": False, "type": None}
        
        info = {"exists": True, "path": str(link_path_obj)}
        
        try:
            if link_path_obj.is_symlink():
                info["type"] = LinkType.SYMLINK
                info["target"] = str(link_path_obj.resolve())
                info["is_valid"] = link_path_obj.resolve().exists()
            elif self.platform_info.is_windows and self._is_junction(link_path_obj):
                info["type"] = LinkType.JUNCTION
                info["target"] = str(link_path_obj.resolve())
                info["is_valid"] = link_path_obj.resolve().exists()
            elif link_path_obj.is_dir():
                # Check if it's a copy link
                marker_file = link_path_obj / ".sacred_copy_link"
                if marker_file.exists():
                    info["type"] = LinkType.COPY
                    try:
                        with open(marker_file, 'r') as f:
                            content = f.read()
                            for line in content.split('\n'):
                                if line.startswith('target='):
                                    info["target"] = line.split('=', 1)[1]
                                    break
                        info["is_valid"] = Path(info.get("target", "")).exists()
                    except Exception:
                        info["target"] = "unknown"
                        info["is_valid"] = False
                else:
                    info["type"] = "directory"
                    info["is_valid"] = True
            else:
                info["type"] = "file"
                info["is_valid"] = True
                
        except Exception as e:
            info["error"] = str(e)
            info["is_valid"] = False
        
        return info
    
    def rebind_link(self, link_path: str, new_target: str, force: bool = True) -> Tuple[bool, str, Dict[str, Any]]:
        """Rebind an existing link to a new target."""
        self.logger.info(f"Rebinding link: {link_path} -> {new_target}")
        
        # Remove existing link
        link_path_obj = Path(link_path)
        if link_path_obj.exists(follow_symlinks=False):
            try:
                self._remove_existing_link(link_path_obj)
            except Exception as e:
                return False, None, {"error": f"Failed to remove existing link: {str(e)}"}
        
        # Create new link
        return self.create_directory_link(link_path, new_target, force=force)
    
    def sync_copy_link(self, link_path: str) -> bool:
        """Synchronize a copy link with its target (for copy-type links only)."""
        link_info = self.get_link_info(link_path)
        
        if not link_info.get("exists") or link_info.get("type") != LinkType.COPY:
            return False
        
        target = link_info.get("target")
        if not target or not Path(target).exists():
            return False
        
        try:
            link_path_obj = Path(link_path)
            
            # Remove existing copy (except marker file)
            marker_file = link_path_obj / ".sacred_copy_link"
            marker_content = None
            if marker_file.exists():
                with open(marker_file, 'r') as f:
                    marker_content = f.read()
            
            # Remove and recreate
            shutil.rmtree(link_path_obj)
            shutil.copytree(target, link_path_obj)
            
            # Restore marker file
            if marker_content:
                with open(marker_file, 'w') as f:
                    f.write(marker_content)
            
            self.logger.info(f"Synchronized copy link: {link_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to sync copy link {link_path}: {str(e)}")
            return False


# Global instance
cross_platform_symlink_manager = CrossPlatformSymlinkManager()


def get_symlink_manager() -> CrossPlatformSymlinkManager:
    """Get the global symlink manager instance."""
    return cross_platform_symlink_manager
