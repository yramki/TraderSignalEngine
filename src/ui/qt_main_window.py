"""
PyQt6-based Main Window for Discord Trading Signal Scraper
Provides a modern, macOS-optimized user interface
"""

import os
import sys
import logging
import threading
import time
from typing import Dict, Any, Optional, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton, QFrame, QGroupBox, QTextEdit,
    QSpinBox, QDoubleSpinBox, QListWidget, QSplitter, QTableWidget, QTableWidgetItem,
    QScrollArea, QFormLayout, QMessageBox, QComboBox, QSlider
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont, QPixmap

# Import application modules - update these paths as needed
from src.screen_capture_enhanced import ScreenCapture
from src.signal_parser import SignalParser
from src.trading_client import PhemexClient
from src.config_enhanced import Config

logger = logging.getLogger(__name__)

class SignalProcessingThread(QThread):
    """Thread for processing trading signals"""
    signal_detected = pyqtSignal(dict)
    
    def __init__(self, screen_capture, signal_parser, trading_client, parent=None):
        super().__init__(parent)
        self.screen_capture = screen_capture
        self.signal_parser = signal_parser
        self.trading_client = trading_client
        self.running = False
    
    def run(self):
        self.running = True
        while self.running:
            try:
                # Check for new messages in the screen capture queue
                if not self.screen_capture.message_queue.empty():
                    message = self.screen_capture.message_queue.get()
                    logger.info(f"Processing message: {message}")
                    
                    # Parse the message
                    signal = self.signal_parser.parse(message)
                    
                    if signal:
                        logger.info(f"Detected signal: {signal}")
                        self.signal_detected.emit(signal)
                        
                        # Auto trade if enabled
                        if self.trading_client.auto_trade:
                            try:
                                logger.info(f"Executing trade for signal: {signal}")
                                trade_result = self.trading_client.execute_trade(signal)
                                logger.info(f"Trade executed: {trade_result}")
                            except Exception as e:
                                logger.error(f"Error executing trade: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error in signal processing thread: {e}", exc_info=True)
            
            # Sleep to prevent high CPU usage
            time.sleep(0.1)
    
    def stop(self):
        self.running = False
        self.wait()

class QtMainWindow(QMainWindow):
    """
    PyQt6-based main application window with macOS-optimized UI
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
        super().__init__()
        
        self.screen_capture = screen_capture
        self.signal_parser = signal_parser
        self.trading_client = trading_client
        self.config = config
        
        self.signal_processing_thread = None
        
        # Initialize UI
        self._init_ui()
        
        # Update status indicators
        self._update_status_indicators()
        
        logger.info("PyQt6 main window initialized")
    
    def _init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("Discord Trading Signal Scraper (macOS)")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        main_layout = QVBoxLayout(self.central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self._create_dashboard_tab()
        self._create_settings_tab()
        self._create_trader_tab()
        self._create_history_tab()
        self._create_logs_tab()
        
        main_layout.addWidget(self.tab_widget)
    
    def _create_dashboard_tab(self):
        """Create the dashboard tab"""
        dashboard_tab = QWidget()
        layout = QVBoxLayout(dashboard_tab)
        
        # Status group
        status_group = QGroupBox("Status")
        status_layout = QFormLayout()
        
        # Status indicators
        self.capture_status_label = QLabel("Stopped")
        self.trading_status_label = QLabel("Disabled")
        self.filtering_status_label = QLabel("Disabled")
        
        status_layout.addRow(QLabel("Screen Capture:"), self.capture_status_label)
        status_layout.addRow(QLabel("Auto Trading:"), self.trading_status_label)
        status_layout.addRow(QLabel("Trader Filtering:"), self.filtering_status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Control buttons
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        self.capture_button = QPushButton("Start Capture")
        self.capture_button.clicked.connect(self._toggle_capture)
        
        self.trading_button = QPushButton("Enable Trading")
        self.trading_button.clicked.connect(self._toggle_trading)
        
        self.filtering_button = QPushButton("Enable Filtering")
        self.filtering_button.clicked.connect(self._toggle_filtering)
        
        control_layout.addWidget(self.capture_button)
        control_layout.addWidget(self.trading_button)
        control_layout.addWidget(self.filtering_button)
        control_layout.addStretch()
        
        layout.addWidget(control_frame)
        
        # Latest signal group
        signal_group = QGroupBox("Latest Signal")
        signal_layout = QVBoxLayout()
        
        self.signal_text = QTextEdit()
        self.signal_text.setReadOnly(True)
        self.signal_text.setText("No signals detected yet.")
        
        signal_layout.addWidget(self.signal_text)
        signal_group.setLayout(signal_layout)
        layout.addWidget(signal_group, 1)  # 1 = stretch factor
        
        self.tab_widget.addTab(dashboard_tab, "Dashboard")
    
    def _create_settings_tab(self):
        """Create the settings tab"""
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)
        
        # Create scroll area for settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Discord settings group
        discord_group = QGroupBox("Discord Settings")
        discord_layout = QFormLayout()
        
        # Scan interval
        self.scan_interval_spin = QDoubleSpinBox()
        self.scan_interval_spin.setRange(0.1, 10.0)
        self.scan_interval_spin.setSingleStep(0.1)
        self.scan_interval_spin.setValue(float(self.config.get_general('scan_interval', 2.0)))
        discord_layout.addRow(QLabel("Scan Interval (seconds):"), self.scan_interval_spin)
        
        # Click hidden messages
        self.click_hidden_check = QCheckBox("Click Hidden Messages")
        self.click_hidden_check.setChecked(self.config.get_discord('click_hidden_messages', 'true').lower() == 'true')
        discord_layout.addRow(self.click_hidden_check)
        
        # Auto scroll
        self.auto_scroll_check = QCheckBox("Auto Scroll")
        self.auto_scroll_check.setChecked(self.config.get_discord('auto_scroll', 'true').lower() == 'true')
        discord_layout.addRow(self.auto_scroll_check)
        
        # Scroll interval
        self.scroll_interval_spin = QDoubleSpinBox()
        self.scroll_interval_spin.setRange(5.0, 120.0)
        self.scroll_interval_spin.setSingleStep(1.0)
        self.scroll_interval_spin.setValue(float(self.config.get_discord('scroll_interval', 30.0)))
        discord_layout.addRow(QLabel("Scroll Interval (seconds):"), self.scroll_interval_spin)
        
        # Monitor specific channel
        self.monitor_channel_check = QCheckBox("Monitor Specific Channel")
        self.monitor_channel_check.setChecked(self.config.get_discord('monitor_specific_channel', 'true').lower() == 'true')
        discord_layout.addRow(self.monitor_channel_check)
        
        discord_group.setLayout(discord_layout)
        scroll_layout.addWidget(discord_group)
        
        # Phemex settings group
        phemex_group = QGroupBox("Phemex Settings")
        phemex_layout = QFormLayout()
        
        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setText(self.config.get_phemex('api_key', ''))
        phemex_layout.addRow(QLabel("API Key:"), self.api_key_edit)
        
        # API Secret
        self.api_secret_edit = QLineEdit()
        self.api_secret_edit.setText(self.config.get_phemex('api_secret', ''))
        self.api_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        phemex_layout.addRow(QLabel("API Secret:"), self.api_secret_edit)
        
        # Testnet
        self.testnet_check = QCheckBox("Use Testnet")
        self.testnet_check.setChecked(self.config.get_phemex('testnet', 'true').lower() == 'true')
        phemex_layout.addRow(self.testnet_check)
        
        phemex_group.setLayout(phemex_layout)
        scroll_layout.addWidget(phemex_group)
        
        # Trading settings group
        trading_group = QGroupBox("Trading Settings")
        trading_layout = QFormLayout()
        
        # Max position size
        self.max_position_spin = QDoubleSpinBox()
        self.max_position_spin.setRange(1.0, 10000.0)
        self.max_position_spin.setSingleStep(10.0)
        self.max_position_spin.setValue(float(self.config.get_trading('max_position_size', 100.0)))
        trading_layout.addRow(QLabel("Max Position Size (USD):"), self.max_position_spin)
        
        # Default leverage
        self.leverage_spin = QSpinBox()
        self.leverage_spin.setRange(1, 50)
        self.leverage_spin.setValue(int(self.config.get_trading('default_leverage', 5)))
        trading_layout.addRow(QLabel("Default Leverage:"), self.leverage_spin)
        
        # Enable stop loss
        self.stop_loss_check = QCheckBox("Enable Stop Loss")
        self.stop_loss_check.setChecked(self.config.get_trading('enable_stop_loss', 'true').lower() == 'true')
        trading_layout.addRow(self.stop_loss_check)
        
        # Enable take profit
        self.take_profit_check = QCheckBox("Enable Take Profit")
        self.take_profit_check.setChecked(self.config.get_trading('enable_take_profit', 'true').lower() == 'true')
        trading_layout.addRow(self.take_profit_check)
        
        trading_group.setLayout(trading_layout)
        scroll_layout.addWidget(trading_group)
        
        # Save button
        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(self._save_settings)
        scroll_layout.addWidget(self.save_settings_button)
        
        # Add stretch to push everything to the top
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(settings_tab, "Settings")
    
    def _create_trader_tab(self):
        """Create the trader filtering tab"""
        trader_tab = QWidget()
        layout = QVBoxLayout(trader_tab)
        
        # Trader filtering settings group
        trader_group = QGroupBox("Trader Filtering Settings")
        trader_layout = QVBoxLayout()
        
        # Enable trader filtering
        self.enable_filtering_check = QCheckBox("Enable Trader Filtering")
        self.enable_filtering_check.setChecked(self.config.get_traders('enable_filtering', 'false').lower() == 'true')
        self.enable_filtering_check.toggled.connect(self._update_trader_filtering)
        trader_layout.addWidget(self.enable_filtering_check)
        
        # Target traders input
        form_layout = QFormLayout()
        
        # Get current target traders
        target_traders = self.config.get_target_traders()
        target_traders_str = ", ".join(target_traders) if target_traders else ""
        
        self.target_traders_edit = QLineEdit()
        self.target_traders_edit.setText(target_traders_str)
        form_layout.addRow(QLabel("Target Traders:"), self.target_traders_edit)
        
        # Help text
        help_label = QLabel("Enter trader handles separated by commas (e.g., @yramki, @Tareeq)")
        help_font = QFont()
        help_font.setItalic(True)
        help_font.setPointSize(10)
        help_label.setFont(help_font)
        form_layout.addRow(help_label)
        
        trader_layout.addLayout(form_layout)
        trader_group.setLayout(trader_layout)
        layout.addWidget(trader_group)
        
        # Current target traders group
        trader_list_group = QGroupBox("Current Target Traders")
        trader_list_layout = QVBoxLayout()
        
        # Trader list
        self.trader_list = QListWidget()
        self._update_trader_list()
        trader_list_layout.addWidget(self.trader_list)
        
        trader_list_group.setLayout(trader_list_layout)
        layout.addWidget(trader_list_group, 1)  # 1 = stretch factor
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.add_trader_button = QPushButton("Add Trader")
        self.add_trader_button.clicked.connect(self._add_trader)
        buttons_layout.addWidget(self.add_trader_button)
        
        self.remove_trader_button = QPushButton("Remove Selected")
        self.remove_trader_button.clicked.connect(self._remove_trader)
        buttons_layout.addWidget(self.remove_trader_button)
        
        buttons_layout.addStretch()
        
        self.apply_trader_button = QPushButton("Apply Changes")
        self.apply_trader_button.clicked.connect(self._apply_trader_changes)
        buttons_layout.addWidget(self.apply_trader_button)
        
        layout.addLayout(buttons_layout)
        
        self.tab_widget.addTab(trader_tab, "Trader Filtering")
    
    def _create_history_tab(self):
        """Create the history tab"""
        history_tab = QWidget()
        layout = QVBoxLayout(history_tab)
        
        # Create table for trade history
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "Timestamp", "Trader", "Symbol", "Direction", 
            "Entry", "SL", "TP", "Status"
        ])
        
        # Set column widths
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.history_table)
        
        # Add controls for history
        controls_layout = QHBoxLayout()
        
        self.refresh_history_button = QPushButton("Refresh History")
        self.refresh_history_button.clicked.connect(self._refresh_history)
        controls_layout.addWidget(self.refresh_history_button)
        
        controls_layout.addStretch()
        
        self.clear_history_button = QPushButton("Clear History")
        self.clear_history_button.clicked.connect(self._clear_history)
        controls_layout.addWidget(self.clear_history_button)
        
        layout.addLayout(controls_layout)
        
        self.tab_widget.addTab(history_tab, "History")
    
    def _create_logs_tab(self):
        """Create the logs tab"""
        logs_tab = QWidget()
        layout = QVBoxLayout(logs_tab)
        
        # Create text area for logs
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        
        # Create a handler to redirect logs to the text area
        self.log_handler = QTextEditLogger(self.logs_text)
        self.log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.log_handler)
        
        layout.addWidget(self.logs_text)
        
        # Add controls for logs
        controls_layout = QHBoxLayout()
        
        self.clear_logs_button = QPushButton("Clear Logs")
        self.clear_logs_button.clicked.connect(self._clear_logs)
        controls_layout.addWidget(self.clear_logs_button)
        
        controls_layout.addStretch()
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText("INFO")
        self.log_level_combo.currentTextChanged.connect(self._change_log_level)
        controls_layout.addWidget(QLabel("Log Level:"))
        controls_layout.addWidget(self.log_level_combo)
        
        layout.addLayout(controls_layout)
        
        self.tab_widget.addTab(logs_tab, "Logs")
    
    def _update_status_indicators(self):
        """Update the status indicators"""
        # Capture status
        if hasattr(self.screen_capture, 'running') and self.screen_capture.running:
            self.capture_status_label.setText("Running")
            self.capture_status_label.setStyleSheet("color: green")
            self.capture_button.setText("Stop Capture")
        else:
            self.capture_status_label.setText("Stopped")
            self.capture_status_label.setStyleSheet("color: red")
            self.capture_button.setText("Start Capture")
        
        # Trading status
        if self.trading_client.auto_trade:
            self.trading_status_label.setText("Enabled")
            self.trading_status_label.setStyleSheet("color: green")
            self.trading_button.setText("Disable Trading")
        else:
            self.trading_status_label.setText("Disabled")
            self.trading_status_label.setStyleSheet("color: red")
            self.trading_button.setText("Enable Trading")
        
        # Filtering status
        if self.config.get_traders('enable_filtering', 'false').lower() == 'true':
            self.filtering_status_label.setText("Enabled")
            self.filtering_status_label.setStyleSheet("color: green")
            self.filtering_button.setText("Disable Filtering")
        else:
            self.filtering_status_label.setText("Disabled")
            self.filtering_status_label.setStyleSheet("color: red")
            self.filtering_button.setText("Enable Filtering")
    
    def _toggle_capture(self):
        """Toggle screen capture on/off"""
        if hasattr(self.screen_capture, 'running') and self.screen_capture.running:
            # Stop capture
            logger.info("Stopping screen capture")
            self.screen_capture.stop()
            if self.signal_processing_thread:
                self.signal_processing_thread.stop()
        else:
            # Start capture
            logger.info("Starting screen capture")
            
            # Apply current settings
            self.screen_capture.scan_interval = self.scan_interval_spin.value()
            self.screen_capture.click_hidden_messages = self.click_hidden_check.isChecked()
            self.screen_capture.auto_scroll = self.auto_scroll_check.isChecked()
            self.screen_capture.scroll_interval = self.scroll_interval_spin.value()
            self.screen_capture.monitor_specific_channel = self.monitor_channel_check.isChecked()
            
            # Start the screen capture
            self.screen_capture.start()
            
            # Start signal processing thread
            if not self.signal_processing_thread:
                self.signal_processing_thread = SignalProcessingThread(
                    self.screen_capture, 
                    self.signal_parser, 
                    self.trading_client
                )
                self.signal_processing_thread.signal_detected.connect(self._on_signal_detected)
            self.signal_processing_thread.start()
        
        # Update status indicators
        self._update_status_indicators()
    
    def _toggle_trading(self):
        """Toggle auto trading on/off"""
        self.trading_client.auto_trade = not self.trading_client.auto_trade
        logger.info(f"Auto trading {'enabled' if self.trading_client.auto_trade else 'disabled'}")
        
        # Save to config
        self.config.set_trading('auto_trade', 'true' if self.trading_client.auto_trade else 'false')
        self.config.save()
        
        # Update status indicators
        self._update_status_indicators()
    
    def _toggle_filtering(self):
        """Toggle trader filtering on/off"""
        current_state = self.config.get_traders('enable_filtering', 'false').lower() == 'true'
        new_state = not current_state
        
        logger.info(f"Trader filtering {'enabled' if new_state else 'disabled'}")
        
        # Save to config
        self.config.set_traders('enable_filtering', 'true' if new_state else 'false')
        self.config.save()
        
        # Update UI
        self.enable_filtering_check.setChecked(new_state)
        
        # Update status indicators
        self._update_status_indicators()
    
    def _save_settings(self):
        """Save settings to config file"""
        try:
            # Discord settings
            self.config.set_general('scan_interval', str(self.scan_interval_spin.value()))
            self.config.set_discord('click_hidden_messages', 'true' if self.click_hidden_check.isChecked() else 'false')
            self.config.set_discord('auto_scroll', 'true' if self.auto_scroll_check.isChecked() else 'false')
            self.config.set_discord('scroll_interval', str(self.scroll_interval_spin.value()))
            self.config.set_discord('monitor_specific_channel', 'true' if self.monitor_channel_check.isChecked() else 'false')
            
            # Phemex settings
            self.config.set_phemex('api_key', self.api_key_edit.text())
            self.config.set_phemex('api_secret', self.api_secret_edit.text())
            self.config.set_phemex('testnet', 'true' if self.testnet_check.isChecked() else 'false')
            
            # Trading settings
            self.config.set_trading('max_position_size', str(self.max_position_spin.value()))
            self.config.set_trading('default_leverage', str(self.leverage_spin.value()))
            self.config.set_trading('enable_stop_loss', 'true' if self.stop_loss_check.isChecked() else 'false')
            self.config.set_trading('enable_take_profit', 'true' if self.take_profit_check.isChecked() else 'false')
            
            # Save config to file
            self.config.save()
            
            # Update trading client settings
            self.trading_client.testnet = self.testnet_check.isChecked()
            self.trading_client.max_position_size = self.max_position_spin.value()
            self.trading_client.default_leverage = self.leverage_spin.value()
            self.trading_client.enable_stop_loss = self.stop_loss_check.isChecked()
            self.trading_client.enable_take_profit = self.take_profit_check.isChecked()
            
            # Update screen capture settings if running
            if hasattr(self.screen_capture, 'running') and self.screen_capture.running:
                self.screen_capture.scan_interval = self.scan_interval_spin.value()
                self.screen_capture.click_hidden_messages = self.click_hidden_check.isChecked()
                self.screen_capture.auto_scroll = self.auto_scroll_check.isChecked()
                self.screen_capture.scroll_interval = self.scroll_interval_spin.value()
                self.screen_capture.monitor_specific_channel = self.monitor_channel_check.isChecked()
            
            logger.info("Settings saved successfully")
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
        except Exception as e:
            logger.error(f"Error saving settings: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error saving settings: {e}")
    
    def _update_trader_list(self):
        """Update the trader list with current target traders"""
        self.trader_list.clear()
        target_traders = self.config.get_target_traders()
        for trader in target_traders:
            self.trader_list.addItem(trader)
    
    def _update_trader_filtering(self, checked):
        """Update trader filtering status"""
        self.config.set_traders('enable_filtering', 'true' if checked else 'false')
        self.config.save()
        self._update_status_indicators()
    
    def _add_trader(self):
        """Add a trader to the list"""
        trader_input = self.target_traders_edit.text().strip()
        if not trader_input:
            return
        
        traders = [t.strip() for t in trader_input.split(',')]
        current_traders = self.config.get_target_traders()
        
        # Add new traders that aren't already in the list
        new_traders = [t for t in traders if t and t not in current_traders]
        if new_traders:
            current_traders.extend(new_traders)
            self.config.set_target_traders(current_traders)
            self.config.save()
            self._update_trader_list()
            
            # Clear input field
            self.target_traders_edit.clear()
    
    def _remove_trader(self):
        """Remove the selected trader from the list"""
        selected_items = self.trader_list.selectedItems()
        if not selected_items:
            return
        
        current_traders = self.config.get_target_traders()
        
        # Remove selected traders
        for item in selected_items:
            trader = item.text()
            if trader in current_traders:
                current_traders.remove(trader)
        
        self.config.set_target_traders(current_traders)
        self.config.save()
        self._update_trader_list()
    
    def _apply_trader_changes(self):
        """Apply changes to target traders from the input field"""
        trader_input = self.target_traders_edit.text().strip()
        
        if trader_input:
            traders = [t.strip() for t in trader_input.split(',')]
            self.config.set_target_traders(traders)
        else:
            self.config.set_target_traders([])
        
        self.config.save()
        self._update_trader_list()
        
        logger.info("Trader filtering settings applied")
        QMessageBox.information(self, "Settings Applied", "Trader filtering settings have been applied.")
        
        # Update screen capture target traders if running
        if hasattr(self.screen_capture, 'running') and self.screen_capture.running:
            self.screen_capture.target_traders = self.config.get_target_traders()
    
    def _refresh_history(self):
        """Refresh the trade history"""
        # Clear the table
        self.history_table.setRowCount(0)
        
        # TODO: Implement fetching actual trade history from a storage source
        
        # For now, add some sample data
        sample_data = [
            {"timestamp": "2025-04-20 12:34:56", "trader": "@yramki", "symbol": "BTC", "direction": "LONG", 
             "entry": "67500", "sl": "65200", "tp": "70000", "status": "OPEN"},
            {"timestamp": "2025-04-20 10:15:30", "trader": "@Tareeq", "symbol": "ETH", "direction": "SHORT", 
             "entry": "3520", "sl": "3650", "tp": "3300", "status": "CLOSED"},
            {"timestamp": "2025-04-19 15:45:12", "trader": "@yramki", "symbol": "SOL", "direction": "LONG", 
             "entry": "150.25", "sl": "145.5", "tp": "160", "status": "CLOSED"},
        ]
        
        # Add sample data to the table
        for row, data in enumerate(sample_data):
            self.history_table.insertRow(row)
            for col, key in enumerate(["timestamp", "trader", "symbol", "direction", "entry", "sl", "tp", "status"]):
                item = QTableWidgetItem(data[key])
                self.history_table.setItem(row, col, item)
        
        logger.info("Trade history refreshed")
    
    def _clear_history(self):
        """Clear the trade history"""
        reply = QMessageBox.question(
            self, "Confirm", "Are you sure you want to clear the trade history?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_table.setRowCount(0)
            logger.info("Trade history cleared")
    
    def _clear_logs(self):
        """Clear the logs display"""
        self.logs_text.clear()
        logger.info("Logs cleared")
    
    def _change_log_level(self, level_name):
        """Change the logging level"""
        level = getattr(logging, level_name)
        logging.getLogger().setLevel(level)
        logger.info(f"Log level changed to {level_name}")
    
    def _on_signal_detected(self, signal):
        """Handle a detected trading signal"""
        # Update signal display
        self.signal_text.clear()
        self.signal_text.append(f"Trader: {signal.get('trader', 'Unknown')}")
        self.signal_text.append(f"Symbol: {signal.get('symbol', 'Unknown')}")
        self.signal_text.append(f"Direction: {'LONG' if signal.get('is_long', True) else 'SHORT'}")
        self.signal_text.append(f"Entry: {signal.get('entry_price', 0)}")
        self.signal_text.append(f"Stop Loss: {signal.get('stop_loss', 0)}")
        self.signal_text.append(f"Take Profit: {signal.get('take_profit', 0)}")
        self.signal_text.append(f"Time: {signal.get('timestamp', 'N/A')}")
        
        # Add to history
        self._add_signal_to_history(signal)
    
    def _add_signal_to_history(self, signal):
        """Add a signal to the history table"""
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)
        
        # Fill in the row
        self.history_table.setItem(row, 0, QTableWidgetItem(signal.get('timestamp', 'N/A')))
        self.history_table.setItem(row, 1, QTableWidgetItem(signal.get('trader', 'Unknown')))
        self.history_table.setItem(row, 2, QTableWidgetItem(signal.get('symbol', 'Unknown')))
        self.history_table.setItem(row, 3, QTableWidgetItem('LONG' if signal.get('is_long', True) else 'SHORT'))
        self.history_table.setItem(row, 4, QTableWidgetItem(str(signal.get('entry_price', 0))))
        self.history_table.setItem(row, 5, QTableWidgetItem(str(signal.get('stop_loss', 0))))
        self.history_table.setItem(row, 6, QTableWidgetItem(str(signal.get('take_profit', 0))))
        self.history_table.setItem(row, 7, QTableWidgetItem('PENDING'))
    
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self, "Confirm Exit", "Are you sure you want to exit the application?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Stop threads
            if self.signal_processing_thread:
                self.signal_processing_thread.stop()
            
            # Stop screen capture
            if hasattr(self.screen_capture, 'running') and self.screen_capture.running:
                self.screen_capture.stop()
            
            # Accept the event to close the window
            event.accept()
        else:
            # Ignore the event to keep the window open
            event.ignore()

class QTextEditLogger(logging.Handler):
    """Custom logging handler that outputs to a QTextEdit"""
    
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
    
    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)
        # Scroll to the bottom to show the latest message
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())

def run_application(screen_capture, signal_parser, trading_client, config):
    """Run the PyQt6 application"""
    app = QApplication(sys.argv)
    
    # Set application style to fusion (looks better on macOS)
    app.setStyle("Fusion")
    
    # Create and show the main window
    main_window = QtMainWindow(screen_capture, signal_parser, trading_client, config)
    main_window.show()
    
    # Start the application event loop
    sys.exit(app.exec())