import { pgTable, text, serial, integer, boolean, timestamp, doublePrecision, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// User schema for authentication
export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
  email: text("email").notNull().unique(),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
});

// User configuration for trading parameters
export const tradeConfigs = pgTable("trade_configs", {
  id: serial("id").primaryKey(),
  tradeType: text("trade_type").notNull().default("Futures"), // Spot, Futures
  leverage: integer("leverage").notNull().default(5),
  amountPerTrade: doublePrecision("amount_per_trade").notNull().default(500),
  stopLossPercent: doublePrecision("stop_loss_percent").notNull().default(2),
  autoExecute: boolean("auto_execute").notNull().default(true),
  allowLong: boolean("allow_long").notNull().default(true),
  allowShort: boolean("allow_short").notNull().default(true),
  minRiskRewardRatio: text("min_risk_reward_ratio").notNull().default("1.5:1"),
  allowedCryptos: text("allowed_cryptos").array().notNull().default(["BTC", "ETH", "SOL"]),
  customStopLoss: boolean("custom_stop_loss").notNull().default(false),
  apiKey: text("api_key"),
  apiSecret: text("api_secret"),
  active: boolean("active").notNull().default(true),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
});

// Discord trading signals
export const tradingSignals = pgTable("trading_signals", {
  id: serial("id").primaryKey(),
  ticker: text("ticker").notNull(),
  entryPrice: doublePrecision("entry_price").notNull(),
  targetPrice: doublePrecision("target_price").notNull(),
  stopLossPrice: doublePrecision("stop_loss_price").notNull(),
  isLong: boolean("is_long").notNull(),
  risk: doublePrecision("risk").notNull(),
  messageContent: text("message_content").notNull(),
  messageId: text("message_id").notNull().unique(),
  discordChannelId: text("discord_channel_id"),
  processed: boolean("processed").notNull().default(false),
  executed: boolean("executed").notNull().default(false),
  ignored: boolean("ignored").notNull().default(false),
  signalDate: timestamp("signal_date").notNull().defaultNow(),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
});

// Active and historical trades
export const trades = pgTable("trades", {
  id: serial("id").primaryKey(),
  signalId: integer("signal_id").references(() => tradingSignals.id),
  ticker: text("ticker").notNull(),
  tradeType: text("trade_type").notNull(),
  isLong: boolean("is_long").notNull(),
  leverage: integer("leverage"),
  entryPrice: doublePrecision("entry_price").notNull(),
  targetPrice: doublePrecision("target_price").notNull(),
  stopLossPrice: doublePrecision("stop_loss_price").notNull(),
  amount: doublePrecision("amount").notNull(),
  currentPrice: doublePrecision("current_price"),
  pnlAmount: doublePrecision("pnl_amount"),
  pnlPercent: doublePrecision("pnl_percent"),
  status: text("status").notNull().default("open"), // open, closed
  closeReason: text("close_reason"), // target_hit, stop_loss, manual
  openTime: timestamp("open_time").notNull().defaultNow(),
  closeTime: timestamp("close_time"),
  phemexOrderId: text("phemex_order_id"),
  phemexOrderData: jsonb("phemex_order_data"),
  phemexCloseData: jsonb("phemex_close_data"),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
});

// Insert Schemas
export const insertUserSchema = createInsertSchema(users).omit({
  id: true,
  createdAt: true,
  updatedAt: true
});

export const insertTradeConfigSchema = createInsertSchema(tradeConfigs).omit({
  id: true,
  createdAt: true,
  updatedAt: true
});

export const insertTradingSignalSchema = createInsertSchema(tradingSignals).omit({
  id: true,
  signalDate: true,
  createdAt: true,
  updatedAt: true
});

export const insertTradeSchema = createInsertSchema(trades).omit({
  id: true,
  openTime: true,
  closeTime: true,
  createdAt: true,
  updatedAt: true
});

// Types
export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

export type InsertTradeConfig = z.infer<typeof insertTradeConfigSchema>;
export type TradeConfig = typeof tradeConfigs.$inferSelect;

export type InsertTradingSignal = z.infer<typeof insertTradingSignalSchema>;
export type TradingSignal = typeof tradingSignals.$inferSelect;

export type InsertTrade = z.infer<typeof insertTradeSchema>;
export type Trade = typeof trades.$inferSelect;
