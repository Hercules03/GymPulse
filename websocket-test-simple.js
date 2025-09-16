const WebSocket = require('ws');

const WEBSOCKET_URL = 'wss://f33iwzqgcd.execute-api.ap-east-1.amazonaws.com/prod';

console.log('Testing WebSocket connection to:', WEBSOCKET_URL);

const ws = new WebSocket(WEBSOCKET_URL);

ws.on('open', function open() {
  console.log('✅ WebSocket connected successfully!');

  // Keep connection open for a few seconds to see if we receive any messages
  setTimeout(() => {
    ws.close();
  }, 10000);
});

ws.on('message', function message(data) {
  console.log('📨 Received message:', data.toString());
});

ws.on('error', function error(err) {
  console.error('❌ WebSocket error:', err);
});

ws.on('close', function close(code, reason) {
  console.log('🔌 WebSocket connection closed:', code, reason.toString());
});