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
    // In a real implementation, this would ping the Discord API
    // For now, just return the simulated connection status
    return this.isConnected;
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
