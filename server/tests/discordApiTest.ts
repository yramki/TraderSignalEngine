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
    // Try multiple auth formats to see which one works
    console.log('Testing various auth formats...');
    
    // Format 1: Bot prefix (standard for bot tokens)
    console.log('Trying with Bot prefix on gateway endpoint...');
    let response = await fetch('https://discord.com/api/v10/gateway', {
      headers: {
        Authorization: `Bot ${apiKey}`
      }
    });
    
    // If first format fails, try Bearer format
    if (!response.ok) {
      console.log('Bot prefix failed, trying Bearer format...');
      response = await fetch('https://discord.com/api/v10/users/@me', {
        headers: {
          Authorization: `Bearer ${apiKey}`
        }
      });
    }
    
    // If both fail, try just the token
    if (!response.ok) {
      console.log('Bearer format failed, trying token directly...');
      response = await fetch('https://discord.com/api/v10/users/@me', {
        headers: {
          Authorization: apiKey
        }
      });
    }
    
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