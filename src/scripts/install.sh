#!/bin/bash

# Discord Trading Signal Scraper - Installation Script
echo "Installing Discord Trading Signal Scraper..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "Setting up Python virtual environment..."
python -m venv "$ROOT_DIR/venv"
source "$ROOT_DIR/venv/bin/activate"

echo "Installing Python dependencies..."
pip install -r "$ROOT_DIR/src/config/requirements.txt"

# Detect operating system
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux OS"
    # Install Tesseract OCR for Linux
    echo "Installing Tesseract OCR..."
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS"
    # Install Tesseract OCR for macOS
    echo "Installing Tesseract OCR via Homebrew..."
    echo "Make sure Homebrew is installed (https://brew.sh)"
    brew install tesseract
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Detected Windows"
    echo "Please install Tesseract OCR manually from: https://github.com/UB-Mannheim/tesseract/wiki"
else
    echo "Unknown operating system. Please install Tesseract OCR manually."
fi

# Create default configuration
echo "Creating default configuration..."
mkdir -p "$ROOT_DIR/config"
cat > "$ROOT_DIR/config/config.ini" << EOL
[General]
debug_mode = false
scan_interval = 2.0
test_mode = true

[Discord]
monitor_enabled = true
click_hidden_messages = true
auto_scroll = true
scroll_interval = 30.0
monitor_specific_channel = true

[Traders]
enable_filtering = true
target_traders = @example_trader

[Phemex]
api_key = YOUR_API_KEY
api_secret = YOUR_API_SECRET
testnet = true

[Trading]
amount_per_trade = 100  # Amount in USD per trade
stop_loss_percentage = 5.0  # Stop loss percentage
take_profit_percentage = 15.0  # Take profit percentage
min_market_cap = 10000000  # Minimum market cap in USD (10 million)
max_position_size = 1000  # Maximum position size in USD
default_leverage = 5  # Default leverage for trades
enable_stop_loss = true  # Whether to use stop loss
enable_take_profit = true  # Whether to use take profit
auto_trade = false  # Whether to automatically execute trades
EOL

echo "Creating start script..."
cat > "$ROOT_DIR/start.sh" << EOL
#!/bin/bash
source "venv/bin/activate"
python src/main_enhanced.py
EOL
chmod +x "$ROOT_DIR/start.sh"

echo "Creating test script..."
cat > "$ROOT_DIR/test_enhanced.sh" << EOL
#!/bin/bash
source "venv/bin/activate"
python -m pytest src/tests/
EOL
chmod +x "$ROOT_DIR/test_enhanced.sh"

echo "Installation complete!"
echo "To start the application, run: ./start.sh"