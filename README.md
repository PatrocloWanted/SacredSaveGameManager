# Sacred Save Game Manager

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/PatrocloWanted/SacredSaveGameManager)

**Sacred Save Game Manager** is a cross-platform Python application built with Tkinter for managing game directories and save files for the game "Sacred Gold". It uses an intelligent symlink-based approach to efficiently manage multiple save directories across different platforms.

## ✨ Features

- **🎮 Game Directory Management**: Add, remove, and reset Sacred Gold game installations
- **💾 Save Directory Management**: Organize and manage multiple save directories
- **🔗 One-Click Linking**: Instantly switch between different save directories
- **🌍 Cross-Platform**: Works on Windows 10/11, macOS, and Linux
- **🔄 Smart Symlinks**: Uses symbolic links, junction points, or directory copying as fallback
- **⚙️ Persistent Configuration**: Settings saved in `config.json`
- **📝 Comprehensive Logging**: Detailed logging for troubleshooting
- **🍷 Wine/Proton Support**: Full compatibility with Wine and Proton on Linux/macOS

## 🚀 Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install sacred-save-game-manager
```

For Windows users (includes additional Windows-specific features):
```bash
pip install sacred-save-game-manager[windows]
```

### Option 2: Install from Source

1. Clone the repository:
```bash
git clone https://github.com/PatrocloWanted/SacredSaveGameManager.git
cd SacredSaveGameManager
```

2. Install the package:
```bash
pip install -e .
```

### Option 3: Development Installation

For developers who want to contribute:

```bash
git clone https://github.com/PatrocloWanted/SacredSaveGameManager.git
cd SacredSaveGameManager
pip install -e .[dev]
```

## 🖥️ Usage

### Running the Application

After installation, you can run the application in several ways:

**Using the installed command:**
```bash
sacred-save-game-manager
```

**Using Python module execution:**
```bash
python -m sacred_save_game_manager
```

**Direct execution (development):**
```bash
python sacred_save_game_manager/main.py
```

### First Time Setup

1. **Add Game Directory**: Click "Add Game" and select your Sacred Gold installation directory
   - Windows: Usually in `C:\Program Files (x86)\Sacred Gold\` or similar
   - Linux/macOS: Your Wine/Proton prefix directory containing `Sacred.exe`

2. **Add Save Directories**: Use the "Save Directories" tab to add folders containing your save games

3. **Link Saves**: Select a game and a save directory, then click to create the link

## 🌐 Cross-Platform Compatibility

### Windows 10/11
- **Symlinks**: Requires Administrator privileges OR Developer Mode enabled
- **Junction Points**: Used as fallback for standard users
- **Directory Copying**: Final fallback method

**To enable Developer Mode on Windows:**
1. Open Settings → Update & Security → For developers
2. Enable "Developer Mode"
3. Restart the application

### macOS
- **Full symlink support** for regular users
- **Wine/Proton detection** for Sacred Gold installations
- **Case-insensitive filesystem** handling

### Linux
- **Native symlink support** (original behavior preserved)
- **Wine/Proton compatibility** for Sacred Gold
- **Case-sensitive filesystem** support

## 📁 Configuration

The application stores its configuration in `config.json` in the application directory. This file contains:

- Game installation paths and names
- Save directory locations
- Application settings and preferences

**Configuration is automatically managed** - no manual editing required.

## 🔧 System Requirements

- **Python**: 3.8 or later
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux
- **Sacred Gold**: Any version (including Wine/Proton installations)
- **Disk Space**: Minimal (application uses symlinks, not copies)

### Platform-Specific Requirements

**Windows:**
- Optional: `pywin32` (automatically installed with `[windows]` extra)
- Administrator privileges OR Developer Mode for symlink support

**Linux:**
- Standard Python installation
- Wine/Proton for Sacred Gold (if not using native version)

**macOS:**
- Python 3.8+ (available via Homebrew: `brew install python`)
- Wine/Proton for Sacred Gold

## 🛠️ Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/PatrocloWanted/SacredSaveGameManager.git
cd SacredSaveGameManager

# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Format code
black sacred_save_game_manager/

# Type checking
mypy sacred_save_game_manager/
```

### Project Structure

```
sacred_save_game_manager/
├── controllers/          # Application logic controllers
├── models/              # Data models and structures
├── utils/               # Utility functions and helpers
├── views/               # UI components (future expansion)
├── main.py             # Main application entry point
└── __init__.py         # Package initialization
```

## 🐛 Troubleshooting

### Common Issues

**"Permission denied" errors on Windows:**
- Enable Developer Mode in Windows Settings
- Or run as Administrator
- Application will automatically use junction points as fallback

**Sacred Gold not detected:**
- Ensure `Sacred.exe` is in the selected directory
- For Wine/Proton: Select the Windows directory containing the executable
- Check that the game directory is not a symlink itself

**Symlinks not working:**
- Check platform-specific requirements above
- Review application logs in the `logs/` directory
- Try the directory copying fallback option

### Getting Help

1. **Check the logs**: Look in the `logs/` directory for detailed error information
2. **GitHub Issues**: Report bugs at [GitHub Issues](https://github.com/PatrocloWanted/SacredSaveGameManager/issues)
3. **Documentation**: See additional docs in the repository

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Guidelines

1. Follow PEP 8 style guidelines
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure cross-platform compatibility

## 🙏 Acknowledgments

- Sacred Gold game by Ascaron Entertainment
- Python community for excellent cross-platform libraries
- Contributors and users who provide feedback and bug reports

## 📊 Project Status

- **Status**: Active Development
- **Version**: 1.0.0
- **Python Support**: 3.8+
- **Platforms**: Windows, macOS, Linux

---

**Note**: This application manages save game directories through symbolic links and does not modify your actual save files. Always backup your save games before making changes.
