#!/bin/bash
# Helper script to run the Enhanced Trading UI from a virtual environment

# Set text colors for better feedback
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Function to print error messages
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if a virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found."
    print_error "Please run the install.sh script first to create a virtual environment."
    exit 1
fi

# Check if the src directory exists
if [ ! -d "src" ]; then
    print_error "src directory not found. Are you in the correct directory?"
    exit 1
fi

# Activate virtual environment and run the GUI directly with Python
print_status "Activating virtual environment..."
source venv/bin/activate

print_status "Starting Enhanced Trading UI..."
python src/run_enhanced_trading_ui.py

# Deactivate virtual environment when done
deactivate