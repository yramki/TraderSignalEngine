# Running the Enhanced Trading UI Locally

This guide will help you set up and run the Enhanced Trading UI on your local machine.

## Prerequisites

1. **Python 3.8+** - Download from [python.org](https://www.python.org/downloads/)
2. **Tesseract OCR** - Required for text recognition from Discord screenshots

   - **Windows:** Download and install from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS:** Install with Homebrew: `brew install tesseract`
   - **Linux:** Install with apt: `sudo apt install tesseract-ocr`

## Step 1: Download the Code

You can download this project in one of two ways:

### Option 1: Download ZIP
1. Download the ZIP file from the repository
2. Extract it to a folder on your computer

### Option 2: Clone the Repository (if you have Git installed)
```bash
git clone [repository-url]
cd discord-trading-signal-scraper
```

## Step 2: Set Up Python Environment

Create a virtual environment and install dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configure the Application

1. Create a `config.ini` file in the root directory (or copy the sample if provided)
2. Configure your settings:

```ini
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
api_key = YOUR_API_KEY
api_secret = YOUR_API_SECRET
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
```

## Step 4: Running the Enhanced UI

1. Make sure your virtual environment is activated
2. Run the enhanced trading UI:

```bash
# On Windows:
python src/run_enhanced_trading_ui.py

# On macOS/Linux:
chmod +x src/run_enhanced_trading_ui.py
./src/run_enhanced_trading_ui.py
```

Or use the provided shell script (on macOS/Linux):

```bash
chmod +x run_enhanced_trading_ui.sh
./run_enhanced_trading_ui.sh
```

## Step 5: Testing Just the Trading Parameters UI

If you want to test just the trading parameters UI without the full system:

```bash
python test_parameters_ui.py
```

## Usage Notes

1. **Discord Setup:** 
   - Open Discord in a separate window
   - Navigate to the channel with trading signals
   - The application will capture screenshots of this window to detect signals

2. **Trading Parameters:**
   - Configure position sizes, stop losses, take profits, etc., in the Trading Parameters tab
   - Click "Save Trading Parameters" to apply changes
   
3. **Target Traders:**
   - Add specific trader handles in the Main tab to filter signals

4. **Manual Trading:**
   - Use the controls at the bottom of the Main tab for manual trading

## Troubleshooting

1. **Screen Capture Issues:**
   - Make sure Discord is visible and the correct channel is focused
   - Adjust the scan interval if CPU usage is high

2. **OCR Problems:**
   - Ensure Tesseract OCR is properly installed
   - Try adjusting your monitor's resolution or Discord's zoom level

3. **Trading Issues:**
   - Verify your API keys are correct
   - Check if testnet mode is appropriately set

## Requirements

The key packages used in this application are:

- `pytesseract` - For text recognition
- `opencv-python` - For image processing
- `pillow` - For image handling
- `numpy` - For numerical operations
- `pyautogui` - For screen capture and automation
- `configparser` - For configuration management
- `requests` - For API requests
- `pycryptodome` - For cryptographic operations