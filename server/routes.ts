import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { z } from "zod";
import { insertTradeConfigSchema, insertTradingSignalSchema, insertTradeSchema } from "@shared/schema";
import { discordService } from "./services/discordService";
import { phemexService } from "./services/phemexService";

export async function registerRoutes(app: Express): Promise<Server> {
  // API Routes
  
  // Test route
  app.get("/api/ping", (req, res) => {
    res.json({ status: "ok", message: "API is working", timestamp: new Date() });
  });
  
  // Configuration routes
  app.get("/api/config", async (req, res) => {
    const config = await storage.getTradeConfig();
    res.json(config);
  });

  app.patch("/api/config", async (req, res) => {
    const parseResult = insertTradeConfigSchema.safeParse(req.body);
    if (!parseResult.success) {
      return res.status(400).json({ error: parseResult.error });
    }
    
    const updatedConfig = await storage.updateTradeConfig(parseResult.data);
    res.json(updatedConfig);
  });

  // Trading signals routes
  app.get("/api/signals", async (req, res) => {
    const signals = await storage.getUnprocessedSignals();
    res.json(signals);
  });

  app.get("/api/signals/recent", async (req, res) => {
    const signals = await storage.getRecentSignals(5);
    res.json(signals);
  });

  app.get("/api/signals/all", async (req, res) => {
    const signals = await storage.getAllSignals();
    res.json(signals);
  });

  app.post("/api/signals", async (req, res) => {
    const parseResult = insertTradingSignalSchema.safeParse(req.body);
    if (!parseResult.success) {
      return res.status(400).json({ error: parseResult.error });
    }
    
    const signal = await storage.createSignal(parseResult.data);
    res.status(201).json(signal);
  });

  app.post("/api/signals/:id/execute", async (req, res) => {
    const signalId = parseInt(req.params.id);
    const signal = await storage.getSignalById(signalId);
    
    if (!signal) {
      return res.status(404).json({ error: "Signal not found" });
    }
    
    if (signal.executed) {
      return res.status(400).json({ error: "Signal already executed" });
    }
    
    if (signal.ignored) {
      return res.status(400).json({ error: "Signal was ignored" });
    }
    
    try {
      // Get trade config
      const config = await storage.getTradeConfig();
      
      // Execute the trade on Phemex
      const tradeResult = await phemexService.executeTrade({
        ticker: signal.ticker,
        isLong: signal.isLong,
        entryPrice: signal.entryPrice,
        stopLossPrice: signal.stopLossPrice,
        targetPrice: signal.targetPrice,
        amount: config.amountPerTrade,
        leverage: config.leverage,
        tradeType: config.tradeType
      });
      
      // Mark signal as executed
      await storage.markSignalExecuted(signalId);
      
      // Create trade record
      const trade = await storage.createTrade({
        signalId,
        ticker: signal.ticker,
        tradeType: config.tradeType,
        isLong: signal.isLong,
        leverage: config.leverage,
        entryPrice: signal.entryPrice,
        targetPrice: signal.targetPrice,
        stopLossPrice: signal.stopLossPrice,
        amount: config.amountPerTrade,
        currentPrice: signal.entryPrice,
        phemexOrderId: tradeResult.orderId,
        phemexOrderData: tradeResult
      });
      
      res.json({ success: true, trade });
    } catch (error) {
      console.error("Error executing trade:", error);
      res.status(500).json({ error: "Failed to execute trade" });
    }
  });

  app.post("/api/signals/:id/ignore", async (req, res) => {
    const signalId = parseInt(req.params.id);
    const signal = await storage.getSignalById(signalId);
    
    if (!signal) {
      return res.status(404).json({ error: "Signal not found" });
    }
    
    if (signal.executed) {
      return res.status(400).json({ error: "Signal already executed" });
    }
    
    await storage.markSignalIgnored(signalId);
    res.json({ success: true });
  });

  // Trades routes
  app.get("/api/trades/active", async (req, res) => {
    const trades = await storage.getActiveTrades();
    res.json(trades);
  });

  app.get("/api/trades/history", async (req, res) => {
    const trades = await storage.getTradeHistory();
    res.json(trades);
  });

  app.post("/api/trades/:id/close", async (req, res) => {
    const tradeId = parseInt(req.params.id);
    const trade = await storage.getTradeById(tradeId);
    
    if (!trade) {
      return res.status(404).json({ error: "Trade not found" });
    }
    
    if (trade.status !== "open") {
      return res.status(400).json({ error: "Trade is already closed" });
    }
    
    try {
      // Close the trade on Phemex
      const closeResult = await phemexService.closeTrade({
        ticker: trade.ticker,
        orderId: trade.phemexOrderId!,
        currentPrice: trade.currentPrice!
      });
      
      // Update trade record
      const updatedTrade = await storage.closeTrade(
        tradeId, 
        "manual", 
        trade.currentPrice!, 
        closeResult
      );
      
      res.json({ success: true, trade: updatedTrade });
    } catch (error) {
      console.error("Error closing trade:", error);
      res.status(500).json({ error: "Failed to close trade" });
    }
  });

  // Stats route
  app.get("/api/stats", async (req, res) => {
    const activeTrades = await storage.getActiveTrades();
    const todaysTrades = await storage.getTodaysTrades();
    const allTrades = await storage.getTradeHistory();
    
    // Calculate stats
    const todayPnl = todaysTrades.reduce((sum, trade) => sum + (trade.pnlAmount || 0), 0);
    const todayStartBalance = 10000; // Mock starting balance
    const todayPnlPercent = (todayPnl / todayStartBalance) * 100;
    
    const closedTrades = allTrades.filter(trade => trade.status === "closed");
    const profitableTrades = closedTrades.filter(trade => (trade.pnlPercent || 0) > 0);
    const winRate = closedTrades.length > 0 
      ? (profitableTrades.length / closedTrades.length) * 100 
      : 0;
    
    // Get signals from today
    const todaySignals = await storage.getTodaysSignals();
    
    res.json({
      activeTrades: activeTrades.length,
      todayPnl,
      todayPnlPercent,
      winRate,
      signalsToday: todaySignals.length
    });
  });

  // Chart data for a specific ticker
  app.get("/api/chart/:ticker", async (req, res) => {
    const ticker = req.params.ticker;
    try {
      const chartData = await phemexService.getChartData(ticker);
      res.json(chartData);
    } catch (error) {
      console.error("Error fetching chart data:", error);
      res.status(500).json({ error: "Failed to fetch chart data" });
    }
  });

  // Service status routes
  app.get("/api/phemex/status", async (req, res) => {
    try {
      const status = await phemexService.checkConnection();
      if (status) {
        res.json({ connected: true });
      } else {
        res.status(503).json({ connected: false });
      }
    } catch (error) {
      res.status(503).json({ connected: false, error: String(error) });
    }
  });

  app.get("/api/discord/status", async (req, res) => {
    try {
      const status = await discordService.checkConnection();
      if (status) {
        res.json({ connected: true });
      } else {
        res.status(503).json({ connected: false });
      }
    } catch (error) {
      res.status(503).json({ connected: false, error: String(error) });
    }
  });

  // Webhook endpoint for Discord messages
  app.post("/api/discord/webhook", async (req, res) => {
    try {
      // Process and store message from Discord
      await discordService.processMessage(req.body);
      res.status(200).json({ success: true });
    } catch (error) {
      console.error("Error processing Discord webhook:", error);
      res.status(500).json({ error: "Failed to process Discord message" });
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
