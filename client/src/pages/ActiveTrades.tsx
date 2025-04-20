import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Trade } from "@shared/schema";
import TabNavigation from "@/components/TabNavigation";
import TradeTable from "@/components/TradeTable";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { RefreshCcw } from "lucide-react";
import { useAppContext } from "@/context/AppContext";

export default function ActiveTrades() {
  const { refreshData } = useAppContext();
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Get all active trades
  const { data: activeTrades = [] } = useQuery<Trade[]>({
    queryKey: ['/api/trades/active'],
  });

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refreshData();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  return (
    <div className="h-full flex flex-col lg:flex-row">
      {/* Left Panel - Trading Configuration */}
      <Sidebar />
      
      {/* Main Trading Dashboard */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <TabNavigation />
        
        {/* Active Trades Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Active Trades</h2>
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
          
          <TradeTable trades={activeTrades} />
        </div>
      </div>
    </div>
  );
}
