# macOS Enhanced Input Control

This application includes special optimizations for macOS users to provide more reliable mouse control and user interface interactions.

## Native macOS Support

The application includes three modes of operation:

1. **PyAutoGUI Mode**: Standard cross-platform mouse control (works on Windows, macOS, Linux)
2. **macOS Native Mode**: Uses native macOS APIs via AppleScript for more reliable control
3. **Hybrid Mode**: Tries macOS native methods first, falls back to PyAutoGUI when necessary

## Benefits of macOS Native Mode

The native macOS input controller offers several advantages:

- More reliable mouse movement and clicking
- Better handling of screen coordinates
- Enhanced button detection using text rather than just position or color
- Ability to focus the Discord application window automatically
- Better emergency cleanup to prevent mouse getting stuck
- Properly handles macOS screen scaling factors

## Configuring the Input Controller

You can configure which input controller to use in `config.ini` under the `[InputControl]` section:

```ini
[InputControl]
; Options: pyautogui, macos_native, hybrid
controller_type = macos_native
; Try to focus Discord window before interactions
auto_focus_app = true
; Try to use text-based button detection (macOS only)
use_text_detection = true
; Fallback to pixel-based detection if text detection fails
enable_fallback = true
```

## Additional macOS Features

### Text-Based Button Detection

When using macOS native mode, the application can detect buttons by their text content. This is particularly useful for detecting "Unlock Content" buttons in Discord that may move or change appearance.

### Application Window Focus

The macOS controller can automatically bring Discord to the foreground before attempting interactions, which reduces errors caused by Discord not being the active window.

### Emergency Cleanup

If the application terminates unexpectedly, the macOS controller includes robust cleanup that ensures your mouse doesn't get stuck in a pressed-down state and returns to a neutral position.

## Testing the Controllers

A test script is included to help you determine which controller works best in your environment:

```bash
python3 test_input_controller.py
```

This script will:
1. Show available controller types
2. Test mouse movement with each controller
3. Capture screenshots to verify functionality
4. Test configuration loading/saving

## Requirements for macOS Native Mode

The macOS native controller requires:
- macOS 10.14 or newer
- Python 3.6+
- Permissions for Accessibility (System Preferences → Security & Privacy → Privacy → Accessibility)
  - Add your Terminal or Python application to this list

If you encounter any issues with mouse control, try switching to a different controller type in the configuration file.