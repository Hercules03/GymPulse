const WebSocket = require('ws');

const WEBSOCKET_URL = 'wss://f33iwzqgcd.execute-api.ap-east-1.amazonaws.com/prod';

console.log('Connecting to WebSocket to listen for messages...');
console.log('URL:', WEBSOCKET_URL);

const ws = new WebSocket(WEBSOCKET_URL);

ws.on('open', function open() {
  console.log('✅ WebSocket connected successfully!');
  console.log('⏳ Listening for messages for 30 seconds...');

  // Keep connection open for 30 seconds to listen for broadcasts
  setTimeout(() => {
    console.log('⏰ Test timeout reached, closing connection');
    ws.close();
  }, 30000);
});

ws.on('message', function message(data) {
  console.log('📨 Received message:', data.toString());
  try {
    const parsed = JSON.parse(data.toString());
    console.log('📋 Parsed message:', JSON.stringify(parsed, null, 2));
  } catch (e) {
    console.log('📋 Message is not JSON, raw content displayed above');
  }
});

ws.on('error', function error(err) {
  console.error('❌ WebSocket error:', err);
});

ws.on('close', function close(code, reason) {
  console.log('🔌 WebSocket connection closed:', code, reason.toString());
  process.exit(0);
});