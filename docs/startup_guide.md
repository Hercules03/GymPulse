## Step 1: Start Frontend Development Server

```bash
cd /Users/GitHub/GymPulse/frontend
npm run dev
```
Expected output: Server running at http://localhost:3000/

## Step 2: Start IoT Simulator (Synthetic Data)
```bash
cd /Users/GitHub/GymPulse/simulator
source .venv/bin/activate
python src/gym_simulator.py
```
Expected output:
- "Created 19 machine simulators"
- "Starting simulation for 19 machines..."
- Continuous machine state changes every 30-90 seconds

## Step 3: Verify System is Working

Check Frontend:

- Open http://localhost:3000/ in browser
- Look for current timestamps (not old ones like "12:55:49 PM")
- Status should change between "Free" and "Occupied"

Check AWS Data Flow:

# Check if data is reaching DynamoDB
aws dynamodb get-item \
--table-name gym-pulse-current-state \
--key '{"machineId": {"S": "leg-press-01"}}' \
--query 'Item.{machineId:machineId.S,status:status.S,lastUpdate:lastUpdate.N}'

Check WebSocket Broadcasts:

# Check broadcast logs
aws logs get-log-events \
--log-group-name /aws/lambda/gym-pulse-websocket-broadcast \
--log-stream-name $(aws logs describe-log-streams --log-group-name /aws/lambda/gym-pulse-websocket-broadcast --order-by LastEventTime --descending --limit 1 --query
'logStreams[0].logStreamName' --output text) \
--limit 5

Complete Data Flow You Should See:

1. Simulator → Publishes MQTT messages to AWS IoT Core
2. AWS IoT Core → Triggers IoT Lambda function
3. IoT Lambda → Updates DynamoDB + calls WebSocket broadcast
4. WebSocket Broadcast → Sends real-time updates to frontend
5. Frontend → Displays live machine statuses with current timestamps

Expected Results:

- ✅ Frontend: Live updates every 30-90 seconds
- ✅ 19 machines across 2 branches updating
- ✅ Status changes: Free ↔ Occupied
- ✅ Current timestamps (not old static ones)

Troubleshooting:

If something doesn't work:
1. Check simulator logs for connection errors
2. Check frontend console for WebSocket connection status
3. Verify timestamps in DynamoDB are current
4. Check WebSocket broadcast logs for successful sends

That's it! Those 2 main commands will start the complete real-time system.