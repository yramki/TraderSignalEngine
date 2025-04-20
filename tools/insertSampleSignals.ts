// This script inserts sample trading signals to test the system
import { storage } from '../server/storage';
import { hasValidSignal, parseDiscordMessage } from '../client/src/lib/discordParser';

const sampleDiscordMessages = [
  {
    id: 'msg_' + Math.random().toString(36).substring(2, 10),
    content: "Longed BTC at 67500 sl- 65200 (1% risk) TPs: 70000",
    author: {
      id: 'user_btc_trader',
      username: 'BTCTrader'
    },
    channel_id: 'channel_signals',
    guild_id: 'guild_crypto',
    timestamp: new Date().toISOString()
  },
  {
    id: 'msg_' + Math.random().toString(36).substring(2, 10),
    content: "Shorted ETH at 3520 sl- 3650 TPs: 3300",
    author: {
      id: 'user_eth_trader',
      username: 'ETHTrader'
    },
    channel_id: 'channel_signals',
    guild_id: 'guild_crypto',
    timestamp: new Date().toISOString()
  },
  {
    id: 'msg_' + Math.random().toString(36).substring(2, 10),
    content: "SOL Entry: 150.25 SL: 145.5 TPs: 160",
    author: {
      id: 'user_sol_trader',
      username: 'SOLTrader'
    },
    channel_id: 'channel_signals',
    guild_id: 'guild_crypto',
    timestamp: new Date().toISOString()
  }
];

async function insertSampleSignals() {
  console.log('Inserting sample trading signals...');
  
  for (const message of sampleDiscordMessages) {
    console.log(`\nProcessing message: "${message.content}"`);
    
    // Check if message contains valid trading signal
    if (!hasValidSignal(message.content)) {
      console.log('Message does not contain a valid trading signal');
      continue;
    }
    
    // Parse the message to extract signal data
    const signalData = parseDiscordMessage(message.content);
    if (!signalData) {
      console.log('Failed to parse trading signal from message');
      continue;
    }
    
    console.log('Parsed signal data:', signalData);
    
    // Check if this message has already been processed
    const existingSignal = await storage.getSignalByMessageId(message.id);
    if (existingSignal) {
      console.log(`Message ${message.id} already processed`);
      continue;
    }
    
    // Create new signal in storage
    try {
      const signal = await storage.createSignal({
        ticker: signalData.ticker,
        entryPrice: signalData.entryPrice,
        targetPrice: signalData.targetPrice,
        stopLossPrice: signalData.stopLossPrice,
        isLong: signalData.isLong,
        risk: signalData.risk,
        messageContent: message.content,
        messageId: message.id,
        discordChannelId: message.channel_id,
        processed: false,
        executed: false,
        ignored: false
      });
      
      console.log(`Created new trading signal for ${signalData.ticker}`, signal);
    } catch (error) {
      console.error('Error creating signal:', error);
    }
  }
  
  // List all signals in the system
  const allSignals = await storage.getAllSignals();
  console.log('\nAll signals in the system:');
  console.log(JSON.stringify(allSignals, null, 2));
}

// Run the function
insertSampleSignals()
  .then(() => console.log('\nDone inserting sample signals'))
  .catch(error => console.error('Error:', error));