import { pgTable, varchar, boolean, integer, timestamp, text } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Define the traders table
export const tradersTable = pgTable("traders", {
  id: varchar("id", { length: 255 }).primaryKey(),
  name: varchar("name", { length: 255 }).notNull(),
  enabled: boolean("enabled").default(true).notNull(),
});

// Define the trading signals table
export const signalsTable = pgTable("signals", {
  id: varchar("id", { length: 255 }).primaryKey(),
  traderId: varchar("trader_id", { length: 255 }).notNull().references(() => tradersTable.id),
  symbol: varchar("symbol", { length: 50 }).notNull(),
  direction: varchar("direction", { length: 10 }).notNull(), // BUY or SELL
  entry: varchar("entry", { length: 50 }).notNull(),
  stopLoss: varchar("stop_loss", { length: 50 }),
  takeProfit: varchar("take_profit", { length: 50 }).array(),
  leverage: integer("leverage"),
  timestamp: timestamp("timestamp").defaultNow().notNull(),
  processed: boolean("processed").default(false).notNull(),
  rawText: text("raw_text").notNull(),
});

// Define the trades table
export const tradesTable = pgTable("trades", {
  id: varchar("id", { length: 255 }).primaryKey(),
  signalId: varchar("signal_id", { length: 255 }).notNull().references(() => signalsTable.id),
  status: varchar("status", { length: 20 }).notNull(), // OPEN, CLOSED, CANCELLED
  entryPrice: varchar("entry_price", { length: 50 }),
  closePrice: varchar("close_price", { length: 50 }),
  size: varchar("size", { length: 50 }).notNull(),
  pnl: varchar("pnl", { length: 50 }),
  pnlPercentage: varchar("pnl_percentage", { length: 50 }),
  closeReason: varchar("close_reason", { length: 50 }), // STOP_LOSS, TAKE_PROFIT, MANUAL
  openedAt: timestamp("opened_at").defaultNow().notNull(),
  closedAt: timestamp("closed_at"),
});

// Define the configuration table
export const configTable = pgTable("config", {
  id: varchar("id", { length: 255 }).primaryKey().default("default"),
  amountPerTrade: integer("amount_per_trade").default(100),
  stopLossPercentage: integer("stop_loss_percentage").default(5),
  takeProfitPercentage: integer("take_profit_percentage").default(15),
  leverageMultiplier: integer("leverage_multiplier").default(5),
  minMarketCapUSD: integer("min_market_cap_usd").default(1000000), // $1M by default
  enableAutoTrading: boolean("enable_auto_trading").default(false),
  enableTraderFiltering: boolean("enable_trader_filtering").default(false),
  discordToken: varchar("discord_token", { length: 255 }),
  phemexApiKey: varchar("phemex_api_key", { length: 255 }),
  phemexApiSecret: varchar("phemex_api_secret", { length: 255 }),
});

// Create Zod schemas for insert operations
export const insertTraderSchema = createInsertSchema(tradersTable);
export const insertSignalSchema = createInsertSchema(signalsTable);
export const insertTradeSchema = createInsertSchema(tradesTable);
export const insertConfigSchema = createInsertSchema(configTable).omit({ id: true });

// Create types from the schemas
export type Trader = typeof tradersTable.$inferSelect;
export type InsertTrader = z.infer<typeof insertTraderSchema>;

export type Signal = typeof signalsTable.$inferSelect;
export type InsertSignal = z.infer<typeof insertSignalSchema>;

export type Trade = typeof tradesTable.$inferSelect;
export type InsertTrade = z.infer<typeof insertTradeSchema>;

export type Config = typeof configTable.$inferSelect;
export type InsertConfig = z.infer<typeof insertConfigSchema>;