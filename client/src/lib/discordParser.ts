import { SignalData } from "./types";

/**
 * Parse Discord message to extract trading signal data
 * Example format:
 * "Longed OL at 0.0628 sl- 0.0584 (1% risk)"
 * "OL Entry: 0.0628 SL: BE TPs: 0.06662"
 */
export function parseDiscordMessage(message: string): SignalData | null {
  try {
    // Extract ticker
    const tickerMatch = message.match(/(?:Longed|Shorted)\s+(\w+)|(\w+)\s+Entry:/i);
    const ticker = (tickerMatch && (tickerMatch[1] || tickerMatch[2])) || null;
    
    if (!ticker) return null;
    
    // Check if long or short
    const isLong = /Longed|LONG/i.test(message);
    
    // Extract entry price
    const entryMatch = message.match(/at\s+([\d.]+)|Entry:\s+([\d.]+)/i);
    const entryPrice = entryMatch 
      ? parseFloat(entryMatch[1] || entryMatch[2]) 
      : null;
    
    if (!entryPrice) return null;
    
    // Extract stop loss price
    const slMatch = message.match(/sl-\s+([\d.]+)|SL:\s+([\d.]+)|SL\s+([\d.]+)/i);
    const stopLossPrice = slMatch 
      ? parseFloat(slMatch[1] || slMatch[2] || slMatch[3]) 
      : null;
    
    if (!stopLossPrice) return null;
    
    // Extract target price
    const tpMatch = message.match(/TPs?:\s+([\d.]+)|target\s+([\d.]+)/i);
    const targetPrice = tpMatch 
      ? parseFloat(tpMatch[1] || tpMatch[2]) 
      : null;
    
    if (!targetPrice) return null;
    
    // Extract risk percentage
    const riskMatch = message.match(/\((\d+)%\s+risk\)/i);
    const risk = riskMatch ? parseFloat(riskMatch[1]) : 1; // Default to 1% if not specified
    
    return {
      ticker,
      entryPrice,
      targetPrice,
      stopLossPrice,
      isLong,
      risk
    };
  } catch (error) {
    console.error("Error parsing Discord message:", error);
    return null;
  }
}

/**
 * Take the raw message content and check if it contains valid trading signal
 */
export function hasValidSignal(message: string): boolean {
  // Check for common trading signal patterns
  const hasEntryPattern = /Entry:|at\s+[\d.]+/i.test(message);
  const hasStopLossPattern = /SL:|sl-\s+[\d.]+/i.test(message);
  const hasTargetPattern = /TP:|TPs:|target\s+[\d.]+/i.test(message);
  const hasDirectionPattern = /Longed|Shorted|LONG|SHORT/i.test(message);
  
  // Require at least 3 of these patterns to consider it a valid signal
  const matchCount = [
    hasEntryPattern,
    hasStopLossPattern,
    hasTargetPattern,
    hasDirectionPattern
  ].filter(Boolean).length;
  
  return matchCount >= 3;
}
