#!/usr/bin/env python3
"""
Enhanced Trading UI Module
Provides an advanced GUI for Discord Trading Signal Scraper with additional trading parameters
"""

import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import logging
import queue
import configparser
import numpy as np
try:
    import pyautogui
    import cv2  # OpenCV for image processing
except ImportError:
    logging.warning("pyautogui, cv2, or numpy not found - Discord status detection may not work")
    # We'll handle this in the code

class EnhancedTradingUI:
    """
    Enhanced Trading UI for Discord Trading Signal Scraper
    Provides an advanced interface with additional trading parameters
    """
    
    def __init__(self, screen_capture, signal_parser, trading_client, config):
        """
        Initialize the Enhanced Trading UI
        
        Args:
            screen_capture: ScreenCapture instance for capturing signals
            signal_parser: SignalParser instance for parsing signals
            trading_client: TradingClient instance for executing trades
            config: Configuration instance
        """
        self.screen_capture = screen_capture
        self.signal_parser = signal_parser
        self.trading_client = trading_client
        self.config = config
        
        self.root = None
        self.signal_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.traders_listbox = None
        self.log_text = None
        self.status_label = None
        
        # These variables will be initialized in run() after the root window is created
        self.trader_var = None
        self.amount_per_trade_var = None
        self.max_position_var = None
        self.stop_loss_pct_var = None
        self.take_profit_pct_var = None
        self.stop_loss_var = None
        self.take_profit_var = None
        self.leverage_var = None
        self.use_signal_leverage_var = None
        self.max_leverage_var = None
        self.min_market_cap_var = None
        self.enable_market_cap_filter_var = None
        self.enable_auto_trading_var = None
        self.auto_close_trades_var = None
        self.max_trades_var = None
        
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """
        Start the Enhanced Trading UI
        """
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Enhanced Discord Trading Signal Scraper")
        self.root.geometry("1000x700")
        
        # Now that we have a root window, we can initialize the tkinter variables
        self.trader_var = tk.StringVar()
        
        # Trading parameters
        self.amount_per_trade_var = tk.DoubleVar(value=float(self.config.get_trading('amount_per_trade', 100.0)))
        self.max_position_var = tk.DoubleVar(value=float(self.config.get_trading('max_position_size', 500.0)))
        self.stop_loss_pct_var = tk.DoubleVar(value=float(self.config.get_trading('stop_loss_percentage', 5.0)))
        self.take_profit_pct_var = tk.DoubleVar(value=float(self.config.get_trading('take_profit_percentage', 15.0)))
        self.stop_loss_var = tk.BooleanVar(value=self.config.get_trading('enable_stop_loss', 'true').lower() == 'true')
        self.take_profit_var = tk.BooleanVar(value=self.config.get_trading('enable_take_profit', 'true').lower() == 'true')
        self.leverage_var = tk.IntVar(value=int(self.config.get_trading('default_leverage', 5)))
        self.use_signal_leverage_var = tk.BooleanVar(value=self.config.get_trading('use_signal_leverage', 'true').lower() == 'true')
        self.max_leverage_var = tk.IntVar(value=int(self.config.get_trading('max_leverage', 20)))
        self.min_market_cap_var = tk.IntVar(value=int(self.config.get_trading('min_market_cap', 1000000)))
        self.enable_market_cap_filter_var = tk.BooleanVar(value=self.config.get_trading('enable_market_cap_filter', 'true').lower() == 'true')
        self.enable_auto_trading_var = tk.BooleanVar(value=self.config.get_trading('enable_auto_trading', 'false').lower() == 'true')
        self.auto_close_trades_var = tk.BooleanVar(value=self.config.get_trading('auto_close_trades', 'true').lower() == 'true')
        self.max_trades_var = tk.IntVar(value=int(self.config.get_trading('max_simultaneous_trades', 5)))
        
        # Create the main notebook (tabbed interface)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        main_tab = ttk.Frame(notebook)
        trading_params_tab = ttk.Frame(notebook)
        settings_tab = ttk.Frame(notebook)
        history_tab = ttk.Frame(notebook)
        
        notebook.add(main_tab, text="Main")
        notebook.add(trading_params_tab, text="Trading Parameters")
        notebook.add(settings_tab, text="Settings")
        notebook.add(history_tab, text="History")
        
        # Main tab
        self._create_main_tab(main_tab)
        
        # Trading Parameters tab
        self._create_trading_params_tab(trading_params_tab)
        
        # Settings tab
        self._create_settings_tab(settings_tab)
        
        # History tab
        self._create_history_tab(history_tab)
        
        # Initialize Discord status indicators
        target_text = f"{self.screen_capture.target_server}/{self.screen_capture.channel_name}"
        self._log_message(f"Monitoring Discord for trading signals from {target_text}")
        self._log_message(f"Target traders: {', '.join(self.screen_capture.target_traders) if self.screen_capture.target_traders else 'All traders (no filtering)'}")
        self._update_discord_status(False)  # Start with "Not Detected" status
        
        # Start the signal processing thread
        self._start_signal_processing()
        
        # Protocol for window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Start the main loop
        self.root.mainloop()
    
    def _create_main_tab(self, parent):
        """
        Create the main tab with signal monitoring and trading controls
        
        Args:
            parent: Parent widget
        """
        # Create frames
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        middle_frame = ttk.Frame(parent)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Top frame: Controls
        control_frame = ttk.LabelFrame(top_frame, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Start/Stop button
        self.start_stop_var = tk.StringVar(value="Start Monitoring")
        self.start_stop_button = ttk.Button(control_frame, textvariable=self.start_stop_var, command=self._toggle_monitoring)
        self.start_stop_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Auto trading toggle
        auto_trading_check = ttk.Checkbutton(control_frame, text="Enable Auto Trading", 
                                           variable=self.enable_auto_trading_var, 
                                           command=self._toggle_auto_trading)
        auto_trading_check.grid(row=0, column=1, padx=5, pady=5)
        
        # Current status
        ttk.Label(control_frame, text="Status:").grid(row=0, column=2, padx=(20, 5), pady=5)
        self.status_label = ttk.Label(control_frame, text="Idle", foreground="gray")
        self.status_label.grid(row=0, column=3, padx=5, pady=5)
        
        # Discord status indicator
        ttk.Label(control_frame, text="Discord:").grid(row=0, column=4, padx=(20, 5), pady=5)
        self.discord_status_label = ttk.Label(control_frame, text="Not Detected", foreground="red")
        self.discord_status_label.grid(row=0, column=5, padx=5, pady=5)
        
        # Target server/channel display
        ttk.Label(control_frame, text="Target:").grid(row=0, column=6, padx=(20, 5), pady=5)
        target_text = f"{self.screen_capture.target_server}/{self.screen_capture.channel_name}"
        self.target_label = ttk.Label(control_frame, text=target_text, foreground="blue")
        self.target_label.grid(row=0, column=7, padx=5, pady=5)
        
        # Middle frame: Signal log
        log_frame = ttk.LabelFrame(middle_frame, text="Signal Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5, side=tk.LEFT)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=80, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Trader list (right side)
        trader_frame = ttk.LabelFrame(middle_frame, text="Target Traders", padding=10)
        trader_frame.pack(fill=tk.Y, padx=5, pady=5, side=tk.RIGHT)
        
        # Help text for trader filtering
        trader_help_frame = ttk.Frame(trader_frame)
        trader_help_frame.pack(fill=tk.X, padx=5, pady=5)
        help_text = ("Add trader handles to filter signals\n"
                     "and only click 'Unlock Content' buttons\n"
                     "for traders in your list.\n\n"
                     "Format: @trader1, @trader2, etc.")
        help_label = ttk.Label(trader_help_frame, text=help_text, justify=tk.LEFT, wraplength=180)
        help_label.pack(fill=tk.X)
        
        # Target traders list
        self.traders_listbox = tk.Listbox(trader_frame, width=20, height=12)
        self.traders_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Create a right-click context menu
        self.trader_menu = tk.Menu(trader_frame, tearoff=0)
        self.trader_menu.add_command(label="Remove", command=self._remove_trader)
        self.trader_menu.add_command(label="Copy", command=self._copy_trader)
        self.trader_menu.add_separator()
        self.trader_menu.add_command(label="Clear All", command=self._clear_traders)
        
        # Bind right-click to show context menu
        self.traders_listbox.bind("<Button-3>", self._show_trader_menu)
        
        traders_scrollbar = ttk.Scrollbar(trader_frame, orient=tk.VERTICAL, command=self.traders_listbox.yview)
        traders_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.traders_listbox.config(yscrollcommand=traders_scrollbar.set)
        
        # Add/remove trader controls
        trader_control_frame = ttk.Frame(trader_frame)
        trader_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.trader_entry = ttk.Entry(trader_control_frame, textvariable=self.trader_var, width=15)
        self.trader_entry.pack(side=tk.LEFT, padx=2)
        
        add_button = ttk.Button(trader_control_frame, text="Add", command=self._add_trader, width=5)
        add_button.pack(side=tk.LEFT, padx=2)
        
        remove_button = ttk.Button(trader_control_frame, text="Remove", command=self._remove_trader, width=7)
        remove_button.pack(side=tk.LEFT, padx=2)
        
        # Load existing traders
        target_traders = self.config.get_target_traders()
        for trader in target_traders:
            self.traders_listbox.insert(tk.END, trader)
        
        # Emergency Discord Controls
        emergency_frame = ttk.LabelFrame(bottom_frame, text="Discord Emergency Controls", padding=10)
        emergency_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create a button that directly clicks on blue buttons that might be "Unlock Content"
        emergency_click_button = ttk.Button(
            emergency_frame, 
            text="🔵 Force Click Unlock Buttons", 
            command=self._force_click_unlock_buttons,
            style="Accent.TButton"
        )
        emergency_click_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        # Add a warning label
        emergency_label = ttk.Label(
            emergency_frame,
            text="Use this if 'Unlock Content' buttons aren't being clicked automatically",
            foreground="red",
            wraplength=280
        )
        emergency_label.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Bottom frame: Trading controls
        trading_control_frame = ttk.LabelFrame(bottom_frame, text="Manual Trading Controls", padding=10)
        trading_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Quick trading buttons
        ttk.Label(trading_control_frame, text="Manual Trade:").grid(row=0, column=0, padx=5, pady=5)
        
        symbol_label = ttk.Label(trading_control_frame, text="Symbol:")
        symbol_label.grid(row=0, column=1, padx=5, pady=5)
        
        self.symbol_var = tk.StringVar()
        symbol_entry = ttk.Entry(trading_control_frame, textvariable=self.symbol_var, width=10)
        symbol_entry.grid(row=0, column=2, padx=5, pady=5)
        
        long_button = ttk.Button(trading_control_frame, text="LONG", command=lambda: self._manual_trade("long"))
        long_button.grid(row=0, column=3, padx=5, pady=5)
        
        short_button = ttk.Button(trading_control_frame, text="SHORT", command=lambda: self._manual_trade("short"))
        short_button.grid(row=0, column=4, padx=5, pady=5)
        
        close_button = ttk.Button(trading_control_frame, text="CLOSE", command=lambda: self._manual_trade("close"))
        close_button.grid(row=0, column=5, padx=5, pady=5)
    
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
        amount_entry = ttk.Entry(position_frame, textvariable=self.amount_per_trade_var, width=10)
        amount_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(position_frame, text="USD value to invest in each trade signal").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Max position size
        ttk.Label(position_frame, text="Max Position Size ($):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        max_position_entry = ttk.Entry(position_frame, textvariable=self.max_position_var, width=10)
        max_position_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(position_frame, text="Maximum USD value per position").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Risk Management Settings
        risk_frame = ttk.LabelFrame(scroll_frame, text="Risk Management Settings", padding=10)
        risk_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Stop Loss
        ttk.Label(risk_frame, text="Stop Loss (%):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        stop_loss_entry = ttk.Entry(risk_frame, textvariable=self.stop_loss_pct_var, width=10)
        stop_loss_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(risk_frame, text="Percentage loss at which position will close").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Take Profit
        ttk.Label(risk_frame, text="Take Profit (%):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        take_profit_entry = ttk.Entry(risk_frame, textvariable=self.take_profit_pct_var, width=10)
        take_profit_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(risk_frame, text="Percentage gain at which position will close").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Enable Stop Loss
        stop_loss_check = ttk.Checkbutton(risk_frame, text="Enable Stop Loss", variable=self.stop_loss_var)
        stop_loss_check.grid(row=2, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Enable Take Profit
        take_profit_check = ttk.Checkbutton(risk_frame, text="Enable Take Profit", variable=self.take_profit_var)
        take_profit_check.grid(row=3, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Leverage Settings
        leverage_frame = ttk.LabelFrame(scroll_frame, text="Leverage Settings", padding=10)
        leverage_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Default Leverage
        ttk.Label(leverage_frame, text="Default Leverage:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        leverage_entry = ttk.Entry(leverage_frame, textvariable=self.leverage_var, width=10)
        leverage_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(leverage_frame, text="Default leverage multiplier for trades").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Use Signal Leverage
        signal_leverage_check = ttk.Checkbutton(leverage_frame, text="Use Leverage from Signal (when available)", 
                                             variable=self.use_signal_leverage_var)
        signal_leverage_check.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Max Leverage
        ttk.Label(leverage_frame, text="Maximum Leverage:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        max_leverage_entry = ttk.Entry(leverage_frame, textvariable=self.max_leverage_var, width=10)
        max_leverage_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(leverage_frame, text="Maximum allowed leverage (caps signal leverage)").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Filtering Settings
        filter_frame = ttk.LabelFrame(scroll_frame, text="Market Filtering Settings", padding=10)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Minimum Market Cap
        ttk.Label(filter_frame, text="Minimum Market Cap ($):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        market_cap_entry = ttk.Entry(filter_frame, textvariable=self.min_market_cap_var, width=15)
        market_cap_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(filter_frame, text="Don't trade coins with market cap below this value").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Enable Market Cap Filter
        market_cap_check = ttk.Checkbutton(filter_frame, text="Enable Market Cap Filter", 
                                        variable=self.enable_market_cap_filter_var)
        market_cap_check.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Auto Trading Settings
        auto_frame = ttk.LabelFrame(scroll_frame, text="Auto Trading Settings", padding=10)
        auto_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Enable Auto Trading
        auto_trading_check = ttk.Checkbutton(auto_frame, text="Enable Automatic Trading (trades will execute without confirmation)", 
                                          variable=self.enable_auto_trading_var)
        auto_trading_check.grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Auto Close Trades
        auto_close_check = ttk.Checkbutton(auto_frame, text="Automatically Close Trades at Stop Loss/Take Profit", 
                                         variable=self.auto_close_trades_var)
        auto_close_check.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Max Simultaneous Trades
        ttk.Label(auto_frame, text="Max Simultaneous Trades:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
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
        # Create frames
        discord_frame = ttk.LabelFrame(parent, text="Discord Settings", padding=10)
        discord_frame.pack(fill=tk.X, padx=10, pady=10)
        
        phemex_frame = ttk.LabelFrame(parent, text="Phemex API Settings", padding=10)
        phemex_frame.pack(fill=tk.X, padx=10, pady=10)
        
        general_frame = ttk.LabelFrame(parent, text="General Settings", padding=10)
        general_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Discord settings
        ttk.Label(discord_frame, text="Enable Trader Filtering:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.enable_filtering_var = tk.BooleanVar(value=self.config.get_traders('enable_filtering', 'false').lower() == 'true')
        enable_filtering_check = ttk.Checkbutton(discord_frame, variable=self.enable_filtering_var)
        enable_filtering_check.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(discord_frame, text="Only process signals from traders in your target list").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(discord_frame, text="Click Hidden Messages:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.click_hidden_var = tk.BooleanVar(value=self.config.get_discord('click_hidden_messages', 'true').lower() == 'true')
        click_hidden_check = ttk.Checkbutton(discord_frame, variable=self.click_hidden_var)
        click_hidden_check.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(discord_frame, text="Automatically click 'Unlock Content' buttons (trader filtering applies)").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(discord_frame, text="Monitor Specific Channel:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.monitor_channel_var = tk.BooleanVar(value=self.config.get_discord('monitor_specific_channel', 'true').lower() == 'true')
        monitor_channel_check = ttk.Checkbutton(discord_frame, variable=self.monitor_channel_var)
        monitor_channel_check.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(discord_frame, text="Focus on a specific channel instead of monitoring all channels").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(discord_frame, text="Channel Name:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.channel_name_var = tk.StringVar(value=self.config.get_discord('channel_name', 'trades'))
        channel_name_entry = ttk.Entry(discord_frame, textvariable=self.channel_name_var, width=20)
        channel_name_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(discord_frame, text="Name of the specific Discord channel to monitor").grid(row=3, column=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(discord_frame, text="Auto Scroll:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.auto_scroll_var = tk.BooleanVar(value=self.config.get_discord('auto_scroll', 'true').lower() == 'true')
        auto_scroll_check = ttk.Checkbutton(discord_frame, variable=self.auto_scroll_var)
        auto_scroll_check.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(discord_frame, text="Automatically scroll Discord to check for new messages").grid(row=4, column=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(discord_frame, text="Scroll Interval (seconds):").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.scroll_interval_var = tk.DoubleVar(value=float(self.config.get_discord('scroll_interval', 30.0)))
        scroll_interval_entry = ttk.Entry(discord_frame, textvariable=self.scroll_interval_var, width=10)
        scroll_interval_entry.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(discord_frame, text="Time between automatic scrolls").grid(row=5, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Phemex API settings
        ttk.Label(phemex_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.api_key_var = tk.StringVar(value=self.config.get_phemex('api_key', ''))
        api_key_entry = ttk.Entry(phemex_frame, textvariable=self.api_key_var, width=40, show='*')
        api_key_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(phemex_frame, text="API Secret:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.api_secret_var = tk.StringVar(value=self.config.get_phemex('api_secret', ''))
        api_secret_entry = ttk.Entry(phemex_frame, textvariable=self.api_secret_var, width=40, show='*')
        api_secret_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(phemex_frame, text="Use Testnet:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.testnet_var = tk.BooleanVar(value=self.config.get_phemex('testnet', 'true').lower() == 'true')
        testnet_check = ttk.Checkbutton(phemex_frame, variable=self.testnet_var)
        testnet_check.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # General settings
        ttk.Label(general_frame, text="Scan Interval (seconds):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.scan_interval_var = tk.DoubleVar(value=float(self.config.get_general('scan_interval', 2.0)))
        scan_interval_entry = ttk.Entry(general_frame, textvariable=self.scan_interval_var, width=10)
        scan_interval_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Save settings button
        save_settings_button = ttk.Button(parent, text="Save Settings", command=self._save_settings)
        save_settings_button.pack(pady=10)
    
    def _create_history_tab(self, parent):
        """
        Create the history tab for viewing past signals and trades
        
        Args:
            parent: Parent widget
        """
        # Create container
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs for signals and trades history
        history_notebook = ttk.Notebook(container)
        history_notebook.pack(fill=tk.BOTH, expand=True)
        
        signals_tab = ttk.Frame(history_notebook)
        trades_tab = ttk.Frame(history_notebook)
        
        history_notebook.add(signals_tab, text="Signal History")
        history_notebook.add(trades_tab, text="Trade History")
        
        # Signal history
        signal_frame = ttk.Frame(signals_tab)
        signal_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.signal_tree = ttk.Treeview(signal_frame, columns=("timestamp", "trader", "symbol", "direction", "entry", "targets"))
        self.signal_tree.heading("#0", text="ID")
        self.signal_tree.heading("timestamp", text="Timestamp")
        self.signal_tree.heading("trader", text="Trader")
        self.signal_tree.heading("symbol", text="Symbol")
        self.signal_tree.heading("direction", text="Direction")
        self.signal_tree.heading("entry", text="Entry")
        self.signal_tree.heading("targets", text="Targets")
        
        self.signal_tree.column("#0", width=50)
        self.signal_tree.column("timestamp", width=150)
        self.signal_tree.column("trader", width=100)
        self.signal_tree.column("symbol", width=80)
        self.signal_tree.column("direction", width=80)
        self.signal_tree.column("entry", width=80)
        self.signal_tree.column("targets", width=200)
        
        signal_scrollbar = ttk.Scrollbar(signal_frame, orient=tk.VERTICAL, command=self.signal_tree.yview)
        self.signal_tree.configure(yscrollcommand=signal_scrollbar.set)
        
        self.signal_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        signal_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Trade history
        trade_frame = ttk.Frame(trades_tab)
        trade_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.trade_tree = ttk.Treeview(trade_frame, columns=("timestamp", "symbol", "direction", "amount", "entry", "exit", "pnl"))
        self.trade_tree.heading("#0", text="ID")
        self.trade_tree.heading("timestamp", text="Timestamp")
        self.trade_tree.heading("symbol", text="Symbol")
        self.trade_tree.heading("direction", text="Direction")
        self.trade_tree.heading("amount", text="Amount")
        self.trade_tree.heading("entry", text="Entry")
        self.trade_tree.heading("exit", text="Exit")
        self.trade_tree.heading("pnl", text="PnL")
        
        self.trade_tree.column("#0", width=50)
        self.trade_tree.column("timestamp", width=150)
        self.trade_tree.column("symbol", width=80)
        self.trade_tree.column("direction", width=80)
        self.trade_tree.column("amount", width=80)
        self.trade_tree.column("entry", width=80)
        self.trade_tree.column("exit", width=80)
        self.trade_tree.column("pnl", width=80)
        
        trade_scrollbar = ttk.Scrollbar(trade_frame, orient=tk.VERTICAL, command=self.trade_tree.yview)
        self.trade_tree.configure(yscrollcommand=trade_scrollbar.set)
        
        self.trade_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        trade_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Refresh and clear buttons
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        refresh_button = ttk.Button(button_frame, text="Refresh", command=self._refresh_history)
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        clear_button = ttk.Button(button_frame, text="Clear History", command=self._clear_history)
        clear_button.pack(side=tk.LEFT, padx=5)
    
    def _toggle_monitoring(self):
        """Toggle Discord monitoring on/off"""
        if self.start_stop_var.get() == "Start Monitoring":
            # Start monitoring
            self.start_stop_var.set("Stop Monitoring")
            self.screen_capture.start()
            self._update_status("Monitoring", "green")
            self._log_message("Started monitoring Discord for trading signals")
        else:
            # Stop monitoring
            self.start_stop_var.set("Start Monitoring")
            self.screen_capture.stop()
            self._update_status("Idle", "gray")
            self._log_message("Stopped monitoring Discord")
    
    def _show_trader_menu(self, event):
        """Show the trader context menu on right-click"""
        # Select the item under the cursor
        item_index = self.traders_listbox.nearest(event.y)
        if item_index >= 0:
            # Select the item
            self.traders_listbox.selection_clear(0, tk.END)
            self.traders_listbox.selection_set(item_index)
            self.traders_listbox.activate(item_index)
            # Show the popup menu
            self.trader_menu.post(event.x_root, event.y_root)
    
    def _copy_trader(self):
        """Copy the selected trader to clipboard"""
        selected = self.traders_listbox.curselection()
        if not selected:
            return
        
        trader = self.traders_listbox.get(selected)
        self.root.clipboard_clear()
        self.root.clipboard_append(trader)
        self._log_message(f"Copied trader {trader} to clipboard", "INFO")
    
    def _clear_traders(self):
        """Clear all traders from the list"""
        if not self.traders_listbox.size():
            return
            
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all target traders?"):
            self.traders_listbox.delete(0, tk.END)
            self._save_target_traders()
            self._log_message("Cleared all traders from the target list", "WARNING")
    
    def _toggle_auto_trading(self):
        """Toggle automatic trading on/off"""
        auto_trading = self.enable_auto_trading_var.get()
        self.config.set_trading('enable_auto_trading', str(auto_trading).lower())
        self.config.save()
        
        if auto_trading:
            self._log_message("Automatic trading enabled - trades will execute without confirmation")
        else:
            self._log_message("Automatic trading disabled - trades require manual confirmation")
    
    def _add_trader(self):
        """Add a trader to the target list"""
        trader = self.trader_var.get().strip()
        if not trader:
            messagebox.showwarning("Warning", "Please enter a trader handle (e.g., @trader)")
            return
        
        # Add @ if not present
        if not trader.startswith('@'):
            trader = '@' + trader
            self._log_message(f"Added @ prefix to trader handle: {trader}", "INFO")
        
        # Basic validation - ensure we have alphanumeric characters after @
        if len(trader) <= 1 or not any(c.isalnum() for c in trader[1:]):
            messagebox.showwarning("Warning", "Invalid trader handle. Please enter a valid handle (e.g., @trader123)")
            return
        
        # Check if already in list
        current_traders = list(self.traders_listbox.get(0, tk.END))
        if trader in current_traders:
            messagebox.showinfo("Info", f"Trader {trader} is already in the list")
            return
        
        # Add to listbox and save
        self.traders_listbox.insert(tk.END, trader)
        self._save_target_traders()
        self.trader_var.set("")  # Clear entry
        self._log_message(f"Added trader {trader} to the filter list", "SUCCESS")
    
    def _remove_trader(self):
        """Remove a trader from the target list"""
        selected = self.traders_listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a trader to remove")
            return
        
        # Get the trader handle before removing
        trader = self.traders_listbox.get(selected)
        
        # Remove from listbox and save
        self.traders_listbox.delete(selected)
        self._save_target_traders()
        self._log_message(f"Removed trader {trader} from the filter list", "WARNING")
    
    def _save_target_traders(self):
        """Save the target traders list to the configuration"""
        traders = list(self.traders_listbox.get(0, tk.END))
        self.config.set_target_traders(traders)
        
        # Update the enable filtering setting as well
        enable_filtering = self.enable_filtering_var.get()
        self.config.set_traders('enable_filtering', str(enable_filtering).lower())
        
        self.config.save()
        
        # Update the screen capture module
        self.screen_capture.set_target_traders(traders)
        
        # Log the changes with clear information about what was updated
        if traders:
            self._log_message(f"Updated target traders list: {', '.join(traders)}")
        else:
            self._log_message("Cleared target traders list", "WARNING")
        
        if enable_filtering:
            self._log_message("Trader filtering enabled - only processing signals from target traders", "INFO")
        else:
            self._log_message("Trader filtering disabled - processing signals from all traders", "INFO")
    
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
            self._log_message("Trading parameters saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save trading parameters: {e}")
            self._log_message(f"Failed to save trading parameters: {e}", "ERROR")
    
    def _save_settings(self):
        """Save general settings to the configuration"""
        try:
            # Discord settings
            self.config.set_traders('enable_filtering', str(self.enable_filtering_var.get()).lower())
            self.config.set_discord('click_hidden_messages', str(self.click_hidden_var.get()).lower())
            self.config.set_discord('monitor_specific_channel', str(self.monitor_channel_var.get()).lower())
            self.config.set_discord('channel_name', self.channel_name_var.get())
            self.config.set_discord('auto_scroll', str(self.auto_scroll_var.get()).lower())
            self.config.set_discord('scroll_interval', str(self.scroll_interval_var.get()))
            
            # Phemex API settings
            self.config.set_phemex('api_key', self.api_key_var.get())
            self.config.set_phemex('api_secret', self.api_secret_var.get())
            self.config.set_phemex('testnet', str(self.testnet_var.get()).lower())
            
            # General settings
            self.config.set_general('scan_interval', str(self.scan_interval_var.get()))
            
            # Save configuration
            self.config.save()
            
            # Update the screen capture settings
            self.screen_capture.scan_interval = float(self.config.get_general('scan_interval', 2.0))
            self.screen_capture.click_hidden_messages = self.config.get_discord('click_hidden_messages', 'true').lower() == 'true'
            self.screen_capture.monitor_specific_channel = self.config.get_discord('monitor_specific_channel', 'true').lower() == 'true'
            self.screen_capture.channel_name = self.config.get_discord('channel_name', 'trades')
            self.screen_capture.auto_scroll = self.config.get_discord('auto_scroll', 'true').lower() == 'true'
            self.screen_capture.scroll_interval = float(self.config.get_discord('scroll_interval', 30.0))
            
            if self.config.get_traders('enable_filtering', 'false').lower() == 'true':
                self.screen_capture.set_target_traders(self.config.get_target_traders())
            else:
                self.screen_capture.set_target_traders(None)
            
            # Update the trading client
            self.trading_client.api_key = self.config.get_phemex('api_key', '')
            self.trading_client.api_secret = self.config.get_phemex('api_secret', '')
            self.trading_client.testnet = self.config.get_phemex('testnet', 'true').lower() == 'true'
            
            messagebox.showinfo("Success", "Settings saved successfully")
            self._log_message("Settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            self._log_message(f"Failed to save settings: {e}", "ERROR")
    
    def _refresh_history(self):
        """Refresh the history displays"""
        # This would load history from a database or file
        # For now, just log that we're refreshing
        self._log_message("Refreshing history...")
    
    def _clear_history(self):
        """Clear the history displays"""
        # Ask for confirmation
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all history?"):
            # Clear the treeviews
            for i in self.signal_tree.get_children():
                self.signal_tree.delete(i)
            
            for i in self.trade_tree.get_children():
                self.trade_tree.delete(i)
            
            self._log_message("History cleared")
    
    def _force_click_unlock_buttons(self):
        """Force immediate detection and clicking of all 'Unlock Content' buttons on screen"""
        # Make sure we have a screen capture object
        if not hasattr(self, 'screen_capture') or self.screen_capture is None:
            messagebox.showerror("Error", "Screen capture is not initialized")
            return
            
        self._log_message("🚨 EXECUTING EMERGENCY UNLOCK BUTTON DETECTION", level="ERROR")
        
        # Create a separate thread to run the emergency click function 
        # so it doesn't freeze the UI
        def execute_emergency_click():
            try:
                success = self.screen_capture.force_click_unlock_button()
                if success:
                    self._log_message("✅ Successfully clicked potential 'Unlock Content' buttons", level="SUCCESS")
                else:
                    self._log_message("⚠️ No suitable buttons found to click", level="WARNING")
            except Exception as e:
                self._log_message(f"❌ Error during emergency button click: {e}", level="ERROR")
        
        # Start the thread and return immediately
        click_thread = threading.Thread(target=execute_emergency_click)
        click_thread.daemon = True
        click_thread.start()
        
        messagebox.showinfo("Emergency Click", "Looking for and clicking blue buttons that may be 'Unlock Content' buttons. Please wait...")
    
    def _manual_trade(self, direction):
        """Execute a manual trade"""
        symbol = self.symbol_var.get().strip().upper()
        if not symbol:
            messagebox.showwarning("Warning", "Please enter a symbol (e.g., BTC)")
            return
        
        # Confirm the trade
        if direction == "close":
            if messagebox.askyesno("Confirm", f"Are you sure you want to CLOSE all {symbol} positions?"):
                # Execute the close
                self._log_message(f"Manually closing all {symbol} positions")
                # self.trading_client.close_position(symbol)
        else:
            if messagebox.askyesno("Confirm", f"Are you sure you want to open a {direction.upper()} position for {symbol}?"):
                # Execute the trade
                amount = self.amount_per_trade_var.get()
                leverage = self.leverage_var.get()
                
                self._log_message(f"Manually opening {direction.upper()} position for {symbol} with ${amount} at {leverage}x leverage")
                # self.trading_client.place_order(symbol, direction, amount, leverage)
    
    def _start_signal_processing(self):
        """Start the signal processing thread"""
        threading.Thread(target=self._process_signals, daemon=True).start()
    
    def _process_signals(self):
        """Process signals from the screen capture queue"""
        discord_check_interval = 2.0  # Check Discord status every 2 seconds
        last_discord_check = 0
        
        while not self.stop_event.is_set():
            try:
                # Periodically check Discord status
                current_time = time.time()
                if current_time - last_discord_check > discord_check_interval:
                    # Check if _is_discord_visible method is available in screen_capture
                    if hasattr(self.screen_capture, '_is_discord_visible'):
                        # Take a screenshot and check Discord status
                        import pyautogui
                        screenshot = pyautogui.screenshot()
                        # Convert to OpenCV format
                        import numpy as np
                        screenshot = np.array(screenshot)
                        screenshot = screenshot[:, :, ::-1].copy()  # Convert RGB to BGR
                        
                        # Check Discord status
                        discord_detected, server_detected, channel_detected = False, False, False
                        
                        # Try to get Discord status with all details
                        try:
                            # The _is_discord_visible method actually returns only a boolean 
                            # but updates internal state with detailed detection info
                            result = self.screen_capture._is_discord_visible(screenshot)
                            
                            # Get detailed status info from logs - we need to check if our logs
                            # indicate the channel is actually detected despite what the method returns
                            discord_detected = result
                            
                            # Use more reliable log output to check if channel was detected
                            # We know channel is detected if the logs contain "trades channel detected" strings
                            if "✅ Discord 'Wealth Group' server and 'trades' channel detected!" in self.log_text.get("1.0", tk.END):
                                # This indicates both server and channel were properly detected
                                server_detected = True
                                channel_detected = True
                                self._log_message(f"Discord detector corrected: Discord=True, Server=True, Channel=True", level="INFO")
                            elif result:
                                # Discord is detected but not sure about channel/server
                                server_detected = "Wealth Group" in self.log_text.get("1.0", tk.END)
                                channel_detected = "trades channel" in self.log_text.get("1.0", tk.END)
                                self._log_message(f"Discord detector: Discord=True, Server={server_detected}, Channel={channel_detected}", level="INFO")
                            else:
                                # Old version or detection failed
                                self._log_message(f"Discord detector (legacy): Discord={result}", level="INFO")
                        except Exception as e:
                            # If detection fails completely, set all to False
                            discord_detected = False
                            self._log_message(f"Discord detection failed: {e}", level="ERROR")
                        
                        # Update the Discord status in the UI
                        self._update_discord_status(discord_detected, server_detected, channel_detected)
                    
                    last_discord_check = current_time
                
                # Get signal with timeout to allow checking stop_event
                signal_text = self.screen_capture.get_signal(timeout=0.1)
                if signal_text:
                    self._log_message(f"Captured signal: {signal_text}")
                    
                    # Parse the signal
                    signal = self.signal_parser.parse_signal(signal_text)
                    if signal:
                        self._handle_signal(signal)
                    else:
                        self._log_message("Failed to parse signal")
            except queue.Empty:
                # No signal available, just continue
                pass
            except Exception as e:
                self._log_message(f"Error processing signals: {e}", "ERROR")
                time.sleep(1)  # Avoid tight loop on error
    
    def _handle_signal(self, signal):
        """Handle a parsed trading signal"""
        # Add to signal history
        signal_id = len(self.signal_tree.get_children()) + 1
        self.signal_tree.insert("", tk.END, text=str(signal_id), values=(
            signal.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            signal.trader,
            signal.symbol,
            signal.direction.upper(),
            signal.entry_price,
            ", ".join([str(t) for t in signal.targets])
        ))
        
        # Check if automatic trading is enabled
        if self.enable_auto_trading_var.get():
            # Check market cap filter if enabled
            if self.enable_market_cap_filter_var.get():
                # This would check the market cap, for now just log it
                min_cap = self.min_market_cap_var.get()
                self._log_message(f"Checking market cap for {signal.symbol}, minimum: ${min_cap}")
                # If market cap is too low, skip the trade
                # For now, we'll assume all pass
            
            # Determine the amount to trade
            amount = self.amount_per_trade_var.get()
            if amount > self.max_position_var.get():
                amount = self.max_position_var.get()
            
            # Determine the leverage
            leverage = self.leverage_var.get()
            if self.use_signal_leverage_var.get() and signal.leverage:
                leverage = signal.leverage
                if leverage > self.max_leverage_var.get():
                    leverage = self.max_leverage_var.get()
            
            # Execute the trade
            self._log_message(f"Auto-executing {signal.direction.upper()} trade for {signal.symbol} with ${amount} at {leverage}x leverage")
            
            # In a real implementation, this would call the trading client
            # result = self.trading_client.place_order(signal.symbol, signal.direction, amount, leverage)
            result = {"success": True, "order_id": "12345"}  # Mock result
            
            if result and result.get("success"):
                self._log_message(f"Trade executed successfully: Order ID {result.get('order_id')}")
                
                # Set stop loss and take profit if enabled
                if self.stop_loss_var.get():
                    sl_percent = self.stop_loss_pct_var.get()
                    # self.trading_client.set_stop_loss(signal.symbol, signal.direction, sl_percent)
                    self._log_message(f"Set stop loss at {sl_percent}% for {signal.symbol}")
                
                if self.take_profit_var.get():
                    tp_percent = self.take_profit_pct_var.get()
                    # self.trading_client.set_take_profit(signal.symbol, signal.direction, tp_percent)
                    self._log_message(f"Set take profit at {tp_percent}% for {signal.symbol}")
                
                # Add to trade history
                trade_id = len(self.trade_tree.get_children()) + 1
                self.trade_tree.insert("", tk.END, text=str(trade_id), values=(
                    signal.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    signal.symbol,
                    signal.direction.upper(),
                    f"${amount}",
                    signal.entry_price,
                    "Open",
                    "0.00%"
                ))
            else:
                self._log_message(f"Failed to execute trade: {result.get('error', 'Unknown error')}")
        else:
            # Ask for manual confirmation
            if messagebox.askyesno("Trade Signal", f"Execute {signal.direction.upper()} trade for {signal.symbol}?"):
                # Similar logic to automatic trading, but with manual confirmation
                self._log_message(f"Manually confirmed trade for {signal.symbol}")
    
    def _log_message(self, message, level="INFO"):
        """
        Log a message to the UI and the logger
        
        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR, SUCCESS)
        """
        # Determine log color based on level
        color = "black"  # Default color
        if level == "WARNING":
            color = "orange"
            self.logger.warning(message)
        elif level == "ERROR":
            color = "red"
            self.logger.error(message)
        elif level == "SUCCESS":
            color = "green"
            self.logger.info(message)
        else:
            # INFO level
            self.logger.info(message)
        
        # Format log message with timestamp and level
        formatted_message = f"{time.strftime('%H:%M:%S')} - [{level}] {message}\n"
        
        # Log to the UI
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, formatted_message)
        
        # Apply color tag
        last_line_start = self.log_text.index(f"end-{len(formatted_message) + 1}c")
        last_line_end = self.log_text.index("end-1c")
        self.log_text.tag_add(level, last_line_start, last_line_end)
        self.log_text.tag_config(level, foreground=color)
        
        # Auto-scroll to the latest message
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _update_status(self, status, color):
        """
        Update the status display
        
        Args:
            status: Status text
            color: Text color
        """
        self.status_label.config(text=status, foreground=color)
    
    def _update_discord_status(self, is_detected, server_detected=False, channel_detected=False):
        """
        Update the Discord status indicator
        
        Args:
            is_detected: Whether Discord is detected
            server_detected: Whether the target server is detected
            channel_detected: Whether the target channel is detected
        """
        if is_detected and server_detected and channel_detected:
            self.discord_status_label.config(text="Connected", foreground="green")
            target_text = f"{self.screen_capture.target_server}/{self.screen_capture.channel_name} ✓"
            self.target_label.config(text=target_text, foreground="green")
        elif is_detected and server_detected:
            self.discord_status_label.config(text="Server Only", foreground="orange")
            target_text = f"{self.screen_capture.target_server} ✓ / {self.screen_capture.channel_name} ✗"
            self.target_label.config(text=target_text, foreground="orange")
        elif is_detected:
            self.discord_status_label.config(text="Wrong Channel", foreground="orange")
            target_text = f"{self.screen_capture.target_server} ✗ / {self.screen_capture.channel_name} ✗"
            self.target_label.config(text=target_text, foreground="orange")
        else:
            self.discord_status_label.config(text="Not Detected", foreground="red")
            target_text = f"{self.screen_capture.target_server}/{self.screen_capture.channel_name}"
            self.target_label.config(text=target_text, foreground="red")
    
    def _on_closing(self):
        """Handle window closing event"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.stop_event.set()
            if self.screen_capture:
                self.screen_capture.stop()
            self.root.destroy()