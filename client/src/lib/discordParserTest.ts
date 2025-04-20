import { parseDiscordMessage, hasValidSignal } from './discordParser';

// Sample Discord messages to test
const testMessages = [
  {
    id: 1,
    content: "Longed BTC at 67500 sl- 65200 (1% risk) TPs: 70000",
    expected: {
      ticker: "BTC",
      entryPrice: 67500,
      stopLossPrice: 65200,
      targetPrice: 70000,
      isLong: true,
      risk: 1
    }
  },
  {
    id: 2,
    content: "Shorted ETH at 3520 sl- 3650 TPs: 3300",
    expected: {
      ticker: "ETH",
      entryPrice: 3520,
      stopLossPrice: 3650,
      targetPrice: 3300,
      isLong: false,
      risk: 1 // Default value
    }
  },
  {
    id: 3,
    content: "SOL Entry: 150.25 SL: 145.5 TPs: 160",
    expected: {
      ticker: "SOL",
      entryPrice: 150.25,
      stopLossPrice: 145.5,
      targetPrice: 160,
      isLong: false, // Indeterminate, defaults to false
      risk: 1 // Default value
    }
  },
  {
    id: 4,
    content: "Random message that doesn't contain trading signal",
    expected: null
  }
];

// Run tests
console.log("Testing Discord Message Parser");
console.log("------------------------------");

testMessages.forEach(test => {
  console.log(`\nTest #${test.id}: "${test.content.substring(0, 30)}..."`);
  
  // Test hasValidSignal first
  const isValid = hasValidSignal(test.content);
  console.log(`Is valid signal: ${isValid}`);
  
  // Then test parsing
  const result = parseDiscordMessage(test.content);
  
  if (test.expected === null) {
    if (result === null) {
      console.log("✅ Correctly returned null");
    } else {
      console.log("❌ Expected null but got:", result);
    }
  } else {
    if (result === null) {
      console.log("❌ Expected valid result but got null");
    } else {
      console.log("Parsed result:", result);
      
      // Compare result with expected
      const keys = ['ticker', 'entryPrice', 'stopLossPrice', 'targetPrice', 'isLong', 'risk'];
      let allMatch = true;
      
      keys.forEach(key => {
        if (result[key as keyof typeof result] !== test.expected[key as keyof typeof test.expected]) {
          console.log(`❌ Mismatch in ${key}: expected=${test.expected[key as keyof typeof test.expected]}, actual=${result[key as keyof typeof result]}`);
          allMatch = false;
        }
      });
      
      if (allMatch) {
        console.log("✅ All fields match");
      }
    }
  }
});