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
            
            -- Try to find by role description (more specific to Discord UI patterns)
            if not buttonFound then
                set allUIElements to every UI element
                repeat with theElement in allUIElements
                    try
                        set elementRole to role description of theElement
                        set elementDesc to description of theElement
                        
                        -- Check both role description and value for button text
                        if (elementRole is "button" and (description of theElement contains "{button_text}" or value of theElement contains "{button_text}")) then
                            click theElement
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

def extract_text_from_ui(x=None, y=None, element_type=None):
    """
    Extract text directly from UI elements using macOS Accessibility APIs
    Much more accurate than OCR for readable text in the UI
    
    Args:
        x: Optional X coordinate to focus search
        y: Optional Y coordinate to focus search
        element_type: Optional type of element to extract text from (text field, etc)
        
    Returns:
        dict: Dictionary of extracted text elements with their coordinates
    """
    # If coordinates provided, create a more focused search
    position_filter = ""
    if x is not None and y is not None:
        # Create a bounding box filter (+/- 200 pixels from point)
        position_filter = f'''
            -- Only look at elements near the target coordinates
            set targetX to {x}
            set targetY to {y}
            set xMin to targetX - 200
            set xMax to targetX + 200
            set yMin to targetY - 200
            set yMax to targetY + 200
            
            -- Filter by elements within the bounding box
            set isInBounds to (xPos ≥ xMin and xPos ≤ xMax and yPos ≥ yMin and yPos ≤ yMax)
            if not isInBounds then
                exit repeat
            end if
        '''
    
    # Type filter if provided
    type_filter = ""
    if element_type:
        type_filter = f'if role description of theElement is not "{element_type}" then exit repeat'
    
    script = f'''
    tell application "System Events"
        tell process "Discord"
            set textElements to {{}}
            
            -- Get all UI elements
            set allUIElements to every UI element
            repeat with theElement in allUIElements
                try
                    -- Get position of element (to filter or return)
                    set elementPosition to position of theElement
                    set xPos to item 1 of elementPosition
                    set yPos to item 2 of elementPosition
                    
                    {position_filter}
                    {type_filter}
                    
                    -- Try to get text from different properties
                    set hasText to false
                    set elementText to ""
                    
                    -- Try name property first (most common)
                    try
                        if name of theElement is not "" then
                            set elementText to name of theElement
                            set hasText to true
                        end if
                    end try
                    
                    -- Try value property if name didn't work
                    if not hasText then
                        try
                            if value of theElement is not "" then
                                set elementText to value of theElement
                                set hasText to true
                            end if
                        end try
                    end if
                    
                    -- Try description as last resort
                    if not hasText then
                        try
                            if description of theElement is not "" then
                                set elementText to description of theElement
                                set hasText to true
                            end if
                        end try
                    end if
                    
                    -- If we found text, add it to our results
                    if hasText and elementText is not "" then
                        -- Prepare data for the result
                        set elementData to {{text:elementText, x:xPos, y:yPos}}
                        
                        -- Add to results
                        set textElements to textElements & elementData
                    end if
                end try
            end repeat
            
            return textElements
        end tell
    end tell
    '''
    
    result = run_applescript(script)
    if not result:
        logger.warning("Failed to extract text from UI elements")
        return {}
    
    # Parse the result into a dictionary
    parsed_results = {}
    
    # The result comes back as a string representation of the AppleScript list
    # We need to parse it into a Python data structure
    try:
        # Split into separate elements
        elements = result.split("}, {")
        for i, element in enumerate(elements):
            # Clean up the format for the first and last element
            if i == 0:
                element = element.replace("{", "")
            if i == len(elements) - 1:
                element = element.replace("}", "")
                
            # Parse the text and coordinates
            element_data = {}
            for pair in element.split(", "):
                try:
                    key, value = pair.split(":")
                    if key == "text":
                        element_data[key] = value
                    else:  # x or y
                        element_data[key] = int(value)
                except ValueError:
                    continue
                    
            # Add to results if we got both text and coordinates
            if "text" in element_data and "x" in element_data and "y" in element_data:
                key = f"text_{i}"
                parsed_results[key] = element_data
        
    except Exception as e:
        logger.error(f"Error parsing UI text extraction results: {e}")
    
    logger.info(f"Extracted {len(parsed_results)} text elements from Discord UI")
    return parsed_results

def navigate_to_discord_channel(server_name, channel_name):
    """
    Navigate to a specific Discord channel within a server
    Much more reliable than trying to find it visually
    
    Args:
        server_name: Name of the Discord server
        channel_name: Name of the channel within the server
        
    Returns:
        bool: True if navigation was successful
    """
    # First make sure Discord is focused
    if not focus_discord():
        logger.error("Could not focus Discord application")
        return False
        
    # Try to use Discord's keyboard shortcuts
    # Cmd+K opens the quick switcher
    script = f'''
    tell application "System Events"
        tell process "Discord"
            -- Open Quick Switcher with Cmd+K
            keystroke "k" using command down
            delay 0.5
            
            -- Type the server and channel
            keystroke "{server_name} {channel_name}"
            delay 0.5
            
            -- Press return to navigate to the result
            keystroke return
            delay 1
            
            -- Check if we're in the right place
            set channelFound to false
            
            -- Try to find channel name in the header
            set allUIElements to every UI element
            repeat with theElement in allUIElements
                try
                    if name of theElement contains "{channel_name}" then
                        set channelFound to true
                        exit repeat
                    end if
                end try
            end repeat
            
            return channelFound
        end tell
    end tell
    '''
    
    result = run_applescript(script)
    if result and result.lower() == "true":
        logger.info(f"Successfully navigated to channel '{channel_name}' in server '{server_name}'")
        return True
    else:
        logger.warning(f"Could not navigate to channel '{channel_name}' in server '{server_name}'")
        
        # Try alternate approach - clicking server in sidebar then finding channel
        script = f'''
        tell application "System Events"
            tell process "Discord"
                -- Try to find and click the server in the sidebar
                set serverFound to false
                set allUIElements to every UI element
                
                -- First look for the server in the sidebar
                repeat with theElement in allUIElements
                    try
                        if name of theElement contains "{server_name}" then
                            click theElement
                            delay 0.5
                            set serverFound to true
                            exit repeat
                        end if
                    end try
                end repeat
                
                -- If server found, look for the channel
                if serverFound then
                    set channelFound to false
                    set allUIElements to every UI element
                    
                    -- Look for the channel in the channel list
                    repeat with theElement in allUIElements
                        try
                            if name of theElement contains "{channel_name}" then
                                click theElement
                                delay 0.5
                                set channelFound to true
                                exit repeat
                            end if
                        end try
                    end repeat
                    
                    return channelFound
                else
                    return false
                end if
            end tell
        end tell
        '''
        
        result = run_applescript(script)
        if result and result.lower() == "true":
            logger.info(f"Successfully navigated to channel '{channel_name}' using alternative method")
            return True
        else:
            logger.error(f"All navigation attempts to channel '{channel_name}' failed")
            return False

def get_discord_messages(count=10):
    """
    Extract the most recent Discord messages directly from the UI
    Much more reliable than OCR for getting clean message text
    
    Args:
        count: Number of recent messages to attempt to extract (may return fewer)
        
    Returns:
        list: List of message dictionaries with text, sender, timestamp and coordinates
    """
    # Make sure Discord is in focus
    if not focus_discord():
        logger.warning("Could not focus Discord to extract messages")
        return []
        
    script = f'''
    tell application "System Events"
        tell process "Discord"
            set messages to {{}}
            
            -- Find the main message container
            set messageElements to every UI element
            
            -- Counter for messages found
            set messageCount to 0
            
            -- Process elements looking for messages
            repeat with theElement in messageElements
                try
                    -- Check if this element might be a message
                    set elementRole to role description of theElement
                    set elementName to name of theElement
                    
                    -- Discord messages often have roles like "text" or "group"
                    -- and usually contain timestamp indicators like "Today at" or "Yesterday at"
                    if (elementRole is "text" or elementRole is "group") and (elementName contains "AM" or elementName contains "PM" or elementName contains "Today at" or elementName contains "Yesterday at") then
                        
                        -- Extract position
                        set elemPosition to position of theElement
                        set elemX to item 1 of elemPosition
                        set elemY to item 2 of elemPosition
                        
                        -- Try to extract timestamp (will be in the name often)
                        set timestampText to ""
                        if elementName contains "Today at" then
                            set timestampText to "Today at" & (rest of elementName after "Today at")
                        else if elementName contains "Yesterday at" then
                            set timestampText to "Yesterday at" & (rest of elementName after "Yesterday at")
                        end if
                        
                        -- Get message sender by looking at nearby elements
                        set senderName to ""
                        set allNearbyElements to every UI element
                        repeat with nearbyElement in allNearbyElements
                            try
                                -- Check if it's close to our message and might be a username
                                set nearbyPosition to position of nearbyElement
                                set nearbyX to item 1 of nearbyPosition
                                set nearbyY to item 2 of nearbyPosition
                                
                                -- If within close proximity above the message
                                if (nearbyX > (elemX - 100)) and (nearbyX < (elemX + 100)) and (nearbyY > (elemY - 30)) and (nearbyY < elemY) then
                                    -- Check if it contains a username format (often has # followed by numbers)
                                    set nearbyName to name of nearbyElement
                                    if nearbyName contains "#" then
                                        set senderName to nearbyName
                                        exit repeat
                                    end if
                                end if
                            end try
                        end repeat
                        
                        -- Extract message text (often in the value or description)
                        set messageText to ""
                        try
                            set messageText to value of theElement
                        end try
                        if messageText is "" then
                            try
                                set messageText to description of theElement
                            end try
                        end if
                        
                        -- If we couldn't get the message directly, check child elements
                        if messageText is "" then
                            try
                                set childElements to UI elements of theElement
                                repeat with childElement in childElements
                                    try
                                        set childText to value of childElement
                                        if childText is not "" then
                                            set messageText to childText
                                            exit repeat
                                        end if
                                    end try
                                end repeat
                            end try
                        end if
                        
                        -- Only count if we got meaningful message content
                        if messageText is not "" then
                            -- Create message data
                            set messageData to {{text:messageText, sender:senderName, timestamp:timestampText, x:elemX, y:elemY}}
                            
                            -- Add to results
                            set messages to messages & messageData
                            
                            -- Increment counter and check if we have enough
                            set messageCount to messageCount + 1
                            if messageCount ≥ {count} then
                                exit repeat
                            end if
                        end if
                    end if
                end try
            end repeat
            
            return messages
        end tell
    end tell
    '''
    
    result = run_applescript(script)
    if not result:
        logger.warning("Failed to extract Discord messages")
        return []
    
    # Parse the result into a list of message dictionaries
    messages = []
    
    try:
        # Split into separate message elements
        message_elements = result.split("}, {")
        for i, element in enumerate(message_elements):
            # Clean up the format for the first and last element
            if i == 0:
                element = element.replace("{", "")
            if i == len(message_elements) - 1:
                element = element.replace("}", "")
                
            # Parse the message data
            message_data = {}
            for pair in element.split(", "):
                try:
                    key, value = pair.split(":")
                    if key in ["text", "sender", "timestamp"]:
                        message_data[key] = value
                    else:  # x or y
                        message_data[key] = int(value)
                except ValueError:
                    continue
                    
            # Add to results if we got text
            if "text" in message_data:
                messages.append(message_data)
        
    except Exception as e:
        logger.error(f"Error parsing Discord messages: {e}")
    
    logger.info(f"Extracted {len(messages)} messages from Discord")
    return messages

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
    
    # Test UI text extraction
    print("Testing UI text extraction...")
    text_elements = extract_text_from_ui(center_x, center_y)
    print(f"Found {len(text_elements)} text elements")
    
    # Test Discord navigation if Discord is running
    try:
        print("Testing Discord channel navigation...")
        if focus_discord():
            navigate_to_discord_channel("Wealth Group", "trades")
            time.sleep(1)
            messages = get_discord_messages(5)
            print(f"Extracted {len(messages)} messages")
    except Exception as e:
        print(f"Discord tests skipped: {e}")
    
    print("Test completed successfully")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # Run the test
    test_mac_controller()