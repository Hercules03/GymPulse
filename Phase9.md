# Phase 9: Testing, QA, and Observability - Step-by-Step Breakdown

## Overview
Implement comprehensive testing, quality assurance, and observability for sustained operation with 10-50 devices and P95 latency targets.

## Prerequisites
- All phases 1-8 implemented and functional
- System running with synthetic device simulation
- Monitoring infrastructure available

---

## Step 1: Sustained Load Testing
**Duration**: 45 minutes  
**Status**: ⏳ Pending

### 1.1 Simulator Scale-Up Testing
- [ ] **File**: `simulator/load-test-config.js`
- [ ] Configure simulator for 50 concurrent devices
- [ ] Test message publishing at realistic rates (1-2 msg/min per device)
- [ ] Monitor system performance under sustained load
- [ ] Validate no message drops or connection failures

### 1.2 End-to-End Latency Measurement
- [ ] **File**: `testing/latency-monitor.py`
```python
import time
import boto3
from datetime import datetime

def measure_end_to_end_latency():
    """
    Measure latency from MQTT publish to UI tile update
    """
    start_time = time.time()
    
    # Publish test message via IoT Core
    iot_client = boto3.client('iot-data')
    test_message = {
        'machineId': 'test-machine-01',
        'status': 'free',
        'timestamp': int(start_time),
        'testId': f'latency-test-{start_time}'
    }
    
    iot_client.publish(
        topic='org/hk-central/machines/test-machine-01/status',
        payload=json.dumps(test_message)
    )
    
    # Monitor WebSocket for corresponding update
    # Measure time until tile receives update
    return measure_websocket_latency(test_message['testId'])
```

### 1.3 Performance Baseline Documentation
- [ ] Record P95 latency measurements
- [ ] Document throughput capabilities
- [ ] Identify performance bottlenecks
- [ ] Create performance regression tests

---

## Step 2: Unit and Integration Tests
**Duration**: 50 minutes  
**Status**: ⏳ Pending

### 2.1 Lambda Function Unit Tests
- [ ] **File**: `backend/tests/test_iot_ingest.py`
- [ ] Test state transition detection logic
- [ ] Test DynamoDB write operations
- [ ] Test error handling and retry logic
- [ ] Mock external dependencies

### 2.2 API Integration Tests
- [ ] **File**: `backend/tests/test_api_endpoints.py`
```python
import pytest
import requests
from moto import mock_dynamodb2

@mock_dynamodb2
def test_branches_endpoint():
    """
    Test /branches endpoint returns correct data format
    """
    # Setup mock DynamoDB data
    setup_mock_data()
    
    response = requests.get(f"{API_BASE_URL}/branches")
    
    assert response.status_code == 200
    data = response.json()
    assert 'branches' in data
    assert len(data['branches']) > 0
    
    # Validate branch structure
    branch = data['branches'][0]
    required_fields = ['id', 'name', 'coordinates', 'categories']
    for field in required_fields:
        assert field in branch
```

### 2.3 Tool-Use Chain Testing
- [ ] **File**: `agent/tests/test_tool_chains.py`
- [ ] Test getAvailabilityByCategory with various inputs
- [ ] Test getRouteMatrix with edge cases
- [ ] Test Bedrock agent response parsing
- [ ] Validate tool execution error handling

### 2.4 AI-Generated Test Evidence
- [ ] Use Q Developer/Kiro to generate additional test cases
- [ ] Document AI-assisted test creation process
- [ ] Create comprehensive test coverage reports
- [ ] Generate test documentation automatically

---

## Step 3: Quality Assurance Workflows
**Duration**: 35 minutes  
**Status**: ⏳ Pending

### 3.1 Automated QA Pipeline
- [ ] **File**: `.github/workflows/qa-pipeline.yml`
- [ ] Automated testing on pull requests
- [ ] Code quality checks (linting, formatting)
- [ ] Security vulnerability scanning
- [ ] Performance regression testing

### 3.2 Cross-Browser Testing
- [ ] Test WebSocket functionality across browsers
- [ ] Validate geolocation API compatibility
- [ ] Check responsive design on different devices
- [ ] Test chat interface across platforms

### 3.3 Accessibility Testing
- [ ] Screen reader compatibility testing
- [ ] Keyboard navigation validation
- [ ] Color contrast and visual accessibility
- [ ] WCAG 2.1 AA compliance verification

---

## Step 4: Observability Implementation
**Duration**: 40 minutes  
**Status**: ⏳ Pending

### 4.1 Metrics Collection
- [ ] **File**: `infra/monitoring-stack.ts`
- [ ] Ingest message count and processing time
- [ ] API response times and error rates
- [ ] WebSocket connection metrics
- [ ] Tool-call success rate and response time

### 4.2 CloudWatch Dashboards
- [ ] **File**: `monitoring/dashboards/system-health.json`
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", "FunctionName", "gym-pulse-iot-ingest"],
          ["AWS/Lambda", "Duration", "FunctionName", "gym-pulse-iot-ingest"],
          ["AWS/Lambda", "Errors", "FunctionName", "gym-pulse-iot-ingest"]
        ],
        "title": "IoT Ingest Lambda Metrics",
        "period": 300
      }
    },
    {
      "type": "metric", 
      "properties": {
        "metrics": [
          ["AWS/ApiGateway", "Count", "ApiName", "gym-pulse-api"],
          ["AWS/ApiGateway", "Latency", "ApiName", "gym-pulse-api"],
          ["AWS/ApiGateway", "4XXError", "ApiName", "gym-pulse-api"]
        ],
        "title": "API Gateway Metrics"
      }
    }
  ]
}
```

### 4.3 Custom Metrics and Alarms
- [ ] End-to-end latency tracking
- [ ] Alert trigger count and success rate
- [ ] Agent response time and accuracy
- [ ] Device health and connectivity status

---

## Step 5: Logging and Debugging
**Duration**: 25 minutes  
**Status**: ⏳ Pending

### 5.1 Structured Logging Implementation
- [ ] **File**: `backend/utils/logger.py`
```python
import json
import logging
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
    
    def log_event(self, event_type, data, level=logging.INFO):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'data': data,
            'level': logging.getLevelName(level)
        }
        self.logger.log(level, json.dumps(log_entry))
    
    def log_api_call(self, method, endpoint, status_code, duration):
        self.log_event('api_call', {
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'duration_ms': duration
        })
```

### 5.2 Debugging and Traceability
- [ ] Request tracing across service boundaries
- [ ] Correlation IDs for multi-service requests
- [ ] Debug mode for development environment
- [ ] Log aggregation and search capability

### 5.3 Error Tracking and Alerting
- [ ] Centralized error tracking
- [ ] Alert trigger conditions
- [ ] Error categorization and prioritization
- [ ] Automated incident creation

---

## Step 6: Performance Validation
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 6.1 Latency Validation
- [ ] Verify P95 latency ≤ 15s for end-to-end updates
- [ ] Validate chatbot response time ≤ 3s P95
- [ ] Test system under various load conditions
- [ ] Identify and resolve performance bottlenecks

### 6.2 Scalability Testing
- [ ] Test horizontal scaling of Lambda functions
- [ ] Validate DynamoDB auto-scaling performance
- [ ] Test WebSocket connection limits
- [ ] Monitor resource utilization patterns

### 6.3 Reliability Testing
- [ ] Test system recovery from failures
- [ ] Validate circuit breaker patterns
- [ ] Test graceful degradation scenarios
- [ ] Verify data consistency under stress

---

## Step 7: Demo Environment Validation
**Duration**: 25 minutes  
**Status**: ⏳ Pending

### 7.1 Demo Scenario Testing
- [ ] **File**: `testing/demo-scenarios.py`
- [ ] Test "live tiles changing with simulator" scenario
- [ ] Validate "notify when free" alert flow
- [ ] Test "leg day nearby" chatbot query end-to-end
- [ ] Verify branch navigation and integration

### 7.2 Demo Environment Stability
- [ ] Ensure simulator runs without failures during demo
- [ ] Validate all UI components load correctly
- [ ] Test presenter flow and timing
- [ ] Create demo reset and recovery procedures

### 7.3 Evidence Documentation
```bash
git add .
git commit -m "feat: Phase 9 testing, QA, and observability

- Sustained load testing with 50 concurrent devices
- Comprehensive unit and integration test suites
- End-to-end latency measurement and validation (P95 ≤ 15s)
- CloudWatch dashboards and custom metrics
- Structured logging and error tracking
- Cross-browser and accessibility testing
- Demo scenario validation and stability testing
- AI-generated tests and documentation

🤖 Generated with Amazon Q Developer
Co-Authored-By: Amazon Q Developer <noreply@aws.amazon.com>"
```

---

## Success Criteria
- [ ] System sustains 50 concurrent devices without message drops
- [ ] End-to-end latency P95 ≤ 15 seconds consistently achieved
- [ ] Chatbot response time P95 ≤ 3 seconds under demo load
- [ ] Comprehensive test coverage (>80% unit, >70% integration)
- [ ] All accessibility and cross-browser requirements met
- [ ] Monitoring dashboards show system health clearly
- [ ] Demo scenarios execute reliably without failures
- [ ] Performance baselines documented and validated

## Estimated Total Time: 3 hours

## Next Phase
Phase 10: Demo script and submission assets