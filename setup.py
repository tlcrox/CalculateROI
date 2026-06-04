#!/usr/bin/env python3
"""
Setup script for ROI Bounding Box Tool
Installs dependencies and verifies the environment
"""

import subprocess
import sys
from pathlib import Path


def install_requirements():
    """Install Python dependencies from requirements.txt"""
    print("Installing dependencies...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Dependencies installed successfully")
            return True
        else:
            print("✗ Failed to install dependencies:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Error during installation: {e}")
        return False


def verify_imports():
    """Verify all required packages can be imported"""
    print("\nVerifying imports...")
    packages = {
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'yaml': 'PyYAML',
        'pyperclip': 'pyperclip',
        'tkinter': 'tkinter (built-in)'
    }

    all_ok = True
    for module, package in packages.items():
        try:
            __import__(module)
            print(f"✓ {module} ({package})")
        except ImportError:
            print(f"✗ {module} ({package}) - NOT FOUND")
            all_ok = False

    return all_ok


def check_files():
    """Verify required files exist"""
    print("\nVerifying project files...")
    required_files = [
        'roi_tool.py',
        'roi_config.yaml',
        'requirements.txt',
        'README.md'
    ]

    all_ok = True
    for filename in required_files:
        if Path(filename).exists():
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename} - NOT FOUND")
            all_ok = False

    return all_ok


def main():
    print("=" * 60)
    print("ROI Bounding Box Tool - Setup")
    print("=" * 60)

    # Check files
    if not check_files():
        print("\n✗ Some project files are missing!")
        sys.exit(1)

    # Install dependencies
    if not install_requirements():
        print("\n✗ Failed to install dependencies!")
        sys.exit(1)

    # Verify imports
    if not verify_imports():
        print("\n✗ Some packages could not be imported!")
        print("Try running: pip install --upgrade -r requirements.txt")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ Setup complete! You're ready to run roi_tool.py")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Edit roi_config.yaml and set your video_path")
    print("  2. Run: python roi_tool.py")
    print("  3. Or: python roi_tool.py --video /path/to/video.mp4")
    print("\nFor more info, see README.md")


if __name__ == "__main__":
    main()
