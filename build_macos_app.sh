#!/bin/bash
# Script to build a macOS application bundle using PyInstaller

# Make sure we're in the correct directory
cd "$(dirname "$0")"

# Ensure required Python packages are installed
python -m pip install --upgrade pip
python -m pip install PyQt6 pyinstaller pyautogui opencv-python pytesseract numpy Pillow requests

echo "Building macOS application..."

# Run PyInstaller to create the app bundle
python -m PyInstaller --name="DiscordTradingBot" \
                      --windowed \
                      --onefile \
                      --add-data="config.ini:." \
                      --icon="app_icon.icns" \
                      src/main_qt.py

echo "Build complete! Application bundle is in the dist folder."
echo "To run the application, open dist/DiscordTradingBot.app"

# Create a zip file for distribution
echo "Creating zip distribution..."
cd dist
zip -r DiscordTradingBot.zip DiscordTradingBot.app
cd ..

echo "Your application is ready for distribution at dist/DiscordTradingBot.zip"