#!/usr/bin/env python3
"""
Fresh install script for ROI Bounding Box Tool
Clears environment and reinstalls dependencies from scratch
"""

import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a shell command and report results"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✓ {description} - OK")
            return True
        else:
            print(f"✗ {description} - FAILED")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"✗ {description} - ERROR: {e}")
        return False


def main():
    print("=" * 70)
    print("ROI Bounding Box Tool - Fresh Install")
    print("=" * 70)

    # Step 1: Check Python
    print("\nStep 1: Checking Python version...")
    try:
        py_version = sys.version
        print(f"✓ Python {py_version.split()[0]}")
    except Exception as e:
        print(f"✗ Failed to get Python version: {e}")
        sys.exit(1)

    # Step 2: Upgrade pip
    if not run_command(
        f"{sys.executable} -m pip install --upgrade pip setuptools wheel",
        "Step 2: Upgrading pip, setuptools, wheel"
    ):
        print("WARNING: Failed to upgrade pip (continuing anyway)")

    # Step 3: Clear pip cache
    if not run_command(
        f"{sys.executable} -m pip cache purge",
        "Step 3: Clearing pip cache"
    ):
        print("WARNING: Could not clear pip cache (non-critical)")

    # Step 4: Uninstall old versions
    print("\nStep 4: Uninstalling old versions...")
    packages_to_remove = ["opencv-python", "cv2", "numpy", "Pillow", "PyYAML", "pyperclip"]
    for pkg in packages_to_remove:
        subprocess.run(
            f"{sys.executable} -m pip uninstall -y {pkg}",
            capture_output=True,
            shell=True
        )
    print("✓ Old packages uninstalled")

    # Step 5: Install fresh
    if not run_command(
        f"{sys.executable} -m pip install --no-cache-dir -r requirements.txt",
        "Step 5: Installing fresh dependencies"
    ):
        print("✗ Failed to install dependencies")
        sys.exit(1)

    # Step 6: Verify imports
    print("\nStep 6: Verifying all imports...")
    packages = {
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'PIL': 'Pillow',
        'yaml': 'PyYAML',
        'pyperclip': 'pyperclip',
    }

    all_ok = True
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError as e:
            print(f"  ✗ {name}: {e}")
            all_ok = False

    if not all_ok:
        print("\n✗ Some packages failed to import!")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("SUCCESS! Fresh installation complete.")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Edit roi_config.yaml and set your video_path")
    print("  2. Run: python roi_tool.py")
    print("  3. Or:  python roi_tool.py --video path/to/video.mp4")
    print()


if __name__ == "__main__":
    main()
