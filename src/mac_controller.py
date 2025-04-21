"""
Mac-specific control module for Discord Trading Signal Scraper
Provides native macOS functionality for more reliable automation
"""

import subprocess
import time
import logging
import atexit

logger = logging.getLogger(__name__)

# Global tracking for cleanup
_mouse_pressed = False

def _emergency_cleanup():
    """Emergency cleanup to ensure mouse is released if program terminates unexpectedly"""
    if _mouse_pressed:
        try:
            release_mouse()
            logger.info("Emergency cleanup: Released mouse button")
        except Exception as e:
            logger.error(f"Error during emergency mouse cleanup: {e}")
    
    # Reset mouse position to center of screen
    try:
        screen_size = get_screen_size()
        center_x, center_y = screen_size[0] // 2, screen_size[1] // 2
        move_mouse(center_x, center_y)
        logger.info(f"Emergency cleanup: Reset mouse position to center ({center_x}, {center_y})")
    except Exception as e:
        logger.error(f"Error resetting mouse position: {e}")

# Register emergency cleanup
atexit.register(_emergency_cleanup)

def run_applescript(script):
    """
    Run an AppleScript and return the result
    
    Args:
        script: AppleScript code to run
        
    Returns:
        str: Output from the script
    """
    try:
        result = subprocess.run(['osascript', '-e', script], 
                             capture_output=True, text=True)
        if result.returncode != 0 and result.stderr:
            logger.error(f"AppleScript error: {result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Failed to run AppleScript: {e}")
        return None

def get_screen_size():
    """
    Get the main screen dimensions using AppleScript
    
    Returns:
        tuple: (width, height) of the main screen
    """
    script = '''
    tell application "Finder"
        set screenSize to bounds of window of desktop
        return item 3 of screenSize & "," & item 4 of screenSize
    end tell
    '''
    result = run_applescript(script)
    if result:
        try:
            width, height = result.split(',')
            return (int(width), int(height))
        except Exception as e:
            logger.error(f"Error parsing screen size: {e}")
    
    # Fallback to a common resolution if we couldn't get the actual size
    logger.warning("Could not determine screen size, using default 1440x900")
    return (1440, 900)

def move_mouse(x, y, duration=0.1):
    """
    Move mouse to specified coordinates smoothly
    
    Args:
        x: X coordinate
        y: Y coordinate
        duration: Time to take for the movement (seconds)
    """
    # Validate coordinates
    screen_width, screen_height = get_screen_size()
    if x < 0 or x >= screen_width or y < 0 or y >= screen_height:
        logger.warning(f"Coordinates ({x}, {y}) outside screen bounds ({screen_width}x{screen_height})")
        x = max(0, min(x, screen_width - 1))
        y = max(0, min(y, screen_height - 1))
        logger.info(f"Adjusted to ({x}, {y})")
    
    script = f'''
    tell application "System Events"
        set mousePosition to {{current_location}}
        set xStart to item 1 of mousePosition
        set yStart to item 2 of mousePosition
        set xEnd to {x}
        set yEnd to {y}
        
        -- Move in small steps for smoother motion
        set steps to 10
        repeat with i from 1 to steps
            set progress to i / steps
            set xNow to xStart + ((xEnd - xStart) * progress)
            set yNow to yStart + ((yEnd - yStart) * progress)
            set cursor position to {{xNow, yNow}}
            delay {duration / 10}
        end repeat
    end tell
    '''
    run_applescript(script)
    logger.debug(f"Moved mouse to ({x}, {y})")

def press_mouse():
    """Press the left mouse button down"""
    global _mouse_pressed
    script = '''
    tell application "System Events"
        set mousePosition to {{current_location}}
        tell application "System Events" to key down {button down}
    end tell
    '''
    run_applescript(script)
    _mouse_pressed = True
    logger.debug("Mouse button pressed")

def release_mouse():
    """Release the left mouse button"""
    global _mouse_pressed
    script = '''
    tell application "System Events"
        tell application "System Events" to key up {button down}
    end tell
    '''
    run_applescript(script)
    _mouse_pressed = False
    logger.debug("Mouse button released")

def click(x, y, duration=0.2):
    """
    Click at the specified coordinates with proper mouse down/up sequence
    
    Args:
        x: X coordinate
        y: Y coordinate
        duration: How long to pause between down and up events
    """
    try:
        # Move to position
        move_mouse(x, y)
        time.sleep(0.1)  # Small pause after movement
        
        # Click with proper down/up sequence
        press_mouse()
        time.sleep(duration)  # Keep button pressed for specified duration
        release_mouse()
        
        # Log the successful click
        logger.info(f"✅ Click successful at ({x}, {y})")
        return True
    except Exception as e:
        logger.error(f"❌ Click failed at ({x}, {y}): {e}")
        # Always make sure mouse is released on error
        try:
            release_mouse()
        except:
            pass
        return False

def capture_screenshot():
    """
    Capture a screenshot of the entire screen
    
    Returns:
        str: Path to the saved screenshot
    """
    import tempfile
    import os
    
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    temp_file.close()
    
    # Capture screenshot using screencapture
    try:
        subprocess.run(['screencapture', '-x', temp_file.name], 
                      check=True, capture_output=True)
        logger.debug(f"Screenshot captured to {temp_file.name}")
        return temp_file.name
    except subprocess.CalledProcessError as e:
        logger.error(f"Screenshot capture failed: {e}")
        # Clean up the file if it failed
        try:
            os.unlink(temp_file.name)
        except:
            pass
        return None

def focus_discord():
    """
    Ensure Discord app is in focus
    
    Returns:
        bool: True if Discord was successfully focused
    """
    script = '''
    tell application "Discord"
        activate
        delay 0.5  -- Give it time to come to foreground
    end tell
    
    -- Verify Discord is frontmost
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
        return frontApp is "Discord"
    end tell
    '''
    result = run_applescript(script)
    if result and result.lower() == "true":
        logger.info("Discord application focused")
        return True
    else:
        logger.warning("Could not focus Discord application")
        return False

def click_button_by_text(button_text):
    """
    Try to click a button with specific text using macOS Accessibility APIs
    This is more reliable than looking for specific colors or coordinates
    
    Args:
        button_text: Text on the button to click
        
    Returns:
        bool: True if button was found and clicked
    """
    script = f'''
    tell application "System Events"
        tell process "Discord"
            set buttonFound to false
            
            -- Try to find button by its name/title
            try
                set allButtons to every button
                repeat with aButton in allButtons
                    if name of aButton contains "{button_text}" then
                        click aButton
                        set buttonFound to true
                        exit repeat
                    end if
                end repeat
            end try
            
            -- Try to find UI elements with the button text
            if not buttonFound then
                set allElements to every UI element
                repeat with anElement in allElements
                    try
                        if name of anElement contains "{button_text}" or description of anElement contains "{button_text}" then
                            click anElement
                            set buttonFound to true
                            exit repeat
                        end if
                    end try
                end repeat
            end if
            
            return buttonFound
        end tell
    end tell
    '''
    result = run_applescript(script)
    if result and result.lower() == "true":
        logger.info(f"Successfully clicked button with text '{button_text}' using accessibility APIs")
        return True
    else:
        logger.warning(f"Could not find button with text '{button_text}' using accessibility APIs")
        return False

# Test function to verify functionality
def test_mac_controller():
    """Run a quick test of the controller's functionality"""
    screen_size = get_screen_size()
    print(f"Screen size: {screen_size[0]}x{screen_size[1]}")
    
    # Move to center of screen
    center_x, center_y = screen_size[0] // 2, screen_size[1] // 2
    print(f"Moving to center: ({center_x}, {center_y})")
    move_mouse(center_x, center_y)
    time.sleep(1)
    
    # Capture a screenshot
    screenshot_path = capture_screenshot()
    print(f"Screenshot saved to: {screenshot_path}")
    
    print("Test completed successfully")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # Run the test
    test_mac_controller()