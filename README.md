# README.md - Discord Trading Signal Scraper

## Project Overview

Discord Trading Signal Scraper is a desktop application that captures trading signals from Discord and automatically executes trades on Phemex. The application uses screen scraping technology to detect and extract trading signals from your Discord window, then processes these signals to place trades on your Phemex account.

## Features

- **Screen Capture**: Monitors Discord for trading signals
- **Signal Parsing**: Extracts trading information from captured signals
- **Automated Trading**: Executes trades on Phemex based on signals
- **User Interface**: Simple dashboard for monitoring and configuration
- **Risk Management**: Configurable position sizes and leverage

## Project Structure

```
discord_phemex_app/
├── src/                      # Source code
│   ├── __init__.py           # Package initialization
│   ├── main.py               # Application entry point
│   ├── screen_capture.py     # Screen capture module
│   ├── signal_parser.py      # Signal parsing module
│   ├── trading_client.py     # Phemex API client
│   └── ui/                   # User interface components
│       ├── __init__.py       # UI package initialization
│       └── main_window.py    # Main application window
├── requirements.txt          # Python dependencies
├── install.sh                # Installation script
├── test.sh                   # Test script
├── USER_GUIDE.md             # User documentation
└── README.md                 # This file
```

## Installation

Run the installation script to set up the application:

```bash
./install.sh
```

This will:
- Set up a Python virtual environment
- Install all required dependencies
- Install Tesseract OCR for text recognition
- Create a default configuration file
- Create desktop shortcuts

## Testing

Run the test script to verify the application is working correctly:

```bash
./test.sh
```

This will test:
- Signal parsing functionality
- Trading client integration
- Screen capture initialization

## Usage

1. Configure your Phemex API keys in `config.ini`
2. Start the application using `./start.sh`
3. Enable screen capture to monitor Discord
4. Enable trading to automatically execute trades

For detailed instructions, see [USER_GUIDE.md](USER_GUIDE.md).

## Requirements

- Python 3.8 or higher
- Tesseract OCR
- Discord desktop client
- Phemex account with API access

## Disclaimer

This application is for personal use only. Using automated tools with Discord may violate Discord's Terms of Service. Use at your own risk. The developers are not responsible for any losses incurred from trading or any account restrictions resulting from the use of this application.

Trading cryptocurrencies involves significant risk and can result in the loss of your invested capital. You should not invest more than you can afford to lose.
