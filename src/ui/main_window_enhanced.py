"""
Enhanced UI Main Window Module for Discord Trading Signal Scraper
Provides the main user interface with trader filtering capabilities
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

class MainWindow:
    """
    Enhanced main application window providing user interface with trader filtering
    """
    
    def __init__(self, screen_capture: ScreenCapture, signal_parser: SignalParser, 
                 trading_client: PhemexClient, config: Config):
        """
        Initialize the main window
        
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
        
        logger.info("Enhanced main window initialized")
    
    def run(self):
        """Start the application UI"""
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Discord Trading Signal Scraper")
        self.root.geometry("800x600")
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
        
        # Settings tab
        settings_tab = ttk.Frame(tab_control)
        tab_control.add(settings_tab, text="Settings")
        self._create_settings_tab(settings_tab)
        
        # Trader Filtering tab (new)
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
        
        # Create frame for Trading settings
        trading_frame = ttk.LabelFrame(parent, text="Trading Settings", padding=10)
        trading_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Max position size
        ttk.Label(trading_frame, text="Max Position Size (USD):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.max_position_var = tk.DoubleVar(value=float(self.config.get_trading('max_position_size', 100.0)))
        max_position_entry = ttk.Entry(trading_frame, textvariable=self.max_position_var, width=10)
        max_position_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Default leverage
        ttk.Label(trading_frame, text="Default Leverage:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.leverage_var = tk.IntVar(value=int(self.config.get_trading('default_leverage', 5)))
        leverage_entry = ttk.Entry(trading_frame, textvariable=self.leverage_var, width=10)
        leverage_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Enable stop loss
        self.stop_loss_var = tk.BooleanVar(value=self.config.get_trading('enable_stop_loss', 'true').lower() == 'true')
        stop_loss_check = ttk.Checkbutton(trading_frame, text="Enable Stop Loss", variable=self.stop_loss_var)
        stop_loss_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        # Enable take profit
        self.take_profit_var = tk.BooleanVar(value=self.config.get_trading('enable_take_profit', 'true').lower() == 'true')
        take_profit_check = ttk.Checkbutton(trading_frame, text="Enable Take Profit", variable=self.take_profit_var)
        take_profit_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
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
        
        # Define column widths
        self.history_tree.column("timestamp", width=150)
        self.history_tree.column("trader", width=100)
        self.history_tree.column("symbol", width=80)
        self.history_tree.column("direction", width=80)
        self.history_tree.column("entry", width=80)
        self.history_tree.column("sl", width=80)
        self.history_tree.column("tp", width=80)
        self.history_tree.column("status", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Refresh button
        refresh_button = ttk.Button(parent, text="Refresh", command=self._refresh_history)
        refresh_button.pack(pady=10)
    
    def _create_logs_tab(self, parent):
        """
        Create the logs tab
        
        Args:
            parent: Parent widget
        """
        # Create frame for logs
        logs_frame = ttk.Frame(parent, padding=10)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create text widget for logs
        self.log_text = scrolledtext.ScrolledText(logs_frame)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Add log handler to update the text widget
        self.log_handler = LogHandler(self.log_text)
        logging.getLogger().addHandler(self.log_handler)
        
        # Clear button
        clear_button = ttk.Button(parent, text="Clear Logs", command=self._clear_logs)
        clear_button.pack(pady=10)
    
    def _toggle_capture(self):
        """Toggle screen capture on/off"""
        if self.capture_status_var.get() == "Running":
            # Stop capture
            self.screen_capture.stop()
            self.capture_status_var.set("Stopped")
            self.capture_button_var.set("Start Capture")
        else:
            # Start capture
            self.screen_capture.start()
            self.capture_status_var.set("Running")
            self.capture_button_var.set("Stop Capture")
    
    def _toggle_trading(self):
        """Toggle auto trading on/off"""
        if self.trading_status_var.get() == "Enabled":
            # Disable trading
            self.trading_client.set_auto_trade(False)
            self.trading_status_var.set("Disabled")
            self.trading_button_var.set("Enable Trading")
            self.config.set_trading('auto_trade', 'false')
        else:
            # Enable trading
            self.trading_client.set_auto_trade(True)
            self.trading_status_var.set("Enabled")
            self.trading_button_var.set("Disable Trading")
            self.config.set_trading('auto_trade', 'true')
        
        # Save configuration
        self.config.save()
    
    def _toggle_filtering(self):
        """Toggle trader filtering on/off"""
        if self.filtering_status_var.get() == "Enabled":
            # Disable filtering
            self.screen_capture.set_target_traders([])
            self.filtering_status_var.set("Disabled")
            self.filtering_button_var.set("Enable Filtering")
            self.config.set_traders('enable_filtering', 'false')
        else:
            # Enable filtering
            target_traders = self.config.get_target_traders()
            if not target_traders:
                messagebox.showwarning(
                    "No Traders Specified", 
                    "No target traders specified. Please add traders in the Trader Filtering tab."
                )
                return
            
            self.screen_capture.set_target_traders(target_traders)
            self.filtering_status_var.set("Enabled")
            self.filtering_button_var.set("Disable Filtering")
            self.config.set_traders('enable_filtering', 'true')
        
        # Save configuration
        self.config.save()
    
    def _save_settings(self):
        """Save settings to config file"""
        try:
            # Update config with current values
            self.config.set_general('scan_interval', str(self.scan_interval_var.get()))
            self.config.set_discord('click_hidden_messages', str(self.click_hidden_var.get()))
            self.config.set_discord('auto_scroll', str(self.auto_scroll_var.get()))
            self.config.set_discord('scroll_interval', str(self.scroll_interval_var.get()))
            self.config.set_discord('monitor_specific_channel', str(self.monitor_channel_var.get()))
            
            self.config.set_phemex('api_key', self.api_key_var.get())
            self.config.set_phemex('api_secret', self.api_secret_var.get())
            self.config.set_phemex('testnet', str(self.testnet_var.get()))
            
            self.config.set_trading('max_position_size', str(self.max_position_var.get()))
            self.config.set_trading('default_leverage', str(self.leverage_var.get()))
            self.config.set_trading('enable_stop_loss', str(self.stop_loss_var.get()))
            self.config.set_trading('enable_take_profit', str(self.take_profit_var.get()))
            
            # Save to file
            self.config.save()
            
            # Update components with new settings
            self.screen_capture.scan_interval = float(self.config.get_general('scan_interval', 2.0))
            self.screen_capture.click_hidden_messages = self.config.get_discord('click_hidden_messages', 'true').lower() == 'true'
            self.screen_capture.auto_scroll = self.config.get_discord('auto_scroll', 'true').lower() == 'true'
            self.screen_capture.scroll_interval = float(self.config.get_discord('scroll_interval', 30.0))
            self.screen_capture.monitor_specific_channel = self.config.get_discord('monitor_specific_channel', 'true').lower() == 'true'
            
            self.trading_client.api_key = self.config.get_phemex('api_key', '')
            self.trading_client.api_secret = self.config.get_phemex('api_secret', '')
            self.trading_client.testnet = self.config.get_phemex('testnet', 'true').lower() == 'true'
            self.trading_client.max_position_size = float(self.config.get_trading('max_position_size', 100.0))
            self.trading_client.default_leverage = int(self.config.get_trading('default_leverage', 5))
            self.trading_client.enable_stop_loss = self.config.get_trading('enable_stop_loss', 'true').lower() == 'true'
            self.trading_client.enable_take_profit = self.config.get_trading('enable_take_profit', 'true').lower() == 'true'
            
            messagebox.showinfo("Settings", "Settings saved successfully")
            logger.info("Settings saved successfully")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error saving settings: {e}")
            logger.error(f"Error saving settings: {e}", exc_info=True)
    
    def _update_trader_filtering(self):
        """Update trader filtering based on checkbox"""
        is_enabled = self.enable_filtering_var.get()
        self.config.set_traders('enable_filtering', str(is_enabled))
        
        if is_enabled:
            # Update target traders from entry field
            traders_str = self.target_traders_var.get()
            if traders_str:
                traders = [t.strip() for t in traders_str.split(',')]
                self.config.set_target_traders(traders)
                self.screen_capture.set_target_traders(traders)
        else:
            # Clear target traders
            self.screen_capture.set_target_traders([])
        
        # Update status indicator
        self._update_status_indicators()
    
    def _update_trader_list(self):
        """Update trader list with current target traders"""
        # Clear list
        self.trader_list.delete(0, tk.END)
        
        # Add current target traders
        target_traders = self.config.get_target_traders()
        for trader in target_traders:
            self.trader_list.insert(tk.END, trader)
    
    def _add_trader(self):
        """Add a trader to the list"""
        # Get trader from entry field
        trader = self.target_traders_var.get().strip()
        if not trader:
            messagebox.showwarning("Invalid Input", "Please enter a trader handle")
            return
        
        # Split by commas if multiple traders are entered
        traders = [t.strip() for t in trader.split(',')]
        
        # Get current target traders
        current_traders = self.config.get_target_traders()
        
        # Add new traders
        for t in traders:
            if t and t not in current_traders:
                current_traders.append(t)
        
        # Update config and list
        self.config.set_target_traders(current_traders)
        self._update_trader_list()
        
        # Clear entry field
        self.target_traders_var.set("")
    
    def _remove_trader(self):
        """Remove selected trader from the list"""
        # Get selected trader
        selection = self.trader_list.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a trader to remove")
            return
        
        # Get trader handle
        trader = self.trader_list.get(selection[0])
        
        # Get current target traders
        current_traders = self.config.get_target_traders()
        
        # Remove trader
        if trader in current_traders:
            current_traders.remove(trader)
        
        # Update config and list
        self.config.set_target_traders(current_traders)
        self._update_trader_list()
    
    def _apply_trader_changes(self):
        """Apply trader filtering changes"""
        # Update trader filtering
        is_enabled = self.enable_filtering_var.get()
        self.config.set_traders('enable_filtering', str(is_enabled))
        
        # Get current target traders
        target_traders = self.config.get_target_traders()
        
        # Update screen capture
        if is_enabled and target_traders:
            self.screen_capture.set_target_traders(target_traders)
            self.filtering_status_var.set("Enabled")
            self.filtering_button_var.set("Disable Filtering")
        else:
            self.screen_capture.set_target_traders([])
            self.filtering_status_var.set("Disabled")
            self.filtering_button_var.set("Enable Filtering")
        
        # Save configuration
        self.config.save()
        
        messagebox.showinfo("Trader Filtering", "Trader filtering settings applied")
        logger.info("Trader filtering settings applied")
    
    def _refresh_history(self):
        """Refresh trade history"""
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Add trade history items
        for trade in self.trading_client.get_trade_history():
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(trade["timestamp"]))
            signal = trade["signal"]
            result = trade["result"]
            
            # Extract trader from signal text if available
            trader = "Unknown"
            for t in self.config.get_target_traders():
                if t in signal.raw_text:
                    trader = t
                    break
            
            self.history_tree.insert("", tk.END, values=(
                timestamp,
                trader,
                signal.symbol,
                signal.direction,
                signal.entry_price,
                signal.stop_loss,
                signal.take_profit,
                "Success" if result["success"] else "Failed"
            ))
    
    def _clear_logs(self):
        """Clear log text widget"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _process_signals(self):
        """Process signals from screen capture"""
        while self.running:
            try:
                # Get signal from queue
                signal_text = self.screen_capture.get_signal()
                
                if signal_text:
                    # Parse signal
                    signal = self.signal_parser.parse_signal(signal_text)
                    
                    if signal:
                        # Update signal text widget
                        self._update_signal_text(signal_text, signal)
                        
                        # Process signal with trading client
                        self.trading_client.process_signal(signal)
                        
                        # Refresh history
                        self._refresh_history()
            
            except Exception as e:
                logger.error(f"Error processing signal: {e}", exc_info=True)
            
            # Sleep briefly to avoid high CPU usage
            time.sleep(0.1)
    
    def _update_signal_text(self, signal_text, signal):
        """
        Update signal text widget with new signal
        
        Args:
            signal_text: Raw signal text
            signal: Parsed TradingSignal object
        """
        if self.root:
            self.signal_text.config(state=tk.NORMAL)
            self.signal_text.delete(1.0, tk.END)
            
            # Extract trader from signal text if available
            trader = "Unknown"
            for t in self.config.get_target_traders():
                if t in signal_text:
                    trader = t
                    break
            
            # Add trader information
            self.signal_text.insert(tk.END, f"Trader: {trader}\n\n")
            
            # Add raw text
            self.signal_text.insert(tk.END, "Raw Signal:\n")
            self.signal_text.insert(tk.END, signal_text)
            self.signal_text.insert(tk.END, "\n\nParsed Signal:\n")
            
            # Add parsed signal details
            self.signal_text.insert(tk.END, f"Symbol: {signal.symbol}\n")
            self.signal_text.insert(tk.END, f"Direction: {signal.direction}\n")
            self.signal_text.insert(tk.END, f"Entry Price: {signal.entry_price}\n")
            self.signal_text.insert(tk.END, f"Stop Loss: {signal.stop_loss}\n")
            self.signal_text.insert(tk.END, f"Take Profit: {signal.take_profit}\n")
            
            if signal.status:
                self.signal_text.insert(tk.END, f"Status: {signal.status}\n")
            
            if signal.timestamp:
                self.signal_text.insert(tk.END, f"Timestamp: {signal.timestamp}\n")
            
            self.signal_text.config(state=tk.DISABLED)
    
    def _update_status_indicators(self):
        """Update status indicators"""
        # Update capture status
        if self.screen_capture.running:
            self.capture_status_var.set("Running")
            self.capture_button_var.set("Stop Capture")
        else:
            self.capture_status_var.set("Stopped")
            self.capture_button_var.set("Start Capture")
        
        # Update trading status
        if self.trading_client.auto_trade:
            self.trading_status_var.set("Enabled")
            self.trading_button_var.set("Disable Trading")
        else:
            self.trading_status_var.set("Disabled")
            self.trading_button_var.set("Enable Trading")
        
        # Update filtering status
        if self.config.get_traders('enable_filtering', 'false').lower() == 'true' and self.config.get_target_traders():
            self.filtering_status_var.set("Enabled")
            self.filtering_button_var.set("Disable Filtering")
        else:
            self.filtering_status_var.set("Disabled")
            self.filtering_button_var.set("Enable Filtering")
    
    def _on_close(self):
        """Handle window close event"""
        # Stop screen capture
        self.screen_capture.stop()
        
        # Stop signal processing
        self.running = False
        if self.signal_processing_thread:
            self.signal_processing_thread.join(timeout=1.0)
        
        # Close window
        self.root.destroy()


class LogHandler(logging.Handler):
    """Custom log handler to update text widget"""
    
    def __init__(self, text_widget):
        """
        Initialize the log handler
        
        Args:
            text_widget: Tkinter text widget to update
        """
        super().__init__()
        self.text_widget = text_widget
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    def emit(self, record):
        """
        Emit a log record
        
        Args:
            record: Log record to emit
        """
        msg = self.format(record)
        
        def _update():
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.config(state=tk.DISABLED)
        
        # Schedule update on main thread
        if self.text_widget.winfo_exists():
            self.text_widget.after(0, _update)
