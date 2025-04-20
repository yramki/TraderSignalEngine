import { useState } from "react";
import Sidebar from "./Sidebar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";

export default function ConfigSection() {
  const [channelId, setChannelId] = useState<string>("");
  const [isFetching, setIsFetching] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [messages, setMessages] = useState<any[]>([]);
  const { toast } = useToast();

  const fetchMessages = async () => {
    if (!channelId) {
      toast({
        title: "Error",
        description: "Please enter a Discord channel ID",
        variant: "destructive",
      });
      return;
    }

    setIsFetching(true);
    try {
      const response = await fetch(`/api/discord/messages/${channelId}`);
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to fetch messages");
      }
      
      const data = await response.json();
      setMessages(data);
      
      toast({
        title: "Success",
        description: `Fetched ${data.length} messages from Discord channel`,
      });
    } catch (error) {
      console.error("Error fetching messages:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to fetch messages",
        variant: "destructive",
      });
    } finally {
      setIsFetching(false);
    }
  };

  const processChannel = async () => {
    if (!channelId) {
      toast({
        title: "Error",
        description: "Please enter a Discord channel ID",
        variant: "destructive",
      });
      return;
    }

    setIsProcessing(true);
    try {
      const response = await fetch(`/api/discord/process-channel/${channelId}`, {
        method: "POST",
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to process channel");
      }
      
      const data = await response.json();
      
      toast({
        title: "Success",
        description: data.message || `Processed channel successfully`,
      });
    } catch (error) {
      console.error("Error processing channel:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to process channel",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col md:flex-row">
      <Sidebar />
      
      <div className="flex-1 p-4 space-y-4">
        <h2 className="text-2xl font-bold">Configuration</h2>
        
        <Card>
          <CardHeader>
            <CardTitle>Discord Channel Integration</CardTitle>
            <CardDescription>
              Enter a Discord channel ID to fetch and process messages for trading signals
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="channel-id">Discord Channel ID</Label>
              <Input 
                id="channel-id"
                placeholder="Enter channel ID"
                value={channelId}
                onChange={(e) => setChannelId(e.target.value)}
              />
            </div>
            
            {messages.length > 0 && (
              <div className="space-y-2">
                <Label>Recent Messages</Label>
                <div className="border rounded-md p-2 max-h-60 overflow-y-auto">
                  {messages.map((message, index) => (
                    <div key={index} className="text-sm p-2 border-b">
                      <div className="font-semibold">{message.author?.username || 'Unknown'}</div>
                      <div>{message.content}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
          <CardFooter className="flex space-x-2">
            <Button
              onClick={fetchMessages}
              disabled={isFetching}
              variant="secondary"
            >
              {isFetching ? "Fetching..." : "Fetch Messages"}
            </Button>
            <Button
              onClick={processChannel}
              disabled={isProcessing}
            >
              {isProcessing ? "Processing..." : "Process Channel for Signals"}
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
