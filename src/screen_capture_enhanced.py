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
import atexit
import sys
import traceback

# Import the input controller for more reliable mouse control
try:
    from input_controller import InputController
    HAS_INPUT_CONTROLLER = True
except ImportError:
    HAS_INPUT_CONTROLLER = False
    print("Warning: input_controller module not found, falling back to basic PyAutoGUI")

# Configure PyAutoGUI safety settings
pyautogui.PAUSE = 0.1  # Add small pause between PyAutoGUI commands for stability
pyautogui.FAILSAFE = True  # Enable fail-safe for mouse movement

# Create input controller instance if available
input_controller = None
if HAS_INPUT_CONTROLLER:
    try:
        # Try to create the input controller with the default settings
        input_controller = InputController()
        logger = logging.getLogger(__name__)
        logger.info(f"✅ Using enhanced input controller: {input_controller.controller_type}")
    except Exception as e:
        print(f"Error initializing input controller: {e}")
        input_controller = None

# Create a global emergency cleanup function to ensure mouse is always released
def _emergency_cleanup():
    """Global emergency cleanup to release mouse if program terminates unexpectedly"""
    try:
        if input_controller:
            # Use enhanced controller if available
            input_controller.emergency_cleanup()
            print("Emergency cleanup: Used enhanced input controller")
        else:
            # Fallback to basic PyAutoGUI cleanup
            pyautogui.mouseUp()
            pyautogui.keyUp('shift')
            pyautogui.keyUp('ctrl')
            pyautogui.keyUp('alt')
            screen_width, screen_height = pyautogui.size()
            pyautogui.moveTo(screen_width // 2, screen_height // 2, duration=0.1)
            print("Emergency cleanup: Released mouse buttons and keyboard modifiers")
    except Exception as e:
        print(f"Error during emergency cleanup: {e}")
        traceback.print_exc()

# Register the emergency cleanup function to run on program exit
atexit.register(_emergency_cleanup)

logger = logging.getLogger(__name__)

class ScreenCapture:
    """
    Handles screen capture operations for Discord window
    Detects and captures trading signals with trader filtering
    """
    
    @staticmethod
    def extract_discord_timestamp(text):
        """
        Extract Discord message timestamp from text
        Returns the actual message timestamp, not the current time
        
        Args:
            text: Full text from OCR
            
        Returns:
            str: Timestamp or None if not found
        """
        discord_timestamp = None
        
        try:
            # Prepare a dictionary to track found timestamps and their confidence level
            timestamp_candidates = {}
            
            # Get current time
            current_time = time.localtime()
            current_hour = int(time.strftime("%I", current_time))  # 12-hour format
            current_minute = int(time.strftime("%M", current_time))
            current_hour_24 = int(time.strftime("%H", current_time))  # 24-hour format
            current_am_pm = time.strftime("%p", current_time)  # AM or PM
            
            # Log current time for debugging
            logging.debug(f"Current time: {current_hour}:{current_minute:02d} {current_am_pm} ({current_hour_24}:{current_minute:02d})")
            
            # Strong pattern: Discord bot followed by time - "WG Bot APP 6:17 AM"
            high_confidence_patterns = [
                r'APP\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])',
                r'WG Bot\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])',
                r'Bot\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])',
                r'Today at\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])',
                r'Posted at\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])',
                r'Posted\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])'
            ]
            
            # Check high confidence patterns first
            for pattern in high_confidence_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    match = match.strip()
                    timestamp_candidates[match] = 10  # High confidence score
            
            # Medium confidence - standalone time patterns but near signal text
            medium_confidence_patterns = [
                r'@\w+\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])',  # Time near a @mention
                r'signal\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])', # Time near "signal" word
                r'(\d{1,2}:\d{2}\s*[AaPp][Mm])\s+@',      # Time before @mention
                r'trade\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])'   # Time near "trade" word
            ]
            
            for pattern in medium_confidence_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    match = match.strip()
                    timestamp_candidates[match] = 5  # Medium confidence score
            
            # Lower confidence - general time patterns, but we'll avoid ones matching current time
            general_patterns = [
                r'(\d{1,2}:\d{2}\s*[AaPp][Mm])',  # 5:17 AM or 11:45 PM
                r'(\d{1,2}:\d{2})'                # 5:17 or 23:45 (24-hour format)
            ]
            
            for pattern in general_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    match = match.strip()
                    
                    # Parse the time components
                    is_current_time = False
                    
                    # Try to parse the time
                    try:
                        # Check if this is 12-hour format with AM/PM
                        am_pm_match = re.search(r'([AaPp][Mm])', match)
                        if am_pm_match:
                            # 12-hour format with AM/PM
                            time_parts = re.search(r'(\d{1,2}):(\d{2})', match)
                            if time_parts:
                                hour = int(time_parts.group(1))
                                minute = int(time_parts.group(2))
                                am_pm = am_pm_match.group(1).upper()
                                
                                # Check if this matches current time
                                if (hour == current_hour and 
                                    abs(minute - current_minute) < 3 and  # Within 3 minutes
                                    am_pm[0] == current_am_pm[0]):  # Same AM/PM
                                    is_current_time = True
                        else:
                            # Assume 24-hour format
                            time_parts = re.search(r'(\d{1,2}):(\d{2})', match)
                            if time_parts:
                                hour = int(time_parts.group(1))
                                minute = int(time_parts.group(2))
                                
                                # Check if this matches current time
                                if hour == current_hour_24 and abs(minute - current_minute) < 3:
                                    is_current_time = True
                    except Exception as parse_error:
                        logging.debug(f"Error parsing time {match}: {parse_error}")
                        continue
                    
                    # Only add if it's not the current time
                    if not is_current_time:
                        timestamp_candidates[match] = 2  # Low confidence score
            
            # If we found candidates, return the one with highest confidence
            if timestamp_candidates:
                best_match = max(timestamp_candidates.items(), key=lambda x: x[1])
                logging.debug(f"Selected timestamp: {best_match[0]} (confidence: {best_match[1]})")
                return best_match[0]
            
            # If no timestamp found, return None
            return None
        except Exception as e:
            # In case of any error, return None
            logging.error(f"Error extracting timestamp: {e}")
            return None
    
    def __init__(self, scan_interval=2.0, click_hidden_messages=True, 
                 target_traders=None, monitor_specific_channel=True, channel_name="trades",
                 target_server="Wealth Group", auto_scroll=True, scroll_interval=30.0):
        """
        Initialize the screen capture module
        
        Args:
            scan_interval (float): Time between screen captures in seconds
            click_hidden_messages (bool): Whether to click on hidden messages to reveal them
            target_traders (list): List of trader handles to filter (e.g., ["@yramki", "@Tareeq"])
            monitor_specific_channel (bool): Whether to focus on a specific channel
            channel_name (str): Name of the target Discord channel to monitor (e.g., "trades")
            target_server (str): Name of the target Discord server (e.g., "Wealth Group")
            auto_scroll (bool): Whether to automatically scroll down to check for new messages
            scroll_interval (float): Time between auto-scrolls in seconds
        """
        self.scan_interval = scan_interval
        self.click_hidden_messages = click_hidden_messages
        self.target_traders = target_traders or []
        self.monitor_specific_channel = monitor_specific_channel
        self.channel_name = channel_name
        self.target_server = target_server
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
        logger.info(f"Target Discord server: {self.target_server}")
        logger.info(f"Target Discord channel: {self.channel_name}")
    
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
        """Stop the screen capture thread and clean up resources"""
        logger.info("Stopping screen capture and releasing resources...")
        self.running = False
        
        try:
            # Reset mouse position to center of screen to prevent cursor flickering
            screen_width, screen_height = pyautogui.size()
            pyautogui.moveTo(screen_width // 2, screen_height // 2, duration=0.1)
            
            # Explicitly release any held keys or buttons (safety measure)
            pyautogui.mouseUp()
            pyautogui.keyUp('shift')  # Release common modifier keys
            pyautogui.keyUp('ctrl')
            pyautogui.keyUp('alt')
            
            # Let the system recover briefly
            time.sleep(0.2)
            
            logger.info("✅ Mouse position reset and keys/buttons released")
        except Exception as e:
            logger.error(f"❌ Error during mouse/keyboard cleanup: {e}")
        
        # Safely stop threads
        if self.capture_thread:
            try:
                self.capture_thread.join(timeout=5.0)
                logger.info("✅ Capture thread stopped successfully")
            except Exception as e:
                logger.error(f"❌ Error stopping capture thread: {e}")
                
        if self.scroll_thread:
            try:
                self.scroll_thread.join(timeout=5.0)
                logger.info("✅ Scroll thread stopped successfully")
            except Exception as e:
                logger.error(f"❌ Error stopping scroll thread: {e}")
                
        # Final cleanup
        pyautogui.FAILSAFE = True  # Reset PyAutoGUI to safe mode
        
        logger.info("✅ Screen capture stopped and all resources released")
    
    def _capture_loop(self):
        """Main capture loop that runs in a separate thread"""
        logger.debug("Capture loop started")
        error_count = 0
        
        while self.running:
            try:
                # Reset mouse state before each capture to prevent issues
                if error_count > 0:
                    # After an error, reset mouse state as precaution
                    try:
                        pyautogui.mouseUp()
                        # Let the system stabilize briefly
                        time.sleep(0.1)
                    except Exception as cleanup_error:
                        logger.error(f"Error resetting mouse state: {cleanup_error}")
                
                # Capture the screen with resource management
                self._process_screen()
                
                # Sleep for the scan interval - different interval if we had errors
                if error_count > 0:
                    logger.info("Slowing down capture rate after errors")
                    time.sleep(self.scan_interval * 2)  # Slower rate after errors
                    error_count = max(0, error_count - 1)  # Gradually reduce error count
                else:
                    time.sleep(self.scan_interval)
                
            except Exception as e:
                # Count errors to adjust scan rate
                error_count += 1
                logger.error(f"Error in capture loop (error #{error_count}): {e}", exc_info=True)
                
                # Safety measure - release mouse and reset state
                try:
                    pyautogui.mouseUp()
                    time.sleep(0.2)
                except:
                    pass
                
                # Exponential backoff based on error count
                wait_time = min(self.scan_interval * 2 * error_count, 30)  # Max 30 second backoff
                logger.warning(f"Waiting {wait_time} seconds before next capture attempt")
                time.sleep(wait_time)
                
                # If we've had too many consecutive errors, force restart the loop
                if error_count > 5:
                    logger.critical("Too many errors, resetting capture state")
                    error_count = 0
                    time.sleep(5)  # Give system time to stabilize
    
    def _auto_scroll_loop(self):
        """Auto-scroll loop to check for new messages"""
        logger.debug("Auto-scroll loop started")
        error_count = 0
        consecutive_success = 0
        
        while self.running:
            try:
                # Check if it's time to scroll
                current_time = time.time()
                
                # Use a more conservative scroll interval if we've had errors
                actual_interval = self.scroll_interval
                if error_count > 0:
                    # Gradually increase interval based on error count to reduce system load
                    actual_interval = min(self.scroll_interval * (1 + error_count * 0.5), 60)
                    
                if current_time - self.last_scroll_time >= actual_interval:
                    # Always reset mouse state before scrolling to ensure clean operation
                    try:
                        pyautogui.mouseUp()
                        time.sleep(0.05)  # Very short pause
                    except:
                        pass
                        
                    # Use a smaller scroll amount if we've had errors
                    scroll_amount = -300  # Default scroll amount (negative = down)
                    if error_count > 0:
                        scroll_amount = -150  # Gentler scrolling after errors
                        
                    # Scroll down to check for new messages
                    pyautogui.scroll(scroll_amount)
                    
                    logger.debug(f"Auto-scrolled down to check for new messages (amount: {scroll_amount})")
                    self.last_scroll_time = current_time
                    
                    # Wait briefly after scrolling to let the screen update
                    time.sleep(0.2)
                    
                    # Success tracking
                    consecutive_success += 1
                    if consecutive_success > 5 and error_count > 0:
                        error_count = max(0, error_count - 1)  # Gradually reduce error count after successful scrolls
                        logger.info(f"Scroll stability improving - reducing error count to {error_count}")
                
                # Sleep to avoid high CPU usage - use longer sleep if we've had errors
                sleep_time = 1.0 if error_count == 0 else min(2.0 * error_count, 5.0)
                time.sleep(sleep_time)
                
            except Exception as e:
                # Error tracking
                error_count += 1
                consecutive_success = 0
                
                logger.error(f"Error in auto-scroll loop (error #{error_count}): {e}", exc_info=True)
                
                # Safety measure - explicitly release mouse control
                try:
                    pyautogui.mouseUp()
                except:
                    pass
                
                # Exponential backoff for errors
                wait_time = min(5.0 * error_count, 30)  # Maximum 30 seconds
                logger.warning(f"Pausing auto-scroll for {wait_time} seconds after error")
                time.sleep(wait_time)
                
                # If too many consecutive errors, temporarily disable auto-scroll
                if error_count > 3:
                    logger.warning(f"Too many scroll errors, pausing auto-scroll for 60 seconds")
                    time.sleep(60)
                    error_count = 1  # Reset but keep some caution
    
    def _process_screen(self):
        """Process the current screen to find trading signals"""
        # Take a screenshot
        logger.debug("Taking screenshot...")
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        
        # Log the checking attempt for visibility
        logger.debug(f"📊 Checking if Discord ('{self.target_server}' server, '{self.channel_name}' channel) is visible...")
        
        # Check if Discord is visible
        if not self._is_discord_visible(screenshot_cv):
            logger.warning("❌ Discord verification failed - Discord window not detected or not showing correct server/channel")
            return
        
        logger.info(f"✅ VERIFIED: Discord with '{self.target_server}' server and '{self.channel_name}' channel is visible")
        
        # Check for unlock text directly in the full screenshot
        pil_image = Image.fromarray(cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2RGB))
        full_text = pytesseract.image_to_string(pil_image)
        
        # Look for unlock phrases
        unlock_phrases = ["Unlock Content", "Press the button to unlock", "Click to unlock"]
        unlock_text_found = False
        found_phrase = None
        for phrase in unlock_phrases:
            if phrase.lower() in full_text.lower():
                unlock_text_found = True
                found_phrase = phrase
                logger.info(f"🔍 DIRECT TEXT DETECTION: Found '{phrase}' in screen")
                break
                
        # If we found unlock text, try an immediate direct blue button search and click
        if unlock_text_found:
            logger.info(f"🔍 FOUND UNLOCK TEXT: '{found_phrase}' - Performing direct button search")
            
            # Convert to HSV for color detection
            hsv = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2HSV)
            
            # Apply a VERY permissive blue mask to catch Discord buttons - even lighter blues
            blue_mask = cv2.inRange(hsv, np.array([70, 30, 100]), np.array([200, 255, 255]))
            contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Sort by area (largest first) and look for button-like rectangles
            sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
            
            # Look through the first several contours (Discord's blue button should be among the larger elements)
            direct_click_candidates = []
            
            # Also look for RGB blue directly as a fallback
            rgb_image = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2RGB)
            
            # If we're having detection issues, also use our emergency detection code right away
            emergency_button_candidates = self._find_emergency_buttons(screenshot_cv)
            if emergency_button_candidates:
                logger.warning("🚨 Using emergency button detection as additional source")
                for x, y, w, h, score in emergency_button_candidates[:5]:  # Add top 5 emergency candidates
                    direct_click_candidates.append((x, y, w, h))
                    logger.info(f"🚨 Emergency detection: Found potential button at ({x}, {y}), size: {w}x{h}, score: {score:.2f}")
            
            for i, contour in enumerate(sorted_contours):
                if i >= 30:  # Check more candidates (30 instead of 20)
                    break
                    
                x, y, w, h = cv2.boundingRect(contour)
                # Much more permissive button dimensions
                if 50 < w < 300 and 15 < h < 70:
                    direct_click_candidates.append((x, y, w, h))
                    logger.info(f"📋 Direct search: Found potential button at ({x}, {y}), size: {w}x{h}")
                    
            # If we found candidates, click the most likely one (typical Discord button size)
            best_candidate = None
            best_score = 0
            
            for x, y, w, h in direct_click_candidates:
                # Score based on how close dimensions are to ideal Discord button size (approx 140x35)
                w_score = 1.0 - min(abs(w - 140) / 100.0, 1.0)  # Higher score = closer to 140px width
                h_score = 1.0 - min(abs(h - 35) / 30.0, 1.0)    # Higher score = closer to 35px height
                score = w_score * 0.6 + h_score * 0.4  # Width more important than height
                
                if score > best_score:
                    best_score = score
                    best_candidate = (x, y, w, h)
                    
            if best_candidate:
                x, y, w, h = best_candidate
                click_x = x + w // 2
                click_y = y + h // 2
                
                # Add slight randomness to click position
                random_offset_x = np.random.randint(-5, 6)
                random_offset_y = np.random.randint(-2, 3)
                click_x += random_offset_x
                click_y += random_offset_y
                
                # First try to identify the trader associated with this button
                trader_name = "Unknown"
                for trader in self.target_traders:
                    if trader in full_text:
                        trader_name = trader
                        break
                
                # Extract Discord message timestamp using our helper method
                discord_timestamp = self.extract_discord_timestamp(full_text)
                if discord_timestamp:
                    logger.info(f"📅 Found Discord message timestamp: {discord_timestamp}")
                
                # Also extract our app timestamp
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Combine timestamps if Discord timestamp was found
                timestamp_info = f"time: {timestamp}"
                if discord_timestamp:
                    timestamp_info = f"Discord time: {discord_timestamp}, detected at: {timestamp}"
                
                logger.info(f"🖱️ DIRECT CLICK: Clicking button at ({click_x}, {click_y}), score: {best_score:.2f}, trader: {trader_name}, {timestamp_info}")
                
                try:
                    # Move to position first, then click with safer approach
                    # Using a step-by-step approach gives better control over the process
                    pyautogui.moveTo(click_x, click_y, duration=0.2)  # Move slightly slower for reliability
                    time.sleep(0.2)
                    pyautogui.mouseDown()  # Press the button down
                    time.sleep(0.1)
                    pyautogui.mouseUp()    # Release the button - proper click cycle
                    
                    message_info = f"for trader {trader_name}"
                    if discord_timestamp:
                        message_info = f"for trader {trader_name} (message sent at {discord_timestamp})"
                    logger.info(f"✅ DIRECT CLICK SUCCESSFUL: Button clicked at ({click_x}, {click_y}) {message_info}")
                    
                    # Ensure mouse is released and in a neutral state
                    try:
                        # Move mouse slightly away from the click position to avoid accidental double-clicks
                        pyautogui.moveRel(10, 10, duration=0.1)
                    except:
                        pass
                    
                    # Wait for content to appear - add longer delay to ensure content loads
                    time.sleep(1.5)
                    
                    # Take a new screenshot after clicking to process the revealed content
                    screenshot = pyautogui.screenshot()
                    screenshot_np = np.array(screenshot)
                    screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
                    
                    # Regular processing will continue after this
                except Exception as e:
                    logger.error(f"❌ DIRECT CLICK FAILED: Error clicking button: {e}", exc_info=True)
                    # Always ensure mouse buttons are released after an error
                    try:
                        pyautogui.mouseUp()
                    except:
                        pass
        
        # Continue with the original button detection as a backup
        # First, scan the entire image for "Unlock Content" buttons directly
        # This ensures we find all buttons even if we can't identify trader messages
        logger.debug("Scanning full screen for 'Unlock Content' buttons using standard detection...")
        unlock_button_region = self._find_unlock_button(screenshot_cv)
        
        if unlock_button_region is not None:
            # Button found directly - handle it
            x, y, w, h = unlock_button_region
            abs_button_x = x + w // 2
            abs_button_y = y + h // 2
            
            # Add randomness to click position to mimic human behavior and avoid detection
            random_offset_x = np.random.randint(-5, 6)  # Random offset between -5 and +5 pixels
            random_offset_y = np.random.randint(-2, 3)  # Random offset between -2 and +2 pixels
            click_x = abs_button_x + random_offset_x
            click_y = abs_button_y + random_offset_y
            
            # Try to identify the trader associated with this button
            pil_image = Image.fromarray(cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2RGB))
            full_text = pytesseract.image_to_string(pil_image)
            
            trader_name = "Unknown"
            for trader in self.target_traders:
                if trader in full_text or self._match_trader(trader, full_text):
                    trader_name = trader
                    break
            
            # Extract Discord message timestamp using our helper method
            discord_timestamp = self.extract_discord_timestamp(full_text)
            if discord_timestamp:
                logger.info(f"📅 Found Discord message timestamp: {discord_timestamp}")
            
            # Get timestamp for tracking
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Combine timestamps if Discord timestamp was found
            timestamp_info = f"time: {timestamp}"
            if discord_timestamp:
                timestamp_info = f"Discord time: {discord_timestamp}, detected at: {timestamp}"
                
            # Click the button - force a click even if we're not sure about the trader
            logger.info(f"🖱️ ATTEMPTING TO CLICK: 'Unlock Content' button at ({click_x}, {click_y}), trader: {trader_name}, {timestamp_info}")
            try:
                # Move to position first, then click with safer approach
                # Using a step-by-step approach gives better control over the process
                pyautogui.moveTo(click_x, click_y, duration=0.2)  # Move slightly slower for reliability
                time.sleep(0.2)
                pyautogui.mouseDown()  # Press the button down
                time.sleep(0.1)
                pyautogui.mouseUp()    # Release the button - proper click cycle
                
                message_info = f"for trader {trader_name}"
                if discord_timestamp:
                    message_info = f"for trader {trader_name} (message sent at {discord_timestamp})"
                logger.info(f"✅ CLICK SUCCESSFUL: 'Unlock Content' button clicked at ({click_x}, {click_y}) {message_info}")
                
                # Ensure mouse is released and in a neutral state
                try:
                    # Move mouse slightly away from the click position to avoid accidental double-clicks
                    pyautogui.moveRel(10, 10, duration=0.1)
                except:
                    pass
            except Exception as e:
                logger.error(f"❌ CLICK FAILED: Error clicking button: {e}", exc_info=True)
                # Always ensure mouse buttons are released after an error
                try:
                    pyautogui.mouseUp()
                except:
                    pass
            
            # Wait for content to appear - add longer delay to ensure content loads
            time.sleep(1.5)
            
            # Take a new screenshot after clicking to process the revealed content
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        
        # Look for messages from target traders
        if self.target_traders:
            logger.debug(f"Looking for messages from target traders: {', '.join(self.target_traders)}")
        
        # Get text from the full screenshot for trader detection
        pil_image = Image.fromarray(cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2RGB))
        full_text = pytesseract.image_to_string(pil_image)
        
        # Log if we find trader names in the text
        for trader in self.target_traders:
            if self._match_trader(trader, full_text):
                logger.info(f"📋 Found target trader {trader} in screen text")
        
        # First, look for messages from target traders
        trader_regions = self._find_trader_messages(screenshot_cv)
        
        if not trader_regions:
            if not self.target_traders:
                # If no target traders specified, look for any trading signals
                logger.debug("No trader filtering active - looking for any trading signals")
                trader_regions = self._find_trading_signals(screenshot_cv)
            else:
                logger.debug("No messages from target traders found")
        
        # Add the whole screen as a region to make sure we don't miss anything
        h, w = screenshot_cv.shape[:2]
        all_regions = trader_regions + [(0, 0, w, h)]
        
        for region in all_regions:
            # Extract the region containing the potential trading signal
            signal_img = self._extract_region(screenshot_cv, region)
            
            # Look for trading signals in this region
            signal_gray = cv2.cvtColor(signal_img, cv2.COLOR_BGR2GRAY)
            signal_gray = self._preprocess_for_ocr(signal_gray)
            
            # Extract text using OCR
            signal_text = self._extract_text(signal_gray)
            
            # If we found a valid signal, add it to the queue
            if self._validate_signal(signal_text):
                logger.info("💹 Trading signal detected!")
                logger.debug(f"Signal text: {signal_text}")
                
                # Add to queue if it's not a duplicate of the last processed signal
                if signal_text != self.last_processed_signal:
                    self.signal_queue.put(signal_text)
                    self.last_processed_signal = signal_text
                    logger.info("📊 Signal added to processing queue")
        
        logger.debug("Screen processing complete")
    
    def _is_discord_visible(self, screenshot):
        """
        Check if Discord is visible on the screen and specifically
        - Wealth Group Discord server is selected
        - trades channel within Wealth Group is selected
        
        Args:
            screenshot: OpenCV image of the screen
            
        Returns:
            bool: True if Discord with correct server/channel is detected, False otherwise
        """
        # Convert screenshot to PIL Image for text detection
        pil_image = Image.fromarray(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))
        
        # Use OCR to extract text
        text = pytesseract.image_to_string(pil_image)
        
        # First check for Discord being visible at all
        discord_visible = "Discord" in text
        
        # Look for required specific indicators:
        # 1. Target server (Wealth Group by default) must be present
        server_present = False
        server_patterns = [
            self.target_server, self.target_server.replace(" ", ""), self.target_server.lower(),
            # The title bar often shows URLs like 'discord.com/.../Wealth Group'
            "discord.com/channels/"
        ]
        for pattern in server_patterns:
            if pattern.lower() in text.lower():
                server_present = True
                logger.debug(f"Target server '{self.target_server}' detected via pattern: {pattern}")
                break
        
        # 2. Target channel must be selected (trades by default)
        channel_present = False
        channel_patterns = [
            f"# {self.channel_name}", f"#{self.channel_name}", f"# | {self.channel_name}", f"#{self.channel_name.lower()}", 
            # Many variations on trades channel
            "# trades", "#trades", "# | trades", "channel trades", "in trades", "trades channel",
            # Add common channel indicators for trading channels
            "active-futures", "active-spot", "active-alerts",
            "orderflow", "stocks", "WG Bot", "Bot"
        ]
        for pattern in channel_patterns:
            if pattern.lower() in text.lower():
                channel_present = True
                logger.debug(f"Target channel '{self.channel_name}' detected via pattern: {pattern}")
                break
                
        # If we detect the Wealth Group server and see an "Unlock Content" button,
        # it's highly likely we're in the trades channel (most common place for such buttons)
        if server_present and ("Unlock Content" in text or "Press the button to unlock" in text):
            channel_present = True
            logger.debug(f"Target channel '{self.channel_name}' inferred from 'Unlock Content' button presence")
            
        # If we find both "@Trader" mentions and the server, we're probably in the right channel
        if server_present and any(trader.lower().replace('@', '') in text.lower() for trader in self.target_traders):
            channel_present = True
            logger.debug(f"Target channel '{self.channel_name}' inferred from trader mentions")
        
        # Log what we found for debugging
        indicators_found = []
        if discord_visible:
            indicators_found.append("Discord")
        if server_present:
            indicators_found.append(self.target_server)
        if channel_present:
            indicators_found.append(f"{self.channel_name} channel")
        
        # We need all three conditions to be true
        all_required_visible = discord_visible and server_present and channel_present
        
        # Look for additional supporting indicators that confirm we're in the right place
        supporting_indicators = [
            "Unlock Content",
            "Press the button to unlock",
            "WG Bot", 
            "Only you can see this"
        ]
        
        for indicator in supporting_indicators:
            if indicator.lower() in text.lower():
                indicators_found.append(indicator)
        
        # Log detailed results
        if all_required_visible:
            logger.info(f"✅ Discord '{self.target_server}' server and '{self.channel_name}' channel detected!")
            logger.info(f"   Found indicators: {', '.join(indicators_found)}")
            
            # Look for specific trader mentions
            for trader in self.target_traders:
                base_name = trader.replace('@', '').replace('-', '')
                if base_name.lower() in text.lower():
                    logger.info(f"👤 Target trader mention detected: {trader}")
        else:
            missing = []
            if not discord_visible:
                missing.append("Discord")
            if not server_present:
                missing.append(f"{self.target_server} server")
            if not channel_present:
                missing.append(f"{self.channel_name} channel")
                
            logger.warning(f"⚠️ Discord verification incomplete. Missing: {', '.join(missing)}")
            logger.debug(f"   Found indicators: {', '.join(indicators_found)}")
            
        return all_required_visible
    
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
        
        # Convert the screenshot to PIL Image for Tesseract
        pil_image = Image.fromarray(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))
        
        # Extract text using Tesseract OCR
        text = pytesseract.image_to_string(pil_image)
        text_lower = text.lower()
        
        # Check if any target trader is mentioned in the text using flexible matching
        for trader in self.target_traders:
            # Use flexible matching for trader names
            if self._match_trader(trader, text):
                logger.info(f"Found message from target trader: {trader}")
                # For now, return the whole screen as a region
                # In a real implementation, we would locate the specific message
                regions.append((0, 0, w, h))
                break
        
        return regions
        
    def _match_trader(self, trader, text):
        """
        Use flexible pattern matching to match trader handles
        
        Args:
            trader: Trader handle to match (e.g., @Bryce)
            text: Text to search in
            
        Returns:
            bool: True if trader is found in text using flexible matching
        """
        # Normalize trader names for comparison
        normalized_trader = re.sub(r'[^a-zA-Z0-9]', '', trader.lower())
        normalized_text = text.lower()
        
        # Create variations to test - more variations to handle different formats
        variations = [
            trader,                                  # Original format (e.g., @Bryce)
            trader.replace('@', '@-'),              # With hyphen (e.g., @-Bryce)
            trader.replace('@-', '@'),              # Without hyphen (e.g., @Bryce)
            normalized_trader,                       # Normalized (e.g., bryce)
            '@' + normalized_trader.lstrip('@'),     # Add @ if missing
            '@' + normalized_trader.lstrip('@').capitalize(),  # Capitalized with @ (e.g., @Bryce)
            '@-' + normalized_trader.lstrip('@').capitalize(),  # Capitalized with @- (e.g., @-Bryce)
            '@-' + normalized_trader.lstrip('@'),   # With hyphen but lowercase (e.g., @-bryce)
        ]
        
        # Special patterns for Discord message format
        discord_patterns = [
            f"@{normalized_trader.lstrip('@')}", # For Discord message format
            f"@-{normalized_trader.lstrip('@')}", # For Discord message format with hyphen
        ]
        variations.extend(discord_patterns)
        
        logger.debug(f"Looking for trader '{trader}' with variations: {', '.join(variations)}")
        
        # First check for direct inclusion of variations in the text
        for var in variations:
            if var.lower() in normalized_text:
                logger.info(f"Found trader match: {var} in text")
                return True
        
        # Then check for patterns - especially targeting Discord's format showing: "@Trader"
        patterns = [
            re.compile(r'@' + re.escape(normalized_trader.lstrip('@')) + r'\b', re.IGNORECASE),
            re.compile(r'@-' + re.escape(normalized_trader.lstrip('@')) + r'\b', re.IGNORECASE)
        ]
        
        for pattern in patterns:
            if pattern.search(text):
                logger.info(f"Found trader match using pattern: {pattern.pattern}")
                return True
                
        return False
    
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
        
        # Apply different color ranges to detect Discord's blue buttons
        # Discord's "Unlock Content" button is a blue color
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Try multiple blue color ranges (Discord blue can vary slightly)
        blue_ranges = [
            # Standard Discord blue
            (np.array([100, 150, 100]), np.array([140, 255, 255])),
            # Lighter blue variation
            (np.array([90, 100, 100]), np.array([150, 255, 255])),
            # Another variation
            (np.array([100, 80, 100]), np.array([150, 255, 255])),
            # Wider range to catch more button variations
            (np.array([80, 60, 100]), np.array([160, 255, 255]))
        ]
        
        all_contours = []
        
        for lower_blue, upper_blue in blue_ranges:
            blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
            
            # Find contours in the blue mask
            contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            all_contours.extend(contours)
        
        logger.debug(f"Scanning for 'Unlock Content' buttons, found {len(all_contours)} potential blue elements")
        
        # Also do a direct search for the text "Unlock Content" in the image
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        full_text = pytesseract.image_to_string(pil_image)
        
        # Log full text for debugging
        logger.debug(f"OCR TEXT (full screen): {full_text[:200]}...")
        
        # Expanded text variations to catch more potential buttons
        button_variations = [
            "Unlock Content", "UnlockContent", "Unlock", "UNLOCK CONTENT", 
            "unlock content", "Unlock content", "Press to unlock", "Click to unlock",
            "Press the button to unlock"
        ]
        
        button_text_found = False
        for var in button_variations:
            if var.lower() in full_text.lower():
                logger.info(f"✓ TEXT FOUND: '{var}' text detected in image! Looking for button contours...")
                button_text_found = True
                break
                
        if not button_text_found:
            logger.info("⚠️ No button text variations found in this frame")
            return None
            
        # DIRECT APPROACH: If we found the button text, let's do a direct blue color detection
        # and click the first reasonable button we find
        if button_text_found:
            logger.info("🔍 DIRECT APPROACH: Using simpler button detection based on color and size")
            
            # Apply a very permissive blue mask to catch Discord buttons
            wide_blue_mask = cv2.inRange(hsv, np.array([80, 40, 100]), np.array([170, 255, 255]))
            contours, _ = cv2.findContours(wide_blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Sort contours by size (area)
            sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
            
            # Check a reasonable number of the largest contours
            checked_count = 0
            for contour in sorted_contours:
                checked_count += 1
                if checked_count > 20:  # Only check the 20 largest contours
                    break
                    
                x, y, w, h = cv2.boundingRect(contour)
                
                # Look for button-like dimensions - Discord "Unlock Content" buttons are typically around 140x35 pixels
                if 80 < w < 200 and 25 < h < 50:
                    logger.info(f"🔍 DIRECT MATCH: Found blue button-like element at ({x}, {y}), size: {w}x{h}")
                    
                    # Check if we need to link this to a trader
                    if self.target_traders:
                        # Look above the button for trader names
                        look_up_height = 200
                        message_y = max(0, y - look_up_height)
                        message_roi = gray[message_y:y, max(0, x-100):min(gray.shape[1], x+w+100)]
                        message_text = pytesseract.image_to_string(message_roi)
                        
                        # Check if any target trader is in this region
                        trader_found = False
                        for trader in self.target_traders:
                            if self._match_trader(trader, message_text):
                                logger.info(f"✅ Found button linked to target trader: {trader}")
                                trader_found = True
                                return (x, y, w, h)
                                
                        # If we didn't find a trader but it's our first good button, remember it
                        if not trader_found and checked_count <= 3:  # One of the first 3 buttons
                            logger.info(f"⚠️ No trader found for this button, but using it as best candidate")
                            return (x, y, w, h)
                    else:
                        # No trader filtering, use the first good button
                        logger.info(f"✅ Found button (no trader filtering active)")
                        return (x, y, w, h)
            
        # Process all blue contours to find button-like shapes
        # Filter contours by size and shape (looking for button-like rectangles)
        potential_buttons = []
        
        for contour in all_contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            
            # Check if it looks like a button (rectangular with reasonable aspect ratio)
            # Allow a wider range of aspect ratios and sizes to match Discord's UI
            if 5.0 > aspect_ratio > 1.0 and w >= 60 and h >= 15:
                # Extract the button region
                button_roi = gray[y:y+h, x:x+w]
                
                # Use OCR to check if it contains "Unlock Content"
                button_text = pytesseract.image_to_string(button_roi)
                
                logger.debug(f"Potential button at ({x}, {y}) detected, size: {w}x{h}, text: '{button_text}'")
                
                # Compare with multiple variations of "Unlock Content"
                matches_text = any(var.lower() in button_text.lower() for var in button_variations)
                
                # If it matches our text patterns or if it's a reasonably-sized blue button when we've detected text
                if matches_text or (button_text_found and 100 < w < 200 and 25 < h < 50):
                    # Add to potential buttons list with confidence score
                    score = 1.0  # Base confidence
                    
                    # Boost score for exact matches
                    if "Unlock Content" in button_text:
                        score += 0.5  # Exact match bonus
                    elif "Unlock" in button_text:
                        score += 0.3  # Partial match bonus
                        
                    # Boost score for ideal button dimensions
                    if 120 < w < 180 and 30 < h < 45:
                        score += 0.2  # Ideal dimensions bonus
                    
                    potential_buttons.append((x, y, w, h, score))
                    
        # Sort potential buttons by confidence score
        potential_buttons.sort(key=lambda b: b[4], reverse=True)
        
        # Even if we don't have target traders, process the first potential button we found
        if potential_buttons and not self.target_traders:
            x, y, w, h, _ = potential_buttons[0]
            logger.info(f"✅ Unlock Content button detected with high confidence (no trader filtering)")
            return (x, y, w, h)
        
        # Process potential buttons
        for x, y, w, h, _ in potential_buttons:
            # Try to determine which trader this button belongs to
            # Extract a larger region above the button to find the trader name
            # Look further up to catch the trader name in Discord messages
            message_y = max(0, y - 200)  # Look 200 pixels above the button
            message_height = y - message_y
            message_x = max(0, x - 150)  # Extend more to the left
            message_width = w + 300  # Extend more to the right
            
            logger.debug(f"Checking for trader name in region: {message_x}, {message_y}, {message_width}x{message_height}")
            
            if message_height > 0:
                message_roi = gray[message_y:y, message_x:message_x+message_width]
                message_text = pytesseract.image_to_string(message_roi)
                
                logger.debug(f"Message text near button: {message_text}")
                
                # Check if any target trader is in this message
                trader_in_message = None
                for trader in self.target_traders:
                    if self._match_trader(trader, message_text):
                        trader_in_message = trader
                        break
                
                if trader_in_message:
                    logger.info(f"✅ Found unlock button from target trader: {trader_in_message}")
                    logger.info(f"🔓 UNLOCK: 'Unlock Content' button for trader {trader_in_message}")
                    return (x, y, w, h)
                elif not self.target_traders:
                    # If no trader filtering is active, unlock anyway
                    logger.info(f"✅ Unlock Content button detected (no trader filtering)")
                    return (x, y, w, h)
                else:
                    # If this isn't one of our target traders but it's the first button we found
                    if potential_buttons[0] == (x, y, w, h):
                        logger.info(f"⚠️ Could not verify trader for the button, but clicking anyway as best candidate")
                        return (x, y, w, h)
                    else:
                        # Skip buttons that don't match our target traders
                        logger.info(f"⏭️ Ignoring unlock button from non-target trader.")
                        continue
            else:
                # Couldn't determine trader, but process the button anyway
                logger.info(f"⚠️ Couldn't identify trader for this message, clicking unlock anyway")
                return (x, y, w, h)
        
        # If we found the "Unlock Content" text but no buttons matched, try a last-ditch effort
        if button_text_found and not potential_buttons:
            logger.warning("Found 'Unlock Content' text but couldn't identify button contours. Looking for blue regions...")
            
            # Try to find ANY blue regions that might be buttons
            blue_mask = cv2.inRange(hsv, np.array([80, 40, 100]), np.array([170, 255, 255]))
            contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # Very permissive size filter - just make sure it's reasonable for a button
                if w > 40 and h > 15 and w < 400 and h < 80:
                    logger.info(f"⚠️ Last-ditch effort: Found potential blue button at ({x}, {y}), size: {w}x{h}")
                    return (x, y, w, h)
        
        logger.debug("No 'Unlock Content' buttons found in this frame")
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
            for trader in self.target_traders:
                if self._match_trader(trader, text):
                    logger.info(f"Found target trader {trader} in signal text")
                    trader_found = True
                    break
            
            if not trader_found:
                logger.debug("Signal not from a target trader, ignoring")
                return False
        
        # Check if all required indicators are present
        indicators_present = all(indicator in text for indicator in self.trading_signal_indicators)
        
        if indicators_present:
            logger.info(f"Valid trading signal detected with indicators: {', '.join(self.trading_signal_indicators)}")
        else:
            missing = [i for i in self.trading_signal_indicators if i not in text]
            logger.debug(f"Not a valid trading signal, missing indicators: {', '.join(missing)}")
            
        return indicators_present
    
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
            traders: List of trader handles (e.g., ["@yramki", "@Tareeq"])
        """
        self.target_traders = traders
        logger.info(f"Updated target traders: {', '.join(traders)}")
        
        if traders:
            logger.info("Trader filtering active - will only process signals from these traders")
            # Log some examples of variations that will be matched
            for trader in traders[:2]:  # Just show a couple examples to avoid log spam
                normalized = re.sub(r'[^a-zA-Z0-9]', '', trader.lower())
                variations = [
                    trader,
                    trader.replace('@', '@-'),
                    trader.replace('@-', '@'),
                    '@' + normalized.lstrip('@')
                ]
                logger.debug(f"Will recognize variations for {trader}: {', '.join(variations)}")
        else:
            logger.info("Trader filtering disabled - will process signals from any trader")
            
    def _find_emergency_buttons(self, screenshot):
        """
        Find potential Discord buttons using aggressive detection
        This method is used by both regular detection and emergency detection
        
        Args:
            screenshot: OpenCV image of the screen
            
        Returns:
            List of potential button candidates (x, y, w, h, score)
        """
        logger.debug("Running emergency button detection")
        
        # Convert to RGB for better color detection
        rgb_image = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        height, width = rgb_image.shape[:2]
        
        # Discord buttons are blue - create mask for blues
        # Use direct RGB channel comparison for more reliable detection
        blue_mask = np.zeros((height, width), dtype=np.uint8)
        
        # Condition for Discord blue: blue channel is significantly higher than others
        for y in range(0, height, 2):  # Skip every other row for speed
            for x in range(0, width, 2):  # Skip every other column for speed
                b, g, r = rgb_image[y, x]
                # Discord blue: high blue, medium green, low red
                if b > 120 and b > r + 30 and b > g + 20:
                    blue_mask[y, x] = 255
        
        # Apply morphological operations to clean up the mask
        kernel = np.ones((3, 3), np.uint8)
        blue_mask = cv2.dilate(blue_mask, kernel, iterations=2)
        blue_mask = cv2.erode(blue_mask, kernel, iterations=1)
        
        # Find contours in the mask
        contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Look for button-sized contours
        candidates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter based on size (Discord buttons are typically ~140x35)
            if 50 < w < 300 and 15 < h < 70:
                # Calculate match score based on aspect ratio and size
                ideal_ratio = 140/35  # Ideal width/height ratio
                actual_ratio = w / max(1, h)  # Avoid division by zero
                ratio_score = 1.0 - min(abs(actual_ratio - ideal_ratio) / 2.0, 1.0)
                
                size_score = 1.0 - (abs(w - 140) / 100 + abs(h - 35) / 25) / 2
                
                # Combine scores with ratio being most important
                score = ratio_score * 0.6 + size_score * 0.4
                
                candidates.append((x, y, w, h, score))
        
        # Sort by score (best first)
        candidates.sort(key=lambda x: x[4], reverse=True)
        
        # Return top candidates
        return candidates[:10]  # Return top 10 candidates
    
    def force_click_unlock_button(self):
        """
        Emergency function to detect and click "Unlock Content" buttons
        This bypasses the normal detection process for problematic cases
        """
        logger.warning("🚨 EXECUTING EMERGENCY UNLOCK BUTTON CLICK")
        
        # Take a screenshot
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        
        # First verify Discord is visible before proceeding
        if not self._is_discord_visible(screenshot_cv):
            logger.warning("❌ EMERGENCY BUTTON CLICK ABORTED - Discord not visible")
            return 0
            
        # Log the screen size to help with coordinate debugging
        screen_width, screen_height = pyautogui.size()
        logger.info(f"Screen resolution: {screen_width}x{screen_height}")
            
        # Find blue pixels (Discord button color)
        blue_channel = screenshot_np[:, :, 2]  # Blue channel in RGB
        red_channel = screenshot_np[:, :, 0]    # Red channel
        green_channel = screenshot_np[:, :, 1]  # Green channel
        
        # Discord buttons are blue - where blue is high and red/green are lower
        potential_button_mask = (blue_channel > 120) & (blue_channel > red_channel + 30) & (blue_channel > green_channel + 30)
        
        # Look for button-sized clusters of blue pixels
        # Convert mask to image format OpenCV can process
        mask_image = potential_button_mask.astype(np.uint8) * 255
        
        # Find contours in the mask
        contours, _ = cv2.findContours(mask_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Discord's "Unlock Content" button dimensions are typically around 140px wide x 35px high
        button_candidates = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # Filter based on typical Discord button dimensions
            if 80 < w < 200 and 25 < h < 50:
                # Calculate distance from ideal Discord button size (approx 140x35)
                size_match = 1.0 - (abs(w - 140) / 100 + abs(h - 35) / 25) / 2
                button_candidates.append((x, y, w, h, size_match))
        
        # Sort by match score
        button_candidates.sort(key=lambda x: x[4], reverse=True)
        
        # Click on the best candidates
        click_count = 0
        MAX_CLICKS = 3  # Limit the number of clicks for safety
        
        for x, y, w, h, score in button_candidates:
            if click_count >= MAX_CLICKS:
                break
                
            # Calculate center with slight randomness
            click_x = x + w // 2 + np.random.randint(-3, 4)
            click_y = y + h // 2 + np.random.randint(-2, 3)
            
            # Get text from current screen to identify trader if possible
            screenshot_for_ocr = pyautogui.screenshot()
            screenshot_np_ocr = np.array(screenshot_for_ocr)
            pil_image = Image.fromarray(screenshot_np_ocr)
            full_text = pytesseract.image_to_string(pil_image)
            
            # Try to identify the trader associated with this button
            trader_name = "Unknown"
            for trader in self.target_traders:
                if trader in full_text or self._match_trader(trader, full_text):
                    trader_name = trader
                    break
            
            # Extract Discord message timestamp using our helper method
            discord_timestamp = self.extract_discord_timestamp(full_text)
            if discord_timestamp:
                logger.info(f"📅 Found Discord message timestamp: {discord_timestamp}")
                    
            # Get our application timestamp for tracking
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Combine timestamps if Discord timestamp was found
            timestamp_info = f"time: {timestamp}"
            if discord_timestamp:
                timestamp_info = f"Discord time: {discord_timestamp}, detected at: {timestamp}"
            
            # Get screen size to validate coordinates
            screen_width, screen_height = pyautogui.size()
            
            # Validate and correct coordinates to ensure they're within screen bounds
            if click_x >= screen_width or click_y >= screen_height:
                logger.warning(f"⚠️ Button coordinates ({click_x}, {click_y}) exceed screen bounds ({screen_width}x{screen_height}) - adjusting")
                
                # Normalize to screen dimensions if coordinates are way off
                # This handles cases where resolution detection was incorrect or OCR returned huge values
                if click_x > screen_width:
                    click_x = int((x / screenshot_np.shape[1]) * screen_width)
                if click_y > screen_height:
                    click_y = int((y / screenshot_np.shape[0]) * screen_height)
                
                logger.warning(f"✓ Adjusted coordinates to ({click_x}, {click_y})")
            
            logger.warning(f"🖱️ EMERGENCY CLICK: Attempting to click at ({click_x}, {click_y}), match score: {score:.2f}, trader: {trader_name}, {timestamp_info}")
            
            try:
                # Move mouse and click using safer approach with explicit down/up
                pyautogui.moveTo(click_x, click_y, duration=0.2)
                time.sleep(0.2)
                pyautogui.mouseDown()  # Press the button down
                time.sleep(0.1)
                pyautogui.mouseUp()    # Release the button - proper click cycle
                
                message_info = f"for trader {trader_name}"
                if discord_timestamp:
                    message_info = f"for trader {trader_name} (message sent at {discord_timestamp})"
                logger.warning(f"✅ EMERGENCY CLICK SUCCESSFUL at ({click_x}, {click_y}) {message_info}")
                click_count += 1
                
                # Ensure mouse is released and in a neutral state
                try:
                    # Move mouse slightly away from the click position to avoid accidental double-clicks
                    pyautogui.moveRel(10, 10, duration=0.1)
                except:
                    pass
                
                # Wait between clicks
                time.sleep(1.0)
            except Exception as e:
                logger.error(f"❌ EMERGENCY CLICK FAILED: {e}")
                # Always ensure mouse buttons are released after an error
                try:
                    pyautogui.mouseUp()
                except:
                    pass
                
        if click_count > 0:
            logger.warning(f"✅ CLICKED {click_count} POTENTIAL UNLOCK BUTTONS")
            return True
        else:
            logger.warning("❌ NO SUITABLE BUTTONS FOUND")
            return False
