#!/usr/bin/env python3
"""
Non-interactive demo of Enhanced Trading Parameters
This script demonstrates trading parameters without requiring user input
"""

import os
import sys
import json
import time
import random

class Config:
    """Simple configuration class for testing"""
    
    def __init__(self):
        self.trading_params = {
            'amount_per_trade': 100.0,
            'max_position_size': 500.0,
            'stop_loss_percentage': 5.0,
            'take_profit_percentage': 15.0,
            'default_leverage': 5,
            'enable_stop_loss': True,
            'enable_take_profit': True,
            'use_signal_leverage': True,
            'max_leverage': 20,
            'min_market_cap': 1000000,
            'enable_market_cap_filter': True,
            'enable_auto_trading': False,
            'auto_close_trades': True,
            'max_simultaneous_trades': 5
        }
    
    def get_trading(self, key, default=None):
        """Get a value from the Trading section"""
        return self.trading_params.get(key, default)
    
    def set_trading(self, key, value):
        """Set a value in the Trading section"""
        self.trading_params[key] = value
    
    def save(self):
        """Save configuration (print for testing)"""
        print("\nSaving configuration...")
        for key, value in self.trading_params.items():
            print(f"  {key} = {value}")
        print("Configuration saved.\n")

class TradingParams:
    """Mock trading parameters class (no GUI)"""
    
    def __init__(self, config):
        """Initialize with a configuration object"""
        self.config = config
        
        # Trading parameters
        self.amount_per_trade = 100.0
        self.max_position_size = 500.0
        self.stop_loss_percentage = 5.0
        self.take_profit_percentage = 15.0
        self.default_leverage = 5
        self.enable_stop_loss = True
        self.enable_take_profit = True
        self.use_signal_leverage = True
        self.max_leverage = 20
        self.min_market_cap = 1000000
        self.enable_market_cap_filter = True
        self.enable_auto_trading = False
        self.auto_close_trades = True
        self.max_simultaneous_trades = 5
        
        # Load parameters from configuration
        self.load_params()
    
    def load_params(self):
        """Load parameters from configuration"""
        self.amount_per_trade = float(self.config.get_trading('amount_per_trade', 100.0))
        self.max_position_size = float(self.config.get_trading('max_position_size', 500.0))
        self.stop_loss_percentage = float(self.config.get_trading('stop_loss_percentage', 5.0))
        self.take_profit_percentage = float(self.config.get_trading('take_profit_percentage', 15.0))
        self.default_leverage = int(self.config.get_trading('default_leverage', 5))
        
        # Handle boolean values (which could be strings or booleans)
        enable_stop_loss = self.config.get_trading('enable_stop_loss', True)
        self.enable_stop_loss = enable_stop_loss if isinstance(enable_stop_loss, bool) else str(enable_stop_loss).lower() == 'true'
        
        enable_take_profit = self.config.get_trading('enable_take_profit', True)
        self.enable_take_profit = enable_take_profit if isinstance(enable_take_profit, bool) else str(enable_take_profit).lower() == 'true'
        
        use_signal_leverage = self.config.get_trading('use_signal_leverage', True)
        self.use_signal_leverage = use_signal_leverage if isinstance(use_signal_leverage, bool) else str(use_signal_leverage).lower() == 'true'
        
        self.max_leverage = int(self.config.get_trading('max_leverage', 20))
        self.min_market_cap = int(self.config.get_trading('min_market_cap', 1000000))
        
        enable_market_cap_filter = self.config.get_trading('enable_market_cap_filter', True)
        self.enable_market_cap_filter = enable_market_cap_filter if isinstance(enable_market_cap_filter, bool) else str(enable_market_cap_filter).lower() == 'true'
        
        enable_auto_trading = self.config.get_trading('enable_auto_trading', False)
        self.enable_auto_trading = enable_auto_trading if isinstance(enable_auto_trading, bool) else str(enable_auto_trading).lower() == 'true'
        
        auto_close_trades = self.config.get_trading('auto_close_trades', True)
        self.auto_close_trades = auto_close_trades if isinstance(auto_close_trades, bool) else str(auto_close_trades).lower() == 'true'
        
        self.max_simultaneous_trades = int(self.config.get_trading('max_simultaneous_trades', 5))
    
    def save_params(self):
        """Save parameters to configuration"""
        self.config.set_trading('amount_per_trade', self.amount_per_trade)
        self.config.set_trading('max_position_size', self.max_position_size)
        self.config.set_trading('stop_loss_percentage', self.stop_loss_percentage)
        self.config.set_trading('take_profit_percentage', self.take_profit_percentage)
        self.config.set_trading('default_leverage', self.default_leverage)
        self.config.set_trading('enable_stop_loss', 'true' if self.enable_stop_loss else 'false')
        self.config.set_trading('enable_take_profit', 'true' if self.enable_take_profit else 'false')
        self.config.set_trading('use_signal_leverage', 'true' if self.use_signal_leverage else 'false')
        self.config.set_trading('max_leverage', self.max_leverage)
        self.config.set_trading('min_market_cap', self.min_market_cap)
        self.config.set_trading('enable_market_cap_filter', 'true' if self.enable_market_cap_filter else 'false')
        self.config.set_trading('enable_auto_trading', 'true' if self.enable_auto_trading else 'false')
        self.config.set_trading('auto_close_trades', 'true' if self.auto_close_trades else 'false')
        self.config.set_trading('max_simultaneous_trades', self.max_simultaneous_trades)
        
        self.config.save()
    
    def display_params(self):
        """Display current parameters"""
        print("\n=== Current Trading Parameters ===")
        print(f"Amount per Trade: ${self.amount_per_trade}")
        print(f"Maximum Position Size: ${self.max_position_size}")
        print(f"Stop Loss: {self.stop_loss_percentage}% {'(Enabled)' if self.enable_stop_loss else '(Disabled)'}")
        print(f"Take Profit: {self.take_profit_percentage}% {'(Enabled)' if self.enable_take_profit else '(Disabled)'}")
        print(f"Default Leverage: {self.default_leverage}x")
        print(f"Use Signal Leverage: {'Yes' if self.use_signal_leverage else 'No'}")
        print(f"Maximum Leverage: {self.max_leverage}x")
        print(f"Minimum Market Cap: ${self.min_market_cap:,} {'(Enabled)' if self.enable_market_cap_filter else '(Disabled)'}")
        print(f"Auto Trading: {'Enabled' if self.enable_auto_trading else 'Disabled'}")
        print(f"Auto Close Trades: {'Yes' if self.auto_close_trades else 'No'}")
        print(f"Maximum Simultaneous Trades: {self.max_simultaneous_trades}")
        print("===================================\n")

def simulate_trading(params):
    """
    Simulate a trading scenario using the parameters
    
    Args:
        params: TradingParams object with trading parameters
    """
    print("\n=== Trading Simulation ===")
    print("Simulating a trading scenario with current parameters...")
    
    # Initial capital
    capital = 1000.0
    print(f"Initial Capital: ${capital}")
    
    # Simulate a trade signal
    symbol = "BTC/USDT"
    price = 50000.0
    leverage = 10
    market_cap = 500000000
    
    print(f"\nReceived signal for {symbol} at ${price}")
    print(f"Signal suggests {leverage}x leverage")
    print(f"Market cap: ${market_cap:,}")
    
    # Check market cap filter
    if params.enable_market_cap_filter and market_cap < params.min_market_cap:
        print(f"Trade rejected: Market cap (${market_cap:,}) is below minimum threshold (${params.min_market_cap:,})")
        return
    
    # Determine leverage
    actual_leverage = leverage if params.use_signal_leverage else params.default_leverage
    if actual_leverage > params.max_leverage:
        actual_leverage = params.max_leverage
        print(f"Leverage capped at {actual_leverage}x (maximum allowed)")
    else:
        print(f"Using leverage: {actual_leverage}x")
    
    # Calculate position size
    position_size = params.amount_per_trade
    if position_size > params.max_position_size:
        position_size = params.max_position_size
        print(f"Position size capped at ${position_size} (maximum allowed)")
    
    # Calculate contracts
    contracts = position_size / price * actual_leverage
    print(f"Opening position: ${position_size} ({contracts:.8f} contracts)")
    
    # Calculate stop loss and take profit
    if params.enable_stop_loss:
        stop_loss_price = price * (1 - params.stop_loss_percentage / 100)
        print(f"Stop Loss set at ${stop_loss_price:.2f} ({params.stop_loss_percentage}% from entry)")
    
    if params.enable_take_profit:
        take_profit_price = price * (1 + params.take_profit_percentage / 100)
        print(f"Take Profit set at ${take_profit_price:.2f} ({params.take_profit_percentage}% from entry)")
    
    # Simulate price movement
    print("\nSimulating price movement...")
    time.sleep(1)
    
    # Random outcome (simplified)
    outcome = random.choice(["profit", "loss", "ongoing"])
    
    if outcome == "profit":
        new_price = price * (1 + params.take_profit_percentage / 100)
        profit = position_size * (params.take_profit_percentage / 100) * actual_leverage
        print(f"Price moved to ${new_price:.2f}")
        print(f"Take profit triggered! Profit: ${profit:.2f}")
        new_capital = capital + profit
    elif outcome == "loss":
        new_price = price * (1 - params.stop_loss_percentage / 100)
        loss = position_size * (params.stop_loss_percentage / 100) * actual_leverage
        print(f"Price moved to ${new_price:.2f}")
        print(f"Stop loss triggered! Loss: ${loss:.2f}")
        new_capital = capital - loss
    else:
        new_price = price * 1.02  # 2% movement
        print(f"Price moved to ${new_price:.2f}")
        print("Position still open, no trigger hit yet")
        unrealized_profit = position_size * 0.02 * actual_leverage
        print(f"Unrealized profit: ${unrealized_profit:.2f}")
        new_capital = capital
    
    print(f"\nCapital: ${new_capital:.2f}")
    print("=========================\n")


def main():
    """Main function - non-interactive demo"""
    print("=======================================================")
    print("    DISCORD TRADING SIGNAL SCRAPER - PARAMETERS DEMO   ")
    print("=======================================================")
    print("This is a non-interactive demo of the enhanced trading parameters")
    print("It demonstrates how the trading parameters affect trade execution")
    
    # Create configuration and parameters objects
    config = Config()
    params = TradingParams(config)
    
    # Display current parameters
    print("\n--- Step 1: Show Current Parameters ---")
    params.display_params()
    time.sleep(1)
    
    # Modify parameters for demo
    print("\n--- Step 2: Modify Parameters ---")
    print("Modifying parameters to show different configurations...")
    
    # Example 1: Conservative trading settings
    print("\nExample 1: Conservative trading settings")
    params.amount_per_trade = 50.0
    params.max_position_size = 200.0
    params.stop_loss_percentage = 2.0
    params.take_profit_percentage = 5.0
    params.default_leverage = 2
    params.max_leverage = 5
    params.min_market_cap = 5000000
    params.display_params()
    simulate_trading(params)
    time.sleep(1)
    
    # Example 2: Aggressive trading settings
    print("\nExample 2: Aggressive trading settings")
    params.amount_per_trade = 200.0
    params.max_position_size = 1000.0
    params.stop_loss_percentage = 10.0
    params.take_profit_percentage = 30.0
    params.default_leverage = 10
    params.max_leverage = 20
    params.min_market_cap = 500000
    params.display_params()
    simulate_trading(params)
    time.sleep(1)
    
    # Example 3: Balanced trading settings
    print("\nExample 3: Balanced trading settings")
    params.amount_per_trade = 100.0
    params.max_position_size = 500.0
    params.stop_loss_percentage = 5.0
    params.take_profit_percentage = 15.0
    params.default_leverage = 5
    params.max_leverage = 10
    params.min_market_cap = 1000000
    params.display_params()
    simulate_trading(params)
    
    # Save final configuration
    print("\n--- Step 3: Save Configuration ---")
    params.save_params()
    
    print("\nDemo completed. In the full application, you can:")
    print("1. Configure all trading parameters through the GUI")
    print("2. Save your configuration for future use")
    print("3. Connect to Discord to monitor for trading signals")
    print("4. Execute trades automatically on Phemex based on your parameters")
    print("\nThank you for testing the Discord Trading Signal Scraper!")

if __name__ == "__main__":
    main()