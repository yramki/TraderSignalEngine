import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { insertTradeConfigSchema, TradeConfig } from "@shared/schema";
import { useAppContext } from "@/context/AppContext";
import { 
  Form, 
  FormControl, 
  FormField, 
  FormItem, 
  FormLabel 
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { X, Plus, Eye } from "lucide-react";

// Extend the schema with validation
const formSchema = insertTradeConfigSchema.extend({
  amountPerTrade: z.coerce.number().min(1, "Amount must be at least 1"),
  stopLossPercent: z.coerce.number().min(0.1, "Stop loss must be at least 0.1%").max(50, "Stop loss cannot exceed 50%"),
  leverage: z.coerce.number().min(1, "Leverage must be at least 1").max(50, "Leverage cannot exceed 50"),
});

export default function Sidebar() {
  const { tradeConfig, updateTradeConfig } = useAppContext();
  const [showApiKey, setShowApiKey] = useState(false);
  const [newCrypto, setNewCrypto] = useState("");

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      tradeType: tradeConfig?.tradeType || "Futures",
      leverage: tradeConfig?.leverage || 5,
      amountPerTrade: tradeConfig?.amountPerTrade || 500,
      stopLossPercent: tradeConfig?.stopLossPercent || 2,
      autoExecute: tradeConfig?.autoExecute || true,
      allowLong: tradeConfig?.allowLong || true,
      allowShort: tradeConfig?.allowShort || true,
      minRiskRewardRatio: tradeConfig?.minRiskRewardRatio || "1.5:1",
      allowedCryptos: tradeConfig?.allowedCryptos || ["BTC", "ETH", "SOL"],
      apiKey: tradeConfig?.apiKey || "",
      apiSecret: tradeConfig?.apiSecret || "",
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    await updateTradeConfig(values);
  }

  const addCrypto = () => {
    if (!newCrypto || newCrypto.length === 0) return;
    
    const currentCryptos = form.getValues("allowedCryptos") || [];
    if (!currentCryptos.includes(newCrypto.toUpperCase())) {
      form.setValue("allowedCryptos", [...currentCryptos, newCrypto.toUpperCase()]);
    }
    setNewCrypto("");
  };

  const removeCrypto = (crypto: string) => {
    const currentCryptos = form.getValues("allowedCryptos") || [];
    form.setValue(
      "allowedCryptos",
      currentCryptos.filter((c) => c !== crypto)
    );
  };

  return (
    <div className="w-full lg:w-96 border-r border-border bg-muted overflow-y-auto">
      <div className="p-4">
        <h2 className="text-lg font-semibold mb-4">Trading Configuration</h2>
        
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Account Settings */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-muted-foreground">ACCOUNT</h3>
              <div className="bg-card rounded-lg p-4 space-y-4">
                <FormField
                  control={form.control}
                  name="apiKey"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>API Key</FormLabel>
                      <div className="relative">
                        <FormControl>
                          <Input
                            {...field}
                            type={showApiKey ? "text" : "password"}
                            className="pr-10"
                          />
                        </FormControl>
                        <button
                          type="button"
                          className="absolute right-2 top-2 text-muted-foreground hover:text-foreground"
                          onClick={() => setShowApiKey(!showApiKey)}
                        >
                          <Eye size={18} />
                        </button>
                      </div>
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="apiSecret"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>API Secret</FormLabel>
                      <div className="relative">
                        <FormControl>
                          <Input
                            {...field}
                            type={showApiKey ? "text" : "password"}
                            className="pr-10"
                          />
                        </FormControl>
                      </div>
                    </FormItem>
                  )}
                />
                
                <div className="flex items-center justify-between">
                  <span className="text-sm">API Status</span>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-200 text-green-800">
                    Active
                  </span>
                </div>
              </div>
            </div>

            {/* Trading Settings */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-muted-foreground">TRADING PARAMETERS</h3>
              <div className="bg-card rounded-lg p-4 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="tradeType"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Trade Type</FormLabel>
                        <Select 
                          onValueChange={field.onChange} 
                          defaultValue={field.value}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select trade type" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="Spot">Spot</SelectItem>
                            <SelectItem value="Futures">Futures</SelectItem>
                          </SelectContent>
                        </Select>
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={form.control}
                    name="leverage"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Leverage</FormLabel>
                        <Select 
                          onValueChange={(value) => field.onChange(parseInt(value))} 
                          defaultValue={field.value.toString()}
                          disabled={form.watch("tradeType") === "Spot"}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select leverage" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="1">1x</SelectItem>
                            <SelectItem value="2">2x</SelectItem>
                            <SelectItem value="5">5x</SelectItem>
                            <SelectItem value="10">10x</SelectItem>
                            <SelectItem value="20">20x</SelectItem>
                            <SelectItem value="50">50x</SelectItem>
                          </SelectContent>
                        </Select>
                      </FormItem>
                    )}
                  />
                </div>
                
                <FormField
                  control={form.control}
                  name="amountPerTrade"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Amount per Trade ($)</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} />
                      </FormControl>
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="stopLossPercent"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Stop Loss (%)</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} step="0.1" />
                      </FormControl>
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="autoExecute"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between pt-2">
                      <FormLabel>Auto-Execute Trades</FormLabel>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
              </div>
            </div>
            
            {/* Signal Filters */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-muted-foreground">SIGNAL FILTERS</h3>
              <div className="bg-card rounded-lg p-4 space-y-4">
                <FormField
                  control={form.control}
                  name="allowLong"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between">
                      <FormLabel>Long Positions</FormLabel>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                          className="data-[state=checked]:bg-green-600"
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="allowShort"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between">
                      <FormLabel>Short Positions</FormLabel>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                          className="data-[state=checked]:bg-red-600"
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="minRiskRewardRatio"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Min Risk-Reward Ratio</FormLabel>
                      <Select 
                        onValueChange={field.onChange} 
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select ratio" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="Any">Any</SelectItem>
                          <SelectItem value="1:1">1:1</SelectItem>
                          <SelectItem value="1.5:1">1.5:1</SelectItem>
                          <SelectItem value="2:1">2:1</SelectItem>
                          <SelectItem value="3:1">3:1</SelectItem>
                        </SelectContent>
                      </Select>
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="allowedCryptos"
                  render={() => (
                    <FormItem>
                      <FormLabel>Allowed Cryptocurrencies</FormLabel>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {form.watch("allowedCryptos")?.map((crypto) => (
                          <Badge key={crypto} variant="secondary" className="flex items-center">
                            {crypto}
                            <button 
                              type="button" 
                              className="ml-1.5 inline-flex text-muted-foreground hover:text-foreground"
                              onClick={() => removeCrypto(crypto)}
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </Badge>
                        ))}
                        <div className="flex">
                          <Input
                            className="h-6 w-16 px-2 text-xs"
                            value={newCrypto}
                            onChange={(e) => setNewCrypto(e.target.value.toUpperCase())}
                            placeholder="BTC"
                          />
                          <Button 
                            type="button" 
                            variant="ghost" 
                            size="icon"
                            className="h-6 w-6"
                            onClick={addCrypto}
                          >
                            <Plus className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </FormItem>
                  )}
                />
              </div>
            </div>
            
            <Button type="submit" className="w-full">
              Save Configuration
            </Button>
          </form>
        </Form>
      </div>
    </div>
  );
}
