#!/usr/bin/env python3
"""
Discord Trading Signal Scraper and Phemex Trading Bot
macOS Desktop Application with PyQt6 UI
"""

import sys
import os
import logging
import time
import argparse

# Import application modules
from screen_capture_enhanced import ScreenCapture
from signal_parser import SignalParser
from trading_client import PhemexClient
from config_enhanced import Config
from ui.qt_main_window import run_application

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("discord_phemex_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Discord Trading Signal Scraper and Phemex Trading Bot')
    parser.add_argument('--config', type=str, default='config.ini', help='Path to configuration file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-trade', action='store_true', help='Disable actual trading (test mode)')
    parser.add_argument('--traders', type=str, help='Comma-separated list of trader handles to filter (e.g., "@yramki,@Tareeq")')
    return parser.parse_args()

def main():
    """Main application entry point"""
    args = parse_arguments()
    
    # Set debug level if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Load configuration
    config = Config(args.config)
    
    # Override config with command line arguments
    if args.no_trade:
        config.set_trading('auto_trade', 'false')
        logger.info("Trading disabled via command line argument")
    
    # Set target traders if specified
    if args.traders:
        traders = [t.strip() for t in args.traders.split(',')]
        config.set_target_traders(traders)
        config.set_traders('enable_filtering', 'true')
        logger.info(f"Filtering for traders: {', '.join(traders)}")
    
    try:
        # Initialize components
        logger.info("Initializing application components...")
        
        # Get target traders from config
        target_traders = config.get_target_traders()
        
        # Initialize screen capture with trader filtering
        screen_capture = ScreenCapture(
            scan_interval=float(config.get_general('scan_interval', 2.0)),
            click_hidden_messages=config.get_discord('click_hidden_messages', 'true').lower() == 'true',
            target_traders=target_traders,
            monitor_specific_channel=config.get_discord('monitor_specific_channel', 'true').lower() == 'true',
            auto_scroll=config.get_discord('auto_scroll', 'true').lower() == 'true',
            scroll_interval=float(config.get_discord('scroll_interval', 30.0))
        )
        
        # Initialize signal parser
        signal_parser = SignalParser()
        
        # Initialize trading client
        trading_client = PhemexClient(
            api_key=config.get_phemex('api_key', ''),
            api_secret=config.get_phemex('api_secret', ''),
            testnet=config.get_phemex('testnet', 'true').lower() == 'true',
            auto_trade=config.get_trading('auto_trade', 'false').lower() == 'true',
            max_position_size=float(config.get_trading('max_position_size', 100.0)),
            default_leverage=int(config.get_trading('default_leverage', 5)),
            enable_stop_loss=config.get_trading('enable_stop_loss', 'true').lower() == 'true',
            enable_take_profit=config.get_trading('enable_take_profit', 'true').lower() == 'true'
        )
        
        # Run application with PyQt6 UI
        run_application(screen_capture, signal_parser, trading_client, config)
        
    except Exception as e:
        logger.error(f"Error in main application: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())