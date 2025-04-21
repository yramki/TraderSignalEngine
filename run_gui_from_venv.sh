#!/bin/bash
# Helper script to run the Enhanced Trading UI from a virtual environment

# Check if a virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Please run the install.sh script first to create a virtual environment."
    exit 1
fi

# Activate virtual environment and run the GUI
source venv/bin/activate
./run_enhanced_trading_ui.sh

# Deactivate virtual environment when done
deactivate