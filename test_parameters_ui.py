#!/usr/bin/env python3
"""
Test script for Enhanced Trading Parameters UI
This script demonstrates the parameters UI without requiring the full system
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class Config:
    """Simple configuration class for testing"""
    
    def __init__(self):
        self.config = {
            'Trading': {
                'amount_per_trade': '100.0',
                'max_position_size': '500.0',
                'stop_loss_percentage': '5.0',
                'take_profit_percentage': '15.0',
                'default_leverage': '5',
                'enable_stop_loss': 'true',
                'enable_take_profit': 'true',
                'use_signal_leverage': 'true',
                'max_leverage': '20',
                'min_market_cap': '1000000',
                'enable_market_cap_filter': 'true',
                'enable_auto_trading': 'false',
                'auto_close_trades': 'true',
                'max_simultaneous_trades': '5'
            }
        }
    
    def get_trading(self, key, default=None):
        """Get a value from the Trading section"""
        if 'Trading' in self.config and key in self.config['Trading']:
            return self.config['Trading'][key]
        return default
    
    def set_trading(self, key, value):
        """Set a value in the Trading section"""
        if 'Trading' not in self.config:
            self.config['Trading'] = {}
        self.config['Trading'][key] = value
        print(f"Set {key} = {value}")
        
    def save(self):
        """Save configuration (print for testing)"""
        print("Configuration saved:")
        for section, values in self.config.items():
            print(f"[{section}]")
            for key, value in values.items():
                print(f"{key} = {value}")

class TradingParametersTest:
    """Test class for trading parameters UI"""
    
    def __init__(self):
        self.config = Config()
        self.root = None
        
    def run(self):
        """Start the UI test"""
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Trading Parameters Test")
        self.root.geometry("850x650")
        
        # Create the main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the trading parameters tab
        self._create_trading_params_tab(main_frame)
        
        # Start the main loop
        self.root.mainloop()
    
    def _create_trading_params_tab(self, parent):
        """
        Create the trading parameters tab with enhanced options
        
        Args:
            parent: Parent widget
        """
        # Create main container with scrollbar
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas for scrolling
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Position Size Settings
        position_frame = ttk.LabelFrame(scroll_frame, text="Position Size Settings", padding=10)
        position_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Amount per trade
        ttk.Label(position_frame, text="Amount per Trade ($):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.amount_per_trade_var = tk.DoubleVar(value=float(self.config.get_trading('amount_per_trade', 100.0)))
        amount_entry = ttk.Entry(position_frame, textvariable=self.amount_per_trade_var, width=10)
        amount_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(position_frame, text="USD value to invest in each trade signal").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Max position size
        ttk.Label(position_frame, text="Max Position Size ($):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_position_var = tk.DoubleVar(value=float(self.config.get_trading('max_position_size', 500.0)))
        max_position_entry = ttk.Entry(position_frame, textvariable=self.max_position_var, width=10)
        max_position_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(position_frame, text="Maximum USD value per position").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Risk Management Settings
        risk_frame = ttk.LabelFrame(scroll_frame, text="Risk Management Settings", padding=10)
        risk_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Stop Loss
        ttk.Label(risk_frame, text="Stop Loss (%):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.stop_loss_pct_var = tk.DoubleVar(value=float(self.config.get_trading('stop_loss_percentage', 5.0)))
        stop_loss_entry = ttk.Entry(risk_frame, textvariable=self.stop_loss_pct_var, width=10)
        stop_loss_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(risk_frame, text="Percentage loss at which position will close").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Take Profit
        ttk.Label(risk_frame, text="Take Profit (%):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.take_profit_pct_var = tk.DoubleVar(value=float(self.config.get_trading('take_profit_percentage', 15.0)))
        take_profit_entry = ttk.Entry(risk_frame, textvariable=self.take_profit_pct_var, width=10)
        take_profit_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(risk_frame, text="Percentage gain at which position will close").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Enable Stop Loss
        self.stop_loss_var = tk.BooleanVar(value=self.config.get_trading('enable_stop_loss', 'true').lower() == 'true')
        stop_loss_check = ttk.Checkbutton(risk_frame, text="Enable Stop Loss", variable=self.stop_loss_var)
        stop_loss_check.grid(row=2, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Enable Take Profit
        self.take_profit_var = tk.BooleanVar(value=self.config.get_trading('enable_take_profit', 'true').lower() == 'true')
        take_profit_check = ttk.Checkbutton(risk_frame, text="Enable Take Profit", variable=self.take_profit_var)
        take_profit_check.grid(row=3, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Leverage Settings
        leverage_frame = ttk.LabelFrame(scroll_frame, text="Leverage Settings", padding=10)
        leverage_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Default Leverage
        ttk.Label(leverage_frame, text="Default Leverage:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.leverage_var = tk.IntVar(value=int(self.config.get_trading('default_leverage', 5)))
        leverage_entry = ttk.Entry(leverage_frame, textvariable=self.leverage_var, width=10)
        leverage_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(leverage_frame, text="Default leverage multiplier for trades").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Use Signal Leverage
        self.use_signal_leverage_var = tk.BooleanVar(value=self.config.get_trading('use_signal_leverage', 'true').lower() == 'true')
        signal_leverage_check = ttk.Checkbutton(leverage_frame, text="Use Leverage from Signal (when available)", variable=self.use_signal_leverage_var)
        signal_leverage_check.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Max Leverage
        ttk.Label(leverage_frame, text="Maximum Leverage:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_leverage_var = tk.IntVar(value=int(self.config.get_trading('max_leverage', 20)))
        max_leverage_entry = ttk.Entry(leverage_frame, textvariable=self.max_leverage_var, width=10)
        max_leverage_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(leverage_frame, text="Maximum allowed leverage (caps signal leverage)").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Filtering Settings
        filter_frame = ttk.LabelFrame(scroll_frame, text="Market Filtering Settings", padding=10)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Minimum Market Cap
        ttk.Label(filter_frame, text="Minimum Market Cap ($):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.min_market_cap_var = tk.IntVar(value=int(self.config.get_trading('min_market_cap', 1000000)))
        market_cap_entry = ttk.Entry(filter_frame, textvariable=self.min_market_cap_var, width=15)
        market_cap_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(filter_frame, text="Don't trade coins with market cap below this value").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Enable Market Cap Filter
        self.enable_market_cap_filter_var = tk.BooleanVar(value=self.config.get_trading('enable_market_cap_filter', 'true').lower() == 'true')
        market_cap_check = ttk.Checkbutton(filter_frame, text="Enable Market Cap Filter", variable=self.enable_market_cap_filter_var)
        market_cap_check.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Auto Trading Settings
        auto_frame = ttk.LabelFrame(scroll_frame, text="Auto Trading Settings", padding=10)
        auto_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Enable Auto Trading
        self.enable_auto_trading_var = tk.BooleanVar(value=self.config.get_trading('enable_auto_trading', 'false').lower() == 'true')
        auto_trading_check = ttk.Checkbutton(auto_frame, text="Enable Automatic Trading (trades will execute without confirmation)", 
                                          variable=self.enable_auto_trading_var)
        auto_trading_check.grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Auto Close Trades
        self.auto_close_trades_var = tk.BooleanVar(value=self.config.get_trading('auto_close_trades', 'true').lower() == 'true')
        auto_close_check = ttk.Checkbutton(auto_frame, text="Automatically Close Trades at Stop Loss/Take Profit", 
                                         variable=self.auto_close_trades_var)
        auto_close_check.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Max Simultaneous Trades
        ttk.Label(auto_frame, text="Max Simultaneous Trades:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_trades_var = tk.IntVar(value=int(self.config.get_trading('max_simultaneous_trades', 5)))
        max_trades_entry = ttk.Entry(auto_frame, textvariable=self.max_trades_var, width=10)
        max_trades_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(auto_frame, text="Maximum number of open positions").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Save button
        save_button = ttk.Button(scroll_frame, text="Save Trading Parameters", command=self._save_trading_params)
        save_button.pack(pady=10)
    
    def _save_trading_params(self):
        """Save trading parameters to the configuration"""
        try:
            # Position size settings
            self.config.set_trading('amount_per_trade', str(self.amount_per_trade_var.get()))
            self.config.set_trading('max_position_size', str(self.max_position_var.get()))
            
            # Risk management settings
            self.config.set_trading('stop_loss_percentage', str(self.stop_loss_pct_var.get()))
            self.config.set_trading('take_profit_percentage', str(self.take_profit_pct_var.get()))
            self.config.set_trading('enable_stop_loss', str(self.stop_loss_var.get()).lower())
            self.config.set_trading('enable_take_profit', str(self.take_profit_var.get()).lower())
            
            # Leverage settings
            self.config.set_trading('default_leverage', str(self.leverage_var.get()))
            self.config.set_trading('use_signal_leverage', str(self.use_signal_leverage_var.get()).lower())
            self.config.set_trading('max_leverage', str(self.max_leverage_var.get()))
            
            # Filtering settings
            self.config.set_trading('min_market_cap', str(self.min_market_cap_var.get()))
            self.config.set_trading('enable_market_cap_filter', str(self.enable_market_cap_filter_var.get()).lower())
            
            # Auto trading settings
            self.config.set_trading('enable_auto_trading', str(self.enable_auto_trading_var.get()).lower())
            self.config.set_trading('auto_close_trades', str(self.auto_close_trades_var.get()).lower())
            self.config.set_trading('max_simultaneous_trades', str(self.max_trades_var.get()))
            
            # Save configuration
            self.config.save()
            
            messagebox.showinfo("Success", "Trading parameters saved successfully")
            logger.info("Trading parameters saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save trading parameters: {e}")
            logger.error(f"Failed to save trading parameters: {e}", exc_info=True)

# Run the test if executed directly
if __name__ == "__main__":
    print("Starting Trading Parameters Test UI...")
    app = TradingParametersTest()
    app.run()