"""
Sacred Save Game Manager

A cross-platform save game manager for Sacred Gold that uses symbolic links
to manage multiple save directories efficiently.
"""

__version__ = "1.0.1"
__author__ = "Patroclo Picchiaduro"
__email__ = "patroclo.wanted@gmail.com"
__description__ = "A cross-platform save game manager for Sacred Gold"

# Make main function available at package level
from .main import main

__all__ = ["main", "__version__", "__author__", "__email__", "__description__"]
