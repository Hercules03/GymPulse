// WebSocket Connection Debug Script
// Open browser console and paste this to debug WebSocket connections

console.log('=== WebSocket Debug Test ===');

// Check environment variables
console.log('Environment Variables:');
console.log('VITE_WEBSOCKET_URL:', import.meta.env.VITE_WEBSOCKET_URL);
console.log('Development Mode:', import.meta.env.DEV);

// Test manual WebSocket connection
const wsUrl = import.meta.env.VITE_WEBSOCKET_URL;
console.log(`\nTesting WebSocket connection to: ${wsUrl}`);

if (wsUrl && wsUrl !== 'undefined') {
  const testWs = new WebSocket(wsUrl);
  
  testWs.onopen = function(event) {
    console.log('✅ WebSocket connection successful!');
    console.log('Connection event:', event);
    testWs.close();
  };
  
  testWs.onclose = function(event) {
    console.log('WebSocket connection closed:', event.code, event.reason);
    if (event.code === 1000) {
      console.log('✅ Clean close - connection test completed successfully');
    } else {
      console.log('❌ Connection closed with error code:', event.code);
    }
  };
  
  testWs.onerror = function(error) {
    console.error('❌ WebSocket connection error:', error);
    console.log('This might indicate:');
    console.log('- WebSocket API not deployed properly');
    console.log('- Incorrect URL or region');
    console.log('- CORS or security policy issues');
    console.log('- Network connectivity issues');
  };
  
  // Test timeout
  setTimeout(() => {
    if (testWs.readyState === WebSocket.CONNECTING) {
      console.log('❌ Connection timeout - WebSocket is still connecting after 10 seconds');
      testWs.close();
    }
  }, 10000);
  
} else {
  console.error('❌ No WebSocket URL configured or invalid URL');
  console.log('Expected format: wss://api-id.execute-api.region.amazonaws.com/stage');
}

console.log('\n=== End WebSocket Debug Test ===');