#!/bin/bash
# First-time installation script for Discord Trading Signal Scraper

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

# Create a proper requirements.txt file
create_requirements_file() {
    print_status "Creating requirements file..."
    cat > requirements.txt << 'EOF'
# Requirements file for Discord Trading Signal Scraper

# Core dependencies
pyautogui==0.9.54
opencv-python==4.8.0.76
pytesseract==0.3.10
numpy==1.24.3
Pillow==10.0.0
requests==2.31.0

# UI dependencies
tk==0.1.0
configparser
pycryptodome
EOF
}

# Create a basic configuration file
create_config_file() {
    print_status "Creating configuration file..."
    
    if [ -f "config.ini" ]; then
        print_warning "Configuration file already exists. Skipping creation."
        return
    fi
    
    cat > config.ini << 'EOF'
[General]
scan_interval = 2.0

[Discord]
click_hidden_messages = true
monitor_specific_channel = true
auto_scroll = true
scroll_interval = 30.0

[Traders]
enable_filtering = true
target_traders = @trader1,@trader2

[Phemex]
api_key = 
api_secret = 
testnet = true

[Trading]
amount_per_trade = 100.0
max_position_size = 500.0
stop_loss_percentage = 5.0
take_profit_percentage = 15.0
default_leverage = 5
enable_stop_loss = true
enable_take_profit = true
use_signal_leverage = true
max_leverage = 20
min_market_cap = 1000000
enable_market_cap_filter = true
enable_auto_trading = false
auto_close_trades = true
max_simultaneous_trades = 5
EOF
}

# Create logs directory
create_logs_dir() {
    print_status "Creating logs directory..."
    mkdir -p logs
}

# Create required directories
create_directories() {
    print_status "Creating required directories..."
    mkdir -p venv
}

# Install required modules
install_modules() {
    print_status "Installing Python modules..."
    
    # Install Python modules
    python3 -m pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        print_error "Failed to install Python modules. Please try again."
        exit 1
    fi
    
    # Mark requirements as installed
    touch venv/requirements_installed
}

# Check Python
check_python() {
    print_status "Checking Python installation..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed or not in PATH. Please install Python 3 and try again."
        exit 1
    fi
    
    python3 --version
}

# Set permissions
set_permissions() {
    print_status "Setting executable permissions..."
    
    chmod +x test_headless.py
    chmod +x run_enhanced_trading_ui.sh
    chmod +x src/run_enhanced_trading_ui.py
}

# Main installation function
install() {
    print_status "Starting installation of Discord Trading Signal Scraper..."
    
    # Check if Python is installed
    check_python
    
    # Create directories
    create_directories
    
    # Create logs directory
    create_logs_dir
    
    # Create proper requirements file
    create_requirements_file
    
    # Create configuration file
    create_config_file
    
    # Install required modules
    install_modules
    
    # Set permissions
    set_permissions
    
    print_status "Installation completed successfully!"
    print_status ""
    print_status "To run the headless test of trading parameters:"
    print_status "python3 test_headless.py"
    print_status ""
    print_status "To run the full application locally with GUI (outside Replit):"
    print_status "./run_enhanced_trading_ui.sh"
}

# Run the installation
install