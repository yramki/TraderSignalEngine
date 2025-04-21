#!/usr/bin/env python
"""
Test script for trader name matching functionality
This script tests the flexible trader name matching we've implemented
"""

import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_trader_matching(trader, test_text):
    """Test if a trader would match in a text with flexible matching"""
    # Normalize trader names for comparison
    normalized_trader = re.sub(r'[^a-zA-Z0-9]', '', trader.lower())
    normalized_text = test_text.lower()
    
    # Create variations to test
    variations = [
        trader,                                  # Original format (e.g., @Bryce)
        trader.replace('@', '@-'),              # With hyphen (e.g., @-Bryce)
        trader.replace('@-', '@'),              # Without hyphen (e.g., @Bryce)
        normalized_trader,                       # Normalized (e.g., bryce)
        '@' + normalized_trader.lstrip('@'),     # Add @ if missing
    ]
    
    logger.info(f"Testing trader '{trader}' against text: '{test_text}'")
    logger.info(f"Variations being checked: {', '.join(variations)}")
    
    # Check if any variation is in the text
    for var in variations:
        if var.lower() in normalized_text:
            logger.info(f"✅ MATCH FOUND: '{var}' found in text")
            return True
    
    logger.info("❌ NO MATCH: None of the variations found in text")
    return False

def main():
    """Main test function"""
    print("=== TRADER MATCHING TEST ===")
    print("Testing the flexible trader matching functionality\n")
    
    # Test cases
    test_cases = [
        # (@trader format in list, Message format, Expected result)
        ("@Bryce", "Message from @Bryce: BTC buy signal", True),
        ("@Bryce", "Message from @-Bryce: BTC buy signal", True),
        ("@-Bryce", "Message from @Bryce: BTC buy signal", True),
        ("@Trader123", "Message from @trader123: BTC buy signal", True),
        ("@CryptoKing", "Message from @-cryptoking: BTC buy signal", True),
        ("@-Expert", "Message from @Expert: ETH sell signal", True),
        ("@Bryce", "Message from @Bryan: ETH sell signal", False),
        ("Bryce", "Message from @Bryce: BTC buy signal", True),  # No @ in list
        ("@Bryce", "Message from Bryce: BTC buy signal", True),  # No @ in message
    ]
    
    for i, (trader, text, expected) in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{trader}' in '{text}'")
        result = test_trader_matching(trader, text)
        if result == expected:
            print(f"✅ TEST PASSED: Got {result}, expected {expected}")
        else:
            print(f"❌ TEST FAILED: Got {result}, expected {expected}")
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    main()