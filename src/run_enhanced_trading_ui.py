#!/usr/bin/env python3
"""
Launcher script for the Enhanced Trading UI
"""

import logging
import os
import sys
from screen_capture_enhanced import ScreenCapture
from signal_parser import SignalParser
from trading_client import PhemexClient
from config_enhanced import Config
from ui.enhanced_trading_ui import EnhancedTradingUI

def setup_logging():
    """Set up logging configuration"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/enhanced_trading_ui.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main entry point for the enhanced trading UI"""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Enhanced Trading UI")
    
    try:
        # Load configuration
        config = Config()
        
        # Create components
        screen_capture = ScreenCapture(
            scan_interval=float(config.get_general('scan_interval', 2.0)),
            click_hidden_messages=config.get_discord('click_hidden_messages', 'true').lower() == 'true',
            target_traders=config.get_target_traders() if config.get_traders('enable_filtering', 'false').lower() == 'true' else None,
            monitor_specific_channel=config.get_discord('monitor_specific_channel', 'true').lower() == 'true',
            channel_name=config.get_discord('channel_name', 'trades'),
            target_server=config.get_discord('target_server', 'Wealth Group'),
            auto_scroll=config.get_discord('auto_scroll', 'true').lower() == 'true',
            scroll_interval=float(config.get_discord('scroll_interval', 30.0))
        )
        
        signal_parser = SignalParser()
        
        trading_client = PhemexClient(
            api_key=config.get_phemex('api_key', ''),
            api_secret=config.get_phemex('api_secret', ''),
            testnet=config.get_phemex('testnet', 'true').lower() == 'true'
        )
        
        # Create and run the UI
        app = EnhancedTradingUI(screen_capture, signal_parser, trading_client, config)
        app.run()
        
    except Exception as e:
        logger.error(f"Error running Enhanced Trading UI: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()