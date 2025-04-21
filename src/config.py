"""
Configuration Module for Discord Trading Signal Scraper
Handles loading and saving configuration with enhanced trader filtering options
"""

import os
import logging
import configparser

logger = logging.getLogger(__name__)

class Config:
    """
    Configuration manager for the application
    """
    
    def __init__(self, config_path='config.ini'):
        """
        Initialize the configuration manager
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        
        # Load configuration
        if os.path.exists(config_path):
            self.load()
        else:
            self.create_default()
            self.save()
            
        logger.info(f"Configuration loaded from {config_path}")
    
    def load(self):
        """Load configuration from file"""
        try:
            self.config.read(self.config_path)
            
            # Ensure all required sections exist
            self._ensure_sections()
            
            logger.debug("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
            self.create_default()
    
    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                self.config.write(f)
            logger.debug("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
    
    def create_default(self):
        """Create default configuration"""
        self.config.clear()
        
        # General settings
        self.config['General'] = {
            'debug_mode': 'false',
            'scan_interval': '2.0',  # seconds
            'test_mode': 'true'
        }
        
        # Discord settings
        self.config['Discord'] = {
            'monitor_enabled': 'true',
            'click_hidden_messages': 'true',
            'auto_scroll': 'true',
            'scroll_interval': '30.0',  # seconds
            'monitor_specific_channel': 'true',
            'channel_name': 'trades',   # Name of the Discord channel to monitor
            'target_server': 'Wealth Group'  # Name of the Discord server to monitor
        }
        
        # Trader filtering settings
        self.config['Traders'] = {
            'enable_filtering': 'false',
            'target_traders': '@yramki, @Tareeq',  # Comma-separated list of trader handles
        }
        
        # Phemex settings
        self.config['Phemex'] = {
            'api_key': '',
            'api_secret': '',
            'testnet': 'true'
        }
        
        # Trading settings
        self.config['Trading'] = {
            'max_position_size': '100',  # USD
            'default_leverage': '5',
            'enable_stop_loss': 'true',
            'enable_take_profit': 'true',
            'auto_trade': 'false'
        }
        
        logger.debug("Default configuration created")
    
    def _ensure_sections(self):
        """Ensure all required sections exist in the configuration"""
        required_sections = ['General', 'Discord', 'Traders', 'Phemex', 'Trading']
        
        for section in required_sections:
            if section not in self.config:
                self.config[section] = {}
                logger.warning(f"Missing section '{section}' created in configuration")
    
    def get_general(self, key, default=None):
        """Get a value from the General section"""
        return self._get_value('General', key, default)
    
    def get_discord(self, key, default=None):
        """Get a value from the Discord section"""
        return self._get_value('Discord', key, default)
    
    def get_traders(self, key, default=None):
        """Get a value from the Traders section"""
        return self._get_value('Traders', key, default)
    
    def get_phemex(self, key, default=None):
        """Get a value from the Phemex section"""
        return self._get_value('Phemex', key, default)
    
    def get_trading(self, key, default=None):
        """Get a value from the Trading section"""
        return self._get_value('Trading', key, default)
    
    def _get_value(self, section, key, default=None):
        """
        Get a value from the configuration
        
        Args:
            section: Section name
            key: Key name
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        if section not in self.config:
            logger.warning(f"Section '{section}' not found in configuration")
            return default
        
        if key not in self.config[section]:
            logger.warning(f"Key '{key}' not found in section '{section}'")
            return default
        
        return self.config[section][key]
    
    def set_general(self, key, value):
        """Set a value in the General section"""
        self._set_value('General', key, value)
    
    def set_discord(self, key, value):
        """Set a value in the Discord section"""
        self._set_value('Discord', key, value)
    
    def set_traders(self, key, value):
        """Set a value in the Traders section"""
        self._set_value('Traders', key, value)
    
    def set_phemex(self, key, value):
        """Set a value in the Phemex section"""
        self._set_value('Phemex', key, value)
    
    def set_trading(self, key, value):
        """Set a value in the Trading section"""
        self._set_value('Trading', key, value)
    
    def _set_value(self, section, key, value):
        """
        Set a value in the configuration
        
        Args:
            section: Section name
            key: Key name
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
            logger.warning(f"Created missing section '{section}'")
        
        self.config[section][key] = str(value)
    
    def get_target_traders(self):
        """
        Get the list of target traders
        
        Returns:
            List of trader handles
        """
        if not self.config.getboolean('Traders', 'enable_filtering', fallback=False):
            return []
        
        traders_str = self.get_traders('target_traders', '')
        if not traders_str:
            return []
        
        # Split by comma and strip whitespace
        return [trader.strip() for trader in traders_str.split(',')]
    
    def set_target_traders(self, traders):
        """
        Set the list of target traders
        
        Args:
            traders: List of trader handles
        """
        # Join with commas
        traders_str = ', '.join(traders)
        self.set_traders('target_traders', traders_str)
        
        # Enable filtering if traders are specified
        if traders:
            self.set_traders('enable_filtering', 'true')
