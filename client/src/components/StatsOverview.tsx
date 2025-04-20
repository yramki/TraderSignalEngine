import { useQuery } from "@tanstack/react-query";
import { 
  ClipboardList, 
  TrendingUp, 
  LineChart, 
  Bell 
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { StatsData } from "@/lib/types";
import { formatPercent } from "@/lib/utils";

export default function StatsOverview() {
  const { data: stats } = useQuery<StatsData>({
    queryKey: ['/api/stats'],
    staleTime: 60000,
  });

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Active Trades</span>
            <ClipboardList className="h-5 w-5 text-primary" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-semibold">{stats?.activeTrades || 0}</span>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Today's P&L</span>
            <TrendingUp className={`h-5 w-5 ${
              (stats?.todayPnl || 0) >= 0 ? 'text-green-500' : 'text-red-500'
            }`} />
          </div>
          <div className="mt-2 flex items-baseline">
            <span className={`text-2xl font-semibold ${
              (stats?.todayPnl || 0) >= 0 ? 'text-green-500' : 'text-red-500'
            }`}>
              {(stats?.todayPnl || 0) >= 0 ? '+' : ''}${Math.abs(stats?.todayPnl || 0).toFixed(2)}
            </span>
            <span className={`ml-2 text-xs ${
              (stats?.todayPnlPercent || 0) >= 0 ? 'text-green-500' : 'text-red-500'
            }`}>
              {formatPercent(stats?.todayPnlPercent || 0, 1)}
            </span>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Win Rate</span>
            <LineChart className="h-5 w-5 text-primary" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-semibold">{stats?.winRate.toFixed(1) || 0}%</span>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Signals Today</span>
            <Bell className="h-5 w-5 text-primary" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-semibold">{stats?.signalsToday || 0}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
