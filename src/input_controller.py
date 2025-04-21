"""
Input Controller Module for Discord Trading Signal Scraper
Provides a unified interface for multiple input control methods
"""

import logging
import time
import atexit
import os
import platform
import pyautogui
from enum import Enum

# Try to import mac-specific controller
try:
    import src.mac_controller as mac_controller
    MAC_CONTROLLER_AVAILABLE = True
except ImportError:
    mac_controller = None  # Define the variable to avoid unbound errors
    MAC_CONTROLLER_AVAILABLE = False

logger = logging.getLogger(__name__)

class ControllerType(Enum):
    """Enum of available controller types"""
    PYAUTOGUI = "pyautogui"  # Cross-platform PyAutoGUI
    MACOS_NATIVE = "macos_native"  # macOS-specific using AppleScript
    HYBRID = "hybrid"  # Try macOS-specific first, fall back to PyAutoGUI

# Default to PyAutoGUI for compatibility
DEFAULT_CONTROLLER = ControllerType.PYAUTOGUI

# Check if we're on macOS and macOS controller is available
if platform.system() == "Darwin" and MAC_CONTROLLER_AVAILABLE:
    DEFAULT_CONTROLLER = ControllerType.MACOS_NATIVE

# Current active controller
_active_controller = None

def _emergency_cleanup():
    """Global emergency cleanup to release resources"""
    try:
        # Release PyAutoGUI resources
        pyautogui.mouseUp()
        pyautogui.keyUp('shift')
        pyautogui.keyUp('ctrl')
        pyautogui.keyUp('alt')
        
        # Move cursor to a safe location
        screen_width, screen_height = pyautogui.size()
        pyautogui.moveTo(screen_width // 2, screen_height // 2, duration=0.1)
        
        # If macOS controller is active, clean it up too
        if MAC_CONTROLLER_AVAILABLE:
            mac_controller._emergency_cleanup()
            
        logger.info("Emergency cleanup: Released all input control resources")
    except Exception as e:
        logger.error(f"Error during emergency cleanup: {e}")

# Register the emergency cleanup function
atexit.register(_emergency_cleanup)

def set_controller(controller_type=None):
    """
    Set the active input controller
    
    Args:
        controller_type: ControllerType enum value or string name
        
    Returns:
        bool: True if controller was set successfully
    """
    global _active_controller
    
    # If no controller specified, use default
    if controller_type is None:
        controller_type = DEFAULT_CONTROLLER
    
    # Convert string to enum if needed
    if isinstance(controller_type, str):
        try:
            controller_type = ControllerType(controller_type)
        except ValueError:
            logger.error(f"Invalid controller type: {controller_type}")
            return False
    
    # Validate controller type
    if not isinstance(controller_type, ControllerType):
        logger.error(f"Invalid controller type: {controller_type}")
        return False
    
    # Check if macOS controller is required but not available
    if controller_type in [ControllerType.MACOS_NATIVE, ControllerType.HYBRID] and not MAC_CONTROLLER_AVAILABLE:
        logger.warning(f"macOS controller requested but not available. Using PyAutoGUI instead.")
        controller_type = ControllerType.PYAUTOGUI
    
    # Set the active controller
    _active_controller = controller_type
    logger.info(f"Input controller set to: {_active_controller.value}")
    return True

def get_controller():
    """Get the current active controller type"""
    global _active_controller
    if _active_controller is None:
        set_controller()
    return _active_controller

def move_mouse(x, y, duration=0.2):
    """
    Move mouse to specified coordinates
    
    Args:
        x: X coordinate
        y: Y coordinate
        duration: Time to take for the movement (seconds)
        
    Returns:
        bool: True if successful
    """
    controller = get_controller()
    
    try:
        if controller == ControllerType.MACOS_NATIVE:
            return mac_controller.move_mouse(x, y, duration)
        elif controller == ControllerType.HYBRID:
            try:
                return mac_controller.move_mouse(x, y, duration)
            except Exception as e:
                logger.warning(f"macOS move failed ({e}), falling back to PyAutoGUI")
                pyautogui.moveTo(x, y, duration=duration)
                return True
        else:  # PyAutoGUI
            pyautogui.moveTo(x, y, duration=duration)
            return True
    except Exception as e:
        logger.error(f"Failed to move mouse to ({x}, {y}): {e}")
        return False

def click(x, y, duration=0.2):
    """
    Click at the specified coordinates
    
    Args:
        x: X coordinate
        y: Y coordinate
        duration: How long to pause between down and up events
        
    Returns:
        bool: True if successful
    """
    controller = get_controller()
    
    # First validate coordinates against screen bounds
    screen_width, screen_height = get_screen_size()
    if x < 0 or x >= screen_width or y < 0 or y >= screen_height:
        logger.warning(f"Click coordinates ({x}, {y}) outside screen bounds ({screen_width}x{screen_height})")
        x = max(0, min(x, screen_width - 1))
        y = max(0, min(y, screen_height - 1))
        logger.info(f"Adjusted to ({x}, {y})")
    
    try:
        if controller == ControllerType.MACOS_NATIVE:
            return mac_controller.click(x, y, duration)
        elif controller == ControllerType.HYBRID:
            try:
                return mac_controller.click(x, y, duration)
            except Exception as e:
                logger.warning(f"macOS click failed ({e}), falling back to PyAutoGUI")
                # Use PyAutoGUI click with proper down/up sequence
                pyautogui.moveTo(x, y, duration=0.2)
                time.sleep(0.1)
                pyautogui.mouseDown()
                time.sleep(duration)
                pyautogui.mouseUp()
                return True
        else:  # PyAutoGUI
            # Use proper down/up sequence instead of simple click
            pyautogui.moveTo(x, y, duration=0.2)
            time.sleep(0.1)
            pyautogui.mouseDown()
            time.sleep(duration)
            pyautogui.mouseUp()
            return True
    except Exception as e:
        logger.error(f"Failed to click at ({x}, {y}): {e}")
        # Always ensure mouse is released on error
        try:
            pyautogui.mouseUp()
        except:
            pass
        return False

def click_button_by_text(button_text):
    """
    Try to click a button with specific text
    This only works with the macOS controller
    
    Args:
        button_text: Text on the button to click
        
    Returns:
        bool: True if button was found and clicked
    """
    controller = get_controller()
    
    if controller == ControllerType.PYAUTOGUI:
        logger.warning("Button text clicking not supported with PyAutoGUI controller")
        return False
    
    try:
        if controller == ControllerType.MACOS_NATIVE:
            return mac_controller.click_button_by_text(button_text)
        elif controller == ControllerType.HYBRID:
            try:
                return mac_controller.click_button_by_text(button_text)
            except Exception as e:
                logger.warning(f"macOS text button click failed ({e}), PyAutoGUI cannot perform this operation")
                return False
    except Exception as e:
        logger.error(f"Failed to click button with text '{button_text}': {e}")
        return False

def extract_text_from_ui(x=None, y=None, element_type=None):
    """
    Extract text directly from UI elements
    This only works with the macOS controller
    
    Args:
        x: Optional X coordinate to focus search
        y: Optional Y coordinate to focus search
        element_type: Optional type of element to extract text from
        
    Returns:
        dict: Dictionary of extracted text elements with their coordinates or empty dict if not supported
    """
    controller = get_controller()
    
    if controller == ControllerType.PYAUTOGUI:
        logger.warning("UI text extraction not supported with PyAutoGUI controller")
        return {}
    
    try:
        if controller == ControllerType.MACOS_NATIVE:
            return mac_controller.extract_text_from_ui(x, y, element_type)
        elif controller == ControllerType.HYBRID:
            try:
                return mac_controller.extract_text_from_ui(x, y, element_type)
            except Exception as e:
                logger.warning(f"macOS text extraction failed ({e}), PyAutoGUI cannot perform this operation")
                return {}
    except Exception as e:
        logger.error(f"Failed to extract text from UI: {e}")
        return {}

def navigate_to_discord_channel(server_name, channel_name):
    """
    Navigate to a specific Discord channel within a server
    This only works with the macOS controller
    
    Args:
        server_name: Name of the Discord server
        channel_name: Name of the channel within the server
        
    Returns:
        bool: True if navigation was successful, False if failed or not supported
    """
    controller = get_controller()
    
    if controller == ControllerType.PYAUTOGUI:
        logger.warning("Discord channel navigation not supported with PyAutoGUI controller")
        return False
    
    try:
        if controller == ControllerType.MACOS_NATIVE:
            return mac_controller.navigate_to_discord_channel(server_name, channel_name)
        elif controller == ControllerType.HYBRID:
            try:
                return mac_controller.navigate_to_discord_channel(server_name, channel_name)
            except Exception as e:
                logger.warning(f"macOS Discord navigation failed ({e}), PyAutoGUI cannot perform this operation")
                return False
    except Exception as e:
        logger.error(f"Failed to navigate to Discord channel: {e}")
        return False

def get_discord_messages(count=10):
    """
    Extract the most recent Discord messages directly from the UI
    This only works with the macOS controller
    
    Args:
        count: Number of recent messages to extract
        
    Returns:
        list: List of message dictionaries with text, sender, timestamp and coordinates,
              or empty list if not supported
    """
    controller = get_controller()
    
    if controller == ControllerType.PYAUTOGUI:
        logger.warning("Discord message extraction not supported with PyAutoGUI controller")
        return []
    
    try:
        if controller == ControllerType.MACOS_NATIVE:
            return mac_controller.get_discord_messages(count)
        elif controller == ControllerType.HYBRID:
            try:
                return mac_controller.get_discord_messages(count)
            except Exception as e:
                logger.warning(f"macOS Discord message extraction failed ({e}), PyAutoGUI cannot perform this operation")
                return []
    except Exception as e:
        logger.error(f"Failed to extract Discord messages: {e}")
        return []

def focus_app(app_name):
    """
    Ensure the specified app is in focus
    
    Args:
        app_name: Name of the application (e.g., "Discord")
        
    Returns:
        bool: True if app was successfully focused
    """
    controller = get_controller()
    
    try:
        if controller == ControllerType.MACOS_NATIVE and app_name.lower() == "discord":
            return mac_controller.focus_discord()
        elif controller == ControllerType.HYBRID and app_name.lower() == "discord":
            try:
                return mac_controller.focus_discord()
            except Exception as e:
                logger.warning(f"macOS focus failed ({e}), PyAutoGUI cannot perform this operation")
                return False
        else:
            logger.warning(f"Application focusing not supported with PyAutoGUI controller")
            return False
    except Exception as e:
        logger.error(f"Failed to focus application '{app_name}': {e}")
        return False

def capture_screenshot():
    """
    Capture a screenshot of the entire screen
    
    Returns:
        PIL.Image or None: Screenshot as a PIL Image object
    """
    controller = get_controller()
    
    try:
        if controller == ControllerType.MACOS_NATIVE:
            screenshot_path = mac_controller.capture_screenshot()
            if screenshot_path:
                from PIL import Image
                return Image.open(screenshot_path)
            return None
        elif controller == ControllerType.HYBRID:
            try:
                screenshot_path = mac_controller.capture_screenshot()
                if screenshot_path:
                    from PIL import Image
                    return Image.open(screenshot_path)
            except Exception as e:
                logger.warning(f"macOS screenshot failed ({e}), falling back to PyAutoGUI")
                return pyautogui.screenshot()
        else:  # PyAutoGUI
            return pyautogui.screenshot()
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
        return None

def get_screen_size():
    """
    Get the screen dimensions
    
    Returns:
        tuple: (width, height) of the screen
    """
    controller = get_controller()
    
    try:
        if controller == ControllerType.MACOS_NATIVE:
            return mac_controller.get_screen_size()
        elif controller == ControllerType.HYBRID:
            try:
                return mac_controller.get_screen_size()
            except Exception as e:
                logger.warning(f"macOS screen size failed ({e}), falling back to PyAutoGUI")
                return pyautogui.size()
        else:  # PyAutoGUI
            return pyautogui.size()
    except Exception as e:
        logger.error(f"Failed to get screen size: {e}")
        # Return a reasonable default
        return (1440, 900)

# Initialize with default controller
set_controller()

# Test function
def test_controllers():
    """Test all available controllers"""
    print("Testing input controllers...")
    
    controllers_to_test = [ControllerType.PYAUTOGUI]
    if MAC_CONTROLLER_AVAILABLE:
        controllers_to_test.extend([ControllerType.MACOS_NATIVE, ControllerType.HYBRID])
    
    for controller in controllers_to_test:
        print(f"\nTesting {controller.value} controller:")
        set_controller(controller)
        
        # Get screen size
        screen_size = get_screen_size()
        print(f"Screen size: {screen_size[0]}x{screen_size[1]}")
        
        # Move to center
        center_x, center_y = screen_size[0] // 2, screen_size[1] // 2
        print(f"Moving to center ({center_x}, {center_y})...")
        move_mouse(center_x, center_y)
        time.sleep(1)
        
        # Move to each corner
        corners = [
            (50, 50),
            (screen_size[0] - 50, 50),
            (screen_size[0] - 50, screen_size[1] - 50),
            (50, screen_size[1] - 50),
        ]
        
        for i, (x, y) in enumerate(corners):
            print(f"Moving to corner {i+1} ({x}, {y})...")
            move_mouse(x, y)
            time.sleep(0.5)
        
        # Capture screenshot
        print("Capturing screenshot...")
        screenshot = capture_screenshot()
        if screenshot:
            print(f"Screenshot captured: {screenshot.width}x{screenshot.height}")
        else:
            print("Screenshot capture failed")
        
        print(f"{controller.value} controller test completed")
    
    print("\nAll controller tests completed")

if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # Run tests
    test_controllers()