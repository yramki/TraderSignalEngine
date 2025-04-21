# Discord Trading Signal Scraper

A trading automation platform that executes trades on Phemex by parsing Discord signals and implementing user-defined trading parameters.

## Key Features

- **Discord Message Monitoring**: Automatically captures and processes trading signals from Discord
- **Trader Filtering**: Target specific traders you trust
- **Enhanced Trading Parameters**: Configure amount per trade, stop loss, take profit, and more
- **Market Cap Filtering**: Only execute trades for assets above your minimum market cap threshold
- **Automated Trade Execution**: Execute trades on Phemex with customizable leverage and position sizes
- **User-friendly Interface**: Easily configure all parameters through a simple GUI

## Installation

### Prerequisites

- Python 3.6 or newer
- pip (Python package manager)
- For GUI: Tkinter support for Python
- For Discord screen capture: Python OpenCV and PyAutoGUI

### Quick Start

1. Clone or download this repository
2. Run the installation script:

```bash
chmod +x install.sh
./install.sh
```

This will:
- Install required dependencies
- Create configuration files
- Set up logs directory

> **Note for Python 3.13+ users**: Please see [PYTHON_313_NOTE.md](PYTHON_313_NOTE.md) for special installation instructions.

## Running the Application

### Testing the Parameters (No GUI)

To test the trading parameters without a GUI:

```bash
python3 test_headless.py
```

This provides a command-line interface to:
- View current parameters
- Modify parameters
- Simulate trading scenarios
- Save your configuration

### Full Application (with GUI)

To run the full application with GUI:

```bash
./run_enhanced_trading_ui.sh
```

## Configuration

The main configuration is stored in `config.ini` and includes:

### Trading Parameters

- `amount_per_trade`: Base amount to invest per trade
- `max_position_size`: Maximum position size limit
- `stop_loss_percentage`: Stop loss percentage from entry
- `take_profit_percentage`: Take profit percentage from entry
- `default_leverage`: Default leverage when not using signal leverage
- `enable_stop_loss`: Enable/disable stop loss orders
- `enable_take_profit`: Enable/disable take profit orders
- `use_signal_leverage`: Use leverage suggested in signal or use default
- `max_leverage`: Maximum allowed leverage
- `min_market_cap`: Minimum market cap for assets to trade
- `enable_market_cap_filter`: Enable/disable market cap filtering
- `enable_auto_trading`: Toggle automatic trade execution
- `auto_close_trades`: Automatically close trades on TP/SL
- `max_simultaneous_trades`: Maximum number of open trades

### Discord Parameters

- `click_hidden_messages`: Click to reveal hidden messages
- `monitor_specific_channel`: Focus on a specific Discord channel
- `auto_scroll`: Automatically scroll to check for new messages

### Phemex API Parameters

- `api_key`: Your Phemex API key
- `api_secret`: Your Phemex API secret
- `testnet`: Use testnet (true) or live trading (false)

## Demo

The repository includes a non-interactive demo that shows how different parameter configurations affect trade execution:

```bash
python3 demo_trading_parameters.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.