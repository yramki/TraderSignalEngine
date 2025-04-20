import fetch from 'node-fetch';

/**
 * Test the Discord API key by making a simple request to the Discord API
 * We'll try to get information about the current application (bot)
 */
async function testDiscordApiKey() {
  console.log('Testing Discord API key...');
  
  const apiKey = process.env.DISCORD_API_KEY;
  if (!apiKey) {
    console.error('❌ DISCORD_API_KEY is not set in environment variables');
    return false;
  }
  
  try {
    // Let's try using a different endpoint - get current user info
    const response = await fetch('https://discord.com/api/v10/users/@me', {
      headers: {
        Authorization: `Bot ${apiKey}`
      }
    });
    
    // Check if we got a successful response
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Discord API key is valid!');
      console.log(`Bot name: ${data.name}`);
      console.log(`Bot ID: ${data.id}`);
      return true;
    } else {
      // If we get an error response, log the details
      const errorData = await response.json().catch(() => ({}));
      console.error(`❌ Discord API returned error ${response.status}: ${response.statusText}`);
      console.error('Error details:', errorData);
      return false;
    }
  } catch (error) {
    console.error('❌ Failed to connect to Discord API:', error);
    return false;
  }
}

// Run the test function
testDiscordApiKey()
  .then(isValid => {
    if (!isValid) {
      console.log('Please check your Discord API key and try again.');
    }
    console.log('Discord API test completed.');
  })
  .catch(error => {
    console.error('An unexpected error occurred:', error);
  });