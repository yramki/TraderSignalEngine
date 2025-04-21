#!/bin/bash
# Run script for Enhanced Trading UI

# Set text colors for better feedback
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Function to print warning messages
print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to print error messages
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment."
        exit 1
    fi
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if [ ! -f "venv/requirements_installed" ]; then
    print_status "Installing requirements..."
    pip install -r requirements_fixed.txt
    if [ $? -ne 0 ]; then
        print_error "Failed to install requirements."
        exit 1
    fi
    touch venv/requirements_installed
fi

# Run the Enhanced Trading UI
print_status "Starting Enhanced Trading UI..."
python3 src/run_enhanced_trading_ui.py

# Deactivate virtual environment
deactivate