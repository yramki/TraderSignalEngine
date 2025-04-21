import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { hasValidSignal, parseDiscordMessage } from "@/lib/discordParser";
import { SignalData } from "@/lib/types";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { useQueryClient } from "@tanstack/react-query";
import SignalCard from "./SignalCard";

export default function ManualSignalInput() {
  const [message, setMessage] = useState<string>("");
  const [parsedSignal, setParsedSignal] = useState<SignalData | null>(null);
  const [isParsing, setIsParsing] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const parseMessage = () => {
    if (!message.trim()) {
      toast({
        variant: "destructive",
        title: "Message is empty",
        description: "Please paste a Discord message containing a trading signal",
      });
      return;
    }

    setIsParsing(true);
    try {
      // Check if the message contains a valid signal
      if (!hasValidSignal(message)) {
        toast({
          variant: "destructive",
          title: "Invalid signal",
          description: "The message doesn't contain a valid trading signal format",
        });
        setParsedSignal(null);
        setIsParsing(false);
        return;
      }

      // Parse the message
      const signal = parseDiscordMessage(message);
      setParsedSignal(signal);

      if (!signal) {
        toast({
          variant: "destructive",
          title: "Parsing failed",
          description: "Could not extract trading details from the message",
        });
      } else {
        toast({
          title: "Signal parsed successfully",
          description: `Detected ${signal.isLong ? "LONG" : "SHORT"} signal for ${signal.ticker}`,
        });
      }
    } catch (error) {
      console.error("Error parsing message:", error);
      toast({
        variant: "destructive",
        title: "Parsing error",
        description: "An error occurred while parsing the message",
      });
      setParsedSignal(null);
    } finally {
      setIsParsing(false);
    }
  };

  const saveSignal = async () => {
    if (!parsedSignal) return;

    setIsSaving(true);
    try {
      // Create a payload with the parsed signal and a generated message ID
      const payload = {
        ...parsedSignal,
        messageContent: message,
        messageId: `manual_${Date.now()}`,
        discordChannelId: "manual_input",
        processed: false,
        executed: false,
        ignored: false,
      };

      // Save to the API
      await apiRequest("/api/discord/manual-signal", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      // Success
      toast({
        title: "Signal saved",
        description: "The trading signal was successfully saved",
      });

      // Clear form
      setMessage("");
      setParsedSignal(null);

      // Invalidate queries to refresh signal lists
      queryClient.invalidateQueries({ queryKey: ["/api/signals"] });
      queryClient.invalidateQueries({ queryKey: ["/api/signals/recent"] });
      queryClient.invalidateQueries({ queryKey: ["/api/signals/unprocessed"] });
    } catch (error) {
      console.error("Error saving signal:", error);
      toast({
        variant: "destructive",
        title: "Save failed",
        description: "Failed to save the trading signal",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Add Discord Signal Manually</CardTitle>
          <CardDescription>
            Copy and paste a trading signal from Discord to parse and save it
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Textarea
              placeholder="Paste Discord message here (e.g., 'Longed BTC at 67500 sl- 65200 TPs: 70000')"
              className="min-h-[120px]"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
            <div className="flex space-x-2">
              <Button
                onClick={parseMessage}
                disabled={isParsing || !message.trim()}
                variant="secondary"
              >
                {isParsing ? "Parsing..." : "Parse Message"}
              </Button>
              <Button
                onClick={saveSignal}
                disabled={isSaving || !parsedSignal}
                variant="default"
              >
                {isSaving ? "Saving..." : "Save Signal"}
              </Button>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-between border-t pt-6">
          <div className="text-sm text-muted-foreground">
            Supported formats:
            <ul className="list-disc list-inside mt-1">
              <li>Longed BTC at 67500 sl- 65200 TPs: 70000</li>
              <li>SOL Entry: 150.25 SL: 145.5 TPs: 160</li>
              <li>Shorted ETH at 3520 sl- 3650 TPs: 3300</li>
            </ul>
          </div>
        </CardFooter>
      </Card>

      {parsedSignal && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Parsed Signal Preview</h3>
          <SignalCard 
            signal={{
              id: 0,
              ticker: parsedSignal.ticker,
              entryPrice: parsedSignal.entryPrice,
              targetPrice: parsedSignal.targetPrice,
              stopLossPrice: parsedSignal.stopLossPrice,
              isLong: parsedSignal.isLong,
              risk: parsedSignal.risk,
              messageContent: message,
              messageId: `preview_${Date.now()}`,
              discordChannelId: "manual_input",
              processed: false,
              executed: false,
              ignored: false,
              signalDate: new Date(),
              createdAt: new Date(),
              updatedAt: new Date()
            }}
          />
        </div>
      )}
    </div>
  );
}