# Changelog

All notable changes to the Sacred Save Game Manager project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-07-26

### Added
- **Cross-Platform Compatibility**: Full support for Windows 10/11, macOS, and Linux
- **Intelligent Symlink Management**: Automatic fallback from symlinks → junction points → directory copying
- **Platform Detection**: Comprehensive platform and capability detection
- **Enhanced Error Handling**: Robust error handling with detailed logging and user-friendly messages
- **Wine/Proton Support**: Full compatibility with Wine and Proton installations on Linux/macOS
- **Comprehensive Logging**: Detailed application logging with rotation and structured output
- **Input Validation**: Enhanced validation for paths, names, and system requirements
- **Modern Packaging**: Updated to modern Python packaging standards with pyproject.toml
- **Development Tools**: Added support for pytest, black, mypy, and other development tools

### Changed
- **Python Version Support**: Lowered minimum requirement from Python 3.13 to Python 3.8 for better compatibility
- **Entry Points**: Fixed console script entry point for proper installation
- **Dependencies**: Removed unused dependencies (Pygments, rich) and added platform-specific optional dependencies
- **Project Structure**: Reorganized code into proper MVC architecture with controllers, models, utils, and views
- **Configuration Management**: Enhanced configuration handling with atomic writes and backup support
- **Game Detection**: Updated to correctly detect Sacred.exe across all platforms (Wine/Proton aware)

### Fixed
- **Entry Point Bug**: Fixed broken console script entry point in setup.py
- **Module Execution**: Added proper `__main__.py` for `python -m sacred_save_game_manager` execution
- **Cross-Platform Paths**: Fixed path handling issues across different operating systems
- **Case Sensitivity**: Proper handling of case-sensitive vs case-insensitive filesystems
- **Windows Compatibility**: Added Windows junction point support and Developer Mode detection
- **Package Structure**: Fixed package imports and module organization

### Technical Improvements
- **Platform Utils**: Added comprehensive platform detection and utilities (`utils/platform_utils.py`)
- **Cross-Platform Symlinks**: Created advanced symlink management system (`utils/cross_platform_symlinks.py`)
- **Exception Hierarchy**: Implemented custom exception classes for better error handling
- **Validators**: Enhanced input validation with security and platform-specific checks
- **Logging System**: Centralized logging with structured output and rotation
- **Build System**: Modern pyproject.toml configuration with proper metadata
- **Distribution**: Added MANIFEST.in and proper package data inclusion

### Documentation
- **README**: Comprehensive installation and usage guide with platform-specific instructions
- **Cross-Platform Guide**: Detailed documentation of cross-platform compatibility improvements
- **Error Handling Guide**: Documentation of enhanced error handling and logging
- **Development Setup**: Clear instructions for development environment setup

### Security
- **Path Validation**: Enhanced path validation to prevent directory traversal attacks
- **Input Sanitization**: Proper sanitization of user input for file names and paths
- **Permission Checks**: Added permission validation before file operations

## [Unreleased]

### Planned Features
- **GUI Improvements**: Enhanced user interface with better visual design
- **Testing Suite**: Comprehensive unit and integration tests
- **CI/CD Pipeline**: Automated testing and deployment
- **Standalone Executables**: PyInstaller-based standalone distributions
- **Configuration Migration**: Support for configuration format upgrades
- **Backup/Restore**: Built-in backup and restore functionality for save games

---

## Version History

- **1.0.0** (2025-07-26): Initial release with cross-platform compatibility
- **0.x.x** (Pre-release): Development versions (not publicly released)

## Migration Guide

### From Development Versions to 1.0.0

If you were using a development version of Sacred Save Game Manager:

1. **Backup your configuration**: Copy your `config.json` file to a safe location
2. **Uninstall old version**: `pip uninstall sacred-save-game-manager`
3. **Install new version**: `pip install sacred-save-game-manager`
4. **Restore configuration**: The new version should automatically detect and use your existing configuration

### Breaking Changes

- **Python Version**: Minimum Python version changed from 3.13 to 3.8 (this is actually more compatible)
- **Entry Point**: Console script name remains the same but internal structure changed
- **Dependencies**: Removed unused dependencies - no action needed for users

## Support

For questions, bug reports, or feature requests:

- **GitHub Issues**: https://github.com/PatrocloWanted/SacredSaveGameManager/issues
- **Documentation**: See README.md and project documentation
- **Logs**: Check the `logs/` directory for detailed error information
