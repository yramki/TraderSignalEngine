import { useState } from "react";
import { Trade } from "@shared/schema";
import { useAppContext } from "@/context/AppContext";
import { formatPrice, formatPercent, formatDuration } from "@/lib/utils";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

interface TradeTableProps {
  trades: Trade[];
  showActions?: boolean;
}

export default function TradeTable({ trades, showActions = true }: TradeTableProps) {
  const { closeTrade } = useAppContext();
  const [closingTrades, setClosingTrades] = useState<Record<number, boolean>>({});

  const handleCloseTrade = async (tradeId: number) => {
    setClosingTrades(prev => ({ ...prev, [tradeId]: true }));
    try {
      await closeTrade(tradeId);
    } finally {
      setClosingTrades(prev => ({ ...prev, [tradeId]: false }));
    }
  };

  if (!trades || trades.length === 0) {
    return (
      <div className="bg-card rounded-lg p-8 text-center">
        <p className="text-muted-foreground">No trades to display</p>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader className="bg-muted">
            <TableRow>
              <TableHead>Symbol</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Entry Price</TableHead>
              <TableHead>Current Price</TableHead>
              <TableHead>P&L</TableHead>
              <TableHead>Duration</TableHead>
              {showActions && <TableHead className="text-right">Actions</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {trades.map((trade) => (
              <TableRow key={trade.id}>
                <TableCell>
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-muted flex items-center justify-center mr-3">
                      <span className="text-sm font-mono font-semibold">
                        {trade.ticker.slice(0, 3)}
                      </span>
                    </div>
                    <div>
                      <div className="font-medium">{trade.ticker}</div>
                      <div className="text-xs text-muted-foreground">
                        {trade.tradeType}
                      </div>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <span className={`px-2 py-0.5 rounded ${
                    trade.isLong
                      ? 'bg-green-500/20 text-green-500'
                      : 'bg-red-500/20 text-red-500'
                  } text-xs font-medium`}>
                    {trade.isLong ? 'LONG' : 'SHORT'}
                  </span>
                </TableCell>
                <TableCell className="font-mono">
                  {formatPrice(trade.entryPrice)}
                </TableCell>
                <TableCell className="font-mono">
                  {formatPrice(trade.currentPrice)}
                </TableCell>
                <TableCell>
                  <span className={`${
                    (trade.pnlPercent || 0) >= 0 ? 'text-green-500' : 'text-red-500'
                  }`}>
                    {formatPercent(trade.pnlPercent)}
                  </span>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {formatDuration(trade.openTime, trade.closeTime)}
                </TableCell>
                {showActions && (
                  <TableCell className="text-right text-sm">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-primary hover:text-primary mr-3"
                    >
                      Edit
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive"
                      onClick={() => handleCloseTrade(trade.id)}
                      disabled={closingTrades[trade.id]}
                    >
                      {closingTrades[trade.id] ? "Closing..." : "Close"}
                    </Button>
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
