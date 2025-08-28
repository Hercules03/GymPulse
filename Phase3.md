# Phase 3: Ingest, State, and Aggregation - Step-by-Step Breakdown

## Overview
Implement IoT message processing, state management, and data aggregation pipeline for real-time availability tracking and historical analytics.

## Prerequisites
- Phase 1 infrastructure deployed
- Phase 2 device simulation running
- Lambda functions created but not fully implemented

---

## Step 1: IoT Rule and Message Routing
**Duration**: 20 minutes  
**Status**: ⏳ Pending

### 1.1 Configure IoT Rule
- [ ] Create IoT Rule "gym-pulse-message-processor"
- [ ] SQL query: `SELECT *, topic() as topic FROM 'org/+/machines/+/status'`
- [ ] Target: Lambda function "gym-pulse-iot-ingest"
- [ ] Error action: Republish to error topic

### 1.2 Test Message Routing
- [ ] Publish test message to MQTT topic
- [ ] Verify Lambda function is triggered
- [ ] Check CloudWatch logs for message processing
- [ ] Validate error handling for malformed messages

---

## Step 2: State Transition Logic Implementation
**Duration**: 45 minutes  
**Status**: ⏳ Pending

### 2.1 Lambda Function: IoT Ingest Processor
- [ ] **File**: `lambda/iot-ingest/handler.py`
- [ ] Parse incoming MQTT messages
- [ ] Extract machineId, gymId, status, timestamp
- [ ] Validate message format and required fields

### 2.2 Current State Management
- [ ] Query existing state from current_state table
- [ ] Compare previous vs. new status
- [ ] Identify state transitions (occupied→free, free→occupied)
- [ ] Handle first-time machine registration

### 2.3 State Transition Detection
```python
def detect_transition(previous_state, new_state):
    """
    Returns: None, 'occupied', 'freed', or 'no_change'
    """
    if previous_state is None:
        return 'initialized'
    elif previous_state != new_state:
        return 'freed' if new_state == 'free' else 'occupied'
    else:
        return 'no_change'
```

### 2.4 Timestamp Validation
- [ ] Reject messages older than current state (prevent out-of-order)
- [ ] Handle clock synchronization issues
- [ ] Set reasonable timestamp tolerance (±5 minutes)

---

## Step 3: Current State Table Updates
**Duration**: 25 minutes  
**Status**: ⏳ Pending

### 3.1 DynamoDB Update Operations
- [ ] Update current_state table with new status
- [ ] Set lastUpdate timestamp
- [ ] Include gymId, category, coordinates for quick lookups
- [ ] Use conditional writes to prevent race conditions

### 3.2 Machine Metadata Enrichment
- [ ] Load machine configuration (category, location)
- [ ] Enrich state record with metadata
- [ ] Validate machine exists in configuration

### 3.3 Error Handling
- [ ] Handle DynamoDB write errors
- [ ] Implement retry logic with exponential backoff
- [ ] Log failed updates for manual review
- [ ] Send to dead letter queue if all retries fail

---

## Step 4: Time-Series Event Recording
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 4.1 Event Table Structure
- [ ] Write state transition events to events table
- [ ] Include: machineId, timestamp, status, transition_type
- [ ] Add TTL for automatic cleanup (30 days)
- [ ] Batch writes when possible for efficiency

### 4.2 Event Processing Logic
```python
def record_event(machine_id, timestamp, status, transition_type):
    """
    Record state transition in time-series table
    """
    event = {
        'machineId': machine_id,
        'timestamp': timestamp,
        'status': status,
        'transition': transition_type,
        'ttl': timestamp + (30 * 24 * 3600)  # 30 days
    }
    events_table.put_item(Item=event)
```

### 4.3 Historical Data Integrity
- [ ] Ensure chronological ordering
- [ ] Handle duplicate events (idempotency)
- [ ] Validate data consistency

---

## Step 5: Real-Time Notification System
**Duration**: 35 minutes  
**Status**: ⏳ Pending

### 5.1 WebSocket Connection Management
- [ ] Query WebSocket connections table
- [ ] Filter connections interested in specific machines/gyms
- [ ] Handle connection lifecycle (connect/disconnect)

### 5.2 Real-Time Update Broadcasting
- [ ] Format real-time update message
- [ ] Send to interested WebSocket connections
- [ ] Handle connection errors and cleanup stale connections
- [ ] Track message delivery success rates

### 5.3 Update Message Format
```json
{
  "type": "machine_update",
  "machineId": "leg-press-01",
  "gymId": "hk-central",
  "category": "legs",
  "status": "free",
  "timestamp": 1634567890,
  "lastChange": 1634567850
}
```

---

## Step 6: Alert System Implementation
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 6.1 Alert Trigger Logic
- [ ] Check for active alerts on state transitions
- [ ] Process occupied→free transitions for alert firing
- [ ] Respect quiet hours configuration
- [ ] Implement alert cooldown period

### 6.2 Alert Notification Processing
- [ ] Query alerts table for machine subscriptions
- [ ] Send notifications (WebSocket/email/push)
- [ ] Mark alerts as fired with timestamp
- [ ] Clean up expired or cancelled alerts

### 6.3 Alert Management
```python
def process_alerts(machine_id, new_status):
    """
    Check and fire alerts for machine state changes
    """
    if new_status == 'free':
        active_alerts = get_active_alerts(machine_id)
        for alert in active_alerts:
            if not in_quiet_hours(alert['quiet_hours']):
                fire_alert(alert)
                mark_alert_fired(alert['alert_id'])
```

---

## Step 7: Aggregation Processing
**Duration**: 40 minutes  
**Status**: ⏳ Pending

### 7.1 15-Minute Aggregation Logic
- [ ] Create scheduled Lambda for aggregation (EventBridge)
- [ ] Query events from last 15-minute window
- [ ] Calculate occupancy ratios per machine and category
- [ ] Store results in aggregates table

### 7.2 Aggregation Calculations
```python
def calculate_occupancy_ratio(events, window_start, window_end):
    """
    Calculate percentage of time machine was occupied
    """
    total_window = window_end - window_start
    occupied_time = 0
    
    current_status = 'free'  # Assume free at start
    last_timestamp = window_start
    
    for event in sorted_events:
        if current_status == 'occupied':
            occupied_time += event['timestamp'] - last_timestamp
        current_status = event['status']
        last_timestamp = event['timestamp']
    
    return (occupied_time / total_window) * 100
```

### 7.3 Category and Gym Aggregates
- [ ] Roll up machine data to category level
- [ ] Roll up category data to gym level
- [ ] Store hierarchical aggregates for efficient querying

---

## Step 8: Device Health Monitoring
**Duration**: 25 minutes  
**Status**: ⏳ Pending

### 8.1 Heartbeat Processing
- [ ] Track last message timestamp per device
- [ ] Identify devices that haven't reported recently (>5 minutes)
- [ ] Mark devices as "offline" in current_state
- [ ] Generate health alerts for maintenance

### 8.2 Device Shadow Integration
- [ ] Update device shadow with health status
- [ ] Store connection metadata (last seen, message count)
- [ ] Track device-specific metrics

### 8.3 Stale State Management
```python
def mark_stale_devices():
    """
    Mark devices as offline if no recent activity
    """
    cutoff_time = int(time.time()) - 300  # 5 minutes ago
    
    stale_devices = scan_current_state_table(
        filter_expression='lastUpdate < :cutoff',
        expression_attribute_values={':cutoff': cutoff_time}
    )
    
    for device in stale_devices:
        update_device_status(device['machineId'], 'offline')
```

---

## Step 9: Performance Optimization
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 9.1 Batch Processing Implementation
- [ ] Group multiple updates into single DynamoDB batch
- [ ] Implement message queuing for high-throughput periods
- [ ] Use DynamoDB batch write APIs where possible

### 9.2 Lambda Performance Tuning
- [ ] Optimize Lambda memory allocation
- [ ] Implement connection pooling for DynamoDB
- [ ] Add performance monitoring and alerts
- [ ] Configure appropriate Lambda timeouts

### 9.3 Error Handling and Reliability
- [ ] Implement circuit breaker pattern
- [ ] Add retry logic with exponential backoff
- [ ] Create comprehensive error logging
- [ ] Set up CloudWatch alarms for failure rates

---

## Step 10: Testing and Validation
**Duration**: 25 minutes  
**Status**: ⏳ Pending

### 10.1 End-to-End Testing
- [ ] Send test messages through complete pipeline
- [ ] Verify state transitions are recorded correctly
- [ ] Check real-time updates are delivered
- [ ] Validate aggregation calculations

### 10.2 Load Testing
- [ ] Test with simulated high message volume
- [ ] Monitor Lambda performance under load
- [ ] Check DynamoDB throttling and capacity
- [ ] Validate system recovery from failures

### 10.3 Data Validation
- [ ] Compare simulator state with recorded state
- [ ] Verify aggregation accuracy
- [ ] Check alert firing correctness
- [ ] Validate time-series data integrity

### 10.4 Evidence Capture and Commit
```bash
git add .
git commit -m "feat: Phase 3 ingest and aggregation pipeline

- IoT Rule routing MQTT messages to Lambda
- State transition detection and current_state management
- Time-series event recording with TTL
- Real-time WebSocket notifications
- Alert system with quiet hours support
- 15-minute aggregation for heatmaps and analytics
- Device health monitoring and stale state handling
- Performance optimization and error handling

🤖 Generated with Amazon Q Developer
Co-Authored-By: Amazon Q Developer <noreply@aws.amazon.com>"
```

---

## Success Criteria
- [ ] Messages flow from simulator → IoT Core → Lambda → DynamoDB
- [ ] State transitions detected and recorded correctly
- [ ] Real-time updates delivered via WebSocket (<15s latency)
- [ ] Alerts fire correctly for occupied→free transitions
- [ ] Aggregation pipeline produces accurate occupancy data
- [ ] System handles device offline scenarios gracefully
- [ ] Performance targets met under load testing

## Estimated Total Time: 4.5 hours

## Next Phase
Phase 4: APIs, streams, and alerts implementation