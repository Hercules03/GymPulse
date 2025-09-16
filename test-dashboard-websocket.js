console.log('Testing dashboard WebSocket...'); 
const ws = new WebSocket('wss://f33iwzqgcd.execute-api.ap-east-1.amazonaws.com/prod?branches=hk-central&categories=legs'); 
ws.onopen = () => console.log('✅ Dashboard WebSocket test connected');
ws.onmessage = (e) => console.log('📦 Dashboard test received:', JSON.parse(e.data));
ws.onerror = (e) => console.log('❌ Dashboard WebSocket error:', e);
setTimeout(() => ws.close(), 10000);
