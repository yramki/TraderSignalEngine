import { createContext, useContext, useState, ReactNode } from "react";
import { TradeConfig, TradingSignal, Trade } from "@shared/schema";
import { useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

interface AppContextType {
  isConnectedToPhemex: boolean;
  isConnectedToDiscord: boolean;
  refreshData: () => void;
  executeTrade: (signalId: number) => Promise<void>;
  ignoreSignal: (signalId: number) => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [isConnectedToPhemex, setIsConnectedToPhemex] = useState(false);
  const [isConnectedToDiscord, setIsConnectedToDiscord] = useState(false);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  const refreshData = () => {
    queryClient.invalidateQueries({ queryKey: ['/api/trades/active'] });
    queryClient.invalidateQueries({ queryKey: ['/api/signals'] });
    queryClient.invalidateQueries({ queryKey: ['/api/signals/all'] });
  };
  
  // Execute a trade from a signal
  const executeTrade = async (signalId: number) => {
    try {
      await apiRequest('/api/trades/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ signalId }),
      });
      
      toast({
        title: "Trade Executed",
        description: "Signal has been successfully executed as a trade",
      });
      
      refreshData();
    } catch (error) {
      console.error('Error executing trade:', error);
      toast({
        title: "Trade Execution Failed",
        description: error instanceof Error ? error.message : "An unknown error occurred",
        variant: "destructive",
      });
    }
  };
  
  // Ignore a signal
  const ignoreSignal = async (signalId: number) => {
    try {
      await apiRequest('/api/signals/ignore', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ signalId }),
      });
      
      toast({
        title: "Signal Ignored",
        description: "Signal has been marked as ignored",
      });
      
      refreshData();
    } catch (error) {
      console.error('Error ignoring signal:', error);
      toast({
        title: "Failed to Ignore Signal",
        description: error instanceof Error ? error.message : "An unknown error occurred",
        variant: "destructive",
      });
    }
  };

  return (
    <AppContext.Provider
      value={{
        isConnectedToPhemex,
        isConnectedToDiscord,
        refreshData,
        executeTrade,
        ignoreSignal
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useAppContext must be used within an AppProvider");
  }
  return context;
}
