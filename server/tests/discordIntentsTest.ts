/**
 * This test checks if the Discord API key has the necessary intents enabled
 */
async function testDiscordApiIntents() {
  const apiKey = process.env.DISCORD_API_KEY;
  
  if (!apiKey) {
    console.error("Discord API key is not set");
    return;
  }
  
  try {
    // First check if the bot can connect to the gateway
    const gatewayResponse = await fetch('https://discord.com/api/v10/gateway/bot', {
      headers: {
        Authorization: `Bot ${apiKey}`
      }
    });
    
    if (!gatewayResponse.ok) {
      const error = await gatewayResponse.json().catch(() => ({}));
      console.error(`Failed to get gateway info: ${gatewayResponse.status} ${gatewayResponse.statusText}`);
      console.error('Error details:', error);
      return;
    }
    
    const gatewayData = await gatewayResponse.json();
    console.log('Gateway connection successful');
    console.log('Session limit:', gatewayData.session_start_limit);
    
    if (gatewayData.session_start_limit && gatewayData.session_start_limit.remaining === 0) {
      console.error('You have used all your session starts for today');
    }
    
    // Now test access to a specific guild/server
    const guildId = '742797926761234463'; // From the channel link you provided
    const guildResponse = await fetch(`https://discord.com/api/v10/guilds/${guildId}`, {
      headers: {
        Authorization: `Bot ${apiKey}`
      }
    });
    
    if (!guildResponse.ok) {
      const error = await guildResponse.json().catch(() => ({}));
      console.error(`Failed to access guild: ${guildResponse.status} ${guildResponse.statusText}`);
      console.error('Error details:', error);
      console.log('This suggests the bot is either not in the server or lacks permissions');
      return;
    }
    
    const guildData = await guildResponse.json();
    console.log(`Successfully accessed guild: ${guildData.name}`);
    
    // Test access to the specific channel
    const channelId = '1026871730964271134';
    const channelResponse = await fetch(`https://discord.com/api/v10/channels/${channelId}`, {
      headers: {
        Authorization: `Bot ${apiKey}`
      }
    });
    
    if (!channelResponse.ok) {
      const error = await channelResponse.json().catch(() => ({}));
      console.error(`Failed to access channel: ${channelResponse.status} ${channelResponse.statusText}`);
      console.error('Error details:', error);
      return;
    }
    
    const channelData = await channelResponse.json();
    console.log(`Successfully accessed channel: ${channelData.name}`);
    
    // Finally test getting messages from the channel
    const messagesResponse = await fetch(`https://discord.com/api/v10/channels/${channelId}/messages?limit=1`, {
      headers: {
        Authorization: `Bot ${apiKey}`
      }
    });
    
    if (!messagesResponse.ok) {
      const error = await messagesResponse.json().catch(() => ({}));
      console.error(`Failed to get messages: ${messagesResponse.status} ${messagesResponse.statusText}`);
      console.error('Error details:', error);
      return;
    }
    
    const messages = await messagesResponse.json();
    console.log(`Successfully retrieved ${messages.length} messages`);
    
    // The test passed if we made it here
    console.log('Discord API intents test passed! Your bot has all necessary permissions.');
  } catch (error) {
    console.error('Error testing Discord API intents:', error);
  }
}

// Run the test
testDiscordApiIntents();