"""
Signal Parser Module for Discord Trading Signal Scraper
Parses extracted text from Discord to identify trading signals
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional, List

logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """Data class representing a trading signal"""
    symbol: str
    direction: str  # "long" or "short"
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: str = ""
    status: str = ""
    raw_text: str = ""

class SignalParser:
    """
    Parses text extracted from Discord to identify trading signals
    """
    
    def __init__(self):
        """Initialize the signal parser"""
        # Regular expressions for extracting trading signal components
        self.symbol_pattern = r'([A-Z]+)'
        self.direction_pattern = r'(long|short)'
        self.entry_pattern = r'Entry:?\s*(\d+\.\d+)'
        self.sl_pattern = r'SL:?\s*(\d+\.\d+)'
        self.tp_pattern = r'TP:?\s*(\d+\.\d+)|TPs:?\s*(\d+\.\d+)'
        self.status_pattern = r'Status:?\s*([^•]+)'
        self.timestamp_pattern = r'Today at (\d+:\d+ [AP]M)'
        
        logger.info("Signal parser initialized")
    
    def parse_signal(self, text: str) -> Optional[TradingSignal]:
        """
        Parse text to extract trading signal information
        
        Args:
            text: Text extracted from Discord message
            
        Returns:
            TradingSignal object if a valid signal is found, None otherwise
        """
        try:
            # Clean up the text
            text = self._clean_text(text)
            
            # Check if this looks like a trading signal
            if not self._is_trading_signal(text):
                logger.debug("Text does not appear to be a trading signal")
                return None
            
            # Extract components
            symbol = self._extract_symbol(text)
            direction = self._extract_direction(text)
            entry_price = self._extract_entry_price(text)
            stop_loss = self._extract_stop_loss(text)
            take_profit = self._extract_take_profit(text)
            status = self._extract_status(text)
            timestamp = self._extract_timestamp(text)
            
            # Validate required components
            if not all([symbol, direction, entry_price, stop_loss, take_profit]):
                logger.warning("Missing required components in trading signal")
                return None
            
            # Create and return the trading signal
            signal = TradingSignal(
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                status=status,
                timestamp=timestamp,
                raw_text=text
            )
            
            logger.info(f"Successfully parsed trading signal for {symbol} {direction}")
            return signal
            
        except Exception as e:
            logger.error(f"Error parsing trading signal: {e}", exc_info=True)
            return None
    
    def _clean_text(self, text: str) -> str:
        """
        Clean up text for better parsing
        
        Args:
            text: Raw text from OCR
            
        Returns:
            Cleaned text
        """
        # Convert to lowercase for case-insensitive matching
        text = text.lower()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Replace common OCR errors
        replacements = {
            'entty': 'entry',
            'eniry': 'entry',
            'sl;': 'sl:',
            'tp;': 'tp:',
            'tps;': 'tps:',
            'shart': 'short',
            'lang': 'long'
        }
        
        for error, correction in replacements.items():
            text = text.replace(error, correction)
        
        return text
    
    def _is_trading_signal(self, text: str) -> bool:
        """
        Check if text appears to be a trading signal
        
        Args:
            text: Cleaned text
            
        Returns:
            True if text appears to be a trading signal, False otherwise
        """
        # Check for key indicators
        indicators = ['entry', 'sl', 'tp']
        return all(indicator in text for indicator in indicators)
    
    def _extract_symbol(self, text: str) -> str:
        """
        Extract cryptocurrency symbol from text
        
        Args:
            text: Cleaned text
            
        Returns:
            Symbol string or empty string if not found
        """
        # Look for symbol in uppercase
        match = re.search(self.symbol_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return ""
    
    def _extract_direction(self, text: str) -> str:
        """
        Extract trading direction from text
        
        Args:
            text: Cleaned text
            
        Returns:
            "long" or "short" or empty string if not found
        """
        match = re.search(self.direction_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return ""
    
    def _extract_entry_price(self, text: str) -> float:
        """
        Extract entry price from text
        
        Args:
            text: Cleaned text
            
        Returns:
            Entry price as float or 0.0 if not found
        """
        match = re.search(self.entry_pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0
        return 0.0
    
    def _extract_stop_loss(self, text: str) -> float:
        """
        Extract stop loss price from text
        
        Args:
            text: Cleaned text
            
        Returns:
            Stop loss price as float or 0.0 if not found
        """
        match = re.search(self.sl_pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0
        return 0.0
    
    def _extract_take_profit(self, text: str) -> float:
        """
        Extract take profit price from text
        
        Args:
            text: Cleaned text
            
        Returns:
            Take profit price as float or 0.0 if not found
        """
        match = re.search(self.tp_pattern, text, re.IGNORECASE)
        if match:
            try:
                # Handle both TP and TPs patterns
                value = match.group(1) if match.group(1) else match.group(2)
                return float(value)
            except ValueError:
                return 0.0
        return 0.0
    
    def _extract_status(self, text: str) -> str:
        """
        Extract status information from text
        
        Args:
            text: Cleaned text
            
        Returns:
            Status string or empty string if not found
        """
        match = re.search(self.status_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_timestamp(self, text: str) -> str:
        """
        Extract timestamp from text
        
        Args:
            text: Cleaned text
            
        Returns:
            Timestamp string or empty string if not found
        """
        match = re.search(self.timestamp_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""
