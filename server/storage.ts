import { 
  trades, tradingSignals, tradeConfigs, users,
  type User, type InsertUser, type TradeConfig, type InsertTradeConfig,
  type TradingSignal, type InsertTradingSignal, type Trade, type InsertTrade
} from "@shared/schema";

export interface IStorage {
  // User methods
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  
  // Trade config methods
  getTradeConfig(): Promise<TradeConfig | null>;
  updateTradeConfig(config: Partial<InsertTradeConfig>): Promise<TradeConfig>;
  
  // Trading signal methods
  getUnprocessedSignals(): Promise<TradingSignal[]>;
  getRecentSignals(limit: number): Promise<TradingSignal[]>;
  getAllSignals(): Promise<TradingSignal[]>;
  getSignalById(id: number): Promise<TradingSignal | undefined>;
  getSignalByMessageId(messageId: string): Promise<TradingSignal | undefined>;
  createSignal(signal: InsertTradingSignal): Promise<TradingSignal>;
  markSignalExecuted(id: number): Promise<void>;
  markSignalIgnored(id: number): Promise<void>;
  getTodaysSignals(): Promise<TradingSignal[]>;
  
  // Trade methods
  getActiveTrades(): Promise<Trade[]>;
  getTradeHistory(): Promise<Trade[]>;
  getTodaysTrades(): Promise<Trade[]>;
  getTradeById(id: number): Promise<Trade | undefined>;
  createTrade(trade: InsertTrade): Promise<Trade>;
  closeTrade(id: number, closeReason: string, closePrice: number, closeData: any): Promise<Trade>;
}

export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private tradeConfig: TradeConfig | null;
  private tradingSignals: Map<number, TradingSignal>;
  private trades: Map<number, Trade>;
  private userCurrentId: number;
  private signalCurrentId: number;
  private tradeCurrentId: number;

  constructor() {
    this.users = new Map();
    this.tradingSignals = new Map();
    this.trades = new Map();
    this.userCurrentId = 1;
    this.signalCurrentId = 1;
    this.tradeCurrentId = 1;
    
    // Initialize default trade config
    this.tradeConfig = {
      id: 1,
      amountPerTrade: 100,
      leverage: 5,
      tradeType: "futures",
      autoExecute: false,
      allowLong: true,
      allowShort: true,
      allowedCryptos: [],
      minRiskRewardRatio: "Any",
      customStopLoss: false,
      stopLossPercent: 2,
      createdAt: new Date(),
      updatedAt: new Date()
    };
  }

  // User methods
  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.userCurrentId++;
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }
  
  // Trade config methods
  async getTradeConfig(): Promise<TradeConfig | null> {
    return this.tradeConfig;
  }
  
  async updateTradeConfig(config: Partial<InsertTradeConfig>): Promise<TradeConfig> {
    if (!this.tradeConfig) {
      this.tradeConfig = {
        id: 1,
        amountPerTrade: config.amountPerTrade || 100,
        leverage: config.leverage || 5,
        tradeType: config.tradeType || "futures",
        autoExecute: config.autoExecute || false,
        allowLong: config.allowLong || true,
        allowShort: config.allowShort || true,
        allowedCryptos: config.allowedCryptos || [],
        minRiskRewardRatio: config.minRiskRewardRatio || "Any",
        customStopLoss: config.customStopLoss || false,
        stopLossPercent: config.stopLossPercent || 2,
        createdAt: new Date(),
        updatedAt: new Date()
      };
    } else {
      this.tradeConfig = {
        ...this.tradeConfig,
        ...config,
        updatedAt: new Date()
      };
    }
    
    return this.tradeConfig;
  }
  
  // Trading signal methods
  async getUnprocessedSignals(): Promise<TradingSignal[]> {
    return Array.from(this.tradingSignals.values())
      .filter(signal => !signal.processed && !signal.executed && !signal.ignored)
      .sort((a, b) => new Date(b.signalDate).getTime() - new Date(a.signalDate).getTime());
  }
  
  async getRecentSignals(limit: number): Promise<TradingSignal[]> {
    return Array.from(this.tradingSignals.values())
      .sort((a, b) => new Date(b.signalDate).getTime() - new Date(a.signalDate).getTime())
      .slice(0, limit);
  }
  
  async getAllSignals(): Promise<TradingSignal[]> {
    return Array.from(this.tradingSignals.values())
      .sort((a, b) => new Date(b.signalDate).getTime() - new Date(a.signalDate).getTime());
  }
  
  async getSignalById(id: number): Promise<TradingSignal | undefined> {
    return this.tradingSignals.get(id);
  }
  
  async getSignalByMessageId(messageId: string): Promise<TradingSignal | undefined> {
    return Array.from(this.tradingSignals.values()).find(
      signal => signal.messageId === messageId
    );
  }
  
  async createSignal(insertSignal: InsertTradingSignal): Promise<TradingSignal> {
    const id = this.signalCurrentId++;
    const signal: TradingSignal = {
      ...insertSignal,
      id,
      signalDate: new Date(),
      processed: false,
      executed: false,
      ignored: false,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.tradingSignals.set(id, signal);
    return signal;
  }
  
  async markSignalExecuted(id: number): Promise<void> {
    const signal = this.tradingSignals.get(id);
    if (signal) {
      signal.executed = true;
      signal.processed = true;
      signal.updatedAt = new Date();
      this.tradingSignals.set(id, signal);
    }
  }
  
  async markSignalIgnored(id: number): Promise<void> {
    const signal = this.tradingSignals.get(id);
    if (signal) {
      signal.ignored = true;
      signal.processed = true;
      signal.updatedAt = new Date();
      this.tradingSignals.set(id, signal);
    }
  }
  
  async getTodaysSignals(): Promise<TradingSignal[]> {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    return Array.from(this.tradingSignals.values()).filter(signal => {
      const signalDate = new Date(signal.signalDate);
      return signalDate >= today;
    });
  }
  
  // Trade methods
  async getActiveTrades(): Promise<Trade[]> {
    return Array.from(this.trades.values())
      .filter(trade => trade.status === "open")
      .sort((a, b) => new Date(b.openTime).getTime() - new Date(a.openTime).getTime());
  }
  
  async getTradeHistory(): Promise<Trade[]> {
    return Array.from(this.trades.values())
      .sort((a, b) => new Date(b.openTime).getTime() - new Date(a.openTime).getTime());
  }
  
  async getTodaysTrades(): Promise<Trade[]> {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    return Array.from(this.trades.values()).filter(trade => {
      const openTime = new Date(trade.openTime);
      return openTime >= today;
    });
  }
  
  async getTradeById(id: number): Promise<Trade | undefined> {
    return this.trades.get(id);
  }
  
  async createTrade(insertTrade: InsertTrade): Promise<Trade> {
    const id = this.tradeCurrentId++;
    const trade: Trade = {
      ...insertTrade,
      id,
      status: "open",
      openTime: new Date(),
      closeTime: null,
      closeReason: null,
      pnlAmount: 0,
      pnlPercent: 0,
      phemexCloseData: null,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.trades.set(id, trade);
    return trade;
  }
  
  async closeTrade(id: number, closeReason: string, closePrice: number, closeData: any): Promise<Trade> {
    const trade = this.trades.get(id);
    if (!trade) {
      throw new Error(`Trade with ID ${id} not found`);
    }
    
    // Calculate P&L
    const entryValue = trade.amount * trade.leverage;
    let pnlAmount = 0;
    
    if (trade.isLong) {
      // For long positions, profit when closePrice > entryPrice
      const priceDiff = closePrice - trade.entryPrice;
      pnlAmount = (priceDiff / trade.entryPrice) * entryValue;
    } else {
      // For short positions, profit when closePrice < entryPrice
      const priceDiff = trade.entryPrice - closePrice;
      pnlAmount = (priceDiff / trade.entryPrice) * entryValue;
    }
    
    const pnlPercent = (pnlAmount / trade.amount) * 100;
    
    // Update trade
    const updatedTrade: Trade = {
      ...trade,
      status: "closed",
      closeTime: new Date(),
      closeReason,
      currentPrice: closePrice,
      pnlAmount,
      pnlPercent,
      phemexCloseData: closeData,
      updatedAt: new Date()
    };
    
    this.trades.set(id, updatedTrade);
    return updatedTrade;
  }
}

export const storage = new MemStorage();
