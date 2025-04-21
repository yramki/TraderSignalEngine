"""
Enhanced Trading UI Module for Discord Trading Signal Scraper
Provides advanced trading parameter configuration
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from typing import Dict, Any, Optional, List

from screen_capture_enhanced import ScreenCapture
from signal_parser import SignalParser
from trading_client import PhemexClient
from config_enhanced import Config

logger = logging.getLogger(__name__)

class EnhancedTradingUI:
    """
    Enhanced trading user interface with advanced trading parameters
    """
    
    def __init__(self, screen_capture: ScreenCapture, signal_parser: SignalParser, 
                 trading_client: PhemexClient, config: Config):
        """
        Initialize the enhanced trading UI
        
        Args:
            screen_capture: ScreenCapture instance
            signal_parser: SignalParser instance
            trading_client: PhemexClient instance
            config: Configuration instance
        """
        self.screen_capture = screen_capture
        self.signal_parser = signal_parser
        self.trading_client = trading_client
        self.config = config
        
        self.root = None
        self.signal_processing_thread = None
        self.running = False
        
        logger.info("Enhanced trading UI initialized")
    
    def run(self):
        """Start the enhanced trading UI"""
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Discord Trading Signal Scraper - Enhanced Trading")
        self.root.geometry("850x650")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Create the main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        tab_control = ttk.Notebook(main_frame)
        
        # Dashboard tab
        dashboard_tab = ttk.Frame(tab_control)
        tab_control.add(dashboard_tab, text="Dashboard")
        self._create_dashboard_tab(dashboard_tab)
        
        # Trading Parameters tab (new)
        trading_params_tab = ttk.Frame(tab_control)
        tab_control.add(trading_params_tab, text="Trading Parameters")
        self._create_trading_params_tab(trading_params_tab)
        
        # Settings tab
        settings_tab = ttk.Frame(tab_control)
        tab_control.add(settings_tab, text="Settings")
        self._create_settings_tab(settings_tab)
        
        # Trader Filtering tab
        trader_tab = ttk.Frame(tab_control)
        tab_control.add(trader_tab, text="Trader Filtering")
        self._create_trader_tab(trader_tab)
        
        # History tab
        history_tab = ttk.Frame(tab_control)
        tab_control.add(history_tab, text="History")
        self._create_history_tab(history_tab)
        
        # Logs tab
        logs_tab = ttk.Frame(tab_control)
        tab_control.add(logs_tab, text="Logs")
        self._create_logs_tab(logs_tab)
        
        tab_control.pack(fill=tk.BOTH, expand=True)
        
        # Start signal processing thread
        self.running = True
        self.signal_processing_thread = threading.Thread(target=self._process_signals)
        self.signal_processing_thread.daemon = True
        self.signal_processing_thread.start()
        
        # Start screen capture
        self.screen_capture.start()
        
        # Start the main loop
        self.root.mainloop()
    
    def _create_dashboard_tab(self, parent):
        """
        Create the dashboard tab
        
        Args:
            parent: Parent widget
        """
        # Create frame for status
        status_frame = ttk.LabelFrame(parent, text="Status", padding=10)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status indicators
        self.capture_status_var = tk.StringVar(value="Stopped")
        self.trading_status_var = tk.StringVar(value="Disabled")
        self.filtering_status_var = tk.StringVar(value="Disabled")
        
        # Capture status
        ttk.Label(status_frame, text="Screen Capture:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(status_frame, textvariable=self.capture_status_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Trading status
        ttk.Label(status_frame, text="Auto Trading:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(status_frame, textvariable=self.trading_status_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Filtering status
        ttk.Label(status_frame, text="Trader Filtering:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(status_frame, textvariable=self.filtering_status_var).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Control buttons
        control_frame = ttk.Frame(parent, padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Start/Stop capture button
        self.capture_button_var = tk.StringVar(value="Start Capture")
        self.capture_button = ttk.Button(
            control_frame, 
            textvariable=self.capture_button_var,
            command=self._toggle_capture
        )
        self.capture_button.pack(side=tk.LEFT, padx=5)
        
        # Enable/Disable trading button
        self.trading_button_var = tk.StringVar(value="Enable Trading")
        self.trading_button = ttk.Button(
            control_frame, 
            textvariable=self.trading_button_var,
            command=self._toggle_trading
        )
        self.trading_button.pack(side=tk.LEFT, padx=5)
        
        # Enable/Disable filtering button
        self.filtering_button_var = tk.StringVar(value="Enable Filtering")
        self.filtering_button = ttk.Button(
            control_frame, 
            textvariable=self.filtering_button_var,
            command=self._toggle_filtering
        )
        self.filtering_button.pack(side=tk.LEFT, padx=5)
        
        # Latest signal frame
        signal_frame = ttk.LabelFrame(parent, text="Latest Signal", padding=10)
        signal_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Signal details
        self.signal_text = scrolledtext.ScrolledText(signal_frame, height=10)
        self.signal_text.pack(fill=tk.BOTH, expand=True)
        self.signal_text.insert(tk.END, "No signals detected yet.")
        self.signal_text.config(state=tk.DISABLED)
        
        # Update status indicators
        self._update_status_indicators()
    
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
    
    def _create_settings_tab(self, parent):
        """
        Create the settings tab
        
        Args:
            parent: Parent widget
        """
        # Create frame for Discord settings
        discord_frame = ttk.LabelFrame(parent, text="Discord Settings", padding=10)
        discord_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Scan interval
        ttk.Label(discord_frame, text="Scan Interval (seconds):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.scan_interval_var = tk.DoubleVar(value=float(self.config.get_general('scan_interval', 2.0)))
        scan_interval_entry = ttk.Entry(discord_frame, textvariable=self.scan_interval_var, width=10)
        scan_interval_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Click hidden messages
        self.click_hidden_var = tk.BooleanVar(value=self.config.get_discord('click_hidden_messages', 'true').lower() == 'true')
        click_hidden_check = ttk.Checkbutton(discord_frame, text="Click Hidden Messages", variable=self.click_hidden_var)
        click_hidden_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        # Auto scroll
        self.auto_scroll_var = tk.BooleanVar(value=self.config.get_discord('auto_scroll', 'true').lower() == 'true')
        auto_scroll_check = ttk.Checkbutton(discord_frame, text="Auto Scroll", variable=self.auto_scroll_var)
        auto_scroll_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        # Scroll interval
        ttk.Label(discord_frame, text="Scroll Interval (seconds):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.scroll_interval_var = tk.DoubleVar(value=float(self.config.get_discord('scroll_interval', 30.0)))
        scroll_interval_entry = ttk.Entry(discord_frame, textvariable=self.scroll_interval_var, width=10)
        scroll_interval_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Monitor specific channel
        self.monitor_channel_var = tk.BooleanVar(value=self.config.get_discord('monitor_specific_channel', 'true').lower() == 'true')
        monitor_channel_check = ttk.Checkbutton(discord_frame, text="Monitor Specific Channel", variable=self.monitor_channel_var)
        monitor_channel_check.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        # Create frame for Phemex settings
        phemex_frame = ttk.LabelFrame(parent, text="Phemex Settings", padding=10)
        phemex_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # API Key
        ttk.Label(phemex_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.api_key_var = tk.StringVar(value=self.config.get_phemex('api_key', ''))
        api_key_entry = ttk.Entry(phemex_frame, textvariable=self.api_key_var, width=40)
        api_key_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # API Secret
        ttk.Label(phemex_frame, text="API Secret:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.api_secret_var = tk.StringVar(value=self.config.get_phemex('api_secret', ''))
        api_secret_entry = ttk.Entry(phemex_frame, textvariable=self.api_secret_var, width=40, show="*")
        api_secret_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Testnet
        self.testnet_var = tk.BooleanVar(value=self.config.get_phemex('testnet', 'true').lower() == 'true')
        testnet_check = ttk.Checkbutton(phemex_frame, text="Use Testnet", variable=self.testnet_var)
        testnet_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        # Save button
        save_button = ttk.Button(parent, text="Save Settings", command=self._save_settings)
        save_button.pack(pady=10)
    
    def _create_trader_tab(self, parent):
        """
        Create the trader filtering tab
        
        Args:
            parent: Parent widget
        """
        # Create frame for trader filtering
        trader_frame = ttk.LabelFrame(parent, text="Trader Filtering Settings", padding=10)
        trader_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Enable trader filtering
        self.enable_filtering_var = tk.BooleanVar(value=self.config.get_traders('enable_filtering', 'false').lower() == 'true')
        enable_filtering_check = ttk.Checkbutton(
            trader_frame, 
            text="Enable Trader Filtering", 
            variable=self.enable_filtering_var,
            command=self._update_trader_filtering
        )
        enable_filtering_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        # Target traders
        ttk.Label(trader_frame, text="Target Traders:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        # Get current target traders
        target_traders = self.config.get_target_traders()
        target_traders_str = ", ".join(target_traders) if target_traders else ""
        
        self.target_traders_var = tk.StringVar(value=target_traders_str)
        target_traders_entry = ttk.Entry(trader_frame, textvariable=self.target_traders_var, width=40)
        target_traders_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Help text
        ttk.Label(
            trader_frame, 
            text="Enter trader handles separated by commas (e.g., @yramki, @Tareeq)",
            font=("", 8, "italic")
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        # Trader list frame
        trader_list_frame = ttk.LabelFrame(parent, text="Current Target Traders", padding=10)
        trader_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Trader list
        self.trader_list = tk.Listbox(trader_list_frame, height=10)
        self.trader_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for trader list
        trader_list_scrollbar = ttk.Scrollbar(trader_list_frame, orient=tk.VERTICAL, command=self.trader_list.yview)
        self.trader_list.configure(yscroll=trader_list_scrollbar.set)
        trader_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate trader list
        self._update_trader_list()
        
        # Buttons frame
        buttons_frame = ttk.Frame(parent, padding=10)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add trader button
        add_trader_button = ttk.Button(buttons_frame, text="Add Trader", command=self._add_trader)
        add_trader_button.pack(side=tk.LEFT, padx=5)
        
        # Remove trader button
        remove_trader_button = ttk.Button(buttons_frame, text="Remove Selected", command=self._remove_trader)
        remove_trader_button.pack(side=tk.LEFT, padx=5)
        
        # Apply button
        apply_button = ttk.Button(buttons_frame, text="Apply Changes", command=self._apply_trader_changes)
        apply_button.pack(side=tk.RIGHT, padx=5)
    
    def _create_history_tab(self, parent):
        """
        Create the history tab
        
        Args:
            parent: Parent widget
        """
        # Create frame for trade history
        history_frame = ttk.Frame(parent, padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for trade history
        columns = ("timestamp", "trader", "symbol", "direction", "entry", "sl", "tp", "status")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        
        # Define column headings
        self.history_tree.heading("timestamp", text="Timestamp")
        self.history_tree.heading("trader", text="Trader")
        self.history_tree.heading("symbol", text="Symbol")
        self.history_tree.heading("direction", text="Direction")
        self.history_tree.heading("entry", text="Entry")
        self.history_tree.heading("sl", text="Stop Loss")
        self.history_tree.heading("tp", text="Take Profit")
        self.history_tree.heading("status", text="Status")
        
        # Set column widths
        self.history_tree.column("timestamp", width=150)
        self.history_tree.column("trader", width=100)
        self.history_tree.column("symbol", width=100)
        self.history_tree.column("direction", width=80)
        self.history_tree.column("entry", width=80)
        self.history_tree.column("sl", width=80)
        self.history_tree.column("tp", width=80)
        self.history_tree.column("status", width=80)
        
        # Add vertical scrollbar
        history_y_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscroll=history_y_scroll.set)
        
        # Add horizontal scrollbar
        history_x_scroll = ttk.Scrollbar(history_frame, orient=tk.HORIZONTAL, command=self.history_tree.xview)
        self.history_tree.configure(xscroll=history_x_scroll.set)
        
        # Pack widgets
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        history_x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Buttons frame
        buttons_frame = ttk.Frame(parent, padding=10)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Clear history button
        clear_button = ttk.Button(buttons_frame, text="Clear History", command=self._clear_history)
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # Export history button
        export_button = ttk.Button(buttons_frame, text="Export History", command=self._export_history)
        export_button.pack(side=tk.LEFT, padx=5)
        
        # Refresh button
        refresh_button = ttk.Button(buttons_frame, text="Refresh", command=self._refresh_history)
        refresh_button.pack(side=tk.RIGHT, padx=5)
        
        # Load initial history
        self._refresh_history()
    
    def _create_logs_tab(self, parent):
        """
        Create the logs tab
        
        Args:
            parent: Parent widget
        """
        # Create logs frame
        logs_frame = ttk.Frame(parent, padding=10)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Logs text area
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=20)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        self.logs_text.config(state=tk.DISABLED)
        
        # Buttons frame
        buttons_frame = ttk.Frame(parent, padding=10)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Clear logs button
        clear_button = ttk.Button(buttons_frame, text="Clear Logs", command=self._clear_logs)
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # Export logs button
        export_button = ttk.Button(buttons_frame, text="Export Logs", command=self._export_logs)
        export_button.pack(side=tk.LEFT, padx=5)
    
    def _toggle_capture(self):
        """Toggle screen capture on/off"""
        if self.screen_capture.is_running():
            self.screen_capture.stop()
            self.capture_button_var.set("Start Capture")
            self.capture_status_var.set("Stopped")
            logger.info("Screen capture stopped")
        else:
            self.screen_capture.start()
            self.capture_button_var.set("Stop Capture")
            self.capture_status_var.set("Running")
            logger.info("Screen capture started")
    
    def _toggle_trading(self):
        """Toggle auto trading on/off"""
        current_value = self.config.get_trading('enable_auto_trading', 'false').lower() == 'true'
        new_value = not current_value
        
        self.config.set_trading('enable_auto_trading', str(new_value).lower())
        self.config.save()
        
        if new_value:
            self.trading_button_var.set("Disable Trading")
            self.trading_status_var.set("Enabled")
            logger.info("Auto trading enabled")
        else:
            self.trading_button_var.set("Enable Trading")
            self.trading_status_var.set("Disabled")
            logger.info("Auto trading disabled")
    
    def _toggle_filtering(self):
        """Toggle trader filtering on/off"""
        current_value = self.config.get_traders('enable_filtering', 'false').lower() == 'true'
        new_value = not current_value
        
        self.config.set_traders('enable_filtering', str(new_value).lower())
        self.config.save()
        
        if new_value:
            self.filtering_button_var.set("Disable Filtering")
            self.filtering_status_var.set("Enabled")
            logger.info("Trader filtering enabled")
        else:
            self.filtering_button_var.set("Enable Filtering")
            self.filtering_status_var.set("Disabled")
            logger.info("Trader filtering disabled")
        
        # Update screen capture with new filtering settings
        self._update_trader_filtering()
    
    def _update_status_indicators(self):
        """Update status indicators based on current settings"""
        # Capture status
        if self.screen_capture.is_running():
            self.capture_button_var.set("Stop Capture")
            self.capture_status_var.set("Running")
        else:
            self.capture_button_var.set("Start Capture")
            self.capture_status_var.set("Stopped")
        
        # Trading status
        if self.config.get_trading('enable_auto_trading', 'false').lower() == 'true':
            self.trading_button_var.set("Disable Trading")
            self.trading_status_var.set("Enabled")
        else:
            self.trading_button_var.set("Enable Trading")
            self.trading_status_var.set("Disabled")
        
        # Filtering status
        if self.config.get_traders('enable_filtering', 'false').lower() == 'true':
            self.filtering_button_var.set("Disable Filtering")
            self.filtering_status_var.set("Enabled")
        else:
            self.filtering_button_var.set("Enable Filtering")
            self.filtering_status_var.set("Disabled")
    
    def _process_signals(self):
        """Process signals in a separate thread"""
        while self.running:
            try:
                # Get signal from the queue with a timeout
                signal_text = self.screen_capture.get_signal(timeout=0.1)
                
                if signal_text:
                    # Parse the signal
                    signal = self.signal_parser.parse(signal_text)
                    
                    # Update UI with the new signal
                    self._update_signal_display(signal_text, signal)
                    
                    # Process the signal if auto trading is enabled
                    if self.config.get_trading('enable_auto_trading', 'false').lower() == 'true':
                        self._process_trade(signal)
                    
                    # Add to history
                    self._add_signal_to_history(signal)
                    
                    logger.info(f"Processed signal: {signal}")
            except Exception as e:
                logger.error(f"Error processing signal: {e}", exc_info=True)
            
            # Short sleep to prevent high CPU usage
            time.sleep(0.1)
    
    def _update_signal_display(self, signal_text: str, signal: Dict[str, Any]):
        """
        Update the UI with the new signal
        
        Args:
            signal_text: Raw signal text
            signal: Parsed signal data
        """
        if self.root:
            self.signal_text.config(state=tk.NORMAL)
            self.signal_text.delete(1.0, tk.END)
            
            # Add raw text
            self.signal_text.insert(tk.END, f"Raw signal:\n{signal_text}\n\n")
            
            # Add parsed data
            self.signal_text.insert(tk.END, f"Parsed data:\n")
            for key, value in signal.items():
                self.signal_text.insert(tk.END, f"{key}: {value}\n")
            
            self.signal_text.config(state=tk.DISABLED)
    
    def _process_trade(self, signal: Dict[str, Any]):
        """
        Process a trade based on the signal
        
        Args:
            signal: Parsed signal data
        """
        try:
            # Check if we should execute this trade
            if not self._should_execute_trade(signal):
                logger.info(f"Skipping trade execution for signal: {signal}")
                return
            
            # Get trading parameters
            amount = float(self.config.get_trading('amount_per_trade', 100.0))
            leverage = int(signal.get('leverage', self.config.get_trading('default_leverage', 5)))
            
            # Cap leverage to maximum
            max_leverage = int(self.config.get_trading('max_leverage', 20))
            if leverage > max_leverage:
                logger.warning(f"Capping leverage from {leverage} to {max_leverage}")
                leverage = max_leverage
            
            # Execute the trade
            result = self.trading_client.execute_trade(
                symbol=signal['symbol'],
                direction=signal['direction'],
                amount=amount,
                leverage=leverage,
                stop_loss=signal.get('stop_loss'),
                take_profit=signal.get('take_profit')
            )
            
            logger.info(f"Trade executed: {result}")
            
            # Update history with the trade result
            self._update_trade_in_history(signal, result)
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}", exc_info=True)
    
    def _should_execute_trade(self, signal: Dict[str, Any]) -> bool:
        """
        Check if we should execute a trade based on the signal and configuration
        
        Args:
            signal: Parsed signal data
            
        Returns:
            bool: True if we should execute the trade, False otherwise
        """
        # Check if we've reached the maximum number of simultaneous trades
        max_trades = int(self.config.get_trading('max_simultaneous_trades', 5))
        current_trades = len(self._get_open_trades())
        if current_trades >= max_trades:
            logger.warning(f"Maximum number of trades ({max_trades}) reached. Skipping trade.")
            return False
        
        # Check market cap if enabled
        if self.config.get_trading('enable_market_cap_filter', 'true').lower() == 'true':
            min_market_cap = int(self.config.get_trading('min_market_cap', 1000000))
            market_cap = self._get_market_cap(signal['symbol'])
            
            if market_cap < min_market_cap:
                logger.warning(f"Market cap for {signal['symbol']} ({market_cap}) is below minimum ({min_market_cap}). Skipping trade.")
                return False
        
        return True
    
    def _get_open_trades(self) -> List[Dict[str, Any]]:
        """
        Get the list of currently open trades
        
        Returns:
            List of open trades
        """
        # This would normally query the trading client or local database
        # For now, returning an empty list as a placeholder
        return []
    
    def _get_market_cap(self, symbol: str) -> int:
        """
        Get the market cap for a symbol
        
        Args:
            symbol: Trading symbol (e.g., BTCUSDT)
            
        Returns:
            Market cap in USD
        """
        # This would normally query an API or other data source
        # For now, returning a placeholder value
        return 10000000000  # $10B for BTC-like assets
    
    def _add_signal_to_history(self, signal: Dict[str, Any]):
        """
        Add a signal to the history
        
        Args:
            signal: Parsed signal data
        """
        if hasattr(self, 'history_tree'):
            # Format timestamp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Format take profit targets
            tp_str = ", ".join(signal.get('take_profit', [])) if signal.get('take_profit') else "N/A"
            
            # Add to treeview
            self.history_tree.insert(
                "", 
                tk.END, 
                values=(
                    timestamp,
                    signal.get('trader', 'Unknown'),
                    signal.get('symbol', 'Unknown'),
                    signal.get('direction', 'Unknown'),
                    signal.get('entry', 'Unknown'),
                    signal.get('stop_loss', 'N/A'),
                    tp_str,
                    "Detected"
                )
            )
    
    def _update_trade_in_history(self, signal: Dict[str, Any], trade_result: Dict[str, Any]):
        """
        Update a trade in the history
        
        Args:
            signal: Parsed signal data
            trade_result: Trade execution result
        """
        # This would update the trade status in the history tree
        # Implementation depends on how trades are tracked in the history
        pass
    
    def _update_trader_list(self):
        """Update the trader list with current target traders"""
        if hasattr(self, 'trader_list'):
            # Clear the list
            self.trader_list.delete(0, tk.END)
            
            # Get current target traders
            target_traders = self.config.get_target_traders()
            
            # Add each trader to the list
            for trader in target_traders:
                self.trader_list.insert(tk.END, trader)
    
    def _update_trader_filtering(self):
        """Update trader filtering based on current settings"""
        # Get current filtering status
        enable_filtering = self.enable_filtering_var.get()
        
        # Update config
        self.config.set_traders('enable_filtering', str(enable_filtering).lower())
        self.config.save()
        
        # Get target traders
        target_traders = []
        if enable_filtering:
            target_traders = self.config.get_target_traders()
        
        # Update screen capture with new target traders
        self.screen_capture.set_target_traders(target_traders if enable_filtering else None)
        
        logger.info(f"Trader filtering {'enabled' if enable_filtering else 'disabled'} with target traders: {target_traders}")
    
    def _add_trader(self):
        """Add a new trader to the list"""
        # Get the current value from the entry
        trader = self.target_traders_var.get().strip()
        
        if not trader:
            messagebox.showwarning("Warning", "Please enter a trader handle")
            return
        
        # Parse multiple traders if comma-separated
        traders = [t.strip() for t in trader.split(',')]
        
        # Get current target traders
        current_traders = self.config.get_target_traders()
        
        # Add new traders (avoiding duplicates)
        for t in traders:
            if t and t not in current_traders:
                current_traders.append(t)
        
        # Update config
        self.config.set_target_traders(current_traders)
        self.config.save()
        
        # Clear entry
        self.target_traders_var.set("")
        
        # Update list
        self._update_trader_list()
        
        # Update screen capture if filtering is enabled
        if self.enable_filtering_var.get():
            self.screen_capture.set_target_traders(current_traders)
        
        logger.info(f"Added trader(s): {traders}")
    
    def _remove_trader(self):
        """Remove the selected trader from the list"""
        # Get the selected index
        selection = self.trader_list.curselection()
        
        if not selection:
            messagebox.showwarning("Warning", "Please select a trader to remove")
            return
        
        # Get the trader handle
        trader = self.trader_list.get(selection[0])
        
        # Get current target traders
        current_traders = self.config.get_target_traders()
        
        # Remove the trader
        if trader in current_traders:
            current_traders.remove(trader)
        
        # Update config
        self.config.set_target_traders(current_traders)
        self.config.save()
        
        # Update list
        self._update_trader_list()
        
        # Update screen capture if filtering is enabled
        if self.enable_filtering_var.get():
            self.screen_capture.set_target_traders(current_traders)
        
        logger.info(f"Removed trader: {trader}")
    
    def _apply_trader_changes(self):
        """Apply changes to trader filtering"""
        # Update trader filtering
        self._update_trader_filtering()
        
        messagebox.showinfo("Success", "Trader filtering settings applied")
        logger.info("Trader filtering settings applied")
    
    def _save_settings(self):
        """Save all settings to the configuration file"""
        try:
            # Discord settings
            self.config.set_general('scan_interval', str(self.scan_interval_var.get()))
            self.config.set_discord('click_hidden_messages', str(self.click_hidden_var.get()).lower())
            self.config.set_discord('auto_scroll', str(self.auto_scroll_var.get()).lower())
            self.config.set_discord('scroll_interval', str(self.scroll_interval_var.get()))
            self.config.set_discord('monitor_specific_channel', str(self.monitor_channel_var.get()).lower())
            
            # Phemex settings
            self.config.set_phemex('api_key', self.api_key_var.get())
            self.config.set_phemex('api_secret', self.api_secret_var.get())
            self.config.set_phemex('testnet', str(self.testnet_var.get()).lower())
            
            # Save configuration
            self.config.save()
            
            # Update screen capture with new settings
            self.screen_capture.scan_interval = float(self.scan_interval_var.get())
            self.screen_capture.click_hidden_messages = self.click_hidden_var.get()
            self.screen_capture.auto_scroll = self.auto_scroll_var.get()
            self.screen_capture.scroll_interval = float(self.scroll_interval_var.get())
            self.screen_capture.monitor_specific_channel = self.monitor_channel_var.get()
            
            # Update trading client with new settings
            self.trading_client.api_key = self.api_key_var.get()
            self.trading_client.api_secret = self.api_secret_var.get()
            self.trading_client.testnet = self.testnet_var.get()
            
            messagebox.showinfo("Success", "Settings saved successfully")
            logger.info("Settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            logger.error(f"Failed to save settings: {e}", exc_info=True)
    
    def _save_trading_params(self):
        """Save trading parameters to the configuration file"""
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
            
            # Update trading client with new settings
            if hasattr(self.trading_client, 'update_trading_params'):
                self.trading_client.update_trading_params(
                    amount_per_trade=float(self.amount_per_trade_var.get()),
                    max_position_size=float(self.max_position_var.get()),
                    stop_loss_percentage=float(self.stop_loss_pct_var.get()),
                    take_profit_percentage=float(self.take_profit_pct_var.get()),
                    default_leverage=int(self.leverage_var.get()),
                    enable_stop_loss=self.stop_loss_var.get(),
                    enable_take_profit=self.take_profit_var.get()
                )
            
            # Update status indicators to reflect any changes
            self._update_status_indicators()
            
            messagebox.showinfo("Success", "Trading parameters saved successfully")
            logger.info("Trading parameters saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save trading parameters: {e}")
            logger.error(f"Failed to save trading parameters: {e}", exc_info=True)
    
    def _clear_history(self):
        """Clear the trade history"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the trade history?"):
            self.history_tree.delete(*self.history_tree.get_children())
            logger.info("Trade history cleared")
    
    def _export_history(self):
        """Export the trade history to a file"""
        # This would implement exporting the history to a CSV file
        messagebox.showinfo("Info", "Export functionality not implemented yet")
    
    def _refresh_history(self):
        """Refresh the trade history"""
        # This would normally query a database or log file
        # For now, just a placeholder
        logger.info("Trade history refreshed")
    
    def _clear_logs(self):
        """Clear the logs"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the logs?"):
            self.logs_text.config(state=tk.NORMAL)
            self.logs_text.delete(1.0, tk.END)
            self.logs_text.config(state=tk.DISABLED)
            logger.info("Logs cleared")
    
    def _export_logs(self):
        """Export the logs to a file"""
        # This would implement exporting the logs to a file
        messagebox.showinfo("Info", "Export functionality not implemented yet")
    
    def _on_close(self):
        """Handle window close event"""
        if messagebox.askyesno("Confirm", "Are you sure you want to exit?"):
            # Stop all threads
            self.running = False
            self.screen_capture.stop()
            
            # Destroy the window
            if self.root:
                self.root.destroy()
            
            logger.info("Application closed")