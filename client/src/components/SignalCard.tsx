import { useState } from "react";
import { MoreHorizontal } from "lucide-react";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TradingSignal } from "@shared/schema";
import { useAppContext } from "@/context/AppContext";
import { formatPrice, formatTimeAgo } from "@/lib/utils";

interface SignalCardProps {
  signal: TradingSignal;
}

export default function SignalCard({ signal }: SignalCardProps) {
  const { executeTrade, ignoreSignal } = useAppContext();
  const [isExecuting, setIsExecuting] = useState(false);
  const [localExecuted, setLocalExecuted] = useState(signal.executed || false);
  const [localIgnored, setLocalIgnored] = useState(signal.ignored || false);

  const handleExecuteTrade = async () => {
    setIsExecuting(true);
    try {
      // Check if this is a sample signal (ID is very large random number)
      if (signal.id > 1000) {
        // For sample signals, we'll just update local state
        setTimeout(() => {
          setLocalExecuted(true);
        }, 500);
      } else {
        // Real signal from the API
        await executeTrade(signal.id);
      }
    } finally {
      setIsExecuting(false);
    }
  };

  const handleIgnoreSignal = async () => {
    // Check if this is a sample signal (ID is very large random number)
    if (signal.id > 1000) {
      // For sample signals, we'll just update local state
      setLocalIgnored(true);
    } else {
      // Real signal from the API
      await ignoreSignal(signal.id);
    }
  };

  return (
    <Card className="overflow-hidden border border-border trade-signal-card">
      <CardHeader className="p-3 border-b border-border flex justify-between items-center">
        <div className="flex items-center">
          <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center mr-2">
            <span className="text-sm font-mono font-semibold">
              {signal.ticker.slice(0, 3)}
            </span>
          </div>
          <div>
            <h3 className="font-medium">{signal.ticker}</h3>
            <div className="flex items-center">
              <span className={`px-1.5 py-0.5 rounded ${
                signal.isLong 
                  ? 'bg-green-500/20 text-green-500' 
                  : 'bg-red-500/20 text-red-500'
              } text-xs font-medium`}>
                {signal.isLong ? 'LONG' : 'SHORT'}
              </span>
            </div>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="h-5 w-5" />
              <span className="sr-only">Actions</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={handleIgnoreSignal}>
              Ignore Signal
            </DropdownMenuItem>
            <DropdownMenuItem>View Details</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      <CardContent className="p-3">
        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <div>
            <span className="text-xs text-muted-foreground">Entry</span>
            <div className="font-medium font-mono">{formatPrice(signal.entryPrice)}</div>
          </div>
          <div>
            <span className="text-xs text-muted-foreground">Target</span>
            <div className="font-medium font-mono">{formatPrice(signal.targetPrice)}</div>
          </div>
          <div>
            <span className="text-xs text-muted-foreground">Stop Loss</span>
            <div className="font-medium font-mono">{formatPrice(signal.stopLossPrice)}</div>
          </div>
          <div>
            <span className="text-xs text-muted-foreground">Risk</span>
            <div className="font-medium">{signal.risk}%</div>
          </div>
        </div>
        <div className="mt-3 flex justify-between">
          <span className="text-xs text-muted-foreground">{formatTimeAgo(signal.signalDate)}</span>
          {signal.executed ? (
            <span className="text-xs px-2 py-1 rounded bg-green-200 text-green-800 font-medium">
              Executed
            </span>
          ) : signal.ignored ? (
            <span className="text-xs px-2 py-1 rounded bg-gray-200 text-gray-800 font-medium">
              Ignored
            </span>
          ) : (
            <Button 
              size="sm" 
              variant="default" 
              className="text-xs px-2 py-1 h-auto"
              onClick={handleExecuteTrade}
              disabled={isExecuting}
            >
              {isExecuting ? "..." : "Execute"}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
