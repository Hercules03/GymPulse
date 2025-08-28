# Phase 2: Synthetic Data and Device Simulation - Step-by-Step Breakdown

## Overview
Set up AWS IoT Device Simulator or custom SDK-based simulator to generate realistic gym equipment telemetry data for demo purposes.

## Prerequisites
- Phase 1 infrastructure deployed and tested
- AWS IoT Core topics configured
- DynamoDB tables created

---

## Step 1: Choose Simulation Approach
**Duration**: 15 minutes  
**Status**: ⏳ Pending

### 1.1 Evaluate Options
- [ ] **Option A**: AWS IoT Device Simulator (managed service)
- [ ] **Option B**: Custom AWS IoT Device SDK simulator (Python/Node.js)
- [ ] **Decision**: Document choice and rationale

### 1.2 Simulator Requirements
- [ ] 10-50 simulated devices (machines)
- [ ] 2 branches (Central, Causeway Bay)
- [ ] 3 categories (legs, chest, back)
- [ ] Realistic occupancy patterns

---

## Step 2: Define Machine Inventory
**Duration**: 20 minutes  
**Status**: ⏳ Pending

### 2.1 Create Machine Configuration
- [ ] **Central Branch** (22.2819, 114.1577):
  - [ ] Legs: leg-press-01, leg-press-02, squat-rack-01, calf-raise-01
  - [ ] Chest: bench-press-01, bench-press-02, chest-fly-01
  - [ ] Back: lat-pulldown-01, rowing-01, pull-up-01

### 2.2 Causeway Bay Branch
- [ ] **Causeway Bay Branch** (22.2783, 114.1747):
  - [ ] Legs: leg-press-03, squat-rack-02, leg-curl-01
  - [ ] Chest: bench-press-03, incline-press-01, dips-01
  - [ ] Back: lat-pulldown-02, rowing-02, t-bar-row-01

### 2.3 Machine Metadata JSON
```json
{
  "machines": [
    {
      "machineId": "leg-press-01",
      "gymId": "hk-central",
      "category": "legs",
      "name": "Leg Press Machine 1",
      "coordinates": {"lat": 22.2819, "lon": 114.1577}
    }
  ]
}
```

---

## Step 3: Model Realistic Usage Patterns
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 3.1 Define Usage Cycles
- [ ] **Occupied Duration**: 30-90 seconds (exercise sets)
- [ ] **Rest Duration**: 60-180 seconds (between sets)
- [ ] **Session Length**: 15-45 minutes per user
- [ ] **Transition Time**: 30-120 seconds (machine changeover)

### 3.2 Peak Hour Patterns
- [ ] **Morning Peak**: 6:00-9:00 AM (70% occupancy)
- [ ] **Lunch Peak**: 12:00-1:00 PM (60% occupancy)
- [ ] **Evening Peak**: 6:00-9:00 PM (85% occupancy)
- [ ] **Off-Peak**: 2:00-5:00 PM (30% occupancy)
- [ ] **Night**: 10:00 PM-6:00 AM (10% occupancy)

### 3.3 Add Realistic Noise
- [ ] **False Positives**: 5% brief occupancy signals (PIR limitations)
- [ ] **Missed Detections**: 3% of actual occupancy events
- [ ] **Network Delays**: Occasional 5-30 second message delays
- [ ] **Device Offline**: Random 2-5 minute offline periods

---

## Step 4: AWS IoT Device Simulator Setup (Option A)
**Duration**: 45 minutes  
**Status**: ⏳ Pending

### 4.1 Deploy IoT Device Simulator
- [ ] Access AWS IoT Device Simulator console
- [ ] Create new simulation project "gym-pulse-simulation"
- [ ] Configure simulation settings

### 4.2 Create Device Type Template
```json
{
  "deviceType": "gym-machine",
  "messageFrequency": "variable",
  "payload": {
    "machineId": "${machineId}",
    "gymId": "${gymId}",
    "status": "${status}",
    "timestamp": "${timestamp}",
    "category": "${category}"
  },
  "topic": "org/${gymId}/machines/${machineId}/status"
}
```

### 4.3 Configure Simulation Logic
- [ ] State machine for occupied/free transitions
- [ ] Variable timing based on usage patterns
- [ ] Peak hour scheduling
- [ ] Multi-device coordination

---

## Step 5: Custom SDK Simulator Setup (Option B)
**Duration**: 60 minutes  
**Status**: ⏳ Pending

### 5.1 Create Simulator Project Structure
```bash
mkdir gym-pulse-simulator
cd gym-pulse-simulator
npm init -y
npm install aws-iot-device-sdk-v2 faker
```

### 5.2 Simulator Core Logic
- [ ] **File**: `src/machine-simulator.js`
  - [ ] Machine state management (occupied/free)
  - [ ] Realistic timing patterns
  - [ ] MQTT publishing logic
  - [ ] Error handling and reconnection

### 5.3 Usage Pattern Engine
- [ ] **File**: `src/usage-patterns.js`
  - [ ] Peak hour calculations
  - [ ] Random but realistic session durations
  - [ ] Category-specific usage patterns
  - [ ] Noise injection logic

### 5.4 Configuration Management
- [ ] **File**: `config/machines.json`
  - [ ] Machine inventory and metadata
  - [ ] Branch and category mappings
  - [ ] Timing configuration parameters

---

## Step 6: Device Certificate Management
**Duration**: 25 minutes  
**Status**: ⏳ Pending

### 6.1 Generate Device Certificates
- [ ] Create certificate for each simulated machine
- [ ] Download private keys and certificates
- [ ] Store securely in simulator configuration

### 6.2 Configure Device Policies
- [ ] Attach IoT policies to certificates
- [ ] Verify publish permissions to correct topics
- [ ] Test certificate activation

### 6.3 Connection Configuration
```javascript
const config = {
  endpoint: process.env.IOT_ENDPOINT,
  cert: fs.readFileSync('certs/device.cert.pem'),
  key: fs.readFileSync('certs/device.private.key'),
  ca: fs.readFileSync('certs/root-CA.crt'),
  clientId: machineId,
  region: 'ap-southeast-1'
};
```

---

## Step 7: Implement Simulation Logic
**Duration**: 40 minutes  
**Status**: ⏳ Pending

### 7.1 State Machine Implementation
- [ ] **States**: idle, occupied, transition
- [ ] **Events**: user_arrives, user_leaves, timeout
- [ ] **Transitions**: Probabilistic based on time and patterns

### 7.2 Message Generation
- [ ] JSON payload formatting
- [ ] Retained message configuration (last known state)
- [ ] QoS level 1 (at least once delivery)
- [ ] Timestamp synchronization

### 7.3 Heartbeat Implementation
- [ ] Periodic health messages every 5 minutes
- [ ] Device shadow updates
- [ ] Connection monitoring

---

## Step 8: Deploy and Test Simulator
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 8.1 Local Testing
- [ ] Start simulator with 5 test machines
- [ ] Verify MQTT message publishing
- [ ] Check message format and timing
- [ ] Monitor CloudWatch logs

### 8.2 IoT Core Verification
- [ ] Use IoT Core test client to subscribe to topics
- [ ] Verify retained messages are working
- [ ] Check device shadow updates
- [ ] Validate message routing to Lambda

### 8.3 End-to-End Testing
- [ ] Verify Lambda receives and processes messages
- [ ] Check DynamoDB current_state updates
- [ ] Confirm time-series event recording
- [ ] Test WebSocket notifications

---

## Step 9: Scale to Full Simulation
**Duration**: 25 minutes  
**Status**: ⏳ Pending

### 9.1 Production Configuration
- [ ] Scale to all 15 machines across 2 branches
- [ ] Configure realistic peak hour patterns
- [ ] Enable noise and variability
- [ ] Set up monitoring and alerting

### 9.2 Performance Validation
- [ ] Monitor message throughput (target: 1-2 msg/min per machine)
- [ ] Check Lambda execution metrics
- [ ] Verify DynamoDB write capacity
- [ ] Test system under sustained load

### 9.3 Demo Scenario Creation
- [ ] Create specific demo sequences
- [ ] Plan machine availability changes for presentation
- [ ] Test chatbot queries with simulated data

---

## Step 10: Documentation and Evidence
**Duration**: 15 minutes  
**Status**: ⏳ Pending

### 10.1 Simulation Documentation
- [ ] Document machine inventory and patterns
- [ ] Create troubleshooting guide
- [ ] Record demo scenarios and timing

### 10.2 Evidence Capture
- [ ] Screenshot simulator dashboard/logs
- [ ] Document AI-assisted development process
- [ ] Create commit with evidence tags

### 10.3 Git Commit
```bash
git add .
git commit -m "feat: Phase 2 synthetic device simulation

- AWS IoT Device Simulator with 15 gym machines
- Realistic usage patterns with peak hour modeling  
- 2 branches (Central, Causeway Bay) with 3 categories
- PIR-like occupancy dynamics with noise injection
- End-to-end validation from MQTT to DynamoDB

🤖 Generated with Amazon Q Developer
Co-Authored-By: Amazon Q Developer <noreply@aws.amazon.com>"
```

---

## Success Criteria
- [ ] 15 simulated machines across 2 branches publishing data
- [ ] Realistic occupancy patterns with peak/off-peak cycles
- [ ] Messages successfully routed to Lambda and DynamoDB
- [ ] WebSocket notifications working for real-time updates
- [ ] Sustained operation without message drops
- [ ] Demo scenarios tested and documented

## Estimated Total Time: 4.5 hours

## Next Phase
Phase 3: Ingest, state, and aggregation processing