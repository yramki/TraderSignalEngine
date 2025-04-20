import { Link, useLocation } from "wouter";

interface TabItem {
  name: string;
  path: string;
}

const tabs: TabItem[] = [
  { name: "Dashboard", path: "/" },
  { name: "Active Trades", path: "/active-trades" },
  { name: "Trade History", path: "/trade-history" },
  { name: "Discord Signals", path: "/discord-signals" }
];

export default function TabNavigation() {
  const [location] = useLocation();

  return (
    <div className="bg-muted px-4 border-b border-border">
      <div className="flex space-x-1">
        {tabs.map((tab) => {
          const isActive = tab.path === "/" 
            ? location === "/"
            : location.startsWith(tab.path);
            
          return (
            <Link key={tab.path} href={tab.path}>
              <a className={`px-4 py-3 text-sm font-medium ${
                isActive 
                  ? 'border-b-2 border-primary text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}>
                {tab.name}
              </a>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
