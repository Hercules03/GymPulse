# Infrastructure Planning - GymPulse

## AWS Resource Naming Conventions

### General Patterns
- **Stack Prefix**: `gym-pulse-`
- **Environment**: `-dev`, `-staging`, `-prod`
- **Resource Type**: Descriptive suffix (e.g., `-table`, `-lambda`, `-api`)

### DynamoDB Tables
- **Current State**: `gym-pulse-current-state`
- **Events**: `gym-pulse-events`
- **Aggregates**: `gym-pulse-aggregates` 
- **Alerts**: `gym-pulse-alerts`
- **Connections**: `gym-pulse-connections` (WebSocket)

### Lambda Functions
- **IoT Ingest**: `gym-pulse-iot-ingest`
- **API Handler**: `gym-pulse-api-handler`
- **WebSocket Connect**: `gym-pulse-ws-connect`
- **WebSocket Disconnect**: `gym-pulse-ws-disconnect`
- **WebSocket Broadcast**: `gym-pulse-ws-broadcast`
- **Availability Tool**: `gym-pulse-availability-tool`
- **Route Matrix Tool**: `gym-pulse-route-matrix-tool`
- **Aggregator**: `gym-pulse-aggregator`

### API Gateway
- **REST API**: `gym-pulse-rest-api`
- **WebSocket API**: `gym-pulse-websocket-api`

### IoT Resources
- **Device Policy**: `GymPulseDevicePolicy`
- **Topic Rule**: `GymPulseMachineStatusRule`
- **Topic Pattern**: `org/{gymId}/machines/{machineId}/status`

### Amazon Location
- **Route Calculator**: `gym-pulse-route-calculator`

### Bedrock
- **Agent Role**: `GymPulseBedrockAgentRole`
- **Agent**: `gym-pulse-chat-agent`

## Planned AWS Resources

### Core Infrastructure
```yaml
IoT Core:
  - Device Policy: Scoped MQTT publish/subscribe
  - Topic Rules: Route messages to Lambda
  - Device Certificates: Per-machine authentication

DynamoDB:
  - current_state: Real-time machine status (PK: machineId)
  - events: Time-series state transitions (PK: machineId, SK: timestamp)
  - aggregates: 15-minute occupancy bins (PK: gymId#category, SK: timestamp)
  - alerts: User alert subscriptions (PK: userId, SK: machineId)
  - connections: WebSocket connection management

Lambda Functions:
  - iot-ingest: Process MQTT messages, update state
  - api-handler: REST API endpoints
  - ws-connect/disconnect: WebSocket lifecycle
  - ws-broadcast: Real-time notifications
  - availability-tool: Bedrock tool function
  - route-matrix-tool: Bedrock tool function
  - aggregator: Scheduled data aggregation

API Gateway:
  - REST API: /branches, /machines, /alerts endpoints
  - WebSocket API: Real-time updates

Amazon Location:
  - Route Calculator: ETA computation
```

### Integration Points
```yaml
Data Flow:
  IoT Devices → IoT Core → Lambda Ingest → DynamoDB
  DynamoDB → API Gateway → Frontend
  DynamoDB → WebSocket API → Frontend
  Bedrock Agent → Tool Lambdas → DynamoDB/Location

Security:
  - Mutual TLS for IoT devices
  - IAM roles with least privilege
  - API Gateway CORS and rate limiting
  - Bedrock agent scoped permissions
```

## IAM Roles and Policies Structure

### Lambda Execution Roles
```yaml
gym-pulse-iot-ingest-role:
  - DynamoDB: Read/Write current_state, events, aggregates
  - CloudWatch: Logs
  - WebSocket API: PostToConnection

gym-pulse-api-handler-role:
  - DynamoDB: Read current_state, aggregates
  - CloudWatch: Logs

gym-pulse-tool-lambda-role:
  - DynamoDB: Read current_state, aggregates
  - Amazon Location: CalculateRouteMatrix
  - CloudWatch: Logs
```

### Bedrock Agent Role
```yaml
gym-pulse-bedrock-agent-role:
  - Lambda: InvokeFunction (tool Lambdas)
  - Bedrock: Model access
  - CloudWatch: Logs
```

### IoT Device Policy
```yaml
GymPulseDevicePolicy:
  - iot:Connect: client/gym-{gymId}-{machineId}
  - iot:Publish: topic/org/{gymId}/machines/{machineId}/status
  - iot:UpdateThingShadow: thing/{machineId}
```

## Resource Capacity Planning

### DynamoDB
- **current_state**: ~100 items, <1KB each
- **events**: ~10K items/day, 1KB each, 30-day TTL
- **aggregates**: ~1K items/day, <1KB each, 90-day TTL
- **alerts**: ~1K items max, <1KB each

### Lambda
- **Memory**: 512MB-1GB depending on function
- **Timeout**: 30s for API, 300s for aggregation
- **Concurrency**: 10-50 concurrent executions expected

### API Gateway
- **Rate Limiting**: 1000 requests/minute per API key
- **CORS**: All origins allowed for development
- **Caching**: 5-minute TTL for /branches endpoint

## Security Considerations

### Data Protection
- All data encrypted at rest (DynamoDB encryption)
- TLS 1.2+ for all communications
- No PII collected - only machine occupancy status

### Access Control
- IoT devices: Certificate-based authentication
- API Gateway: Optional API keys for rate limiting
- Bedrock: Service-to-service with IAM roles

### Monitoring
- CloudWatch metrics for all resources
- CloudTrail for API access logging
- IoT Device Defender for anomaly detection

## Cost Optimization

### Pay-Per-Request Resources
- DynamoDB: On-demand billing mode
- Lambda: Pay per invocation
- API Gateway: Pay per request

### Fixed Cost Resources
- Amazon Location: Route Calculator (~$4/1K requests)
- IoT Core: Message routing (~$1/1M messages)

### Estimated Monthly Costs (Development)
- DynamoDB: $5-10
- Lambda: $10-20
- API Gateway: $5-10
- IoT Core: $5-10
- Amazon Location: $10-20
- **Total**: ~$35-70/month for development workload