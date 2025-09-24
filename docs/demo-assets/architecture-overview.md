# GymPulse System Architecture

## High-Level Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IoT Devices   │    │   Frontend Web  │    │  Bedrock Agent  │
│  (Simulated)    │    │      App        │    │   (Chat/AI)     │
│                 │    │                 │    │                 │
│ • 15 machines   │    │ • React/Vite    │    │ • Tool-use      │
│ • 2 branches    │    │ • Real-time UI  │    │ • Converse API  │
│ • MQTT/TLS      │    │ • WebSocket     │    │ • Cross-region  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │ MQTT Publish          │ HTTP/WS               │ API Calls
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Cloud Services                       │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  IoT Core   │  │API Gateway  │  │  Location   │            │
│  │             │  │             │  │  Service    │            │
│  │ • Topics    │  │ • REST APIs │  │ • Route     │            │
│  │ • Rules     │  │ • WebSocket │  │   Calculator│            │
│  │ • Security  │  │ • CORS      │  │ • ETAs      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│         │                 │                 │                 │
│         ▼                 ▼                 ▼                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    Lambda Functions                     │  │
│  │                                                         │  │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │  │
│  │ │ IoT Ingest  │ │ API Handlers│ │Bedrock Tools│        │  │
│  │ │             │ │             │ │             │        │  │
│  │ │ • State     │ │ • Branches  │ │ • Availability      │  │
│  │ │   Transitions│ │ • Machines  │ │ • Route Matrix     │  │
│  │ │ • Alerts    │ │ • History   │ │ • Chat Handler     │  │
│  │ │ • Real-time │ │ • WebSocket │ │ • Tool Orchestration │ │
│  │ └─────────────┘ └─────────────┘ └─────────────┘        │  │
│  └─────────────────────────────────────────────────────────┘  │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    DynamoDB Tables                      │  │
│  │                                                         │  │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │  │
│  │ │Current State│ │   Events    │ │ Aggregates  │        │  │
│  │ │             │ │             │ │             │        │  │
│  │ │ • Real-time │ │ • Time      │ │ • 15-min    │        │  │
│  │ │   Status    │ │   Series    │ │   Bins      │        │  │
│  │ │ • Machine   │ │ • History   │ │ • Heatmaps  │        │  │
│  │ │   Metadata  │ │ • TTL 30d   │ │ • Forecasts │        │  │
│  │ └─────────────┘ └─────────────┘ └─────────────┘        │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Architecture Features

### Real-Time Data Flow
1. **IoT Devices** → MQTT publish → **IoT Core** → **Lambda** → **DynamoDB**
2. **DynamoDB** → **Lambda** → **WebSocket** → **Frontend** (≤15s P95)

### AI-Powered Recommendations  
1. **User Query** → **Bedrock Agent** → **Tool Functions**
2. **Tools** → **DynamoDB** + **Location Service** → **Ranked Results**
3. **Response** → **Chat UI** (≤3s P95)

### Data Architecture
- **Current State**: Real-time machine status
- **Events**: Historical transitions (30d TTL)
- **Aggregates**: 15-min bins for heatmaps (90d TTL)
- **Alerts**: User subscriptions with quiet hours

### Security & Privacy
- **IoT Security**: Mutual TLS, device certificates, least-privilege policies
- **Privacy**: No PII collection, session-only geolocation, PDPO compliance
- **API Security**: CORS, rate limiting, input validation, security headers

## Performance Characteristics

### Latency Targets (All P95)
- **IoT to UI**: ≤15 seconds end-to-end
- **Chatbot Response**: ≤3 seconds including tool calls
- **API Response**: ≤200ms for REST endpoints
- **WebSocket**: ≤1 second for real-time updates

### Scalability
- **Devices**: Tested with 50 concurrent, scales horizontally
- **Users**: API Gateway auto-scaling, Lambda concurrent execution
- **Data**: DynamoDB on-demand scaling, time-based partitioning

### Reliability
- **Availability**: Multi-AZ deployment across ap-east-1 and us-east-1
- **Fault Tolerance**: Circuit breakers, retry logic, graceful degradation
- **Monitoring**: CloudWatch dashboards, structured logging, alerting