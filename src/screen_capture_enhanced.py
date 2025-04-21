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

# Import the input controller for reliable macOS control
try:
    import src.input_controller as input_controller
    HAS_INPUT_CONTROLLER = True
except ImportError:
    try:
        import input_controller
        HAS_INPUT_CONTROLLER = True
    except ImportError:
        HAS_INPUT_CONTROLLER = False
        print("Error: input_controller module not found. This app requires macOS native controls.")
        sys.exit(1)  # Exit since this is a Mac-only app

# Configure PyAutoGUI safety settings (used as fallback only)
pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True

# Setup logger
logger = logging.getLogger(__name__)

# Create a global emergency cleanup function for macOS
def _emergency_cleanup():
    """Global emergency cleanup for macOS to ensure mouse is released and system resources are freed"""
    try:
        # Use macOS native controller for cleanup
        screen_size = input_controller.get_screen_size()
        center_x, center_y = screen_size[0] // 2, screen_size[1] // 2
        
        # Handle any pressed mouse buttons
        input_controller.release_mouse() if hasattr(input_controller, 'release_mouse') else None
        
        # Reset cursor position to screen center
        input_controller.move_mouse(center_x, center_y)
        
        # Use AppleScript to ensure any stuck key modifiers are released
        if hasattr(input_controller, 'run_applescript'):
            script = '''
            tell application "System Events"
                key up shift
                key up command
                key up option
                key up control
            end tell
            '''
            input_controller.run_applescript(script)
        
        print("macOS emergency cleanup: Released all input controls and reset cursor position")
    except Exception as e:
        print(f"Error during macOS emergency cleanup: {e}")
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
        Extract Discord message timestamp from text with improved accuracy
        Returns the actual message timestamp visible in the current message, not the current time
        
        Args:
            text: Full text from OCR for a specific message region
            
        Returns:
            str: Timestamp or None if not found
        """
        discord_timestamp = None
        
        try:
            # Text should be specific to one message block to avoid timestamp confusion
            text = text.strip()
            
            # Skip processing if text is too short
            if len(text) < 5:
                return None
                
            # Get current time to validate that extracted timestamps are reasonable
            current_time = time.localtime()
            current_hour = int(time.strftime("%I", current_time))  # 12-hour format
            current_minute = int(time.strftime("%M", current_time))
            current_hour_24 = int(time.strftime("%H", current_time))  # 24-hour format
            current_am_pm = time.strftime("%p", current_time)  # AM or PM
            
            # Track timestamp candidates with their confidence scores and positions
            timestamp_candidates = []  # List of (timestamp, confidence, position)
            
            # Discord uses different timestamp formats:
            # 1. Today at 11:02 AM - Full format in Discord header
            # 2. 11:02 AM - Condensed format in messages
            # 3. APP 11:02 AM - Discord bot message prefix
            
            # Check for specific Discord timestamp patterns with exact position
            patterns = [
                # Discord bot with timestamp - highest confidence
                (r'APP\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])', 10),
                (r'WG Bot\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])', 10),
                (r'WG BOT\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])', 10),
                
                # Discord standard timestamp formats - high confidence
                (r'Today at\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])', 9),
                (r'Yesterday at\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])', 9),
                (r'message at\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])', 8),
                
                # Context that helps identify timestamps - medium confidence  
                (r'@\w+\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])', 7),  # @username 11:02 AM
                (r'Posted at\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])', 6),
                (r'sent at\s+(\d{1,2}:\d{2}\s*[AaPp][Mm])', 6),
                
                # Standalone timestamps at beginning of lines - lower confidence
                (r'^\s*(\d{1,2}:\d{2}\s*[AaPp][Mm])', 5),  # 11:02 AM at start of line
                (r'[^\d:](\d{1,2}:\d{2}\s*[AaPp][Mm])', 4),  # 11:02 AM not preceded by numbers
                
                # Generic patterns as fallback - lowest confidence
                (r'(\d{1,2}:\d{2}\s*[AaPp][Mm])', 3),     # Any 11:02 AM pattern as fallback
            ]
            
            # Find all timestamp patterns and record them with position information
            for pattern, confidence in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                    # Extract the timestamp group
                    timestamp = match.group(1).strip() if match.groups() else match.group(0).strip()
                    position = match.start()
                    
                    # Add to candidates with position information
                    timestamp_candidates.append((timestamp, confidence, position))
                    
            # Sort by confidence (high to low), then position (early in text)
            timestamp_candidates.sort(key=lambda x: (-x[1], x[2]))
            
            # No candidates found
            if not timestamp_candidates:
                return None
                
            # Take the highest confidence timestamp
            best_timestamp = timestamp_candidates[0][0]
            
            # Clean and normalize the timestamp format
            best_timestamp = best_timestamp.strip().upper()
            
            # Log the chosen timestamp
            logger.info(f"📅 Found Discord message timestamp: {best_timestamp}")
            
            # Return the best timestamp we found
            return best_timestamp
            
        except Exception as e:
            # In case of any error, return None
            logger.error(f"Error extracting timestamp: {e}")
            return None
    
    def _enhanced_ocr(self, image, preprocess=True):
        """
        Enhanced OCR function with improved preprocessing and consensus algorithm
        
        Args:
            image: OpenCV image to process
            preprocess: Whether to apply preprocessing for better results
            
        Returns:
            str: Extracted text with highest confidence
        """
        try:
            if preprocess:
                # Convert to grayscale if it's not already
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image.copy()
                    
                # Apply different preprocessing techniques to maximize detection chances
                # 1. Basic thresholding
                _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                
                # 2. Adaptive thresholding
                adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                               cv2.THRESH_BINARY, 11, 2)
                
                # 3. Noise reduction
                denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
                
                # 4. Contrast enhancement
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                enhanced = clahe.apply(gray)
                
                # Resize to 2x for better OCR results
                h, w = gray.shape
                resized = cv2.resize(gray, (w*2, h*2), interpolation=cv2.INTER_CUBIC)
                
                # Convert all preprocessed images to PIL for OCR
                pil_binary = Image.fromarray(binary)
                pil_adaptive = Image.fromarray(adaptive)
                pil_denoised = Image.fromarray(denoised)
                pil_enhanced = Image.fromarray(enhanced)
                pil_resized = Image.fromarray(resized)
                pil_original = Image.fromarray(gray)
                
                # Perform OCR on each preprocessed image
                text_binary = pytesseract.image_to_string(pil_binary)
                text_adaptive = pytesseract.image_to_string(pil_adaptive)
                text_denoised = pytesseract.image_to_string(pil_denoised)
                text_enhanced = pytesseract.image_to_string(pil_enhanced)
                text_resized = pytesseract.image_to_string(pil_resized)
                text_original = pytesseract.image_to_string(pil_original)
                
                # Choose the text with the most content (usually the best quality)
                candidates = [
                    (text_binary, len(text_binary)),
                    (text_adaptive, len(text_adaptive)),
                    (text_denoised, len(text_denoised)),
                    (text_enhanced, len(text_enhanced)),
                    (text_resized, len(text_resized)),
                    (text_original, len(text_original))
                ]
                
                # Sort by text length (prefer longer extractions which usually have more information)
                candidates.sort(key=lambda x: x[1], reverse=True)
                
                # Debug logging for the top results only
                logger.debug(f"Top OCR method produced {candidates[0][1]} chars")
                
                return candidates[0][0]  # Return the text with most content
            else:
                # Standard OCR without preprocessing
                pil_image = Image.fromarray(image if len(image.shape) == 2 else 
                                       cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                return pytesseract.image_to_string(pil_image)
        except Exception as e:
            logger.error(f"Error during enhanced OCR: {e}")
            # Fallback to basic OCR
            try:
                pil_image = Image.fromarray(image if len(image.shape) == 2 else 
                                       cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                return pytesseract.image_to_string(pil_image)
            except Exception as fallback_error:
                logger.error(f"Fallback OCR also failed: {fallback_error}")
                return ""
    
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
            logger.info(f"✅ Target traders to monitor: {', '.join(self.target_traders)}")
        else:
            logger.info("⚠️ No target traders configured - monitoring all traders")
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
        
        # Track when we last checked Discord channel
        last_channel_check = 0
        channel_check_interval = 60  # Check if we're in the right channel every minute
        
        # Start by navigating to the correct Discord channel if needed
        if self.monitor_specific_channel:
            logger.info(f"🔍 Navigating to Discord channel '{self.channel_name}' in server '{self.target_server}'...")
            try:
                success = input_controller.navigate_to_discord_channel(self.target_server, self.channel_name)
                if success:
                    logger.info(f"✅ Successfully navigated to Discord channel '{self.channel_name}'")
                else:
                    logger.warning(f"⚠️ Could not automatically navigate to channel '{self.channel_name}'. Please manually navigate to it.")
            except Exception as nav_error:
                logger.error(f"❌ Error during initial channel navigation: {nav_error}")
        
        # Main processing loop
        while self.running:
            try:
                # Reset mouse state before each capture to prevent issues
                if error_count > 0:
                    # After an error, reset mouse state as precaution
                    try:
                        # Use macOS native input control
                        if hasattr(input_controller, 'release_mouse'):
                            input_controller.release_mouse()
                        else:
                            pyautogui.mouseUp()
                        # Let the system stabilize briefly
                        time.sleep(0.1)
                    except Exception as cleanup_error:
                        logger.error(f"Error resetting mouse state: {cleanup_error}")
                
                # Check if we need to verify current Discord channel
                current_time = time.time()
                if self.monitor_specific_channel and (current_time - last_channel_check) > channel_check_interval:
                    try:
                        # First just try to focus Discord
                        input_controller.focus_app("Discord")
                        
                        # Check if we can see the target channel in any UI text elements
                        ui_text = input_controller.extract_text_from_ui()
                        channel_found = False
                        
                        for key, element in ui_text.items():
                            element_text = element.get('text', '').lower()
                            # Look for channel name in UI elements (usually in header)
                            if self.channel_name.lower() in element_text:
                                channel_found = True
                                logger.debug(f"✓ Verified current Discord channel is '{self.channel_name}'")
                                break
                        
                        # If channel not found in UI, try to navigate to it
                        if not channel_found:
                            logger.info(f"🔍 Re-navigating to Discord channel '{self.channel_name}'...")
                            input_controller.navigate_to_discord_channel(self.target_server, self.channel_name)
                        
                        # Update timestamp
                        last_channel_check = current_time
                    except Exception as channel_error:
                        logger.error(f"Error checking Discord channel: {channel_error}")
                
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
                        
                    # Scroll down to check for new messages - use enhanced macOS controls if available
                    try:
                        # First make sure Discord is in focus
                        input_controller.focus_app("Discord")
                        
                        # Use AppleScript to do smooth scrolling in a more reliable way
                        if hasattr(input_controller, 'run_applescript'):
                            # Note: scroll direction is reversed in AppleScript (negative = up in UI, positive = down)
                            # So we need to negate our scroll_amount
                            scroll_script = f'''
                            tell application "System Events"
                                set frontApp to name of first application process whose frontmost is true
                                if frontApp is "Discord" then
                                    tell application process "Discord"
                                        set scrollArea to a reference to (first scroll area of first window)
                                        scroll scrollArea by {{0, {-scroll_amount}}}
                                    end tell
                                end if
                            end tell
                            '''
                            input_controller.run_applescript(scroll_script)
                            logger.debug(f"Used AppleScript for smoother Discord scrolling (amount: {-scroll_amount})")
                        else:
                            # Fall back to PyAutoGUI if needed
                            pyautogui.scroll(scroll_amount)
                            logger.debug(f"Used PyAutoGUI for scrolling (amount: {scroll_amount})")
                    except Exception as scroll_error:
                        # If AppleScript fails, fall back to PyAutoGUI
                        logger.warning(f"AppleScript scrolling failed, falling back to PyAutoGUI: {scroll_error}")
                        pyautogui.scroll(scroll_amount)
                    
                    self.last_scroll_time = current_time
                    
                    # Wait briefly after scrolling to let the screen update
                    time.sleep(0.3)  # Slightly longer wait for macOS animations
                    
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
        
        # Look for both unlock phrases and WG Bot mentions
        unlock_phrases = ["Unlock Content", "Press the button to unlock", "Click to unlock"]
        wg_bot_phrases = ["WG Bot", "Bot"]
        
        unlock_text_found = False
        found_phrase = None
        wg_bot_found = False
        
        # First check for unlock phrases
        for phrase in unlock_phrases:
            if phrase.lower() in full_text.lower():
                unlock_text_found = True
                found_phrase = phrase
                logger.debug(f"🔍 Found '{phrase}' text in screen")
                break
                
        # Check for WG Bot mentions
        for phrase in wg_bot_phrases:
            if phrase in full_text:
                wg_bot_found = True
                logger.debug(f"🔍 Found '{phrase}' in screen")
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
                
                # Use improved trader detection with confidence scoring
                trader_name = "Unknown"
                best_trader = None
                highest_confidence = 0.0
                
                for trader in self.target_traders:
                    # Use our improved confidence-based matching
                    confidence = self._match_trader_with_confidence(trader, full_text)
                    
                    # Only consider reasonably confident matches
                    if confidence > 0.6 and confidence > highest_confidence:
                        highest_confidence = confidence
                        best_trader = trader
                        trader_name = best_trader
                
                # If we're filtering by trader but didn't find a match with high confidence, abort the click
                if self.target_traders and not best_trader and len(self.target_traders) > 0:
                    logger.warning(f"⚠️ No target trader match found with direct text detection - skipping click")
                    logger.debug(f"Target traders: {', '.join(self.target_traders)}")
                    return
                    
                # Extract message timestamp for Discord
                discord_timestamp = self.extract_discord_timestamp(full_text)
                wg_bot_text = "WG Bot"
                    
                # Only log trader detection when we have:
                # 1. A trader name
                # 2. An Unlock Content button
                # 3. Optionally, a WG Bot reference
                if best_trader:
                    # This is the core functionality you requested
                    if wg_bot_found and unlock_text_found:
                        logger.info(f"👤 Target trader mention detected: {best_trader}")
                        logger.info(f"📍 Trader Button Coordinates: ({click_x}, {click_y}), size: {w}x{h}")
                        
                        # Add timestamp info if available
                        if discord_timestamp:
                            logger.info(f"⏰ Message timestamp: {discord_timestamp}")
                    elif unlock_text_found:
                        logger.info(f"👤 Target trader mention detected: {best_trader}")
                        logger.info(f"📍 Trader Button Coordinates: ({click_x}, {click_y}), size: {w}x{h}")
                
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
                
                # Get screen size for safety validation
                screen_width, screen_height = pyautogui.size()
                
                # Define safe margins to avoid triggering PyAutoGUI's failsafe
                safety_margin = 50  # pixels from the edge
                safe_width = screen_width - safety_margin
                safe_height = screen_height - safety_margin
                
                # Validate coordinates before clicking
                if click_x >= safe_width or click_y >= safe_height or click_x <= safety_margin or click_y <= safety_margin:
                    logger.warning(f"⚠️ Button coordinates ({click_x}, {click_y}) outside safe region ({safety_margin}-{safe_width}x{safety_margin}-{safe_height}) - adjusting")
                    
                    # If coordinates are extremely off, use a fallback position
                    if click_x > screen_width * 1.2 or click_y > screen_height * 1.2 or click_x < 0 or click_y < 0:
                        logger.warning("❌ Coordinates extremely out of range - using fallback center position")
                        # Use center of screen with a slight random offset
                        click_x = screen_width // 2 + np.random.randint(-50, 50)  
                        click_y = screen_height // 2 + np.random.randint(-50, 50)
                    else:
                        # Clamp coordinates to safe region
                        click_x = max(safety_margin, min(click_x, safe_width))
                        click_y = max(safety_margin, min(click_y, safe_height))
                    
                    logger.warning(f"✓ Adjusted coordinates to ({click_x}, {click_y})")
                
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
        # First, try to find "Unlock Content" buttons using macOS native Accessibility APIs
        logger.debug("Scanning for 'Unlock Content' buttons using macOS Accessibility APIs...")
        button_found_via_api = False
        button_click_success = False
        button_coordinates = None
        
        try:
            # Check if we have macOS-specific controller features available
            if hasattr(input_controller, 'focus_app'):
                # Try to focus Discord first
                input_controller.focus_app("Discord")
                
                # Try to find and click button by text directly (much more accurate than image detection)
                unlock_button_texts = ["Unlock Content", "Press to unlock", "Click to unlock", "Unlock", "Unlock this"]
                
                # First try using the get_button_coordinates function if available
                # This gives us more reliable coordinate detection and validation
                if hasattr(input_controller, 'get_button_coordinates'):
                    logger.debug("Using enhanced coordinate detection via macOS Accessibility APIs")
                    
                    # Try each possible button text to find coordinates
                    for button_text in unlock_button_texts:
                        coords = input_controller.get_button_coordinates(button_text)
                        if coords and len(coords) == 2 and coords[0] > 0 and coords[1] > 0:
                            # Get screen size for validation
                            screen_width, screen_height = pyautogui.size()
                            
                            # Set safe region
                            safety_margin = 50  # pixels from the edge
                            safe_width = screen_width - safety_margin
                            safe_height = screen_height - safety_margin
                            
                            click_x, click_y = coords
                            
                            # Validate coordinates before using
                            if click_x >= safe_width or click_y >= safe_height or click_x <= safety_margin or click_y <= safety_margin:
                                logger.warning(f"⚠️ Button coordinates ({click_x}, {click_y}) outside safe region ({safety_margin}-{safe_width}x{safety_margin}-{safe_height}) - adjusting")
                                
                                # If coordinates are extremely off, use a fallback position
                                if click_x > screen_width * 1.2 or click_y > screen_height * 1.2 or click_x < 0 or click_y < 0:
                                    logger.warning("❌ Coordinates extremely out of range - using fallback center position")
                                    click_x = screen_width // 2
                                    click_y = screen_height // 2
                                else:
                                    # Clamp coordinates to safe region
                                    click_x = max(safety_margin, min(click_x, safe_width))
                                    click_y = max(safety_margin, min(click_y, safe_height))
                                
                                logger.warning(f"✓ Adjusted coordinates to ({click_x}, {click_y})")
                                
                            # Now we have safe coordinates, perform the click
                            button_found_via_api = True
                            logger.info(f"🖱️ DIRECT CLICK: Clicking button at ({click_x}, {click_y}), trader: {trader_name}, Discord time: {discord_timestamp}, detected at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            # Use direct PyAutoGUI for consistent click mechanism
                            pyautogui.moveTo(click_x, click_y, duration=0.2)
                            time.sleep(0.1)
                            pyautogui.click(click_x, click_y)
                            time.sleep(0.8)  # Wait for click to register
                            
                            button_click_success = True
                            button_coordinates = (click_x, click_y)
                            logger.info(f"✅ DIRECT CLICK SUCCESSFUL: Button clicked at ({click_x}, {click_y}) for trader {trader_name}")
                            break
                
                # If coordinate detection failed, fall back to direct click method
                if not button_found_via_api and hasattr(input_controller, 'click_button_by_text'):
                    logger.debug("Coordinate detection failed, trying direct click via Accessibility APIs")
                    # Try each possible button text with direct clicking
                    for button_text in unlock_button_texts:
                        click_success = input_controller.click_button_by_text(button_text)
                        if click_success:
                            button_found_via_api = True
                            button_click_success = True
                            logger.info(f"✅ Successfully clicked '{button_text}' button using macOS Accessibility APIs")
                            time.sleep(0.8)  # Wait for button click to take effect
                            break
            
            if not button_found_via_api:
                # Fall back to image processing
                logger.debug("No button found via macOS APIs, falling back to standard detection...")
                unlock_button_region = self._find_unlock_button(screenshot_cv)
                
                if unlock_button_region is not None:
                    # Button found directly via image processing - handle it
                    x, y, w, h = unlock_button_region
                    abs_button_x = x + w // 2
                    abs_button_y = y + h // 2
                    
                    # Add randomness to click position to mimic human behavior and avoid detection
                    random_offset_x = np.random.randint(-5, 6)  # Random offset between -5 and +5 pixels
                    random_offset_y = np.random.randint(-2, 3)  # Random offset between -2 and +2 pixels
                    click_x = abs_button_x + random_offset_x
                    click_y = abs_button_y + random_offset_y
                    
                    # Save the coordinates for later use
                    button_coordinates = (click_x, click_y)
                    logger.info(f"📍 Button detected via image processing at coordinates: {button_coordinates}")
        except Exception as api_error:
            logger.error(f"❌ Error using macOS Accessibility APIs for button detection: {api_error}")
            logger.debug("Falling back to standard image-based button detection...")
            
            # Traditional image-based detection as fallback
            unlock_button_region = self._find_unlock_button(screenshot_cv)
            
            if unlock_button_region is not None:
                # Button found directly - handle it
                x, y, w, h = unlock_button_region
                abs_button_x = x + w // 2
                abs_button_y = y + h // 2
                
                # Add randomness to click position to mimic human behavior
                random_offset_x = np.random.randint(-5, 6)  # Random offset between -5 and +5 pixels
                random_offset_y = np.random.randint(-2, 3)  # Random offset between -2 and +2 pixels
                click_x = abs_button_x + random_offset_x
                click_y = abs_button_y + random_offset_y
                
                # Save the coordinates for later use
                button_coordinates = (click_x, click_y)
            
            # Try to identify the trader associated with this button
            pil_image = Image.fromarray(cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2RGB))
            full_text = pytesseract.image_to_string(pil_image)
            
            trader_name = "Unknown"
            best_trader = None
            highest_confidence = 0.0
            
            for trader in self.target_traders:
                # Use our improved confidence-based matching
                confidence = self._match_trader_with_confidence(trader, full_text)
                
                # Only consider reasonably confident matches
                if confidence > 0.6 and confidence > highest_confidence:
                    highest_confidence = confidence
                    best_trader = trader
                    trader_name = f"{trader} [confidence: {confidence:.2f}]"
            
            # If we're filtering by target traders and didn't find a match, don't click
            if self.target_traders and not best_trader and len(self.target_traders) > 0:
                logger.warning(f"⚠️ No target trader match found in button area - skipping click")
                logger.debug(f"Target traders: {', '.join(self.target_traders)}")
                return
            
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
                
            # Validate coordinates before clicking
            screen_width, screen_height = pyautogui.size()
            safety_margin = 50  # pixels from the edge
            safe_width = screen_width - safety_margin
            safe_height = screen_height - safety_margin
            
            # Check if coordinates are outside safe region
            if click_x >= safe_width or click_y >= safe_height or click_x <= safety_margin or click_y <= safety_margin:
                logger.warning(f"⚠️ Button coordinates ({click_x}, {click_y}) outside safe region ({safety_margin}-{safe_width}x{safety_margin}-{safe_height}) - adjusting")
                
                # If coordinates are extremely off, use a fallback center position
                if click_x > screen_width * 1.2 or click_y > screen_height * 1.2 or click_x < 0 or click_y < 0:
                    logger.warning("❌ Coordinates extremely out of range - using fallback center position")
                    click_x = screen_width // 2 + np.random.randint(-50, 50)
                    click_y = screen_height // 2 + np.random.randint(-50, 50)
                else:
                    # Clamp coordinates to safe region
                    click_x = max(safety_margin, min(click_x, safe_width))
                    click_y = max(safety_margin, min(click_y, safe_height))
                
                logger.warning(f"✓ Adjusted coordinates to ({click_x}, {click_y})")
            
            # Click the button - force a click even if we're not sure about the trader
            logger.info(f"🖱️ ATTEMPTING TO CLICK: 'Unlock Content' button at ({click_x}, {click_y}), trader: {trader_name}, {timestamp_info}")
            try:
                # Move to position first, then click with safer approach
                # Using a step-by-step approach gives better control over the process
                # Log detailed click attempt information first
                click_attempt_details = {
                    "coordinates": (click_x, click_y),
                    "trader": trader_name,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "discord_timestamp": discord_timestamp,
                    "button_region": unlock_button_region if 'unlock_button_region' in locals() else None
                }
                logger.info(f"🖱️ Executing click at ({click_x}, {click_y}) for trader {trader_name}")
                
                # Perform the click with precise control
                pyautogui.moveTo(click_x, click_y, duration=0.2)  # Move slightly slower for reliability
                time.sleep(0.2)
                pyautogui.mouseDown()  # Press the button down
                time.sleep(0.1)
                pyautogui.mouseUp()    # Release the button - proper click cycle
                
                # Construct detailed success message
                message_info = f"for trader {trader_name}"
                if discord_timestamp:
                    message_info = f"for trader {trader_name} (message sent at {discord_timestamp})"
                
                # Add more details to success log
                button_type = "detected via image processing"
                if button_found_via_api:
                    button_type = "detected via macOS API"
                
                logger.info(f"✅ CLICK SUCCESSFUL: 'Unlock Content' button ({button_type}) clicked at ({click_x}, {click_y}) {message_info}")
                
                # Ensure mouse is released and in a neutral state
                try:
                    # Move mouse slightly away from the click position to avoid accidental double-clicks
                    pyautogui.moveRel(10, 10, duration=0.1)
                except:
                    pass
            except Exception as e:
                # Record detailed error information
                error_details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "coordinates": (click_x, click_y) if 'click_x' in locals() and 'click_y' in locals() else "Unknown",
                    "trader": trader_name,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                logger.error(f"❌ CLICK FAILED: Error clicking button at {error_details['coordinates']} for trader {trader_name}: {e}", exc_info=True)
                
                # Always ensure mouse buttons are released after an error
                try:
                    pyautogui.mouseUp()
                    logger.info("🖱️ Mouse button released after click failure")
                except Exception as release_error:
                    logger.error(f"❌ Failed to release mouse button: {release_error}")
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
        
        # First, try to get Discord messages using macOS Accessibility APIs
        discord_messages_found = False
        trader_regions = []
        
        try:
            # Check if we have the enhanced macOS capabilities available
            if hasattr(input_controller, 'get_discord_messages'):
                # First, ensure Discord is in focus
                input_controller.focus_app("Discord")
                time.sleep(0.2)  # Small pause to ensure Discord is focused
                
                # Try to get recent Discord messages directly via accessibility APIs
                logger.info("🔍 Attempting to read Discord messages using macOS Accessibility APIs...")
                messages = input_controller.get_discord_messages(count=15)  # Get up to 15 recent messages
                
                if messages and len(messages) > 0:
                    discord_messages_found = True
                    logger.info(f"✅ Successfully retrieved {len(messages)} Discord messages via macOS APIs")
                    
                    # Process each message to look for target traders
                    for message in messages:
                        message_text = message.get('text', '')
                        sender = message.get('sender', '')
                        timestamp = message.get('timestamp', '')
                        coordinates = message.get('coordinates', None)
                        
                        # Combine sender and message text for trader matching
                        full_message = f"{sender}: {message_text}"
                        
                        # Check for target traders in this message
                        for trader in self.target_traders:
                            # Use our improved confidence-based matching
                            confidence = self._match_trader_with_confidence(trader, full_message)
                            
                            if confidence > 0.6:  # Reasonably confident match
                                # Check for the presence of "Unlock Content" button
                                has_unlock_button = False
                                button_coordinates = None
                                
                                # First check via macOS APIs if available
                                if hasattr(input_controller, 'get_button_coordinates'):
                                    for button_text in ["Unlock Content", "Press to unlock", "Click to unlock"]:
                                        coords = input_controller.get_button_coordinates(button_text)
                                        if coords:
                                            has_unlock_button = True
                                            button_coordinates = coords
                                            break
                                
                                # Only log at INFO level if there's an "Unlock Content" button
                                if has_unlock_button:
                                    button_info = f" with UNLOCK BUTTON at {button_coordinates} ✓" if button_coordinates else " with UNLOCK BUTTON ✓"
                                    logger.info(f"👤 Target trader {trader} found in message from '{sender}' [confidence: {confidence:.2f}]{button_info}")
                                    logger.info(f"📱 Message content: {message_text[:100]}...")
                                    if timestamp:
                                        logger.info(f"⏰ Message timestamp: {timestamp}")
                                    
                                    # If we have coordinates, add this as a region to check
                                    if coordinates:
                                        x, y, w, h = coordinates
                                        trader_regions.append((x, y, w, h))
                                        logger.info(f"📍 Message region at ({x}, {y}) with size {w}x{h}")
                                else:
                                    # Log at debug level if no button is found
                                    logger.debug(f"Trader {trader} found in message from '{sender}' but no 'Unlock Content' button detected")
                                    
                                    # Save screenshot with the trader region highlighted
                                    screenshot_file = self._save_screenshot_with_highlight(
                                        screenshot_cv, 
                                        (x, y, w, h),
                                        f"trader_{trader.replace('@', '').replace('-', '_')}_macos_api"
                                    )
                                    if screenshot_file:
                                        logger.info(f"📸 Saved trader detection screenshot: {screenshot_file}")
        except Exception as api_error:
            logger.error(f"❌ Error using macOS Accessibility APIs for message detection: {api_error}")
            logger.debug("Falling back to OCR-based message detection...")
        
        # If no Discord messages found via API, fall back to OCR
        if not discord_messages_found:
            logger.info("⚠️ No Discord messages found via macOS APIs, falling back to OCR...")
            
            # Get text from the full screenshot for trader detection
            pil_image = Image.fromarray(cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2RGB))
            full_text = pytesseract.image_to_string(pil_image)
            
            # Log if we find trader names in the text
            for trader in self.target_traders:
                if self._match_trader(trader, full_text):
                    logger.info(f"📋 Found target trader {trader} in screen text via OCR")
            
            # Look for messages from target traders using image processing
            ocr_trader_regions = self._find_trader_messages(screenshot_cv)
            trader_regions.extend(ocr_trader_regions)
        
        # If we still didn't find any targeted trader messages
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
        # First try to use macOS Accessibility APIs for more accurate detection
        try:
            if hasattr(input_controller, 'extract_text_from_ui'):
                # Ensure Discord app is in focus
                input_controller.focus_app("Discord")
                time.sleep(0.1)  # Short pause to ensure Discord is in focus
                
                # Extract text from UI elements
                ui_elements = input_controller.extract_text_from_ui()
                
                # Track what we found
                discord_visible = False
                server_present = False
                channel_present = False
                
                # Process text elements to find Discord, server, and channel indicators
                for element_id, element_data in ui_elements.items():
                    element_text = element_data.get('text', '').lower()
                    
                    # Check for Discord indicators
                    if "discord" in element_text or "discord.com" in element_text:
                        discord_visible = True
                        logger.debug(f"Discord detected via UI element: '{element_text[:30]}...'")
                    
                    # Check for server indicators
                    if self.target_server.lower() in element_text:
                        server_present = True
                        logger.debug(f"Target server '{self.target_server}' detected via UI element: '{element_text[:30]}...'")
                    
                    # Check for channel indicators - expanded with more pattern variations
                    channel_patterns = [
                        f"#{self.channel_name.lower()}", 
                        f"# {self.channel_name.lower()}", 
                        f"{self.channel_name.lower()} channel",
                        f"{self.channel_name.lower()}",
                        "trades",
                        "channel trades",
                        "trade channel",
                        "trade signals",
                        "signals",
                        "trading",
                        "trading-signals",
                        "trade-signals"
                    ]
                    
                    # If any pattern is found in the UI element text
                    for pattern in channel_patterns:
                        if pattern in element_text:
                            channel_present = True
                            logger.debug(f"Target channel '{self.channel_name}' detected via UI element: '{element_text[:30]}...'")
                            break
                            
                    # Additional heuristic: If we see a message from one of our target traders
                    # in a Discord element, we're likely in the right channel
                    for trader in self.target_traders:
                        trader_name = trader.lower().replace('@', '')
                        if trader_name in element_text and "discord" in element_text.lower():
                            channel_present = True
                            logger.info(f"Target channel '{self.channel_name}' inferred from trader mention: '{trader_name}'")
                            break
                
                # Check for "Unlock Content" buttons as they typically appear in trading channels
                unlock_button_present = False
                for element_id, element_data in ui_elements.items():
                    element_text = element_data.get('text', '').lower()
                    if "unlock" in element_text or "unlock content" in element_text or "press to unlock" in element_text:
                        unlock_button_present = True
                        logger.debug(f"'Unlock Content' button detected via UI element: '{element_text[:30]}...'")
                        break
                
                # Basic detection through Accessibility APIs
                basic_api_detection = discord_visible and (server_present or channel_present)
                
                # If we find unlock buttons in Discord, that's a strong signal we're in the right channel
                alternative_api_detection = discord_visible and unlock_button_present
                
                if basic_api_detection or alternative_api_detection:
                    logger.info("✅ Discord with correct server/channel detected via macOS Accessibility APIs")
                    return True
                
                # If we weren't able to confirm via APIs, fall back to OCR
                logger.debug("Couldn't confirm Discord channel via APIs, falling back to OCR...")
                
        except Exception as api_error:
            logger.warning(f"❌ Error using macOS Accessibility APIs for Discord detection: {api_error}")
            logger.debug("Falling back to OCR-based Discord detection...")
        
        # Fall back to OCR-based detection if API detection fails
        # Use enhanced OCR with multiple preprocessings for more accurate text detection
        text = self._enhanced_ocr(screenshot)
        
        # First check for Discord being visible at all
        discord_visible = "Discord" in text
        
        # Look for required specific indicators:
        # 1. Target server (Wealth Group by default) must be present
        server_present = False
        server_patterns = [
            self.target_server, self.target_server.replace(" ", ""), self.target_server.lower(),
            # The title bar often shows URLs like 'discord.com/.../Wealth Group'
            "discord.com/channels/", "discord.com",
            # Other common Discord UI elements
            "Direct Messages", "Friends", "Mentions"
        ]
        for pattern in server_patterns:
            if pattern.lower() in text.lower():
                server_present = True
                logger.debug(f"Target server '{self.target_server}' detected via OCR pattern: '{pattern}'")
                break
        
        # 2. Target channel must be selected (trades by default)
        channel_present = False
        channel_patterns = [
            f"# {self.channel_name}", f"#{self.channel_name}", f"# | {self.channel_name}", f"#{self.channel_name.lower()}", 
            # Many variations on trades channel
            "# trades", "#trades", "# | trades", "channel trades", "in trades", "trades channel",
            # Add common channel indicators for trading channels
            "active-futures", "active-spot", "active-alerts",
            "orderflow", "stocks", "WG Bot", "Bot",
            # Additional variations with typographic variations
            "channel-trades", "trades-channel", "#-trades", "# - trades",
            # Sometimes OCR might miss spaces
            "channeltrades", "tradeschannel"
        ]
        for pattern in channel_patterns:
            if pattern.lower() in text.lower():
                channel_present = True
                logger.debug(f"Target channel '{self.channel_name}' detected via OCR pattern: '{pattern}'")
                break
                
        # If we detect the Wealth Group server and see an "Unlock Content" button,
        # it's highly likely we're in the trades channel (most common place for such buttons)
        if server_present and any(p.lower() in text.lower() for p in ["Unlock Content", "Press the button to unlock", "Click to unlock"]):
            channel_present = True
            logger.info(f"Target channel '{self.channel_name}' inferred from 'Unlock Content' button presence")
            
        # If we find both "@Trader" mentions and the server, we're probably in the right channel
        if server_present and any(trader.lower().replace('@', '') in text.lower() for trader in self.target_traders):
            channel_present = True
            logger.info(f"Target channel '{self.channel_name}' inferred from trader mentions")
        
        # Log what we found for debugging
        indicators_found = []
        if discord_visible:
            indicators_found.append("Discord")
        if server_present:
            indicators_found.append(self.target_server)
        if channel_present:
            indicators_found.append(f"{self.channel_name} channel")
        
        # Look for additional supporting indicators that confirm we're in the right place
        supporting_indicators = [
            "Unlock Content",
            "Press the button to unlock",
            "WG Bot", 
            "Only you can see this",
            "Click to unlock",
            "Trader",
            "Signal",
            "Message"
        ]
        
        for indicator in supporting_indicators:
            if indicator.lower() in text.lower():
                indicators_found.append(indicator)
                
        # We need all three conditions to be true normally, BUT:
        # If we detect both Discord and unlock buttons, we should assume we're in the right channel
        # This handles cases where detection is imperfect but we're clearly in a trading channel
        basic_detection = discord_visible and server_present and channel_present
        
        # Alternative detection logic: if we detect Discord + "Unlock Content" buttons + any trader name
        # it's almost certainly the right server/channel 
        has_unlock_buttons = any(p.lower() in text.lower() for p in ["Unlock Content", "Press the button to unlock", "Click to unlock"])
        has_trader_mentions = any(trader.lower().replace('@', '') in text.lower() for trader in self.target_traders)
        alternative_detection = discord_visible and has_unlock_buttons and has_trader_mentions
        
        all_required_visible = basic_detection or alternative_detection
        
        # Log detailed results
        if all_required_visible:
            level = "info" if basic_detection else "warning"
            if level == "info":
                logger.info(f"✅ Discord '{self.target_server}' server and '{self.channel_name}' channel detected!")
            else:
                logger.warning(f"💡 Discord detected with trader mentions and unlock buttons - assuming correct channel")
            
            logger.info(f"   Found indicators: {', '.join(indicators_found)}")
            
            # Only log specific trader mentions when there's an "Unlock Content" button
            # This prevents excessive logging
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
    
    def _save_screenshot_with_highlight(self, screenshot, region=None, label=None):
        """
        Save the current screenshot with optional highlighting of a specific region
        
        Args:
            screenshot: OpenCV image of the screen
            region: Optional tuple (x, y, w, h) to highlight
            label: Optional label to add to the filename
        """
        try:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            tag = f"_{label}" if label else ""
            filename = f"discord_capture_{timestamp}{tag}.png"
            
            # Create a copy of the screenshot to draw on
            annotated = screenshot.copy()
            
            # If a region is provided, highlight it
            if region:
                x, y, w, h = region
                cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 255, 0), 2)  # Green rectangle
                
                # Add text label above the region
                if label:
                    cv2.putText(annotated, label, (x, max(0, y-10)), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Save the image
            cv2.imwrite(filename, annotated)
            logger.info(f"📸 Screenshot saved as {filename}")
            
            return filename
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            return None
    
    def _find_trader_messages(self, screenshot):
        """
        Find regions containing messages from target traders with improved accuracy
        and positional awareness to avoid false matches
        
        Args:
            screenshot: OpenCV image of the screen
            
        Returns:
            list: List of regions (x, y, width, height) containing trader messages
        """
        if not self.target_traders:
            return []
        
        # Get dimensions for region calculation
        h, w = screenshot.shape[:2]
        regions = []
        
        # First, divide the screen into message-like regions by looking for Discord's message structure
        # Typically Discord messages have a username at the top left of each message block
        potential_message_regions = self._identify_message_blocks(screenshot)
        
        # If we couldn't identify specific blocks, fall back to whole screen analysis
        # but with higher confidence requirements
        if not potential_message_regions:
            logger.debug("No message blocks identified, using whole screen with high confidence threshold")
            potential_message_regions = [(0, 0, w, h)]
        
        # Check each region for trader mentions
        traders_found = []
        
        # Track what we've already found to avoid duplicates
        already_matched_traders = set()
        
        for region_x, region_y, region_w, region_h in potential_message_regions:
            # Extract the region
            message_region = screenshot[region_y:region_y+region_h, region_x:region_x+region_w]
            
            # Skip tiny regions that can't contain a message
            if message_region.size == 0 or region_w < 100 or region_h < 30:
                continue
                
            # Use OCR with different preprocessing methods on this specific region
            try:
                # Get localized text from this region
                region_text = self._enhanced_ocr(message_region)
                
                # Use higher confidence threshold for smaller regions to avoid false matches
                confidence_threshold = 0.8 if region_w * region_h < (w * h / 4) else 0.6
                
                # Check for specific message-context indicators like timestamp patterns
                # that suggest this is a real Discord message and not other UI elements
                is_likely_message = any(pattern in region_text for pattern in 
                                        ['Today at', 'AM', 'PM', 'message', '@', 'WG Bot', 'Press the button'])
                
                if not is_likely_message:
                    continue
                    
                # Check for trader mentions in this specific block
                for trader in self.target_traders:
                    # Skip traders we've already matched to avoid duplicates
                    if trader in already_matched_traders:
                        continue
                        
                    # Use strict matching with confidence scoring to prevent false matches
                    confidence = self._match_trader_with_confidence(trader, region_text)
                    
                    if confidence > confidence_threshold:
                        # Extract the timestamp from this message if possible
                        timestamp = self.extract_discord_timestamp(region_text)
                        timestamp_info = f" (message sent at {timestamp})" if timestamp else ""
                        
                        # Save screenshot with the trader region highlighted
                        screenshot_file = self._save_screenshot_with_highlight(
                            screenshot, 
                            (region_x, region_y, region_w, region_h),
                            f"trader_{trader.replace('@', '').replace('-', '_')}"
                        )
                        
                        # Before logging trader detection, check if there's an "Unlock Content" button nearby
                        # Extract the region to look for the button
                        message_with_context = screenshot[max(0, region_y-50):min(screenshot.shape[0], region_y+region_h+150), 
                                                        max(0, region_x-50):min(screenshot.shape[1], region_x+region_w+150)]
                        
                        # Check for unlock button in this region
                        unlock_button_region = self._find_unlock_button(message_with_context)
                        has_unlock_button = unlock_button_region is not None
                        
                        # Only log trader detection if there's an "Unlock Content" button nearby
                        if has_unlock_button:
                            # Log detailed information with exact coordinates and button status
                            logger.info(f"👤 Target trader mention detected: {trader}{timestamp_info} [confidence: {confidence:.2f}] with UNLOCK BUTTON ✓")
                            logger.info(f"📍 Trader location: x={region_x}, y={region_y}, width={region_w}, height={region_h}")
                            if screenshot_file:
                                logger.info(f"📸 Saved trader detection screenshot: {screenshot_file}")
                        else:
                            # Just log at debug level if no button is present
                            logger.debug(f"Trader mention found: {trader}{timestamp_info} - but no 'Unlock Content' button nearby")
                            
                        traders_found.append(trader)
                        already_matched_traders.add(trader)
                        
                        # Add this region to our results
                        regions.append((region_x, region_y, region_w, region_h))
                        break
            except Exception as e:
                logger.error(f"Error processing region for trader detection: {e}")
        
        # Log if no traders found after enhanced detection
        if not traders_found:
            logger.debug("No target traders found in visible messages")
        elif len(traders_found) > 1:
            logger.info(f"Multiple traders detected in separate message regions: {', '.join(traders_found)}")
            
        return regions
        
    def _identify_message_blocks(self, screenshot):
        """
        Identify potential Discord message blocks
        
        Args:
            screenshot: OpenCV image of the screen
            
        Returns:
            list: List of regions (x, y, width, height) that could contain messages
        """
        try:
            # In Discord, messages are often separated by vertical space
            # We'll use horizontal line detection to find message boundaries
            
            # Convert to grayscale
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # Use edge detection to find potential message boundaries
            edges = cv2.Canny(gray, 50, 150)
            
            # Find horizontal lines using HoughLinesP
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 
                                    threshold=100, minLineLength=150, maxLineGap=10)
            
            # If no lines detected, fall back to simple division
            if lines is None or len(lines) < 2:
                h, w = screenshot.shape[:2]
                # Divide the screen into 4 equal horizontal sections
                # (Discord messages are usually stacked vertically)
                sections = []
                section_height = h // 4
                for i in range(4):
                    y = i * section_height
                    sections.append((0, y, w, section_height))
                return sections
            
            # Sort lines by y-coordinate to find horizontal message boundaries
            horizontal_lines = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if abs(y2 - y1) < 10:  # Only nearly horizontal lines
                    horizontal_lines.append((min(y1, y2), max(x1, x2) - min(x1, x2)))
            
            # Sort by y-coordinate
            horizontal_lines.sort(key=lambda x: x[0])
            
            # Group nearby lines
            grouped_lines = []
            if horizontal_lines:
                current_group = [horizontal_lines[0]]
                for i in range(1, len(horizontal_lines)):
                    if horizontal_lines[i][0] - current_group[-1][0] < 20:  # Within 20 pixels
                        current_group.append(horizontal_lines[i])
                    else:
                        # Use the line with maximum length in this group
                        max_line = max(current_group, key=lambda x: x[1])
                        grouped_lines.append(max_line[0])  # Use y-coordinate
                        current_group = [horizontal_lines[i]]
                
                # Add last group
                if current_group:
                    max_line = max(current_group, key=lambda x: x[1])
                    grouped_lines.append(max_line[0])
            
            # Convert line positions to message regions
            message_regions = []
            h, w = screenshot.shape[:2]
            
            if len(grouped_lines) < 2:
                # If we couldn't find multiple lines, fall back to simple division
                section_height = h // 4
                for i in range(4):
                    y = i * section_height
                    message_regions.append((0, y, w, section_height))
            else:
                # Use detected lines to define message regions
                for i in range(len(grouped_lines) - 1):
                    y1 = grouped_lines[i]
                    y2 = grouped_lines[i + 1]
                    # Only consider regions taller than 50 pixels
                    if y2 - y1 > 50:
                        message_regions.append((0, y1, w, y2 - y1))
            
            return message_regions
            
        except Exception as e:
            logger.error(f"Error identifying message blocks: {e}")
            # Fall back to simple division of the screen
            h, w = screenshot.shape[:2]
            # Divide into 4 horizontal sections
            return [(0, 0, w, h//4), 
                    (0, h//4, w, h//4), 
                    (0, h//2, w, h//4), 
                    (0, 3*h//4, w, h//4)]
                    
    def _match_trader_with_confidence(self, trader, text):
        """
        Match trader handle with confidence scoring
        
        Args:
            trader: Trader handle to match (e.g., @Bryce)
            text: Text to search in
            
        Returns:
            float: Confidence score (0.0-1.0) where 1.0 is highest confidence
        """
        # Normalize text and trader name
        normalized_trader = re.sub(r'[^a-zA-Z0-9]', '', trader.lower())
        normalized_text = text.lower()
        
        # Start with no confidence
        confidence = 0.0
        
        # Check for exact matches first (highest confidence)
        exact_patterns = [
            f"@{normalized_trader.lstrip('@')}", # Discord's specific format
            f"@-{normalized_trader.lstrip('@')}", # With hyphen
            f"@{normalized_trader.lstrip('@')} "  # With trailing space (common in mentions)
        ]
        
        for pattern in exact_patterns:
            if pattern.lower() in normalized_text:
                # Position-dependent scoring - matches at start of text are more reliable
                # (Discord messages typically start with the username)
                if text.lower().find(pattern.lower()) < len(text) // 3:
                    confidence = max(confidence, 0.95)  # Very high confidence for start of message
                else:
                    confidence = max(confidence, 0.85)  # High confidence for mentions elsewhere
                    
        # Check for context-aware matches
        context_patterns = [
            (f"@{normalized_trader.lstrip('@')}", "Today at", 0.9),  # @User Today at ...
            (f"@{normalized_trader.lstrip('@')}", "message", 0.8),   # @User ... message
            (f"@{normalized_trader.lstrip('@')}", "content", 0.8),   # @User ... content
            (f"@{normalized_trader.lstrip('@')}", "unlock", 0.7),    # @User ... unlock
            (f"@{normalized_trader.lstrip('@')}", ":", 0.7),         # @User: ...
            (normalized_trader.lstrip('@'), "bot", 0.7),             # User ... bot
        ]
        
        for term, context, score in context_patterns:
            if term.lower() in normalized_text and context.lower() in normalized_text:
                # Check if they're reasonably close to each other
                term_pos = normalized_text.find(term.lower())
                context_pos = normalized_text.find(context.lower())
                distance = abs(term_pos - context_pos)
                
                # Closer terms get higher confidence
                if distance < 50:
                    confidence = max(confidence, score)
        
        # Check for partial matches (lower confidence)
        if normalized_trader.lstrip('@') in normalized_text:
            # Make sure it's a meaningful match - avoid matching small sections of other words
            # (e.g., "@Jo" shouldn't match "Johnson")
            if len(normalized_trader.lstrip('@')) >= 3:
                confidence = max(confidence, 0.5)
                
                # Look for trader name near message timestamp indicators
                if any(time_indicator in text for time_indicator in ["AM", "PM", "Today at"]):
                    confidence = max(confidence, 0.6)
        
        # Log match details for debugging at debug level only
        if confidence > 0:
            logger.debug(f"Trader '{trader}' matched with confidence {confidence:.2f}")
            
        return confidence
        
    def _match_trader(self, trader, text):
        """
        Use flexible pattern matching to match trader handles
        Legacy method maintained for backward compatibility
        Use _match_trader_with_confidence for better accuracy
        
        Args:
            trader: Trader handle to match (e.g., @Bryce)
            text: Text to search in
            
        Returns:
            bool: True if trader is found in text using flexible matching
        """
        # Use our improved confidence-based matching, but maintain binary output for backward compatibility
        confidence = self._match_trader_with_confidence(trader, text)
        result = confidence >= 0.6  # Only consider reasonably confident matches
        
        if result:
            logger.info(f"Found trader match: {trader} in text (confidence: {confidence:.2f})")
        
        return result
    
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
        
        # Use our enhanced OCR for better text detection
        full_text = self._enhanced_ocr(image)
        
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
                
                # Check if any target trader is in this message with improved confidence scoring
                trader_in_message = None
                highest_confidence = 0.0
                trader_timestamp = None
                
                for trader in self.target_traders:
                    # Use our improved confidence-based matching
                    confidence = self._match_trader_with_confidence(trader, message_text)
                    
                    # Only consider reasonably confident matches
                    if confidence > 0.6 and confidence > highest_confidence:
                        # Extract the timestamp from this specific message region to ensure proper association
                        timestamp = self.extract_discord_timestamp(message_text)
                        
                        # Store the best match
                        highest_confidence = confidence
                        trader_in_message = trader
                        trader_timestamp = timestamp
                
                if trader_in_message:
                    timestamp_info = f" (message sent at {trader_timestamp})" if trader_timestamp else ""
                    logger.info(f"✅ Found unlock button from target trader: {trader_in_message}{timestamp_info} [confidence: {highest_confidence:.2f}]")
                    logger.info(f"🔓 UNLOCK: 'Unlock Content' button for trader {trader_in_message}")
                    return (x, y, w, h)
                elif not self.target_traders:
                    # If no trader filtering is active, unlock anyway
                    logger.info(f"✅ Unlock Content button detected (no trader filtering)")
                    return (x, y, w, h)
                else:
                    # If this isn't one of our target traders but it's the first button we found
                    if potential_buttons[0] == (x, y, w, h):
                        # Try to extract timestamp anyway for logging
                        timestamp = self.extract_discord_timestamp(message_text)
                        timestamp_info = f" (message sent at {timestamp})" if timestamp else ""
                        
                        logger.info(f"⚠️ Could not verify trader for the button{timestamp_info}, but clicking anyway as best candidate")
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
            best_trader = None
            highest_confidence = 0.0
            message_timestamp = None
            
            for trader in self.target_traders:
                # Use our improved confidence-based matching
                confidence = self._match_trader_with_confidence(trader, text)
                
                # Only consider reasonably confident matches
                if confidence > 0.6 and confidence > highest_confidence:
                    highest_confidence = confidence
                    best_trader = trader
                    
                    # Try to extract timestamp while we're at it
                    message_timestamp = self.extract_discord_timestamp(text)
            
            if best_trader:
                timestamp_info = f" (message from {message_timestamp})" if message_timestamp else ""
                logger.info(f"✅ Found target trader {best_trader}{timestamp_info} in signal text [confidence: {highest_confidence:.2f}]")
                trader_found = True
            
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
        # Convert to int32 to prevent overflow in addition operations
        blue_channel_int = blue_channel.astype(np.int32)
        red_channel_int = red_channel.astype(np.int32)
        green_channel_int = green_channel.astype(np.int32)
        
        # Create mask using integers to prevent overflow
        potential_button_mask = (blue_channel_int > 120) & (blue_channel_int > (red_channel_int + 30)) & (blue_channel_int > (green_channel_int + 30))
        
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
            
            # Try to identify the trader associated with this button using improved confidence matching
            trader_name = "Unknown"
            highest_confidence = 0.0
            best_trader = None
            
            for trader in self.target_traders:
                # Use our improved confidence-based matching
                confidence = self._match_trader_with_confidence(trader, full_text)
                
                # Only consider reasonably confident matches
                if confidence > 0.6 and confidence > highest_confidence:
                    highest_confidence = confidence
                    best_trader = trader
                    trader_name = f"{trader} [confidence: {confidence:.2f}]"
            
            # If we're filtering by trader but didn't find a match with high confidence, abort the click
            if self.target_traders and not best_trader and len(self.target_traders) > 0:
                logger.warning(f"⚠️ No target trader match found in emergency detection - aborting click")
                logger.debug(f"Target traders: {', '.join(self.target_traders)}")
                return False
            
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
            # Define safe margins to avoid triggering PyAutoGUI's failsafe
            safety_margin = 50  # pixels from the edge
            safe_width = screen_width - safety_margin
            safe_height = screen_height - safety_margin
            
            # Check if coordinates are well outside screen or too close to edges
            if click_x >= safe_width or click_y >= safe_height or click_x <= safety_margin or click_y <= safety_margin:
                logger.warning(f"⚠️ Button coordinates ({click_x}, {click_y}) outside safe region ({safety_margin}-{safe_width}x{safety_margin}-{safe_height}) - adjusting")
                
                # If coordinates are extremely off, use a fallback position near the center of the screen
                if click_x > screen_width * 1.2 or click_y > screen_height * 1.2 or click_x < 0 or click_y < 0:
                    logger.warning("❌ Coordinates extremely out of range - using fallback center position")
                    # Use center of screen with a slight random offset
                    click_x = screen_width // 2 + np.random.randint(-50, 50)  
                    click_y = screen_height // 2 + np.random.randint(-50, 50)
                else:
                    # Clamp coordinates to safe region
                    click_x = max(safety_margin, min(click_x, safe_width))
                    click_y = max(safety_margin, min(click_y, safe_height))
                
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
