import { Switch, Route } from "wouter";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import Dashboard from "@/pages/Dashboard";
import ActiveTrades from "@/pages/ActiveTrades";
import TradeHistory from "@/pages/TradeHistory";
import DiscordSignals from "@/pages/DiscordSignals";
import Header from "@/components/Header";
import { AppProvider } from "./context/AppContext";

function Router() {
  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <Header />
      <main className="flex-1 overflow-hidden">
        <Switch>
          <Route path="/" component={Dashboard} />
          <Route path="/active-trades" component={ActiveTrades} />
          <Route path="/trade-history" component={TradeHistory} />
          <Route path="/discord-signals" component={DiscordSignals} />
          <Route component={NotFound} />
        </Switch>
      </main>
    </div>
  );
}

function App() {
  return (
    <AppProvider>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </AppProvider>
  );
}

export default App;
