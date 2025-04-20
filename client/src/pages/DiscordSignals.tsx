import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { TradingSignal } from "@shared/schema";
import TabNavigation from "@/components/TabNavigation";
import SignalCard from "@/components/SignalCard";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { RefreshCcw, Filter, Plus } from "lucide-react";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from "@/components/ui/tabs";
import { useAppContext } from "@/context/AppContext";
import { hasValidSignal, parseDiscordMessage } from "@/lib/discordParser";
import { runDiscordParserTests } from "@/lib/discordParserTest";
import { useToast } from "@/hooks/use-toast";

export default function DiscordSignals() {
  const { refreshData } = useAppContext();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [timeFilter, setTimeFilter] = useState("all");
  const [executionFilter, setExecutionFilter] = useState("all");
  const [sampleSignals, setSampleSignals] = useState<TradingSignal[]>([]);
  const { toast } = useToast();
  
  // Get all discord signals from API
  const { data: apiSignals = [] } = useQuery<TradingSignal[]>({
    queryKey: ['/api/signals/all'],
  });
  
  // Combine API signals with our sample signals
  const allSignals = [...apiSignals, ...sampleSignals];
  
  // Run Discord parser test when component mounts
  useEffect(() => {
    const testResults = runDiscordParserTests();
    if (testResults.failedTests === 0 && testResults.passedTests > 0) {
      console.log("All Discord parser tests passed successfully!");
    }
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refreshData();
    setTimeout(() => setIsRefreshing(false), 500);
  };
  
  // Add sample signals for testing
  const addSampleSignals = () => {
    const now = new Date();
    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    const twoDaysAgo = new Date(now);
    twoDaysAgo.setDate(now.getDate() - 2);
    
    const sampleData = [
      {
        id: Math.floor(Math.random() * 10000),
        ticker: "BTC",
        entryPrice: 67500,
        targetPrice: 70000,
        stopLossPrice: 65200,
        isLong: true,
        risk: 1,
        messageContent: "Longed BTC at 67500 sl- 65200 (1% risk) TPs: 70000",
        messageId: "sample_" + Date.now() + "_1",
        discordChannelId: "sample_channel",
        processed: true,
        executed: false,
        ignored: false,
        signalDate: now,
        createdAt: now,
        updatedAt: now
      },
      {
        id: Math.floor(Math.random() * 10000),
        ticker: "ETH",
        entryPrice: 3520,
        targetPrice: 3300,
        stopLossPrice: 3650,
        isLong: false,
        risk: 1,
        messageContent: "Shorted ETH at 3520 sl- 3650 TPs: 3300",
        messageId: "sample_" + Date.now() + "_2",
        discordChannelId: "sample_channel",
        processed: true,
        executed: true,
        ignored: false,
        signalDate: yesterday,
        createdAt: yesterday,
        updatedAt: yesterday
      },
      {
        id: Math.floor(Math.random() * 10000),
        ticker: "SOL",
        entryPrice: 150.25,
        targetPrice: 160,
        stopLossPrice: 145.5,
        isLong: true,
        risk: 1,
        messageContent: "SOL Entry: 150.25 SL: 145.5 TPs: 160",
        messageId: "sample_" + Date.now() + "_3",
        discordChannelId: "sample_channel",
        processed: true,
        executed: false,
        ignored: true,
        signalDate: twoDaysAgo,
        createdAt: twoDaysAgo,
        updatedAt: twoDaysAgo
      }
    ];
    
    setSampleSignals(prev => [...prev, ...sampleData]);
    
    toast({
      title: "Sample Signals Added",
      description: `Added ${sampleData.length} sample signals for testing`,
    });
  };

  const filteredSignals = allSignals.filter(signal => {
    // Apply execution filter
    if (executionFilter === "executed" && !signal.executed) return false;
    if (executionFilter === "pending" && (signal.executed || signal.ignored)) return false;
    if (executionFilter === "ignored" && !signal.ignored) return false;
    
    // Apply time filter
    if (timeFilter !== "all") {
      const today = new Date();
      const signalDate = new Date(signal.signalDate);
      
      if (timeFilter === "today") {
        return signalDate.toDateString() === today.toDateString();
      } else if (timeFilter === "week") {
        const weekAgo = new Date();
        weekAgo.setDate(today.getDate() - 7);
        return signalDate >= weekAgo;
      } else if (timeFilter === "month") {
        const monthAgo = new Date();
        monthAgo.setMonth(today.getMonth() - 1);
        return signalDate >= monthAgo;
      }
    }
    
    return true;
  });

  const pendingSignals = filteredSignals.filter(s => !s.executed && !s.ignored);
  const executedSignals = filteredSignals.filter(s => s.executed);
  const ignoredSignals = filteredSignals.filter(s => s.ignored);

  return (
    <div className="h-full flex flex-col lg:flex-row">
      {/* Left Panel - Trading Configuration */}
      <Sidebar />
      
      {/* Main Trading Dashboard */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <TabNavigation />
        
        {/* Discord Signals Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Discord Trade Signals</h2>
            <div className="flex items-center space-x-2">
              <Button 
                variant="outline"
                size="sm"
                onClick={addSampleSignals}
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Sample Signals
              </Button>
            
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
              
              <Select value={executionFilter} onValueChange={setExecutionFilter}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Signals</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="executed">Executed</SelectItem>
                  <SelectItem value="ignored">Ignored</SelectItem>
                </SelectContent>
              </Select>
              
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
          
          {/* Signal Count Summary */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Signal Summary</CardTitle>
              <CardDescription>
                Overview of trading signals based on current filters
              </CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-3 gap-4">
              <div className="flex flex-col items-center">
                <Badge variant="outline" className="mb-2 bg-muted">Pending</Badge>
                <span className="text-2xl font-semibold">{pendingSignals.length}</span>
              </div>
              <div className="flex flex-col items-center">
                <Badge variant="outline" className="mb-2 bg-green-500/20 text-green-500">Executed</Badge>
                <span className="text-2xl font-semibold">{executedSignals.length}</span>
              </div>
              <div className="flex flex-col items-center">
                <Badge variant="outline" className="mb-2 bg-muted-foreground/20">Ignored</Badge>
                <span className="text-2xl font-semibold">{ignoredSignals.length}</span>
              </div>
            </CardContent>
          </Card>
          
          {/* Signals Tabs */}
          <Tabs defaultValue="all">
            <TabsList className="mb-4">
              <TabsTrigger value="all">All Signals</TabsTrigger>
              <TabsTrigger value="pending">Pending</TabsTrigger>
              <TabsTrigger value="executed">Executed</TabsTrigger>
              <TabsTrigger value="ignored">Ignored</TabsTrigger>
            </TabsList>
            
            <TabsContent value="all" className="mt-0">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredSignals.length > 0 ? (
                  filteredSignals.map(signal => (
                    <SignalCard key={signal.id} signal={signal} />
                  ))
                ) : (
                  <div className="col-span-3 text-center py-10 text-muted-foreground">
                    No signals found matching the current filters
                  </div>
                )}
              </div>
            </TabsContent>
            
            <TabsContent value="pending" className="mt-0">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {pendingSignals.length > 0 ? (
                  pendingSignals.map(signal => (
                    <SignalCard key={signal.id} signal={signal} />
                  ))
                ) : (
                  <div className="col-span-3 text-center py-10 text-muted-foreground">
                    No pending signals found
                  </div>
                )}
              </div>
            </TabsContent>
            
            <TabsContent value="executed" className="mt-0">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {executedSignals.length > 0 ? (
                  executedSignals.map(signal => (
                    <SignalCard key={signal.id} signal={signal} />
                  ))
                ) : (
                  <div className="col-span-3 text-center py-10 text-muted-foreground">
                    No executed signals found
                  </div>
                )}
              </div>
            </TabsContent>
            
            <TabsContent value="ignored" className="mt-0">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {ignoredSignals.length > 0 ? (
                  ignoredSignals.map(signal => (
                    <SignalCard key={signal.id} signal={signal} />
                  ))
                ) : (
                  <div className="col-span-3 text-center py-10 text-muted-foreground">
                    No ignored signals found
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
