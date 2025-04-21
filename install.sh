#!/bin/bash
# Improved Installation and deployment script for Discord Trading Signal Scraper

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            OS="debian"
        elif command_exists yum; then
            OS="fedora"
        else
            OS="linux-other"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
    print_status "Detected operating system: $OS"
}

# Install system dependencies based on OS
install_system_dependencies() {
    print_status "Installing system dependencies..."
    
    case $OS in
        debian)
            print_status "Installing dependencies for Debian/Ubuntu..."
            sudo apt-get update
            sudo apt-get install -y python3-venv python3-pip python3-tk python3-dev scrot tesseract-ocr
            ;;
        fedora)
            print_status "Installing dependencies for Fedora/CentOS..."
            sudo yum -y install python3-devel python3-pip python3-tkinter tesseract
            ;;
        macos)
            print_status "Installing dependencies for macOS..."
            if ! command_exists brew; then
                print_error "Homebrew is not installed. Please install Homebrew first."
                exit 1
            fi
            brew install python3 python-tk tesseract
            ;;
        windows)
            print_status "For Windows, please ensure you have Python 3.8+ installed with pip."
            print_status "Also install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki"
            ;;
        *)
            print_warning "Unknown operating system. You may need to install dependencies manually."
            ;;
    esac
}

# Set up virtual environment
setup_venv() {
    print_status "Setting up virtual environment..."
    
    # Check if Python 3 is installed
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
    print_status "Python version: $PYTHON_VERSION"
    
    # Create virtual environment
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing and recreating..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment. Please install python3-venv package."
        exit 1
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    if [ $? -ne 0 ]; then
        print_error "Failed to activate virtual environment."
        exit 1
    fi
    
    print_status "Virtual environment created and activated."
}

# Install Python dependencies
install_python_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies with verbose output
    pip install -v pyautogui
    pip install -v opencv-python
    pip install -v pytesseract
    pip install -v numpy
    pip install -v Pillow
    pip install -v requests
    pip install -v tk
    
    # Verify installations
    print_status "Verifying installations..."
    python -c "import pyautogui; print('PyAutoGUI version:', pyautogui.__version__)"
    python -c "import cv2; print('OpenCV version:', cv2.__version__)"
    python -c "import pytesseract; print('Pytesseract imported successfully')"
    python -c "import numpy; print('NumPy version:', numpy.__version__)"
    python -c "import PIL; print('Pillow version:', PIL.__version__)"
    python -c "import requests; print('Requests version:', requests.__version__)"
    
    print_status "Python dependencies installed successfully."
}

# Create default configuration
create_config() {
    print_status "Creating default configuration..."
    
    if [ -f "config.ini" ]; then
        print_warning "Configuration file already exists. Creating backup..."
        cp config.ini config.ini.bak
    fi
    
    cat > config.ini << 'EOF'
[General]
debug_mode = false
scan_interval = 2.0
test_mode = true

[Discord]
monitor_enabled = true
click_hidden_messages = true

[Phemex]
api_key = 
api_secret = 
testnet = true

[Trading]
max_position_size = 100
default_leverage = 5
enable_stop_loss = true
enable_take_profit = true
auto_trade = false
EOF

    print_status "Default configuration created."
}

# Create desktop shortcut
create_shortcut() {
    print_status "Creating desktop shortcut..."
    
    cat > discord_phemex_app.desktop << EOF
[Desktop Entry]
Name=Discord Trading Signal Scraper
Comment=Automatically capture trading signals from Discord and execute trades on Phemex
Exec=bash -c "cd $(pwd) && source venv/bin/activate && python3 src/main.py"
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;
EOF

    chmod +x discord_phemex_app.desktop
    
    # Check if we're in a desktop environment
    if [ -d "$HOME/Desktop" ]; then
        cp discord_phemex_app.desktop "$HOME/Desktop/"
        print_status "Desktop shortcut created in $HOME/Desktop/"
    else
        print_warning "Desktop environment not detected, shortcut created in current directory"
    fi
}

# Create startup script
create_startup_script() {
    print_status "Creating startup script..."
    
    cat > start.sh << 'EOF'
#!/bin/bash
# Start Discord Trading Signal Scraper

# Set text colors for better feedback
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Change to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}[ERROR]${NC} Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}[INFO]${NC} Activating virtual environment..."
source venv/bin/activate

# Verify key dependencies
echo -e "${GREEN}[INFO]${NC} Verifying dependencies..."
python3 -c "import pyautogui" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} PyAutoGUI not installed. Please run install.sh again."
    echo -e "${YELLOW}[TIP]${NC} You can also try: source venv/bin/activate && pip install pyautogui"
    exit 1
fi

# Run application
echo -e "${GREEN}[INFO]${NC} Starting Discord Trading Signal Scraper..."
python3 src/main.py "$@"
EOF

    chmod +x start.sh
    print_status "Startup script created."
}

# Main installation process
main() {
    print_status "Starting installation of Discord Trading Signal Scraper..."
    
    # Detect operating system
    detect_os
    
    # Install system dependencies
    install_system_dependencies
    
    # Set up virtual environment
    setup_venv
    
    # Install Python dependencies
    install_python_dependencies
    
    # Create default configuration
    create_config
    
    # Create desktop shortcut
    create_shortcut
    
    # Create startup script
    create_startup_script
    
    print_status "Installation complete!"
    print_status ""
    print_status "To start the application, run:"
    print_status "./start.sh"
    print_status ""
    print_status "Before using the application, please configure your Phemex API keys in config.ini"
    
    # Deactivate virtual environment
    deactivate
}

# Run the main installation process
main
