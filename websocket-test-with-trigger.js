const WebSocket = require('ws');

console.log('🔄 Starting WebSocket real-time test...');

// Connect to WebSocket
const ws = new WebSocket('wss://f33iwzqgcd.execute-api.ap-east-1.amazonaws.com/prod');

let receivedMessages = 0;

ws.onopen = function() {
    console.log('✅ WebSocket connected successfully!');
    console.log('⏳ Listening for real-time updates...');

    // Give the connection a moment to register, then trigger a state change
    setTimeout(() => {
        console.log('🚀 Triggering machine state change...');

        // Use AWS CLI to trigger a test machine state change
        const { spawn } = require('child_process');
        const awsProcess = spawn('aws', [
            'iot-data', 'publish',
            '--topic', 'org/hk-central/machines/test-machine-realtime/status',
            '--payload', JSON.stringify({
                machineId: 'test-machine-realtime',
                status: 'occupied',
                timestamp: Math.floor(Date.now() / 1000),
                gymId: 'hk-central',
                category: 'legs'
            })
        ]);

        awsProcess.on('close', (code) => {
            if (code === 0) {
                console.log('✅ Published test message to MQTT');
            } else {
                console.log('❌ Failed to publish test message');
            }
        });

    }, 2000); // Wait 2 seconds for connection to register
};

ws.onmessage = function(event) {
    receivedMessages++;
    console.log('📨 RECEIVED MESSAGE #' + receivedMessages + ':', event.data);

    try {
        const message = JSON.parse(event.data);
        console.log('  └─ Machine:', message.machineId, 'Status:', message.status);
    } catch (e) {
        console.log('  └─ Raw message (not JSON)');
    }
};

ws.onerror = function(error) {
    console.error('❌ WebSocket error:', error);
};

ws.onclose = function(event) {
    console.log(`🔌 WebSocket closed: ${event.code} ${event.reason}`);
    console.log(`📊 Total messages received: ${receivedMessages}`);

    if (receivedMessages === 0) {
        console.log('❌ No real-time messages received - there is still an issue');
    } else {
        console.log('✅ Real-time messaging is working!');
    }
};

// Run test for 15 seconds
setTimeout(() => {
    console.log('⏰ Test timeout - closing connection');
    ws.close();
}, 15000);