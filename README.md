# GymPulse - Real-Time Gym Equipment Availability System

**Live per-machine availability tracking with AI-powered route recommendations for Hong Kong's 24/7 gym network**

## Project Overview

GymPulse solves the problem of arriving at the gym only to find your planned equipment occupied. Our system provides:

- **Real-time machine availability** across multiple branches
- **AI-powered chatbot** that answers "leg day nearby?" with ETA-optimized recommendations
- **Smart alerts** for "notify when free" subscriptions
- **24-hour heatmaps** and forecasting for optimal workout timing

## High-Level Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   IoT Devices   │───▶│   AWS IoT Core   │───▶│   Lambda Ingest │
│  (Simulators)   │    │  MQTT Topics     │    │  State Manager  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Frontend React │◀───│  API Gateway     │◀───│   DynamoDB      │
│   WebSocket     │    │  REST + WS APIs  │    │ State/Events/   │
└─────────────────┘    └──────────────────┘    │   Aggregates    │
                                                └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐             │
         └──────────────▶│  Bedrock Agent  │◀────────────┘
                        │   Tool-Use API   │
                        └──────────────────┘
                                 │
                        ┌──────────────────┐
                        │ Amazon Location  │
                        │ Route Calculator │
                        └──────────────────┘
```

### Data Flow

1. **IoT Telemetry**: Simulated gym equipment publishes occupied/free status via MQTT
2. **State Processing**: Lambda functions detect transitions, update current state, record events
3. **Real-time Updates**: WebSocket connections push live status to frontend tiles
4. **Analytics**: 15-minute aggregations power heatmaps and forecasting
5. **AI Recommendations**: Chatbot uses availability + routing tools for optimized suggestions

### Technology Stack

- **Infrastructure**: AWS CDK (TypeScript)
- **IoT Ingestion**: AWS IoT Core, Lambda, DynamoDB
- **APIs**: API Gateway (REST + WebSocket)
- **AI/Chat**: Amazon Bedrock with Converse API tool-use
- **Routing**: Amazon Location Service Route Calculator
- **Frontend**: React + Vite + TypeScript
- **Simulation**: AWS IoT Device SDK

### AWS Services Architecture

- **AWS IoT Core**: Device connectivity and MQTT message routing
- **AWS Lambda**: Message processing, API handlers, Bedrock tool functions
- **Amazon DynamoDB**: Current state, time-series events, aggregates, alerts
- **Amazon API Gateway**: REST endpoints and WebSocket real-time streaming
- **Amazon Bedrock**: AI agent with tool-use for availability queries and routing
- **Amazon Location**: ETA calculations via CalculateRouteMatrix API
- **AWS CloudWatch**: Monitoring, logging, and performance metrics

## Repository Structure

```
├── infra/              # CDK infrastructure code
│   ├── lib/           # CDK stack definitions
│   └── lambda/        # Lambda function source
├── backend/           # Lambda functions
│   └── src/lambdas/   # Organized by function type
├── frontend/          # React/Vite web application
├── agent/             # Bedrock agent and tool schemas
├── simulator/         # IoT device simulation
├── docs/              # Documentation and evidence
└── test/              # Test suites and validation
```

## Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Node.js 18+ and npm
- Python 3.9+ for Lambda functions
- AWS CDK CLI: `npm install -g aws-cdk`

### Development Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Deploy infrastructure**:
   ```bash
   cdk bootstrap  # First time only
   cdk deploy --all
   ```

3. **Start simulator**:
   ```bash
   cd simulator
   node iot_simulator.js
   ```

4. **Run frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

## CDK Commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `npx cdk deploy`  deploy this stack to your default AWS account/region
* `npx cdk diff`    compare deployed stack with current state
* `npx cdk synth`   emits the synthesized CloudFormation template
