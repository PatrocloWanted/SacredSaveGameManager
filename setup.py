from setuptools import setup, find_packages
import os

# Read version from package
def get_version():
    """Get version from package __init__.py"""
    version_file = os.path.join(os.path.dirname(__file__), 'sacred_save_game_manager', '__init__.py')
    with open(version_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return "1.0.0"

# Read long description
def get_long_description():
    """Get long description from README.md"""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "A cross-platform save game manager for Sacred Gold"

setup(
    name="sacred-save-game-manager",
    version=get_version(),
    author="Patroclo Picchiaduro",
    author_email="patroclo.picchiaduro.25@gmail.com",
    description="A cross-platform save game manager for Sacred Gold",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/PatrocloWanted/SacredSaveGameManager",
    project_urls={
        "Bug Reports": "https://github.com/PatrocloWanted/SacredSaveGameManager/issues",
        "Source": "https://github.com/PatrocloWanted/SacredSaveGameManager",
        "Documentation": "https://github.com/PatrocloWanted/SacredSaveGameManager#readme",
    },
    packages=find_packages(),
    install_requires=[
        # Core dependencies only - removed unused Pygments and rich
    ],
    python_requires=">=3.8",  # Lowered from 3.13 for better compatibility
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment",
        "Topic :: System :: Archiving :: Backup",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Environment :: X11 Applications :: GTK",
        "Natural Language :: English",
    ],
    keywords="sacred gold save game manager symlink backup gaming",
    entry_points={
        "console_scripts": [
            "sacred-save-game-manager=sacred_save_game_manager.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    platforms=["any"],
)
