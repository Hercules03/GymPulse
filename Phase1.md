# Phase 1: Infrastructure as Code - Step-by-Step Breakdown

## Overview
Provision AWS infrastructure using CDK with IoT Core, storage, compute, Location Service, and Bedrock agent runtime. Generate code using Amazon Q Developer or Kiro with evidence capture for hackathon submission.

## Prerequisites
- AWS CLI configured with appropriate permissions
- Node.js and npm installed
- CDK CLI installed (`npm install -g aws-cdk`)
- Python 3.9+ for Lambda functions

---

## Step 1: Project Structure Setup
**Duration**: 15 minutes  
**Tools**: Local filesystem, CDK CLI

### 1.1 Initialize CDK Project
```bash
mkdir gym-pulse-infra
cd gym-pulse-infra
cdk init app --language typescript
```

### 1.2 Create Directory Structure
```
gym-pulse-infra/
├── lib/
│   ├── gym-pulse-stack.ts          # Main CDK stack
│   ├── iot-stack.ts                # IoT Core resources
│   ├── storage-stack.ts            # DynamoDB tables
│   ├── compute-stack.ts            # Lambda functions
│   ├── api-stack.ts                # API Gateway + WebSocket
│   ├── bedrock-stack.ts            # Bedrock agent setup
│   └── location-stack.ts           # Amazon Location Service
├── lambda/
│   ├── iot-ingest/                 # IoT message processor
│   ├── api-handlers/               # REST API handlers
│   ├── websocket-handlers/         # WebSocket handlers
│   └── bedrock-tools/              # Chatbot tool handlers
└── config/
    └── constants.ts                # Configuration constants
```

### 1.3 Install Dependencies
```bash
npm install @aws-cdk/aws-iot @aws-cdk/aws-dynamodb @aws-cdk/aws-lambda @aws-cdk/aws-apigateway @aws-cdk/aws-location @aws-cdk/aws-bedrock
```

---

## Step 2: IoT Core Infrastructure
**Duration**: 30 minutes  
**AI Tool**: Amazon Q Developer for CDK patterns

### 2.1 Create IoT Device Policy
- **Prompt Q Developer**: "Generate CDK code for IoT device policy with MQTT topics org/{gymId}/machines/{machineId}/status"
- Define least-privilege permissions for device publishing
- Enable retained messages for last-known state

### 2.2 Configure MQTT Topics Structure
```typescript
// Topics pattern: org/{gymId}/machines/{machineId}/status
// Retained messages: true
// QoS: 1 (at least once delivery)
```

### 2.3 Setup Device Shadow (Optional)
- Configure device shadow for health monitoring
- Heartbeat mechanism for stale device detection

### 2.4 Create IoT Rule for Lambda Trigger
- Route MQTT messages to transform Lambda
- Filter and transform JSON payload
- Error handling and dead letter queue

---

## Step 3: Storage Layer - DynamoDB
**Duration**: 25 minutes  
**AI Tool**: Q Developer for time-series table design

### 3.1 Current State Table
```typescript
// Table: gym-pulse-current-state
// Partition Key: machineId (string)
// Attributes: status, lastUpdate, gymId, category, coordinates
// TTL: none (current state persists)
```

### 3.2 Time-Series Events Table
```typescript
// Table: gym-pulse-events
// Partition Key: machineId (string)
// Sort Key: timestamp (number)
// Attributes: status, transition, gymId, category
// TTL: 30 days
```

### 3.3 Aggregates Table
```typescript
// Table: gym-pulse-aggregates
// Partition Key: gymId#category (string)
// Sort Key: timestamp15min (number)
// Attributes: occupancyRatio, freeCount, totalCount
// TTL: 90 days
```

### 3.4 Alerts Table
```typescript
// Table: gym-pulse-alerts
// Partition Key: userId (string)
// Sort Key: machineId (string)
// Attributes: active, quietHours, createdAt
// GSI: machineId-index for alert triggers
```

---

## Step 4: Compute Layer - Lambda Functions
**Duration**: 45 minutes  
**AI Tool**: Q Developer for Lambda scaffolding

### 4.1 IoT Ingest/Transform Lambda
- **Prompt**: "Create Python Lambda for IoT message processing with state transitions"
- Process occupied→free, free→occupied transitions
- Update current_state table
- Write events to time-series table
- Trigger aggregation updates
- WebSocket notification publishing

### 4.2 API Handler Lambdas
```python
# GET /branches - List branches with free counts
# GET /branches/{id}/categories/{category}/machines - Machine details
# GET /machines/{id}/history?range=24h - Historical data
# POST /alerts - Create alert subscriptions
```

### 4.3 WebSocket Handler Lambdas
```python
# $connect - Connection management
# $disconnect - Cleanup subscriptions
# broadcast - Send real-time updates
```

### 4.4 Bedrock Tool Handler Lambdas
```python
# getAvailabilityByCategory - Query current state + aggregates
# getRouteMatrix - Amazon Location integration
# Tool response formatting for Bedrock agent
```

### 4.5 Aggregation Lambda
- Scheduled every 15 minutes via EventBridge
- Compute occupancy ratios per machine/category
- Update aggregates table
- Trigger forecast calculations

---

## Step 5: API Gateway Setup
**Duration**: 30 minutes  
**AI Tool**: Q Developer for API Gateway patterns

### 5.1 REST API Endpoints
```typescript
// API Gateway REST API with Lambda integrations
// CORS enabled for web frontend
// API key optional for rate limiting
```

### 5.2 WebSocket API
```typescript
// WebSocket API for real-time updates
// Connection management with DynamoDB
// Broadcast capabilities for live tiles
```

### 5.3 API Documentation
- OpenAPI spec generation
- Postman collection export
- Integration testing endpoints

---

## Step 6: Amazon Location Service
**Duration**: 20 minutes  
**AI Tool**: Q Developer for Location Service CDK

### 6.1 Route Calculator Resource
```typescript
// Route calculator for ETA computation
// Optimization: fastest route
// Travel mode: car (default for Hong Kong)
// Region: Asia Pacific
```

### 6.2 IAM Permissions
- Lambda execution role permissions
- Route calculation API access
- Batch route matrix operations

---

## Step 7: Bedrock Agent Configuration
**Duration**: 35 minutes  
**AI Tool**: Q Developer for Bedrock setup

### 7.1 Agent Runtime Setup
```typescript
// Bedrock agent with Converse API
// Tool-use enabled configuration
// Model: Claude 3.5 Sonnet or similar
```

### 7.2 Tool Schema Definitions
```json
{
  "getAvailabilityByCategory": {
    "inputSchema": {
      "lat": "number",
      "lon": "number", 
      "radius": "number",
      "category": "string"
    },
    "outputSchema": {
      "branches": "array of branch objects with coordinates and free counts"
    }
  },
  "getRouteMatrix": {
    "inputSchema": {
      "userCoord": "object",
      "branchCoords": "array"
    },
    "outputSchema": {
      "etaMatrix": "array of ETA and distance objects"
    }
  }
}
```

### 7.3 Agent Endpoint Configuration
- API Gateway integration
- Request/response mapping
- Error handling and timeouts

---

## Step 8: Environment Configuration
**Duration**: 15 minutes

### 8.1 CDK Context Values
```json
{
  "gymBranches": [
    {"id": "hk-central", "name": "Central Branch", "lat": 22.2819, "lon": 114.1577},
    {"id": "hk-causeway", "name": "Causeway Bay Branch", "lat": 22.2783, "lon": 114.1747}
  ],
  "categories": ["legs", "chest", "back"],
  "region": "ap-southeast-1"
}
```

### 8.2 Constants File
```typescript
export const GYM_CONFIG = {
  MQTT_TOPIC_PATTERN: 'org/{gymId}/machines/{machineId}/status',
  AGGREGATION_INTERVAL: 900, // 15 minutes in seconds
  DEVICE_TIMEOUT: 300, // 5 minutes for heartbeat
  ALERT_QUIET_HOURS: { start: 22, end: 7 }
};
```

---

## Step 9: Deployment and Testing
**Duration**: 25 minutes

### 9.1 Bootstrap CDK (if first time)
```bash
cdk bootstrap
```

### 9.2 Synthesize and Deploy
```bash
cdk synth
cdk deploy --all --require-approval never
```

### 9.3 Smoke Test Endpoints
```bash
# Test API Gateway endpoints
curl -X GET https://{api-id}.execute-api.{region}.amazonaws.com/prod/branches

# Test WebSocket connection
wscat -c wss://{websocket-id}.execute-api.{region}.amazonaws.com/prod
```

### 9.4 IoT Core Testing
```bash
# Publish test message to MQTT topic
aws iot-data publish --topic "org/hk-central/machines/leg-press-01/status" --payload '{"status":"occupied","timestamp":1234567890}'
```

---

## Step 10: Evidence Capture for Hackathon
**Duration**: 15 minutes

### 10.1 Q Developer/Kiro Usage Documentation
- Screenshot code generation sessions
- Save chat transcripts with AI assistant
- Commit messages indicating AI-generated code
- PR descriptions with AI contribution details

### 10.2 Console-to-Code Capture
- Record any manual console configurations
- Generate equivalent CDK code using Q Developer
- Document the conversion process

### 10.3 Git Commit Evidence
```bash
git add .
git commit -m "feat: Phase 1 infrastructure setup

- IoT Core topics and device policies
- DynamoDB tables for current state, events, aggregates
- Lambda functions for ingest, API, WebSocket, Bedrock tools  
- API Gateway REST and WebSocket APIs
- Amazon Location Route Calculator
- Bedrock agent with tool-use configuration

🤖 Generated with Amazon Q Developer
Co-Authored-By: Amazon Q Developer <noreply@aws.amazon.com>"
```

---

## Success Criteria
- [ ] All CDK stacks deploy successfully
- [ ] IoT Core accepts MQTT messages
- [ ] API endpoints return valid responses
- [ ] WebSocket connections establish
- [ ] Bedrock agent responds to test queries
- [ ] Location Service calculates ETAs
- [ ] Evidence documented for hackathon submission

## Estimated Total Time: 4.5 hours

## Next Phase
Phase 2: Synthetic data and device simulation setup