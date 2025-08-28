# Phase 4: APIs, Streams, and Alerts - Step-by-Step Breakdown

## Overview
Implement REST endpoints, real-time WebSocket streaming, and alert system for machine availability notifications with quiet hours support.

## Prerequisites
- Phase 1 infrastructure deployed
- Phase 2 device simulation running
- Phase 3 ingest pipeline operational
- Lambda functions ready for API implementation

---

## Step 1: REST API Endpoint Implementation
**Duration**: 45 minutes  
**Status**: ⏳ Pending

### 1.1 GET /branches Endpoint
- [ ] **File**: `lambda/api-handlers/branches.py`
- [ ] Query current_state table for all machines
- [ ] Aggregate free counts by branch and category
- [ ] Include branch coordinates and metadata
- [ ] Return JSON with branch list and availability

### 1.2 GET /branches/{id}/categories/{category}/machines
- [ ] **File**: `lambda/api-handlers/machines.py`
- [ ] Query machines by branch and category
- [ ] Include current status, last change timestamp
- [ ] Add alert eligibility information
- [ ] Format machine details with metadata

### 1.3 GET /machines/{id}/history Endpoint
- [ ] **File**: `lambda/api-handlers/history.py`
- [ ] Query aggregates table for 24-hour data
- [ ] Return 15-minute bins for heatmap rendering
- [ ] Include occupancy ratios and patterns
- [ ] Add "likely free in 30m" prediction

### 1.4 POST /alerts Endpoint
- [ ] **File**: `lambda/api-handlers/alerts.py`
- [ ] Create alert subscriptions in alerts table
- [ ] Validate machine existence and user input
- [ ] Support quiet hours configuration
- [ ] Return alert ID and subscription details

---

## Step 2: API Gateway Configuration
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 2.1 REST API Routes Setup
- [ ] Configure API Gateway REST API
- [ ] Set up Lambda proxy integrations
- [ ] Enable CORS for web frontend access
- [ ] Configure request/response mappings

### 2.2 Error Handling and Validation
- [ ] Implement input validation schemas
- [ ] Set up error response formats
- [ ] Add request throttling and rate limiting
- [ ] Configure API Gateway logging

### 2.3 API Documentation
- [ ] Generate OpenAPI/Swagger specification
- [ ] Create Postman collection for testing
- [ ] Document authentication requirements
- [ ] Add example requests and responses

---

## Step 3: WebSocket/SSE Real-Time Streaming
**Duration**: 40 minutes  
**Status**: ⏳ Pending

### 3.1 WebSocket API Setup
- [ ] Create WebSocket API in API Gateway
- [ ] Configure $connect, $disconnect, $default routes
- [ ] Set up connection management table
- [ ] Implement connection lifecycle handlers

### 3.2 Connection Management
- [ ] **File**: `lambda/websocket-handlers/connect.py`
  - [ ] Store connection ID and metadata
  - [ ] Handle connection authentication
  - [ ] Subscribe to relevant machine updates
- [ ] **File**: `lambda/websocket-handlers/disconnect.py`
  - [ ] Clean up connection subscriptions
  - [ ] Remove from connection management table

### 3.3 Real-Time Broadcasting
- [ ] **File**: `lambda/websocket-handlers/broadcast.py`
- [ ] Send machine updates to subscribed connections
- [ ] Handle connection errors and cleanup
- [ ] Batch updates for efficiency
- [ ] Track message delivery metrics

### 3.4 Message Format Standardization
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

## Step 4: Alert System Implementation
**Duration**: 35 minutes  
**Status**: ⏳ Pending

### 4.1 Alert Processing Logic
- [ ] **File**: `lambda/api-handlers/alert-processor.py`
- [ ] Monitor occupied→free transitions
- [ ] Check active alerts for affected machines
- [ ] Respect quiet hours configuration
- [ ] Implement alert cooldown periods

### 4.2 Notification Delivery
- [ ] Send WebSocket notifications to subscribers
- [ ] Format alert messages with machine details
- [ ] Include ETA and availability information
- [ ] Mark alerts as fired with timestamp

### 4.3 Alert Management
- [ ] **File**: `lambda/api-handlers/alert-manager.py`
- [ ] List active alerts for users
- [ ] Cancel/modify existing alerts
- [ ] Clean up expired alerts
- [ ] Alert subscription analytics

### 4.4 Quiet Hours Implementation
```python
def in_quiet_hours(quiet_hours_config, current_time):
    """
    Check if current time falls within quiet hours
    """
    start = quiet_hours_config.get('start', 22)  # 10 PM
    end = quiet_hours_config.get('end', 7)       # 7 AM
    
    current_hour = current_time.hour
    if start > end:  # Spans midnight
        return current_hour >= start or current_hour < end
    else:
        return start <= current_hour < end
```

---

## Step 5: Rate Limiting and Security
**Duration**: 25 minutes  
**Status**: ⏳ Pending

### 5.1 API Rate Limiting
- [ ] Configure API Gateway throttling
- [ ] Set per-user rate limits
- [ ] Implement backoff strategies
- [ ] Add rate limiting headers

### 5.2 Security Headers and CORS
- [ ] Configure CORS policies
- [ ] Add security headers (HSTS, CSP)
- [ ] Implement API key authentication (optional)
- [ ] Set up request signing validation

### 5.3 Input Validation and Sanitization
- [ ] Validate all API inputs
- [ ] Sanitize user-provided data
- [ ] Prevent injection attacks
- [ ] Add request size limits

---

## Step 6: Error Handling and Monitoring
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 6.1 Comprehensive Error Handling
- [ ] Standardize error response format
- [ ] Implement retry logic for transient failures
- [ ] Add circuit breaker patterns
- [ ] Create error categorization system

### 6.2 Logging and Observability
- [ ] Structured logging for all API calls
- [ ] Track API response times and success rates
- [ ] Monitor WebSocket connection metrics
- [ ] Set up CloudWatch alarms

### 6.3 Health Check Endpoints
- [ ] Create /health endpoint for load balancers
- [ ] Implement dependency health checks
- [ ] Add service status reporting
- [ ] Monitor downstream service availability

---

## Step 7: Performance Optimization
**Duration**: 25 minutes  
**Status**: ⏳ Pending

### 7.1 Caching Strategy
- [ ] Implement API response caching
- [ ] Cache frequently accessed data
- [ ] Set appropriate cache TTL values
- [ ] Add cache invalidation logic

### 7.2 Database Query Optimization
- [ ] Optimize DynamoDB queries with proper indexes
- [ ] Implement connection pooling
- [ ] Use batch operations where possible
- [ ] Monitor query performance metrics

### 7.3 Lambda Performance Tuning
- [ ] Right-size Lambda memory allocation
- [ ] Minimize cold start impact
- [ ] Optimize package sizes
- [ ] Configure provisioned concurrency if needed

---

## Step 8: Integration Testing and Validation
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 8.1 API Integration Testing
- [ ] Test all REST endpoints with various inputs
- [ ] Validate error handling scenarios
- [ ] Test rate limiting and throttling
- [ ] Verify CORS functionality

### 8.2 WebSocket Testing
- [ ] Test connection lifecycle management
- [ ] Validate real-time message delivery
- [ ] Test connection cleanup on disconnect
- [ ] Verify message ordering and delivery

### 8.3 Alert System Testing
- [ ] Test alert creation and management
- [ ] Validate quiet hours functionality
- [ ] Test notification delivery
- [ ] Verify alert cleanup and expiration

### 8.4 Evidence Capture and Commit
```bash
git add .
git commit -m "feat: Phase 4 APIs, streams, and alerts

- REST API endpoints: /branches, /machines, /history, /alerts
- WebSocket real-time streaming with connection management
- Alert system with quiet hours and notification delivery
- Rate limiting, security headers, and CORS configuration
- Error handling, monitoring, and performance optimization
- Comprehensive integration testing and validation

🤖 Generated with Amazon Q Developer
Co-Authored-By: Amazon Q Developer <noreply@aws.amazon.com>"
```

---

## Success Criteria
- [ ] All REST endpoints return correct data formats
- [ ] WebSocket connections establish and receive real-time updates
- [ ] Alert system creates and fires notifications correctly
- [ ] Rate limiting and security measures function properly
- [ ] API documentation complete and accurate
- [ ] Performance targets met under load testing
- [ ] Integration tests pass for all functionality

## Estimated Total Time: 3.5 hours

## Next Phase
Phase 5: Frontend web app development