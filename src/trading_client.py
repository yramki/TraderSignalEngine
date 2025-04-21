"""
Phemex Trading Client Module for Discord Trading Signal Scraper
Handles communication with Phemex API for executing trades
"""

import logging
import time
import hmac
import hashlib
import json
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from signal_parser import TradingSignal

logger = logging.getLogger(__name__)

class PhemexClient:
    """
    Client for interacting with Phemex API to execute trades
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True, 
                 auto_trade: bool = False, max_position_size: float = 100.0,
                 default_leverage: int = 5, enable_stop_loss: bool = True,
                 enable_take_profit: bool = True):
        """
        Initialize the Phemex API client
        
        Args:
            api_key: Phemex API key
            api_secret: Phemex API secret
            testnet: Whether to use testnet (True) or mainnet (False)
            auto_trade: Whether to automatically execute trades
            max_position_size: Maximum position size in USD
            default_leverage: Default leverage to use
            enable_stop_loss: Whether to enable stop loss orders
            enable_take_profit: Whether to enable take profit orders
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.auto_trade = auto_trade
        self.max_position_size = max_position_size
        self.default_leverage = default_leverage
        self.enable_stop_loss = enable_stop_loss
        self.enable_take_profit = enable_take_profit
        
        # Set API base URL based on testnet flag
        if testnet:
            self.base_url = "https://testnet-api.phemex.com"
        else:
            self.base_url = "https://api.phemex.com"
        
        # Trading history
        self.trade_history = []
        
        logger.info(f"Phemex client initialized (testnet: {testnet}, auto_trade: {auto_trade})")
    
    def process_signal(self, signal: TradingSignal) -> Dict[str, Any]:
        """
        Process a trading signal and execute trade if auto_trade is enabled
        
        Args:
            signal: TradingSignal object containing trade information
            
        Returns:
            Dict containing result of the operation
        """
        logger.info(f"Processing signal: {signal.symbol} {signal.direction} at {signal.entry_price}")
        
        # Validate signal
        if not self._validate_signal(signal):
            logger.warning("Invalid signal, skipping")
            return {"success": False, "message": "Invalid signal"}
        
        # Prepare order parameters
        order_params = self._prepare_order_params(signal)
        
        # Execute trade if auto_trade is enabled
        if self.auto_trade:
            logger.info("Auto-trade enabled, executing trade")
            result = self._execute_trade(order_params)
            
            # Add to trade history
            self.trade_history.append({
                "timestamp": time.time(),
                "signal": signal,
                "result": result
            })
            
            return result
        else:
            logger.info("Auto-trade disabled, not executing trade")
            return {
                "success": True,
                "message": "Auto-trade disabled, trade not executed",
                "order_params": order_params
            }
    
    def _validate_signal(self, signal: TradingSignal) -> bool:
        """
        Validate a trading signal
        
        Args:
            signal: TradingSignal object to validate
            
        Returns:
            True if signal is valid, False otherwise
        """
        # Check required fields
        if not signal.symbol or not signal.direction or not signal.entry_price:
            logger.warning("Missing required fields in signal")
            return False
        
        # Check direction
        if signal.direction not in ["long", "short"]:
            logger.warning(f"Invalid direction: {signal.direction}")
            return False
        
        # Check prices
        if signal.entry_price <= 0:
            logger.warning(f"Invalid entry price: {signal.entry_price}")
            return False
        
        # Check stop loss for short positions
        if signal.direction == "short" and signal.stop_loss <= signal.entry_price:
            logger.warning(f"Invalid stop loss for short position: {signal.stop_loss} <= {signal.entry_price}")
            return False
        
        # Check stop loss for long positions
        if signal.direction == "long" and signal.stop_loss >= signal.entry_price:
            logger.warning(f"Invalid stop loss for long position: {signal.stop_loss} >= {signal.entry_price}")
            return False
        
        # Check take profit for short positions
        if signal.direction == "short" and signal.take_profit >= signal.entry_price:
            logger.warning(f"Invalid take profit for short position: {signal.take_profit} >= {signal.entry_price}")
            return False
        
        # Check take profit for long positions
        if signal.direction == "long" and signal.take_profit <= signal.entry_price:
            logger.warning(f"Invalid take profit for long position: {signal.take_profit} <= {signal.entry_price}")
            return False
        
        return True
    
    def _prepare_order_params(self, signal: TradingSignal) -> Dict[str, Any]:
        """
        Prepare order parameters for Phemex API
        
        Args:
            signal: TradingSignal object containing trade information
            
        Returns:
            Dict containing order parameters
        """
        # Convert symbol to Phemex format (e.g., XRP -> XRPUSD)
        symbol = f"{signal.symbol}USD"
        
        # Convert direction to Phemex format
        side = "Buy" if signal.direction == "long" else "Sell"
        
        # Calculate position size based on max_position_size
        # In a real implementation, this would be more sophisticated
        position_size = self.max_position_size
        
        # Prepare order parameters
        params = {
            "symbol": symbol,
            "clOrdID": f"signal_{int(time.time())}",
            "side": side,
            "orderQty": position_size,
            "ordType": "Limit",
            "priceEp": int(signal.entry_price * 10000),  # Convert to Phemex price format
            "timeInForce": "GoodTillCancel",
            "reduceOnly": False,
        }
        
        # Add stop loss if enabled
        if self.enable_stop_loss and signal.stop_loss > 0:
            params["stopLossEp"] = int(signal.stop_loss * 10000)
        
        # Add take profit if enabled
        if self.enable_take_profit and signal.take_profit > 0:
            params["takeProfitEp"] = int(signal.take_profit * 10000)
        
        return params
    
    def _execute_trade(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade on Phemex
        
        Args:
            order_params: Dict containing order parameters
            
        Returns:
            Dict containing result of the operation
        """
        try:
            # Endpoint for placing an order
            endpoint = "/orders"
            
            # Convert order_params to JSON
            order_data = json.dumps(order_params)
            
            # Make API request
            response = self._send_request("POST", endpoint, data=order_data)
            
            # Check response
            if response.get("code") == 0:
                logger.info("Trade executed successfully")
                return {
                    "success": True,
                    "message": "Trade executed successfully",
                    "order_id": response.get("data", {}).get("orderID"),
                    "response": response
                }
            else:
                logger.error(f"Error executing trade: {response}")
                return {
                    "success": False,
                    "message": f"Error executing trade: {response.get('msg')}",
                    "response": response
                }
        
        except Exception as e:
            logger.error(f"Exception executing trade: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Exception executing trade: {str(e)}"
            }
    
    def _send_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, 
                     data: str = None) -> Dict[str, Any]:
        """
        Send a request to Phemex API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters for GET requests
            data: JSON data for POST requests
            
        Returns:
            Dict containing API response
        """
        # Prepare URL
        url = f"{self.base_url}{endpoint}"
        
        # Prepare query string for GET requests
        query_string = ""
        if params:
            query_string = urlencode(params)
            url = f"{url}?{query_string}"
        
        # Set expiry timestamp (current time + 1 minute)
        expiry = int(time.time()) + 60
        
        # Prepare signature
        signature_payload = f"{endpoint}{query_string}{expiry}"
        if data:
            signature_payload += data
        
        signature = hmac.new(
            bytes(self.api_secret, "utf-8"),
            bytes(signature_payload, "utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "x-phemex-access-token": self.api_key,
            "x-phemex-request-expiry": str(expiry),
            "x-phemex-request-signature": signature
        }
        
        # Send request
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, data=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, data=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Parse response
            return response.json()
        
        except Exception as e:
            logger.error(f"Error sending request to Phemex API: {e}", exc_info=True)
            return {"code": -1, "msg": f"Error sending request: {str(e)}"}
    
    def get_account_positions(self, currency: str = "USD") -> Dict[str, Any]:
        """
        Get account positions
        
        Args:
            currency: Currency to get positions for
            
        Returns:
            Dict containing account positions
        """
        endpoint = "/accounts/accountPositions"
        params = {"currency": currency}
        return self._send_request("GET", endpoint, params=params)
    
    def get_trade_history(self) -> list:
        """
        Get trade history
        
        Returns:
            List of executed trades
        """
        return self.trade_history
    
    def set_auto_trade(self, enabled: bool) -> None:
        """
        Enable or disable auto-trading
        
        Args:
            enabled: Whether to enable auto-trading
        """
        self.auto_trade = enabled
        logger.info(f"Auto-trade {'enabled' if enabled else 'disabled'}")
    
    def set_max_position_size(self, size: float) -> None:
        """
        Set maximum position size
        
        Args:
            size: Maximum position size in USD
        """
        self.max_position_size = size
        logger.info(f"Max position size set to {size} USD")
