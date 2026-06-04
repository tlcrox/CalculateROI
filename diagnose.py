#!/usr/bin/env python3
"""
Diagnostic script for ROI Bounding Box Tool
Helps identify environment and dependency issues
"""

import sys
import subprocess
from pathlib import Path


def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def check_python():
    """Check Python version and location"""
    print_section("Python Environment")
    print(f"Executable: {sys.executable}")
    print(f"Version: {sys.version}")
    print(f"Path: {sys.prefix}")


def check_pip():
    """Check pip version"""
    print_section("Pip Information")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True
    )
    print(result.stdout)


def check_packages():
    """Check installed packages"""
    print_section("Installed Packages")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list"],
        capture_output=True,
        text=True
    )

    # Filter to relevant packages
    relevant = ['opencv', 'numpy', 'Pillow', 'PyYAML', 'pyperclip']
    lines = result.stdout.split('\n')

    found = False
    for line in lines:
        for pkg in relevant:
            if pkg.lower() in line.lower():
                print(line)
                found = True

    if not found:
        print("No relevant packages found!")


def check_imports():
    """Try to import each package and report detailed errors"""
    print_section("Import Testing")

    packages = {
        'numpy': 'NumPy',
        'cv2': 'OpenCV',
        'PIL': 'Pillow',
        'yaml': 'PyYAML',
        'pyperclip': 'pyperclip',
    }

    for module, name in packages.items():
        try:
            mod = __import__(module)
            version = getattr(mod, '__version__', 'unknown')
            print(f"✓ {name:15} - OK (v{version})")
        except ImportError as e:
            print(f"✗ {name:15} - FAILED")
            print(f"    Error: {e}")
        except Exception as e:
            print(f"✗ {name:15} - ERROR")
            print(f"    Error: {e}")


def check_specific_issue():
    """Check for the specific numpy.core.multiarray issue"""
    print_section("NumPy/OpenCV Compatibility Check")

    try:
        import numpy
        print(f"✓ NumPy imported: v{numpy.__version__}")
        print(f"  Location: {numpy.__file__}")
    except Exception as e:
        print(f"✗ Failed to import NumPy: {e}")
        return

    try:
        import cv2
        print(f"✓ OpenCV imported: v{cv2.__version__}")
        print(f"  Location: {cv2.__file__}")

        # Try to actually use cv2
        import numpy as np
        test_arr = np.zeros((100, 100, 3), dtype=np.uint8)
        result = cv2.cvtColor(test_arr, cv2.COLOR_BGR2RGB)
        print(f"✓ OpenCV working - color conversion successful")
    except Exception as e:
        print(f"✗ Failed to use OpenCV: {e}")


def check_roi_tool():
    """Try to import the roi_tool script"""
    print_section("ROI Tool Import Test")

    roi_tool_path = Path(__file__).parent / "roi_tool.py"

    if not roi_tool_path.exists():
        print(f"✗ roi_tool.py not found at {roi_tool_path}")
        return

    print(f"✓ roi_tool.py found")

    # Try to compile it at least
    try:
        with open(roi_tool_path) as f:
            code = f.read()
        compile(code, str(roi_tool_path), 'exec')
        print(f"✓ roi_tool.py compiles successfully")
    except SyntaxError as e:
        print(f"✗ Syntax error in roi_tool.py: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    print("\n" + "="*70)
    print("  ROI Bounding Box Tool - Diagnostic Report")
    print("="*70)

    check_python()
    check_pip()
    check_packages()
    check_imports()
    check_specific_issue()
    check_roi_tool()

    print_section("Recommendations")
    print("""
If you see import errors:

1. Run fresh_install.py to do a clean reinstall:
   python fresh_install.py

2. Or run the batch file (Windows only):
   fresh_install.bat

3. If problems persist, try creating a fresh virtual environment:
   python -m venv roi_env

   Then activate it:
   Windows: roi_env\\Scripts\\activate
   Linux/Mac: source roi_env/bin/activate

   Then install: pip install -r requirements.txt

4. Make sure Python is 3.8 or newer:
   python --version
    """)

    print("\n" + "="*70)


if __name__ == "__main__":
    main()
