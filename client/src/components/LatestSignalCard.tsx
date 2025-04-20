import { useState } from "react";
import { TradingSignal } from "@shared/schema";
import { useAppContext } from "@/context/AppContext";
import { formatPrice, calculateRiskReward, formatTimeAgo } from "@/lib/utils";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Zap, CheckCircle2 } from "lucide-react";
import ChartComponent from "./ChartComponent";
import { useQuery } from "@tanstack/react-query";
import { ChartPoint } from "@/lib/types";

interface LatestSignalCardProps {
  signal: TradingSignal;
}

export default function LatestSignalCard({ signal }: LatestSignalCardProps) {
  const { executeTrade, ignoreSignal } = useAppContext();
  const [isExecuting, setIsExecuting] = useState(false);
  const [isIgnoring, setIsIgnoring] = useState(false);

  const { data: chartData = [] } = useQuery<ChartPoint[]>({
    queryKey: [`/api/chart/${signal.ticker}`],
  });

  const handleExecuteTrade = async () => {
    setIsExecuting(true);
    try {
      await executeTrade(signal.id);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleIgnoreSignal = async () => {
    setIsIgnoring(true);
    try {
      await ignoreSignal(signal.id);
    } finally {
      setIsIgnoring(false);
    }
  };

  const { risk, reward, ratio } = calculateRiskReward(
    signal.entryPrice,
    signal.targetPrice,
    signal.stopLossPrice,
    signal.isLong
  );

  // Calculate risk-reward ratio in percentage for progress bar
  const riskRewardRatio = ratio / (ratio + 1) * 100;

  return (
    <Card className="overflow-hidden">
      <CardHeader className="p-4 bg-gradient-to-r from-primary/20 to-card border-b border-border">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded-md bg-primary/30 flex items-center justify-center">
              <Zap className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 className="font-medium">New Signal Detected</h3>
              <p className="text-xs text-muted-foreground">From Discord • {formatTimeAgo(signal.signalDate)}</p>
            </div>
          </div>
          <div className="flex space-x-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleIgnoreSignal}
              disabled={isIgnoring || isExecuting || signal.executed || signal.ignored}
            >
              {isIgnoring ? "Ignoring..." : "Ignore"}
            </Button>
            <Button 
              size="sm" 
              onClick={handleExecuteTrade}
              disabled={isExecuting || isIgnoring || signal.executed || signal.ignored}
            >
              {isExecuting ? "Executing..." : "Execute Trade"}
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="p-4 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Signal Details */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center mr-3">
                <span className="text-lg font-mono font-semibold">
                  {signal.ticker.slice(0, 2)}
                </span>
              </div>
              <div>
                <h3 className="text-lg font-semibold">{signal.ticker}</h3>
                <div className="flex items-center">
                  <span className={`px-2 py-0.5 rounded ${
                    signal.isLong 
                      ? 'bg-green-500/20 text-green-500' 
                      : 'bg-red-500/20 text-red-500'
                  } text-xs font-medium`}>
                    {signal.isLong ? 'LONG' : 'SHORT'}
                  </span>
                  <span className="ml-2 text-xs text-muted-foreground">Perpetual Futures</span>
                </div>
              </div>
            </div>
            <div className="text-right">
              <span className="text-xs text-muted-foreground">Risk</span>
              <div className="text-sm font-medium">{signal.risk}%</div>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-x-4 gap-y-3">
            <div>
              <span className="text-xs text-muted-foreground">Entry Price</span>
              <div className="text-sm font-medium font-mono">{formatPrice(signal.entryPrice)}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Stop Loss</span>
              <div className="text-sm font-medium font-mono">{formatPrice(signal.stopLossPrice)}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Target Price</span>
              <div className="text-sm font-medium font-mono">{formatPrice(signal.targetPrice)}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Status</span>
              <div className="text-sm font-medium">
                {signal.executed ? (
                  <span className="inline-flex items-center">
                    <CheckCircle2 className="h-4 w-4 text-green-500 mr-1" />
                    Executed
                  </span>
                ) : signal.ignored ? (
                  <span className="text-muted-foreground">Ignored</span>
                ) : (
                  <span>Pending</span>
                )}
              </div>
            </div>
          </div>
          
          <div className="pt-2">
            <div className="text-xs text-muted-foreground mb-1">Risk-Reward Ratio</div>
            <Progress value={riskRewardRatio} className="h-2" />
            <div className="flex justify-between text-xs mt-1">
              <span>Risk: {signal.isLong ? '-' : '+'}{formatPrice(Math.abs(signal.entryPrice - signal.stopLossPrice), 4)}</span>
              <span>Reward: {signal.isLong ? '+' : '-'}{formatPrice(Math.abs(signal.targetPrice - signal.entryPrice), 4)}</span>
            </div>
          </div>
        </div>
        
        {/* Chart */}
        <div className="chart-container rounded-lg overflow-hidden">
          <ChartComponent 
            ticker={signal.ticker}
            data={chartData}
            entryPrice={signal.entryPrice}
            targetPrice={signal.targetPrice}
            stopLossPrice={signal.stopLossPrice}
            isLong={signal.isLong}
          />
        </div>
      </CardContent>
    </Card>
  );
}
