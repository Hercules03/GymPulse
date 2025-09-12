const WebSocket = require('ws');

console.log('Testing WebSocket connection...');
const wsUrl = 'wss://f33iwzqgcd.execute-api.ap-east-1.amazonaws.com/prod';
console.log(`Connecting to: ${wsUrl}`);

const ws = new WebSocket(wsUrl);

ws.on('open', function() {
    console.log('✅ WebSocket connection successful!');
    console.log('Connection opened at:', new Date().toISOString());
    
    // Send a test message
    ws.send(JSON.stringify({
        action: 'test',
        message: 'Hello WebSocket!'
    }));
    
    // Close after 5 seconds
    setTimeout(() => {
        console.log('Closing connection...');
        ws.close(1000, 'Test completed');
    }, 5000);
});

ws.on('message', function(data) {
    console.log('📨 Received message:', data.toString());
});

ws.on('error', function(error) {
    console.error('❌ WebSocket error:', error.message);
    console.error('Full error:', error);
});

ws.on('close', function(code, reason) {
    console.log(`🔌 Connection closed: ${code} - ${reason.toString()}`);
    
    if (code === 1000) {
        console.log('✅ Clean close - connection test completed successfully');
    } else {
        console.log('❌ Connection closed with error code:', code);
        console.log('Common error codes:');
        console.log('- 1006: Abnormal closure (server rejected connection)');
        console.log('- 1002: Protocol error');
        console.log('- 1011: Server error');
    }
    
    process.exit(code === 1000 ? 0 : 1);
});

// Set timeout for connection
setTimeout(() => {
    if (ws.readyState === WebSocket.CONNECTING) {
        console.log('❌ Connection timeout after 10 seconds');
        ws.close();
    }
}, 10000);