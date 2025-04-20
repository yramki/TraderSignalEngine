import { createContext, useContext, useState, ReactNode } from "react";
import { TradeConfig, TradingSignal, Trade } from "@shared/schema";
import { useQueryClient } from "@tanstack/react-query";

interface AppContextType {
  isConnectedToPhemex: boolean;
  isConnectedToDiscord: boolean;
  refreshData: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [isConnectedToPhemex, setIsConnectedToPhemex] = useState(false);
  const [isConnectedToDiscord, setIsConnectedToDiscord] = useState(false);
  const queryClient = useQueryClient();
  
  const refreshData = () => {
    queryClient.invalidateQueries({ queryKey: ['/api/trades/active'] });
    queryClient.invalidateQueries({ queryKey: ['/api/signals'] });
  };

  return (
    <AppContext.Provider
      value={{
        isConnectedToPhemex,
        isConnectedToDiscord,
        refreshData
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
