import { storage } from "../storage";
import { hasValidSignal, parseDiscordMessage } from "../../client/src/lib/discordParser";

interface DiscordMessageContent {
  id: string;
  content: string;
  author: {
    id: string;
    username: string;
  };
  channel_id: string;
  guild_id: string;
  timestamp: string;
}

class DiscordService {
  private apiKey: string;
  private isConnected: boolean = false;

  constructor() {
    this.apiKey = process.env.DISCORD_API_KEY || "";
    // In a real implementation, this would initialize a Discord client
    // using a library like discord.js
    
    // For this implementation, we'll simulate connection status
    this.isConnected = !!this.apiKey;
  }

  async checkConnection(): Promise<boolean> {
    try {
      // Use the gateway endpoint which worked in our tests
      const response = await fetch('https://discord.com/api/v10/gateway', {
        headers: {
          Authorization: `Bot ${this.apiKey}`
        }
      });
      
      this.isConnected = response.ok;
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error(`Discord API check failed: ${response.status} ${response.statusText}`);
        console.error('Error details:', errorData);
      } else {
        console.log('✅ Successfully connected to Discord API');
      }
      
      return this.isConnected;
    } catch (error) {
      console.error('Failed to connect to Discord API:', error);
      this.isConnected = false;
      return false;
    }
  }

  async fetchMessages(channelId: string, limit: number = 10): Promise<DiscordMessageContent[]> {
    try {
      if (!this.isConnected) {
        await this.checkConnection();
        if (!this.isConnected) {
          throw new Error('Not connected to Discord API');
        }
      }
      
      // This is the common format for channel messages API
      const url = `https://discord.com/api/v10/channels/${channelId}/messages?limit=${limit}`;
      console.log(`Fetching messages from Discord channel ${channelId}...`);
      
      const response = await fetch(url, {
        headers: {
          Authorization: `Bot ${this.apiKey}`
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error(`Failed to fetch Discord messages: ${response.status} ${response.statusText}`);
        console.error('Error details:', errorData);
        
        // Don't silently fail - throw a proper error with context
        if (response.status === 401) {
          throw new Error(`Bot not authorized to access channel ${channelId}. Check bot permissions.`);
        } else if (response.status === 403) {
          throw new Error(`Bot lacks permission to view channel ${channelId}. Add bot to the channel with read permissions.`);
        } else if (response.status === 404) {
          throw new Error(`Channel ${channelId} not found. Verify the channel ID is correct.`);
        } else {
          throw new Error(`Discord API error: ${response.status} ${response.statusText}`);
        }
      }
      
      const messages: DiscordMessageContent[] = await response.json();
      console.log(`Fetched ${messages.length} messages from Discord channel ${channelId}`);
      return messages;
    } catch (error) {
      console.error('Error fetching Discord messages:', error);
      throw error; // Re-throw to let the caller handle it
    }
  }
  
  async processMessage(message: DiscordMessageContent): Promise<void> {
    console.log(`Processing Discord message: ${message.id}`);
    
    // Check if message contains valid trading signal
    if (!hasValidSignal(message.content)) {
      console.log("Message does not contain a valid trading signal");
      return;
    }
    
    // Parse the message to extract signal data
    const signalData = parseDiscordMessage(message.content);
    if (!signalData) {
      console.log("Failed to parse trading signal from message");
      return;
    }
    
    // Check if this message has already been processed
    const existingSignal = await storage.getSignalByMessageId(message.id);
    if (existingSignal) {
      console.log(`Message ${message.id} already processed`);
      return;
    }
    
    // Create new signal in storage
    await storage.createSignal({
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
    
    console.log(`Created new trading signal for ${signalData.ticker}`);
    
    // Check auto-execute setting and potentially execute trade
    const config = await storage.getTradeConfig();
    if (config.autoExecute) {
      // Check if signal meets criteria for auto-execution
      const shouldAutoExecute = this.shouldAutoExecuteSignal(signalData, config);
      if (shouldAutoExecute) {
        // In a real implementation, this would call into a trade execution service
        console.log(`Auto-executing trade for ${signalData.ticker}`);
      }
    }
  }
  
  async processChannelMessages(channelId: string, limit: number = 20): Promise<number> {
    try {
      const messages = await this.fetchMessages(channelId, limit);
      let processedCount = 0;
      
      // Process each message to see if it contains valid trading signals
      for (const message of messages) {
        try {
          await this.processMessage(message);
          processedCount++;
        } catch (error) {
          console.error(`Error processing message ${message.id}:`, error);
        }
      }
      
      return processedCount;
    } catch (error) {
      console.error(`Error processing channel ${channelId}:`, error);
      return 0;
    }
  }
  
  private shouldAutoExecuteSignal(signalData: any, config: any): boolean {
    // Check if this position type is allowed
    if (signalData.isLong && !config.allowLong) return false;
    if (!signalData.isLong && !config.allowShort) return false;
    
    // Check if this crypto is allowed
    if (config.allowedCryptos.length > 0 && 
        !config.allowedCryptos.includes(signalData.ticker)) {
      return false;
    }
    
    // Check risk-reward ratio if configured
    if (config.minRiskRewardRatio !== "Any") {
      const requiredRatio = parseFloat(config.minRiskRewardRatio.split(':')[0]);
      
      // Calculate actual ratio
      let risk, reward;
      if (signalData.isLong) {
        risk = Math.abs(signalData.entryPrice - signalData.stopLossPrice);
        reward = Math.abs(signalData.targetPrice - signalData.entryPrice);
      } else {
        risk = Math.abs(signalData.entryPrice - signalData.stopLossPrice);
        reward = Math.abs(signalData.entryPrice - signalData.targetPrice);
      }
      
      const actualRatio = reward / risk;
      if (actualRatio < requiredRatio) return false;
    }
    
    return true;
  }
}

export const discordService = new DiscordService();
