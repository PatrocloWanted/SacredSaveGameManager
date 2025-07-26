"""
Basic tests for Sacred Save Game Manager.

These tests verify that the package can be imported and basic functionality works.
"""

import pytest
import sys
from pathlib import Path

# Add the package to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_package_import():
    """Test that the main package can be imported."""
    import sacred_save_game_manager
    assert sacred_save_game_manager.__version__ == "1.0.0"
    assert sacred_save_game_manager.__author__ == "Patroclo Picchiaduro"

def test_main_function_exists():
    """Test that the main function exists and is callable."""
    from sacred_save_game_manager import main
    assert callable(main)

def test_utils_import():
    """Test that utility modules can be imported."""
    from sacred_save_game_manager.utils import get_logger, ValidationError
    from sacred_save_game_manager.utils.platform_utils import get_platform_info
    from sacred_save_game_manager.utils.cross_platform_symlinks import CrossPlatformSymlinkManager
    
    # Test basic functionality
    logger = get_logger("test")
    assert logger is not None
    
    platform_info = get_platform_info()
    assert hasattr(platform_info, 'system')
    assert hasattr(platform_info, 'can_create_symlinks')
    
    symlink_manager = CrossPlatformSymlinkManager()
    assert symlink_manager is not None

def test_controllers_import():
    """Test that controller modules can be imported."""
    from sacred_save_game_manager.controllers import ConfigManager, GameManager
    
    # Test basic instantiation (without actual file operations)
    config_manager = ConfigManager()
    assert config_manager is not None
    
    game_manager = GameManager(config_manager)
    assert game_manager is not None

def test_validators():
    """Test basic validator functionality."""
    from sacred_save_game_manager.utils.validators import sanitize_name, ValidationError
    
    # Test name sanitization
    assert sanitize_name("Valid Name") == "Valid Name"
    assert sanitize_name("Name/With\\Invalid:Chars") == "NameWithInvalidChars"
    
    # Test validation error
    with pytest.raises(ValidationError):
        sanitize_name("")  # Empty name should raise ValidationError

def test_exceptions():
    """Test that custom exceptions can be imported and used."""
    from sacred_save_game_manager.utils.exceptions import (
        ValidationError, ConfigurationError, GameDirectoryError, FileOperationError
    )
    
    # Test that exceptions can be raised and caught
    with pytest.raises(ValidationError):
        raise ValidationError("Test validation error")
    
    with pytest.raises(ConfigurationError):
        raise ConfigurationError("Test configuration error")
    
    with pytest.raises(GameDirectoryError):
        raise GameDirectoryError("Test game directory error")
    
    with pytest.raises(FileOperationError):
        raise FileOperationError("Test file operation error")

if __name__ == "__main__":
    pytest.main([__file__])
