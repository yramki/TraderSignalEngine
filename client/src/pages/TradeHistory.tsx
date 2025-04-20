import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Trade } from "@shared/schema";
import TabNavigation from "@/components/TabNavigation";
import TradeTable from "@/components/TradeTable";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { RefreshCcw } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";
import { ChevronDown } from "lucide-react";
import { useAppContext } from "@/context/AppContext";

export default function TradeHistory() {
  const { refreshData } = useAppContext();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [timeFilter, setTimeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  // Get all trade history
  const { data: tradeHistory = [] } = useQuery<Trade[]>({
    queryKey: ['/api/trades/history', timeFilter, statusFilter],
  });

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refreshData();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const filteredTrades = tradeHistory.filter(trade => {
    // Apply status filter
    if (statusFilter !== "all") {
      if (statusFilter === "profitable" && (trade.pnlPercent || 0) <= 0) return false;
      if (statusFilter === "loss" && (trade.pnlPercent || 0) >= 0) return false;
    }
    
    // Apply time filter
    if (timeFilter !== "all") {
      const today = new Date();
      const tradeDate = new Date(trade.closeTime || trade.openTime);
      
      if (timeFilter === "today") {
        return tradeDate.toDateString() === today.toDateString();
      } else if (timeFilter === "week") {
        const weekAgo = new Date();
        weekAgo.setDate(today.getDate() - 7);
        return tradeDate >= weekAgo;
      } else if (timeFilter === "month") {
        const monthAgo = new Date();
        monthAgo.setMonth(today.getMonth() - 1);
        return tradeDate >= monthAgo;
      }
    }
    
    return true;
  });

  // Calculate summary statistics
  const profitableTrades = filteredTrades.filter(trade => (trade.pnlPercent || 0) > 0);
  const totalTrades = filteredTrades.length;
  const winRate = totalTrades > 0 ? (profitableTrades.length / totalTrades) * 100 : 0;
  
  const totalPnl = filteredTrades.reduce((sum, trade) => sum + (trade.pnlAmount || 0), 0);
  const pnlClass = totalPnl >= 0 ? "text-green-500" : "text-red-500";

  return (
    <div className="h-full flex flex-col lg:flex-row">
      {/* Left Panel - Trading Configuration */}
      <Sidebar />
      
      {/* Main Trading Dashboard */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <TabNavigation />
        
        {/* Trade History Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Trade History</h2>
            <div className="flex items-center space-x-2">
              <Select value={timeFilter} onValueChange={setTimeFilter}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Time Period" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Time</SelectItem>
                  <SelectItem value="today">Today</SelectItem>
                  <SelectItem value="week">This Week</SelectItem>
                  <SelectItem value="month">This Month</SelectItem>
                </SelectContent>
              </Select>
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    {statusFilter === "all" ? "All Trades" : 
                     statusFilter === "profitable" ? "Profitable" : "Loss"}
                    <ChevronDown className="ml-2 h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem onClick={() => setStatusFilter("all")}>
                    All Trades
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setStatusFilter("profitable")}>
                    Profitable
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setStatusFilter("loss")}>
                    Loss
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              
              <Button 
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isRefreshing}
              >
                <RefreshCcw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
          
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <Card>
              <CardContent className="pt-6">
                <div className="text-xs text-muted-foreground">Total Trades</div>
                <div className="text-2xl font-semibold mt-1">{totalTrades}</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6">
                <div className="text-xs text-muted-foreground">Win Rate</div>
                <div className="text-2xl font-semibold mt-1">{winRate.toFixed(1)}%</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6">
                <div className="text-xs text-muted-foreground">Total P&L</div>
                <div className={`text-2xl font-semibold mt-1 ${pnlClass}`}>
                  {totalPnl >= 0 ? '+' : ''}${totalPnl.toFixed(2)}
                </div>
              </CardContent>
            </Card>
          </div>
          
          <TradeTable trades={filteredTrades} showActions={false} />
        </div>
      </div>
    </div>
  );
}
