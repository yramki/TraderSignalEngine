#!/bin/bash
# Script to run the Discord Trading Bot with the PyQt6 UI

# Make sure we're in the correct directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the application
python src/main_qt.py "$@"