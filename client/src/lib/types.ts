export interface SignalData {
  ticker: string;
  entryPrice: number;
  targetPrice: number;
  stopLossPrice: number;
  isLong: boolean;
  risk: number;
}

export interface StatsData {
  activeTrades: number;
  todayPnl: number;
  todayPnlPercent: number;
  winRate: number;
  signalsToday: number;
}

export interface ChartPoint {
  time: string;
  price: number;
}

export interface RiskRewardData {
  risk: number;
  reward: number;
  ratio: number;
}
