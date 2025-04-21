"""
Enhanced Screen Capture Module for Discord Trading Signal Scraper
Handles capturing screenshots of Discord window, detecting trading signals,
filtering by trader, and clicking "Unlock Content" buttons
"""

import logging
import time
import threading
import queue
import pyautogui
import cv2
import numpy as np
import pytesseract
from PIL import Image
import re

logger = logging.getLogger(__name__)

class ScreenCapture:
    """
    Handles screen capture operations for Discord window
    Detects and captures trading signals with trader filtering
    """
    
    def __init__(self, scan_interval=2.0, click_hidden_messages=True, 
                 target_traders=None, monitor_specific_channel=True,
                 auto_scroll=True, scroll_interval=30.0):
        """
        Initialize the screen capture module
        
        Args:
            scan_interval (float): Time between screen captures in seconds
            click_hidden_messages (bool): Whether to click on hidden messages to reveal them
            target_traders (list): List of trader handles to filter (e.g., ["@yramki", "@Tareeq"])
            monitor_specific_channel (bool): Whether to focus on a specific channel
            auto_scroll (bool): Whether to automatically scroll down to check for new messages
            scroll_interval (float): Time between auto-scrolls in seconds
        """
        self.scan_interval = scan_interval
        self.click_hidden_messages = click_hidden_messages
        self.target_traders = target_traders or []
        self.monitor_specific_channel = monitor_specific_channel
        self.auto_scroll = auto_scroll
        self.scroll_interval = scroll_interval
        self.running = False
        self.capture_thread = None
        self.scroll_thread = None
        self.signal_queue = queue.Queue()
        self.last_processed_signal = None
        self.last_scroll_time = 0
        
        # Patterns to look for in Discord
        self.hidden_message_pattern = "Only you can see this"
        self.unlock_button_text = "Unlock Content"
        self.trading_signal_indicators = ["Entry:", "SL:", "TP"]
        
        logger.info("Enhanced screen capture module initialized")
        if self.target_traders:
            logger.info(f"Filtering for traders: {', '.join(self.target_traders)}")
    
    def start(self):
        """Start the screen capture thread"""
        if self.running:
            logger.warning("Screen capture already running")
            return
        
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        # Start auto-scroll thread if enabled
        if self.auto_scroll:
            self.scroll_thread = threading.Thread(target=self._auto_scroll_loop)
            self.scroll_thread.daemon = True
            self.scroll_thread.start()
            
        logger.info("Enhanced screen capture started")
    
    def stop(self):
        """Stop the screen capture thread"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=5.0)
        if self.scroll_thread:
            self.scroll_thread.join(timeout=5.0)
        logger.info("Screen capture stopped")
    
    def _capture_loop(self):
        """Main capture loop that runs in a separate thread"""
        logger.debug("Capture loop started")
        
        while self.running:
            try:
                # Capture the screen
                self._process_screen()
                
                # Sleep for the scan interval
                time.sleep(self.scan_interval)
            
            except Exception as e:
                logger.error(f"Error in capture loop: {e}", exc_info=True)
                time.sleep(self.scan_interval * 2)  # Wait longer after an error
    
    def _auto_scroll_loop(self):
        """Auto-scroll loop to check for new messages"""
        logger.debug("Auto-scroll loop started")
        
        while self.running:
            try:
                # Check if it's time to scroll
                current_time = time.time()
                if current_time - self.last_scroll_time >= self.scroll_interval:
                    # Scroll down to check for new messages
                    pyautogui.scroll(-300)  # Negative value scrolls down
                    logger.debug("Auto-scrolled down to check for new messages")
                    self.last_scroll_time = current_time
                
                # Sleep briefly to avoid high CPU usage
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in auto-scroll loop: {e}", exc_info=True)
                time.sleep(5.0)  # Wait longer after an error
    
    def _process_screen(self):
        """Process the current screen to find trading signals"""
        # Take a screenshot
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        
        # Check if Discord is visible
        if not self._is_discord_visible(screenshot_cv):
            logger.debug("Discord window not detected")
            return
        
        # First, look for messages from target traders
        trader_regions = self._find_trader_messages(screenshot_cv)
        found_traders = []  # Store which trader was found for each region
        
        # Extract texts from trader regions to identify which trader is in which region
        for i, region in enumerate(trader_regions):
            region_img = self._extract_region(screenshot_cv, region)
            gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
            gray = self._preprocess_for_ocr(gray)
            text = self._extract_text(gray)
            
            # Check which trader this region belongs to with flexible matching
            for trader in self.target_traders:
                # Normalize trader names for comparison - remove special characters and normalize case
                normalized_trader = re.sub(r'[^a-zA-Z0-9]', '', trader.lower())
                normalized_text = text.lower()
                
                # Try different variations of the trader name
                variations = [
                    trader,                                  # Original format (e.g., @Bryce)
                    trader.replace('@', '@-'),              # With hyphen (e.g., @-Bryce)
                    trader.replace('@-', '@'),              # Without hyphen (e.g., @Bryce)
                    normalized_trader,                       # Normalized (e.g., bryce)
                    '@' + normalized_trader.lstrip('@'),     # Add @ if missing
                ]
                
                # Check if any variation is in the text
                if any(var in normalized_text for var in variations):
                    logger.info(f"Found trader match: {trader} in text")
                    found_traders.append(trader)
                    break
            else:
                found_traders.append(None)  # No specific trader identified
        
        # If no traders specified or found, look for any trading signals
        if not trader_regions and not self.target_traders:
            trader_regions = self._find_trading_signals(screenshot_cv)
            found_traders = [None] * len(trader_regions)  # No specific traders for these regions
        
        for i, region in enumerate(trader_regions):
            # Extract the region containing the potential trading signal
            signal_img = self._extract_region(screenshot_cv, region)
            
            # Look for "Unlock Content" button in this region
            unlock_button_region = self._find_unlock_button(signal_img)
            
            if unlock_button_region is not None:
                # Only click button if it's from a trader in our target list or if no filter is applied
                trader = found_traders[i]
                
                if trader is not None:
                    # We have a specific trader - only click if in our list
                    if trader in self.target_traders:
                        logger.info(f"Found unlock button from target trader: {trader}")
                    else:
                        logger.info(f"Ignoring unlock button from non-target trader")
                        continue  # Skip clicking this button
                elif not self.target_traders:
                    # No filtering applied, process all signals
                    logger.info("No trader filtering applied, processing all signals")
                else:
                    # We have target traders but couldn't identify which trader this is from
                    logger.info("Couldn't identify trader for this message, skipping")
                    continue  # Skip this button
                
                # Calculate the absolute position of the button
                x, y, w, h = region
                button_x, button_y, button_w, button_h = unlock_button_region
                abs_button_x = x + button_x + button_w // 2
                abs_button_y = y + button_y + button_h // 2
                
                # Click the button
                logger.info(f"Clicking 'Unlock Content' button at ({abs_button_x}, {abs_button_y})")
                pyautogui.click(abs_button_x, abs_button_y)
                
                # Wait for content to appear
                time.sleep(1.0)
                
                # Take a new screenshot after clicking
                screenshot = pyautogui.screenshot()
                screenshot_np = np.array(screenshot)
                screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
                
                # Extract the updated region
                signal_img = self._extract_region(screenshot_cv, region)
            
            # Convert to grayscale and apply preprocessing for better OCR
            signal_gray = cv2.cvtColor(signal_img, cv2.COLOR_BGR2GRAY)
            signal_gray = self._preprocess_for_ocr(signal_gray)
            
            # Extract text using OCR
            signal_text = self._extract_text(signal_gray)
            
            # If we found a valid signal, add it to the queue
            if self._validate_signal(signal_text):
                logger.info("Trading signal detected")
                logger.debug(f"Signal text: {signal_text}")
                
                # Add to queue if it's not a duplicate of the last processed signal
                if signal_text != self.last_processed_signal:
                    self.signal_queue.put(signal_text)
                    self.last_processed_signal = signal_text
    
    def _is_discord_visible(self, screenshot):
        """
        Check if Discord is visible on the screen
        
        Args:
            screenshot: OpenCV image of the screen
            
        Returns:
            bool: True if Discord is detected, False otherwise
        """
        # This is a simplified implementation
        # In a real implementation, we would look for Discord-specific UI elements
        # For now, we'll assume Discord is always visible
        return True
    
    def _find_trader_messages(self, screenshot):
        """
        Find regions containing messages from target traders
        
        Args:
            screenshot: OpenCV image of the screen
            
        Returns:
            list: List of regions (x, y, width, height) containing trader messages
        """
        if not self.target_traders:
            return []
        
        # Convert to grayscale for text detection
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        # Use OCR to find text
        h, w = gray.shape
        regions = []
        
        # For demonstration, we'll use a simple approach
        # In a real implementation, we would use more sophisticated techniques
        
        # Convert the screenshot to PIL Image for Tesseract
        pil_image = Image.fromarray(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))
        
        # Extract text using Tesseract OCR
        text = pytesseract.image_to_string(pil_image)
        
        # Check if any target trader is mentioned in the text with flexible matching
        for trader in self.target_traders:
            # Normalize trader names for comparison - remove special chars and normalize case
            normalized_trader = re.sub(r'[^a-zA-Z0-9]', '', trader.lower())
            normalized_text = text.lower()
            
            # Try different variations of the trader name
            variations = [
                trader,                                  # Original format (e.g., @Bryce)
                trader.replace('@', '@-'),              # With hyphen (e.g., @-Bryce)
                trader.replace('@-', '@'),              # Without hyphen (e.g., @Bryce)
                normalized_trader,                       # Normalized (e.g., bryce)
                '@' + normalized_trader.lstrip('@'),     # Add @ if missing
            ]
                
            # Check if any variation is in the text
            if any(var in normalized_text for var in variations):
                logger.info(f"Found message from target trader: {trader}")
                # For now, return the whole screen as a region
                # In a real implementation, we would locate the specific message
                regions.append((0, 0, w, h))
                break
        
        return regions
    
    def _find_unlock_button(self, image):
        """
        Find "Unlock Content" button in an image
        
        Args:
            image: OpenCV image to search in
            
        Returns:
            tuple: (x, y, width, height) of button or None if not found
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to highlight text
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        # Look for blue button color (typical Discord button)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([100, 150, 100])
        upper_blue = np.array([140, 255, 255])
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # Find contours in the blue mask
        contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by size and shape (looking for button-like rectangles)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            
            # Check if it looks like a button (rectangular with reasonable aspect ratio)
            if 2.0 > aspect_ratio > 1.5 and w > 100 and h > 30:
                # Extract the button region
                button_roi = gray[y:y+h, x:x+w]
                
                # Use OCR to check if it contains "Unlock Content"
                button_text = pytesseract.image_to_string(button_roi)
                
                if self.unlock_button_text.lower() in button_text.lower():
                    logger.debug(f"Found 'Unlock Content' button at ({x}, {y})")
                    return (x, y, w, h)
        
        return None
    
    def _find_trading_signals(self, screenshot):
        """
        Find regions containing trading signals in Discord
        
        Args:
            screenshot: OpenCV image of the screen
            
        Returns:
            list: List of regions (x, y, width, height) containing trading signals
        """
        # This is a simplified implementation
        # In a real implementation, we would use template matching or ML-based detection
        
        # For now, we'll use a simple approach:
        # 1. Convert to grayscale
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        # 2. Apply thresholding to highlight text
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        # 3. Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 4. Filter contours by size
        regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # Filter by size (adjust these values based on your screen resolution)
            if w > 300 and h > 100 and w < 800 and h < 400:
                regions.append((x, y, w, h))
        
        # For demonstration purposes, just return a region covering the whole screen
        # In a real implementation, we would return actual detected regions
        h, w = screenshot.shape[:2]
        return [(0, 0, w, h)]
    
    def _extract_region(self, screenshot, region):
        """
        Extract a region from the screenshot
        
        Args:
            screenshot: OpenCV image of the screen
            region: Tuple (x, y, width, height) defining the region to extract
            
        Returns:
            OpenCV image of the extracted region
        """
        x, y, w, h = region
        return screenshot[y:y+h, x:x+w]
    
    def _preprocess_for_ocr(self, image):
        """
        Preprocess an image for better OCR results
        
        Args:
            image: Grayscale OpenCV image
            
        Returns:
            Preprocessed image ready for OCR
        """
        # Apply thresholding to make text more visible
        _, thresh = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY_INV)
        
        # Apply noise reduction
        denoised = cv2.GaussianBlur(thresh, (3, 3), 0)
        
        # Apply dilation to make text thicker
        kernel = np.ones((2, 2), np.uint8)
        dilated = cv2.dilate(denoised, kernel, iterations=1)
        
        return dilated
    
    def _extract_text(self, image):
        """
        Extract text from an image using OCR
        
        Args:
            image: Preprocessed grayscale OpenCV image
            
        Returns:
            str: Extracted text
        """
        # Convert OpenCV image to PIL Image for Tesseract
        pil_image = Image.fromarray(image)
        
        # Extract text using Tesseract OCR
        text = pytesseract.image_to_string(pil_image)
        
        return text
    
    def _validate_signal(self, text):
        """
        Validate if the extracted text contains a trading signal
        
        Args:
            text: Extracted text from OCR
            
        Returns:
            bool: True if text contains a valid trading signal, False otherwise
        """
        # First, check if this is from a target trader (if we have targets)
        if self.target_traders:
            trader_found = False
            normalized_text = text.lower()
            
            for trader in self.target_traders:
                # Normalize trader names for comparison - remove special chars and normalize case
                normalized_trader = re.sub(r'[^a-zA-Z0-9]', '', trader.lower())
                
                # Try different variations of the trader name
                variations = [
                    trader,                                  # Original format (e.g., @Bryce)
                    trader.replace('@', '@-'),              # With hyphen (e.g., @-Bryce)
                    trader.replace('@-', '@'),              # Without hyphen (e.g., @Bryce)
                    normalized_trader,                       # Normalized (e.g., bryce)
                    '@' + normalized_trader.lstrip('@'),     # Add @ if missing
                ]
                
                # Check if any variation is in the text
                if any(var in normalized_text for var in variations):
                    trader_found = True
                    logger.info(f"Found target trader {trader} in signal text")
                    break
            
            if not trader_found:
                logger.debug("Signal not from a target trader, ignoring")
                return False
        
        # Check if all required indicators are present
        return all(indicator in text for indicator in self.trading_signal_indicators)
    
    def get_signal(self, timeout=0.1):
        """
        Get the next trading signal from the queue
        
        Args:
            timeout: Time to wait for a signal in seconds
            
        Returns:
            str: Trading signal text or None if no signal is available
        """
        try:
            return self.signal_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def set_target_traders(self, traders):
        """
        Set the list of target traders to filter
        
        Args:
            traders: List of trader handles (e.g., ["@yramki", "@Tareeq"]) or None to disable filtering
        """
        if traders is None or len(traders) == 0:
            logger.info("Trader filtering disabled - no target traders specified")
            self.target_traders = []
        else:
            self.target_traders = traders
            logger.info(f"Updated target traders: {', '.join(traders)}")
            logger.info("Trader filtering active - will only process signals from these traders")
            
            # Print variations we'll be looking for to help with debugging
            for trader in self.target_traders:
                variations = [
                    trader,                                  # Original format
                    trader.replace('@', '@-'),              # With hyphen
                    trader.replace('@-', '@'),              # Without hyphen
                ]
                logger.debug(f"Will recognize variations for {trader}: {', '.join(variations)}")
