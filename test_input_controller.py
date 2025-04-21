#!/usr/bin/env python3
"""
Test script for input controller functionality
This script demonstrates the different controller types available for mouse control
"""

import logging
import time
import sys
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("InputControllerTest")

def test_input_controllers():
    """Test the different controller types"""
    from src.input_controller import ControllerType, set_controller, get_controller
    from src.input_controller import move_mouse, click, get_screen_size, capture_screenshot
    
    print("\n===== Input Controller Test =====")
    available_controllers = [c.value for c in ControllerType]
    print(f"Available controller types: {', '.join(available_controllers)}")
    
    for controller_type in ControllerType:
        print(f"\n----- Testing {controller_type.value} controller -----")
        
        # Set the controller
        set_controller(controller_type)
        active = get_controller()
        print(f"Active controller: {active.value}")
        
        # Get screen dimensions
        screen_size = get_screen_size()
        print(f"Screen size: {screen_size[0]}x{screen_size[1]}")
        
        # Test mouse movement
        print("\nTesting mouse movement...")
        print("Moving to center of screen")
        center_x, center_y = screen_size[0] // 2, screen_size[1] // 2
        move_mouse(center_x, center_y)
        time.sleep(0.5)
        
        # Move in a small pattern
        print("Moving in square pattern")
        offsets = [(50, 50), (50, -50), (-50, -50), (-50, 50)]
        for dx, dy in offsets:
            x, y = center_x + dx, center_y + dy
            print(f"Moving to ({x}, {y})")
            move_mouse(x, y)
            time.sleep(0.5)
        
        # Move back to center
        print("Moving back to center")
        move_mouse(center_x, center_y)
        time.sleep(0.5)
        
        # Test screenshot
        print("\nTesting screenshot capture...")
        screenshot = capture_screenshot()
        if screenshot:
            # Save the screenshot with controller type in filename
            filename = f"screenshot_{controller_type.value}.png"
            screenshot.save(filename)
            print(f"Screenshot saved as {filename}")
        else:
            print("Failed to capture screenshot")
        
        print(f"\n{controller_type.value} controller test completed")
        
        # Ask user if they want to continue to next controller
        if controller_type != list(ControllerType)[-1]:  # Not the last controller
            response = input("Continue to next controller? (y/n): ")
            if response.lower() != 'y':
                break
    
    print("\n===== All controller tests completed =====")

def test_config_integration():
    """Test the configuration integration"""
    from src.config import Config
    from src.input_controller import set_controller, get_controller
    
    print("\n===== Configuration Integration Test =====")
    
    # Create a test config
    config = Config()
    
    # Get the current controller type from config
    controller_type = config.get_input_control('controller_type', 'hybrid')
    print(f"Controller type from config: {controller_type}")
    
    # Set the controller based on config
    set_controller(controller_type)
    active = get_controller()
    print(f"Active controller set to: {active.value}")
    
    # Test changing the controller through config
    new_type = 'pyautogui'
    print(f"Changing controller to {new_type} through config")
    config.set_input_control('controller_type', new_type)
    config.save()
    
    # Re-read config and set controller
    controller_type = config.get_input_control('controller_type')
    print(f"Updated controller type from config: {controller_type}")
    set_controller(controller_type)
    active = get_controller()
    print(f"Active controller now set to: {active.value}")
    
    print("\nConfiguration integration test completed")

def main():
    """Main test function"""
    print("===== Discord Trading Signal Scraper - Input Controller Test =====")
    print("This script tests the various input controllers available")
    print("You'll see the mouse move and screenshots will be captured")
    
    test_input_controllers()
    test_config_integration()
    
    print("\nAll tests completed. Thank you for testing!")

if __name__ == "__main__":
    main()