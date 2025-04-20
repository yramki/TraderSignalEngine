import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { RiskRewardData } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(value: number | null | undefined, precision = 2): string {
  if (value === null || value === undefined) return '-';
  
  if (value > 1000) {
    return value.toLocaleString('en-US', {
      minimumFractionDigits: precision,
      maximumFractionDigits: precision
    });
  }
  
  // For crypto prices less than 1, use more precision
  const needsMorePrecision = value < 1 && value > 0;
  const actualPrecision = needsMorePrecision ? 6 : precision;
  
  return value.toLocaleString('en-US', {
    minimumFractionDigits: actualPrecision,
    maximumFractionDigits: actualPrecision
  });
}

export function formatPercent(value: number | null | undefined, precision = 2): string {
  if (value === null || value === undefined) return '-';
  return `${value >= 0 ? '+' : ''}${value.toFixed(precision)}%`;
}

export function calculateRiskReward(
  entryPrice: number,
  targetPrice: number,
  stopLossPrice: number,
  isLong: boolean
): RiskRewardData {
  if (isLong) {
    const risk = Math.abs(entryPrice - stopLossPrice) / entryPrice * 100;
    const reward = Math.abs(targetPrice - entryPrice) / entryPrice * 100;
    return {
      risk,
      reward,
      ratio: reward / risk
    };
  } else {
    const risk = Math.abs(entryPrice - stopLossPrice) / entryPrice * 100;
    const reward = Math.abs(entryPrice - targetPrice) / entryPrice * 100;
    return {
      risk,
      reward,
      ratio: reward / risk
    };
  }
}

export function formatTimeAgo(date: Date | string | number): string {
  const now = new Date();
  const past = new Date(date);
  const diffMs = now.getTime() - past.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
  if (diffDays < 30) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
  
  const month = past.toLocaleString('default', { month: 'short' });
  const day = past.getDate();
  return `${month} ${day}`;
}

export function formatDuration(startTime: Date | string, endTime: Date | string | null = null): string {
  const start = new Date(startTime);
  const end = endTime ? new Date(endTime) : new Date();
  
  const diffMs = end.getTime() - start.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const hours = Math.floor(diffMins / 60);
  const mins = diffMins % 60;
  
  return `${hours ? `${hours}h ` : ''}${mins}m`;
}
