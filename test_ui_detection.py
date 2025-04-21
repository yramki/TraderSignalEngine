#!/usr/bin/env python3
"""
Test script for enhanced UI channel detection
Tests the improved log pattern matching for server/channel status
"""

import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

class TestUI:
    """Simple test UI to verify the enhanced detection pattern matching"""
    
    def __init__(self):
        """Initialize the test UI"""
        self.root = tk.Tk()
        self.root.title("Discord Detection Test")
        self.root.geometry("800x600")
        
        # Create the log text widget to simulate real logs
        self.log_frame = ttk.LabelFrame(self.root, text="Log Output")
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Test controls
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Add test log buttons
        ttk.Button(control_frame, text="Add Sample Log 1", 
                  command=lambda: self.add_sample_log(1)).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Add Sample Log 2", 
                  command=lambda: self.add_sample_log(2)).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Add Sample Log 3", 
                  command=lambda: self.add_sample_log(3)).pack(side=tk.LEFT, padx=5)
        
        # Test detection button
        ttk.Button(control_frame, text="Test Detection", 
                  command=self.test_detection).pack(side=tk.LEFT, padx=20)
        
        # Status display
        status_frame = ttk.LabelFrame(self.root, text="Detection Status")
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Not tested yet")
        self.status_label.pack(pady=10)
        
        self.discord_status = ttk.Label(status_frame, text="Discord: Not Detected")
        self.discord_status.pack(pady=5)
        
        self.server_status = ttk.Label(status_frame, text="Server: Not Detected")
        self.server_status.pack(pady=5)
        
        self.channel_status = ttk.Label(status_frame, text="Channel: Not Detected")
        self.channel_status.pack(pady=5)
    
    def add_sample_log(self, sample_num):
        """Add a sample log to the text widget"""
        self.log_text.config(state=tk.NORMAL)
        
        if sample_num == 1:
            # Sample log with successful detection in the format we've seen in the logs
            self.log_text.insert(tk.END, """
2025-04-21 13:58:21,840 - screen_capture_enhanced - INFO - ✅ Discord 'Wealth Group' server and 'trades' channel detected!
2025-04-21 13:58:21,840 - screen_capture_enhanced - INFO -    Found indicators: Discord, Wealth Group, trades channel, Unlock Content, Press the button to unlock, Only you can see this, Message
2025-04-21 13:58:21,840 - ui.enhanced_trading_ui - INFO - Discord detection successful via screen_capture method
2025-04-21 13:58:21,840 - ui.enhanced_trading_ui - INFO - UI Status update: Discord=True, Server=False, Channel=False
            """)
        elif sample_num == 2:
            # Sample log with detection via individual indicators
            self.log_text.insert(tk.END, """
2025-04-21 14:05:10,123 - screen_capture_enhanced - INFO - Discord detected via OCR
2025-04-21 14:05:10,234 - screen_capture_enhanced - INFO - Target server 'Wealth Group' detected via UI element
2025-04-21 14:05:10,345 - screen_capture_enhanced - INFO - Target channel 'trades' inferred from 'Unlock Content' button presence
2025-04-21 14:05:10,456 - ui.enhanced_trading_ui - INFO - UI Status update: Discord=True, Server=True, Channel=False
            """)
        elif sample_num == 3:
            # Sample log with successful combined detection in original format
            self.log_text.insert(tk.END, """
2025-04-21 14:10:30,789 - screen_capture_enhanced - INFO - ✅ Discord with correct server/channel detected
2025-04-21 14:10:30,901 - screen_capture_enhanced - INFO - Found indicators: Discord, Wealth Group, trades channel
2025-04-21 14:10:31,012 - ui.enhanced_trading_ui - INFO - Discord detection successful via screen_capture method
            """)
        
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
    
    def test_detection(self):
        """Test the enhanced detection logic against current logs"""
        # Get the log content
        log_content = self.log_text.get("1.0", tk.END)
        
        # Set initial detection values
        discord_detected = False
        server_detected = False
        channel_detected = False
        
        # Check for direct full detection message with checkmark emoji
        if "✅ Discord 'Wealth Group' server and 'trades' channel detected!" in log_content:
            discord_detected = True
            server_detected = True
            channel_detected = True
            self.status_label.config(text="Full detection confirmed via checkmark pattern")
        
        # Check for alternative message format
        elif "Discord 'Wealth Group' server and 'trades' channel detected" in log_content:
            discord_detected = True
            server_detected = True
            channel_detected = True
            self.status_label.config(text="Full detection confirmed via alternative pattern")
        
        # Check for the Found indicators pattern we're seeing in the logs
        elif "Found indicators: Discord" in log_content and "Wealth Group" in log_content and "trades channel" in log_content:
            discord_detected = True
            server_detected = True
            channel_detected = True
            self.status_label.config(text="Full detection confirmed via indicators list")
        
        # Check individual indicators and inferences
        elif "Discord detected" in log_content:
            discord_detected = True
            
            # Check server detection
            server_indicators = ["'Wealth Group' server", "Target server 'Wealth Group'"]
            server_detected = any(indicator in log_content for indicator in server_indicators)
            
            # Check channel detection
            channel_indicators = ["trades channel", "# trades", "channel: trades"]
            channel_detected = any(indicator in log_content for indicator in channel_indicators)
            
            # Check for inferred detection
            if "Target channel 'trades' inferred from" in log_content:
                channel_detected = True
                self.status_label.config(text="Partial detection with inference")
            else:
                self.status_label.config(text="Partial detection based on indicators")
        else:
            self.status_label.config(text="No detection patterns found")
        
        # Update status display
        self.discord_status.config(text=f"Discord: {'Detected' if discord_detected else 'Not Detected'}")
        self.server_status.config(text=f"Server: {'Detected' if server_detected else 'Not Detected'}")
        self.channel_status.config(text=f"Channel: {'Detected' if channel_detected else 'Not Detected'}")
        
        # Test our exact fix for the specific pattern in the log
        if "INFO - ✅ Discord 'Wealth Group' server and 'trades' channel detected!" in log_content:
            messagebox.showinfo("Test Result", "Exact pattern match success! The fix should work.")
        
        # Mark pattern successful or not
        if discord_detected and server_detected and channel_detected:
            self.status_label.config(foreground="green")
        else:
            self.status_label.config(foreground="red")
        
    def run(self):
        """Run the test UI"""
        self.root.mainloop()

if __name__ == "__main__":
    test_ui = TestUI()
    test_ui.run()