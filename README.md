# Discord Trading Signal Scraper with Enhanced Trading UI

A trading automation platform that executes trades on Phemex by parsing Discord signals and implementing user-defined trading parameters.

## Key Features

- **Screen Capture**: Monitors Discord for trading signals
- **Signal Parsing**: Extracts trading information from captured signals
- **Automated Trading**: Executes trades on Phemex based on signals
- **Trader Filtering**: Filter signals by specific traders
- **"Unlock Content" Detection**: Automatically clicks Discord's "Unlock Content" buttons
- **Continuous Monitoring**: Auto-scrolls to check for new messages
- **Risk Management**: Configurable position sizes and leverage
- **History Tracking**: Keep track of all signals and trades

## Enhanced Trading Parameters UI

The new Enhanced Trading UI provides an intuitive interface for configuring advanced trading parameters:

### Position Size Settings
- **Amount per Trade ($)**: Determines how much USD value you wish to invest in each trade signal.
- **Max Position Size ($)**: Limits the maximum USD value per position.

### Risk Management Settings
- **Stop Loss (%)**: Defines the percentage loss at which your position will automatically close to prevent further losses.
- **Take Profit (%)**: Defines the percentage gain at which your position will automatically close to secure profits.
- **Enable Stop Loss**: Toggle to enable/disable stop loss for all trades.
- **Enable Take Profit**: Toggle to enable/disable take profit for all trades.

### Leverage Settings
- **Default Leverage**: Sets the default leverage multiplier for trades.
- **Use Signal Leverage**: Use the leverage specified in the signal when available.
- **Maximum Leverage**: Caps the maximum leverage allowed for any trade.

### Market Filtering Settings
- **Minimum Market Cap ($)**: Filter that prevents trading on low-capitalization cryptocurrencies.
- **Enable Market Cap Filter**: Toggle to enable/disable filtering by market cap.

### Auto Trading Settings
- **Enable Automatic Trading**: When enabled, trades will execute without confirmation.
- **Automatically Close Trades**: When enabled, trades will automatically close at stop loss/take profit levels.
- **Max Simultaneous Trades**: Limits the number of open positions at any time.

## Running the Enhanced UI

To run the enhanced trading UI, execute:

```bash
./run_enhanced_trading_ui.sh
```

This script will:
1. Create a Python virtual environment (if it doesn't exist)
2. Install the required dependencies
3. Launch the enhanced trading UI

## Testing

To test the enhanced features, run:

```bash
./test_enhanced.sh
```

This script tests:
- Trader filtering functionality
- Unlock button detection
- Continuous channel monitoring
- Signal parsing
- Trading integration

## Requirements

- Python 3.8+
- Tesseract OCR (for text recognition)
- Required Python packages (installed automatically)

## Disclaimer

This software is for educational purposes only. Trading cryptocurrency involves significant risk. Always do your own research and never trade more than you can afford to lose.

## License

MIT License