# Enhanced Discord Trading Signal Scraper - User Guide

This guide provides detailed instructions for installing, configuring, and using the Enhanced Discord Trading Signal Scraper application.

## Table of Contents

1. [Overview](#overview)
2. [New Features](#new-features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Using the Application](#using-the-application)
6. [Trader Filtering](#trader-filtering)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

## Overview

The Enhanced Discord Trading Signal Scraper is a desktop application that monitors Discord for trading signals and automatically executes trades on Phemex. This enhanced version includes trader filtering, automatic "Unlock Content" button detection, and continuous channel monitoring.

## New Features

### Trader Filtering
- Filter messages by specific trader handles (e.g., @yramki, @Tareeq)
- Only process signals from traders you're interested in
- Manage your list of target traders through a dedicated UI

### "Unlock Content" Button Detection
- Automatically detects and clicks "Unlock Content" buttons
- Uses image recognition to identify Discord's blue buttons
- Confirms button text using OCR before clicking

### Continuous Channel Monitoring
- Automatically scrolls to check for new messages
- Configurable scroll interval
- Ensures you don't miss any signals, even when they appear off-screen

## Installation

### System Requirements
- Python 3.8 or higher
- Operating System: Windows, macOS, or Linux
- Discord desktop application installed
- Internet connection for trading on Phemex

### Installation Steps

1. **Extract the package**
   ```
   unzip discord_phemex_app_enhanced.zip
   cd discord_phemex_app_enhanced
   ```

2. **Run the installation script**
   ```
   chmod +x install.sh
   ./install.sh
   ```

   The improved installation script will:
   - Detect your operating system
   - Install required system dependencies
   - Set up a Python virtual environment
   - Install all required Python packages
   - Create a desktop shortcut (if applicable)

3. **Verify installation**
   ```
   ./test_enhanced.sh
   ```

## Configuration

### Basic Configuration

The application uses a `config.ini` file for configuration. You can edit this file directly or use the Settings tab in the application.

Key configuration options:

```ini
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
target_traders = @yramki, @Tareeq

[Phemex]
api_key = YOUR_API_KEY
api_secret = YOUR_API_SECRET
testnet = true

[Trading]
max_position_size = 100
default_leverage = 5
enable_stop_loss = true
enable_take_profit = true
auto_trade = false
```

### Phemex API Setup

1. Log in to your Phemex account
2. Navigate to API Management
3. Create a new API key with trading permissions
4. Copy the API key and secret to your config.ini file

**Important**: Always start with `testnet = true` to ensure everything works correctly before enabling live trading.

## Using the Application

### Starting the Application

```
./start.sh
```

Or use the desktop shortcut created during installation.

### Dashboard Overview

The dashboard provides:
- Status indicators for screen capture, auto trading, and trader filtering
- Control buttons to start/stop capture and enable/disable features
- Latest signal display showing the most recently detected signal

### Settings Tab

Configure:
- Discord monitoring settings (scan interval, auto-scroll, etc.)
- Phemex API credentials
- Trading parameters (position size, leverage, etc.)

### Trader Filtering Tab

Manage which traders you want to monitor:
- Enable/disable trader filtering
- Add or remove trader handles
- View current list of target traders

### History Tab

View a history of detected signals and executed trades:
- Timestamp
- Trader
- Symbol
- Direction
- Entry price
- Stop loss and take profit levels
- Execution status

### Logs Tab

View application logs for troubleshooting and monitoring:
- Screen capture events
- Signal detection
- Trading actions
- Errors and warnings

## Trader Filtering

### Setting Up Trader Filtering

1. Go to the "Trader Filtering" tab
2. Enable trader filtering by checking "Enable Trader Filtering"
3. Add trader handles in the format `@username` (e.g., `@yramki`)
4. Click "Add Trader" to add to the list
5. Click "Apply Changes" to save and activate filtering

### How Trader Filtering Works

The application:
1. Scans Discord messages visible on screen
2. Checks if the message contains one of your target trader handles
3. If a match is found, processes the message for trading signals
4. If "Unlock Content" buttons are detected, automatically clicks them
5. Extracts and parses the trading signal information
6. Executes trades based on your configuration

### Best Practices

- Use the exact handle format shown in Discord (including the @ symbol)
- Add multiple traders to diversify your signal sources
- Monitor the logs to ensure the application is detecting your target traders

## Troubleshooting

### Common Issues

#### Application doesn't detect signals
- Ensure Discord is open and visible on your screen
- Check that you've clicked "Start Capture" on the dashboard
- Verify trader filtering is properly configured with correct handles
- Try increasing the scan interval in Settings

#### "Unlock Content" buttons aren't being clicked
- Make sure "Click Hidden Messages" is enabled in settings
- Ensure Discord is using a standard theme (dark or light)
- Check that the button is fully visible on screen

#### Auto-scrolling isn't working
- Verify "Auto Scroll" is enabled in settings
- Try adjusting the scroll interval
- Ensure Discord has focus when auto-scrolling is needed

#### Trading isn't executing
- Check your API keys are correct
- Verify "Auto Trade" is enabled
- Ensure you have sufficient funds in your Phemex account
- Check the logs for any error messages

### Dependency Issues

If you encounter dependency issues, refer to the TROUBLESHOOTING.md file for detailed solutions.

## FAQ

**Q: Is this application against Discord's Terms of Service?**  
A: Screen scraping Discord is against their Terms of Service. This application is for personal use only, and you use it at your own risk.

**Q: Can I filter for multiple traders at once?**  
A: Yes, you can add multiple trader handles in the Trader Filtering tab.

**Q: Does the application work with Discord's web version?**  
A: The application is designed for the Discord desktop application, but may work with the web version in some browsers.

**Q: How can I test the application without risking real money?**  
A: Set `testnet = true` in the config.ini file to use Phemex's testnet environment.

**Q: Can I customize the trading logic?**  
A: Yes, the application is open source. You can modify the trading logic in the `trading_client.py` file.

**Q: How do I update to newer versions?**  
A: Download the latest version and run the installation script. Your configuration will be preserved.

**Q: Can I run this on a server without a GUI?**  
A: No, this application requires a graphical environment as it uses screen capture to monitor Discord.
