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
**Status**: ✅ Completed

### 1.1 Evaluate Options
- [x] **Option A**: AWS IoT Device Simulator (managed service)
- [x] **Option B**: Custom AWS IoT Device SDK simulator (Python)
- [x] **Decision**: Choose Option B (Custom Python SDK) - Better control, consistent with Python backend, easier debugging

### 1.2 Simulator Requirements
- [x] 15 simulated devices (machines) total
- [x] 2 branches (Central, Causeway Bay)
- [x] 3 categories (legs, chest, back)
- [x] Realistic occupancy patterns with peak hours

---

## Step 2: Define Machine Inventory
**Duration**: 20 minutes  
**Status**: ✅ Completed

### 2.1 Create Machine Configuration
- [x] **Central Branch** (22.2819, 114.1577):
  - [x] Legs: leg-press-01, leg-press-02, squat-rack-01, calf-raise-01
  - [x] Chest: bench-press-01, bench-press-02, chest-fly-01
  - [x] Back: lat-pulldown-01, rowing-01, pull-up-01

### 2.2 Causeway Bay Branch
- [x] **Causeway Bay Branch** (22.2783, 114.1747):
  - [x] Legs: leg-press-03, squat-rack-02, leg-curl-01
  - [x] Chest: bench-press-03, incline-press-01, dips-01
  - [x] Back: lat-pulldown-02, rowing-02, t-bar-row-01

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
**Status**: ✅ Completed

### 3.1 Define Usage Cycles
- [x] **Occupied Duration**: 30-90 seconds (exercise sets)
- [x] **Rest Duration**: 60-180 seconds (between sets)
- [x] **Session Length**: 15-45 minutes per user
- [x] **Transition Time**: 30-120 seconds (machine changeover)

### 3.2 Peak Hour Patterns
- [x] **Morning Peak**: 6:00-9:00 AM (70% occupancy)
- [x] **Lunch Peak**: 12:00-1:00 PM (60% occupancy)
- [x] **Evening Peak**: 6:00-9:00 PM (85% occupancy)
- [x] **Off-Peak**: 2:00-5:00 PM (30% occupancy)
- [x] **Night**: 10:00 PM-6:00 AM (10% occupancy)

### 3.3 Add Realistic Noise
- [x] **False Positives**: 5% brief occupancy signals (PIR limitations)
- [x] **Missed Detections**: 3% of actual occupancy events
- [x] **Network Delays**: Occasional 5-30 second message delays
- [x] **Device Offline**: Random 2-5 minute offline periods

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
**Status**: ✅ Completed

### 5.1 Create Simulator Project Structure
```bash
mkdir gym-pulse-simulator
cd gym-pulse-simulator
uv init
uv add boto3 awsiotsdk faker
```

### 5.2 Simulator Core Logic
- [x] **File**: `src/machine_simulator.py`
  - [x] Machine state management (occupied/free)
  - [x] Realistic timing patterns
  - [x] MQTT publishing logic
  - [x] Error handling and reconnection

### 5.3 Usage Pattern Engine
- [x] **File**: `src/usage_patterns.py`
  - [x] Peak hour calculations
  - [x] Random but realistic session durations
  - [x] Category-specific usage patterns
  - [x] Noise injection logic

### 5.4 Configuration Management
- [x] **File**: `config/machines.json`
  - [x] Machine inventory and metadata
  - [x] Branch and category mappings
  - [x] Timing configuration parameters

---

## Step 6: Device Certificate Management
**Duration**: 25 minutes  
**Status**: ✅ Completed

### 6.1 Generate Device Certificates
- [x] Create certificate placeholders for each simulated machine
- [x] Set up certificate directory structure
- [x] Store certificates in simulator configuration

### 6.2 Configure Device Policies
- [x] Configure IoT policies for MQTT publishing
- [x] Set up topic permissions structure
- [x] Test certificate loading functionality

### 6.3 Connection Configuration
```python
import os

config = {
    'endpoint': os.environ['IOT_ENDPOINT'],
    'cert_path': 'certs/device.cert.pem',
    'key_path': 'certs/device.private.key',
    'ca_path': 'certs/root-CA.crt',
    'client_id': machine_id,
    'region': 'ap-southeast-1'
}
```

---

## Step 7: Implement Simulation Logic
**Duration**: 40 minutes  
**Status**: ✅ Completed

### 7.1 State Machine Implementation
- [x] **States**: free, occupied, offline
- [x] **Events**: state transitions based on usage patterns
- [x] **Transitions**: Probabilistic based on time and patterns

### 7.2 Message Generation
- [x] JSON payload formatting
- [x] Retained message configuration (last known state)
- [x] QoS level 1 (at least once delivery)
- [x] Timestamp synchronization

### 7.3 Heartbeat Implementation
- [x] State change monitoring and publishing
- [x] Connection management
- [x] Offline simulation periods

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
**Status**: ✅ Completed

### 10.1 Simulation Documentation
- [x] Document machine inventory and patterns
- [x] Create comprehensive README with usage instructions
- [x] Record demo scenarios and timing

### 10.2 Evidence Capture
- [x] Document simulator functionality and architecture
- [x] Document AI-assisted development process
- [x] Create commit with evidence tags

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