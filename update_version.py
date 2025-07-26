#!/usr/bin/env python3
"""
Version update utility for Sacred Save Game Manager.

This script helps update the version number across the project.
Usage: python update_version.py <new_version>
Example: python update_version.py 1.1.0
"""

import sys
import re
from pathlib import Path


def update_version(new_version: str) -> None:
    """Update version in __init__.py and provide guidance for other files."""
    
    # Validate version format (basic semantic versioning)
    if not re.match(r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+)?$', new_version):
        print(f"Error: Invalid version format '{new_version}'")
        print("Expected format: X.Y.Z or X.Y.Z-suffix (e.g., 1.0.0, 1.0.0-beta)")
        sys.exit(1)
    
    # Update __init__.py
    init_file = Path("sacred_save_game_manager/__init__.py")
    if not init_file.exists():
        print(f"Error: {init_file} not found")
        sys.exit(1)
    
    # Read current content
    content = init_file.read_text(encoding='utf-8')
    
    # Find current version
    version_match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
    if not version_match:
        print("Error: Could not find __version__ in __init__.py")
        sys.exit(1)
    
    current_version = version_match.group(1)
    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")
    
    # Update version
    new_content = re.sub(
        r'__version__ = ["\'][^"\']+["\']',
        f'__version__ = "{new_version}"',
        content
    )
    
    # Write updated content
    init_file.write_text(new_content, encoding='utf-8')
    print(f"✅ Updated {init_file}")
    
    # Provide guidance for other files
    print("\n📝 Manual updates needed:")
    print("1. Update CHANGELOG.md:")
    print(f"   - Add new section: ## [{new_version}] - {get_current_date()}")
    print("   - Document changes in this release")
    print("\n2. Consider updating README.md if version is mentioned")
    print("\n3. After testing, create a git tag:")
    print(f"   git tag -a v{new_version} -m 'Release v{new_version}'")
    print("   git push origin v{new_version}")
    print("\n4. Build and publish:")
    print("   python -m build")
    print("   twine upload dist/*")
    
    print(f"\n🎉 Version updated from {current_version} to {new_version}")


def get_current_date() -> str:
    """Get current date in YYYY-MM-DD format."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <new_version>")
        print("Example: python update_version.py 1.1.0")
        sys.exit(1)
    
    new_version = sys.argv[1]
    update_version(new_version)


if __name__ == "__main__":
    main()
