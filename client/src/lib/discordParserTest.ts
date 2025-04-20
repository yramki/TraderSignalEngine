import { hasValidSignal, parseDiscordMessage } from './discordParser';

// Test cases
const testCases = [
  {
    message: "Longed BTC at 67500 sl- 65200 (1% risk) TPs: 70000",
    expected: {
      ticker: "BTC",
      entryPrice: 67500,
      targetPrice: 70000,
      stopLossPrice: 65200,
      isLong: true,
      risk: 1
    }
  },
  {
    message: "Shorted ETH at 3520 sl- 3650 TPs: 3300",
    expected: {
      ticker: "ETH",
      entryPrice: 3520,
      targetPrice: 3300,
      stopLossPrice: 3650,
      isLong: false,
      risk: 1
    }
  },
  {
    message: "SOL Entry: 150.25 SL: 145.5 TPs: 160",
    expected: {
      ticker: "SOL",
      entryPrice: 150.25,
      targetPrice: 160,
      stopLossPrice: 145.5,
      isLong: false,
      risk: 1
    }
  }
];

// Run tests
export function runDiscordParserTests() {
  console.log("Running Discord parser tests...");
  
  let passedTests = 0;
  let failedTests = 0;
  
  for (const test of testCases) {
    console.log(`\nTesting message: "${test.message}"`);
    
    // Check if message is valid
    const isValid = hasValidSignal(test.message);
    console.log(`Is valid signal: ${isValid}`);
    
    if (!isValid) {
      console.log("❌ FAILED: Message should be valid");
      failedTests++;
      continue;
    }
    
    // Parse message
    const result = parseDiscordMessage(test.message);
    console.log("Parsed result:", result);
    
    if (!result) {
      console.log("❌ FAILED: Could not parse message");
      failedTests++;
      continue;
    }
    
    // Compare with expected
    let testPassed = true;
    for (const key in test.expected) {
      // @ts-ignore
      if (result[key] !== test.expected[key]) {
        // @ts-ignore
        console.log(`❌ FAILED: Property ${key} mismatch. Expected ${test.expected[key]}, got ${result[key]}`);
        testPassed = false;
      }
    }
    
    if (testPassed) {
      console.log("✅ PASSED");
      passedTests++;
    } else {
      failedTests++;
    }
  }
  
  console.log(`\nTest summary: ${passedTests} passed, ${failedTests} failed`);
  return { passedTests, failedTests };
}