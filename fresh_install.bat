@echo off
REM Fresh install script for ROI Bounding Box Tool
REM Clears pip cache and reinstalls dependencies from scratch

echo.
echo ============================================================
echo ROI Bounding Box Tool - Fresh Install
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please ensure Python is installed and added to PATH
    pause
    exit /b 1
)

echo Step 1: Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip
    pause
    exit /b 1
)

echo.
echo Step 2: Clearing pip cache...
python -m pip cache purge
if errorlevel 1 (
    echo WARNING: Could not clear pip cache (non-critical)
)

echo.
echo Step 3: Uninstalling old versions...
python -m pip uninstall -y opencv-python cv2 numpy Pillow PyYAML pyperclip 2>nul
if errorlevel 1 (
    echo WARNING: Some packages were not installed (this is ok)
)

echo.
echo Step 4: Installing compatible versions...
python -m pip install --no-cache-dir -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Step 5: Verifying installation...
python -c "import cv2; import numpy; import PIL; import yaml; import pyperclip; print('SUCCESS: All packages imported correctly')"
if errorlevel 1 (
    echo ERROR: Failed to import packages
    echo Run this to diagnose: python -c "import cv2"
    pause
    exit /b 1
)

echo.
echo ============================================================
echo SUCCESS! Installation complete.
echo ============================================================
echo.
echo Next steps:
echo   1. Edit roi_config.yaml and set your video_path
echo   2. Run the tool: python roi_tool.py
echo   3. Or: python roi_tool.py --video path\to\video.mp4
echo.
pause
