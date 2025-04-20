import { Button } from "@/components/ui/button";
import { RefreshCcw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Dashboard() {
  return (
    <div className="h-full flex flex-col">
      {/* Main Trading Dashboard */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <nav className="bg-background border-b border-border py-2">
          <div className="container mx-auto flex items-center space-x-4">
            <a href="/" className="text-primary font-medium">Dashboard</a>
            <a href="/active-trades" className="text-muted-foreground">Active Trades</a>
            <a href="/trade-history" className="text-muted-foreground">Trade History</a>
            <a href="/discord-signals" className="text-muted-foreground">Discord Signals</a>
          </div>
        </nav>
        
        {/* Dashboard Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Active Trades
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">4</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Today's P&L
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-500">+$243</div>
                <p className="text-xs text-muted-foreground">+2.4%</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Win Rate
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">68%</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Signals Today
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">12</div>
              </CardContent>
            </Card>
          </div>
          
          {/* Placeholder content */}
          <div className="rounded-lg border border-border bg-card p-6 text-center">
            <h2 className="text-xl font-semibold mb-4">Crypto Trading Bot Dashboard</h2>
            <p className="text-muted-foreground mb-4">
              This interface allows you to monitor and manage trades executed automatically
              based on Discord trading signals. Connect your Phemex account and configure 
              your trading preferences to start.
            </p>
            <Button>Configure Trading Bot</Button>
          </div>
        </div>
      </div>
    </div>
  );
}
