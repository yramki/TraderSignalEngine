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

# Function to print help information
print_help() {
    echo -e "${YELLOW}[HELP]${NC} $1"
}

# Function to print important notices
print_important() {
    echo -e "${YELLOW}[IMPORTANT]${NC} $1"
}

# Create a proper requirements.txt file
create_requirements_file() {
    print_status "Creating requirements file..."
    cat > requirements.txt << 'EOF'
# Requirements file for Discord Trading Signal Scraper

# Core dependencies
pyautogui
opencv-python
pytesseract
numpy
Pillow
requests

# UI dependencies
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

# Check for macOS Homebrew Python
check_macos_homebrew() {
    # Check if we're on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_status "Detected macOS operating system"
        
        # Check if Python was installed via Homebrew
        if command -v brew &> /dev/null && brew list | grep -q python; then
            print_status "Detected Homebrew-installed Python"
            return 0
        fi
    fi
    
    return 1
}

# Check for tkinter
check_tkinter() {
    print_status "Checking for tkinter..."
    
    if python3 -c "import tkinter" 2>/dev/null; then
        print_status "Tkinter is installed"
        return 0
    else
        print_warning "Tkinter is not installed. GUI applications will not work."
        
        if check_macos_homebrew; then
            print_help "To install tkinter on macOS with Homebrew, run: brew install python-tk"
        elif [ -f "/etc/debian_version" ]; then
            print_help "To install tkinter on Debian/Ubuntu, run: sudo apt-get install python3-tk"
        elif [ -f "/etc/redhat-release" ]; then
            print_help "To install tkinter on RHEL/CentOS/Fedora, run: sudo dnf install python3-tkinter"
        else
            print_help "Please install tkinter for your system to use the GUI application"
        fi
        
        return 1
    fi
}

# Install required modules
install_modules() {
    print_status "Installing Python modules..."
    
    # Variable to track if we're using a virtual environment
    USE_VENV=0
    
    # Check for macOS with Homebrew Python (externally managed)
    if check_macos_homebrew; then
        print_important "Detected macOS with Homebrew Python, which is usually an externally managed environment."
        print_status "This installation will use a virtual environment to avoid conflicts."
        USE_VENV=1
    else
        # For other systems, check if we're in an externally managed environment
        if python3 -m pip install --dry-run -r requirements.txt 2>&1 | grep -q "externally-managed-environment"; then
            print_warning "Detected externally managed environment."
            print_status "This installation will use a virtual environment to avoid conflicts."
            USE_VENV=1
        fi
    fi
    
    if [ "$USE_VENV" -eq 1 ]; then
        print_status "Creating a virtual environment to install dependencies."
        
        # Create a virtual environment
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            print_error "Failed to create virtual environment."
            print_help "You may need to install the venv module with: python3 -m pip install --user virtualenv"
            exit 1
        fi
        
        # Activate the virtual environment
        source venv/bin/activate
        
        # For Python 3.13+, we need to ensure setuptools is installed first
        PYTHON_VERSION=$(python --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 13 ]; then
            print_status "Detected Python 3.13+, installing setuptools first..."
            pip install --upgrade pip setuptools wheel
            
            if [ $? -ne 0 ]; then
                print_error "Failed to install setuptools. This is critical for Python 3.13."
                print_help "Try manually running: pip install --upgrade pip setuptools wheel"
                print_help "If the issue persists, check PYTHON_313_NOTE.md for more solutions."
                exit 1
            fi
        else
            # Still upgrade pip for older Python versions
            pip install --upgrade pip
        fi
        
        # Install in the virtual environment
        print_status "Installing required packages..."
        pip install -r requirements.txt
        
        if [ $? -ne 0 ]; then
            print_warning "First attempt failed. Trying to install packages one by one..."
            
            # Try installing packages one by one
            while read -r package; do
                # Skip comments and empty lines
                [[ $package =~ ^#.*$ ]] && continue
                [[ -z "$package" ]] && continue
                
                print_status "Installing $package..."
                pip install $package
                if [ $? -ne 0 ]; then
                    print_warning "Failed to install $package, continuing with other packages."
                fi
            done < requirements.txt
        fi
        
        # Check if tk module is available in the virtual environment
        if ! python -c "import tkinter" 2>/dev/null; then
            print_warning "Tkinter not available in virtual environment."
            
            if check_macos_homebrew; then
                print_help "On macOS, install tkinter with: brew install python-tk"
                print_help "After installation, you may need to recreate your virtual environment."
            fi
        fi
        
        # Create scripts to run from the virtual environment
        cat > run_from_venv.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python3 "$@"
EOF
        chmod +x run_from_venv.sh
        
        cat > run_gui_from_venv.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
./run_enhanced_trading_ui.sh
EOF
        chmod +x run_gui_from_venv.sh
        
        print_status "Modules installed successfully in virtual environment"
        print_important "To run the application from the virtual environment, use:"
        print_help "  - For demo: ./run_from_venv.sh demo_trading_parameters.py"
        print_help "  - For headless: ./run_from_venv.sh test_headless.py"
        print_help "  - For GUI: ./run_gui_from_venv.sh"
        
        # Deactivate the virtual environment
        deactivate
    else
        # Standard installation (non-virtual environment)
        print_status "Performing standard pip installation..."
        python3 -m pip install -r requirements.txt
        
        if [ $? -ne 0 ]; then
            print_warning "Standard installation failed. Trying to install packages one by one..."
            
            # Try installing packages one by one
            while read -r package; do
                # Skip comments and empty lines
                [[ $package =~ ^#.*$ ]] && continue
                [[ -z "$package" ]] && continue
                
                print_status "Installing $package..."
                python3 -m pip install $package
                if [ $? -ne 0 ]; then
                    print_warning "Failed to install $package, continuing with other packages."
                fi
            done < requirements.txt
        else
            print_status "Modules installed successfully using standard pip"
        fi
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
    
    # Get Python version
    PYTHON_VERSION=$(python3 --version)
    print_status "Found $PYTHON_VERSION"
    
    # Extract version numbers
    PYTHON_VERSION_NUM=$(python3 --version | sed -n 's/Python \([0-9]*\.[0-9]*\.[0-9]*\)/\1/p')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION_NUM | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION_NUM | cut -d'.' -f2)
    
    # Check Python version
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 6 ]); then
        print_error "Python 3.6 or higher is required. Your version is $PYTHON_VERSION_NUM."
        exit 1
    fi
    
    # Special note for Python 3.13+
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 13 ]; then
        print_important "You're using Python 3.13 or higher, which may have issues with setuptools."
        print_help "If you encounter installation problems, please refer to PYTHON_313_NOTE.md for guidance."
    fi
}

# Set permissions
set_permissions() {
    print_status "Setting executable permissions..."
    
    chmod +x test_headless.py
    chmod +x run_enhanced_trading_ui.sh
    chmod +x src/run_enhanced_trading_ui.py
}

# Create a special note for macOS users
create_macos_note() {
    if check_macos_homebrew; then
        print_status "Creating macOS specific instructions..."
        # The file MACOS_NOTE.md has been created separately
    fi
}

# Show final instructions
show_instructions() {
    # Different instructions based on the installation method
    if [ "$USE_VENV" -eq 1 ]; then
        # Virtual environment instructions
        print_status "==================================================================="
        print_status "INSTALLATION COMPLETED SUCCESSFULLY IN VIRTUAL ENVIRONMENT"
        print_status "==================================================================="
        print_status ""
        print_important "To run the application:"
        print_status ""
        print_help "1. Non-interactive demo (shows different trading configurations):"
        print_help "   ./run_from_venv.sh demo_trading_parameters.py"
        print_status ""
        print_help "2. Interactive headless version (command-line interface):"
        print_help "   ./run_from_venv.sh test_headless.py"
        print_status ""
        print_help "3. Full GUI application:"
        print_help "   ./run_gui_from_venv.sh"
        print_status ""
        
        if check_macos_homebrew; then
            print_important "You're using macOS with Homebrew. For more information, see MACOS_NOTE.md"
        fi
        
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 13 ]; then
            print_important "You're using Python 3.13+. For special information, see PYTHON_313_NOTE.md"
        fi
        
        print_status "==================================================================="
    else
        # Standard installation instructions
        print_status "==================================================================="
        print_status "INSTALLATION COMPLETED SUCCESSFULLY"
        print_status "==================================================================="
        print_status ""
        print_important "To run the application:"
        print_status ""
        print_help "1. Non-interactive demo (shows different trading configurations):"
        print_help "   python3 demo_trading_parameters.py"
        print_status ""
        print_help "2. Interactive headless version (command-line interface):"
        print_help "   python3 test_headless.py"
        print_status ""
        print_help "3. Full GUI application:"
        print_help "   ./run_enhanced_trading_ui.sh"
        print_status ""
        
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 13 ]; then
            print_important "You're using Python 3.13+. For special information, see PYTHON_313_NOTE.md"
        fi
        
        print_status "==================================================================="
    fi
}

# Main installation function
install() {
    print_status "==================================================================="
    print_status "DISCORD TRADING SIGNAL SCRAPER - INSTALLATION"
    print_status "==================================================================="
    print_status ""
    
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
    
    # Check for tkinter
    check_tkinter
    
    # Install required modules
    install_modules
    
    # Set permissions
    set_permissions
    
    # Create a special note for macOS users
    create_macos_note
    
    # Show final instructions
    show_instructions
}

# Run the installation
install