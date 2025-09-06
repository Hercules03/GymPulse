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

## 🎯 Current Status (40% Complete)

**Latest Update**: January 5, 2025  
**Phases Complete**: 3 of 11 (Phases 0, 1, 2)  
**Demo Status**: Frontend functional with mock data, AWS infrastructure deployed

### ✅ Completed Achievements
- **Phase 0**: Repository setup and AI assistant configuration
- **Phase 1**: Complete AWS infrastructure deployed (CDK, IoT Core, DynamoDB, Lambda, API Gateway, Bedrock, Location Service) 
- **Phase 2**: 15-machine IoT simulation across 2 Hong Kong branches with realistic usage patterns
- **Phase 5 (Partial)**: React frontend with branch listing, WebSocket integration, and error handling

### 🚧 Next Priority: Phase 3 - Data Pipeline (Ready to Begin)
- IoT message processing and state transitions
- Real-time WebSocket broadcasting
- Time-series aggregation for heatmaps

📊 **[View Detailed Progress →](docs/DEVELOPMENT_PROGRESS.md)**

## Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Node.js 18+ and npm (v22.18.0/10.9.3 recommended)
- Python 3.9+ with uv package manager
- AWS CDK CLI: `npm install -g aws-cdk`

### Current Development Setup (Phases 0-2 Complete)

1. **Clone and setup**:
   ```bash
   git clone https://github.com/your-org/GymPulse.git
   cd GymPulse
   npm install
   ```

2. **Deploy infrastructure** (Phase 1 ✅ Complete):
   ```bash
   cd infra
   uv sync
   source .venv/bin/activate
   cdk bootstrap  # First time only
   cdk deploy --all
   ```

3. **Start IoT simulator** (Phase 2 ✅ Complete):
   ```bash
   cd simulator
   uv sync
   source .venv/bin/activate
   python src/main.py
   ```

4. **Run frontend** (Phase 5 🔄 Partial):
   ```bash
   cd frontend
   pnpm install
   pnpm run dev
   # Opens http://localhost:3000
   ```

### Current Demo Capabilities
- ✅ **Branch Listing**: View 2 gym branches with mock availability data
- ✅ **IoT Simulation**: 15 machines publishing realistic occupancy data  
- ✅ **AWS Infrastructure**: Complete serverless backend deployed
- ⏳ **Real-time Updates**: WebSocket infrastructure ready (Phase 3)
- ⏳ **AI Chatbot**: Bedrock tools ready for implementation (Phase 6)

## 🤖 How AI Built This (Hackathon Evidence)

This project demonstrates extensive AI-assisted development using **Amazon Q Developer** for infrastructure and backend generation, with significant code generation across all layers.

### AI Contribution Metrics
- **Total Lines of Code**: ~8,500 lines (Phases 0-2)
- **AI-Generated Code**: ~70% (5,950 lines)
- **Infrastructure (CDK)**: ~95% AI-generated
- **Lambda Functions**: ~80% AI-generated with human refinement
- **React Components**: ~60% AI-generated with custom business logic
- **Documentation**: ~50% AI-generated with domain-specific content

### Key AI-Generated Components

#### 🏗️ Infrastructure as Code (Phase 1)
- **CDK Stack Architecture**: Complete Python CDK infrastructure
- **AWS Service Configuration**: IoT Core, DynamoDB, Lambda, API Gateway setup
- **IAM Roles and Policies**: Least-privilege security configurations  
- **Resource Naming and Tagging**: Consistent AWS resource organization

#### 🔌 IoT Simulation System (Phase 2)
- **Device SDK Integration**: Python-based MQTT publishing with certificates
- **Realistic Usage Patterns**: Peak hours, session durations, and occupancy modeling
- **State Machine Logic**: Occupied/free transitions with noise injection
- **CLI Interface**: Command-line controls and configuration management

#### ⚛️ React Frontend (Phase 5 Partial)
- **Component Architecture**: TypeScript React components with hooks
- **Service Layer**: API client and WebSocket integration
- **UI/UX Components**: Branch listing, search, real-time status display
- **Error Handling**: Graceful fallbacks and mock data integration

### AI Development Workflow
1. **Requirements Analysis**: PRD and phase-specific specifications
2. **Architecture Generation**: System design and AWS service selection
3. **Code Scaffolding**: Component structure and boilerplate generation
4. **Implementation**: Business logic and integration code
5. **Refinement**: Human review, optimization, and domain expertise
6. **Testing**: AI-generated test suites and validation logic

### Evidence Documentation
- **Git History**: Commits tagged with AI attribution and co-authorship
- **Code Comments**: AI generation markers and human modification notes  
- **Development Logs**: Amazon Q Developer session transcripts and screenshots
- **Architecture Decisions**: AI-suggested patterns and human architectural choices

🔗 **[View Complete AI Evidence →](docs/ai-evidence/)**

## CDK Commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile  
* `npm run test`    perform the jest unit tests
* `npx cdk deploy`  deploy this stack to your default AWS account/region
* `npx cdk diff`    compare deployed stack with current state
* `npx cdk synth`   emits the synthesized CloudFormation template

## 📖 Documentation

- **[Development Progress](docs/DEVELOPMENT_PROGRESS.md)**: Detailed phase-by-phase progress
- **[Phase Documentation](Phase0.md)**: Step-by-step implementation guides (Phase0.md - Phase10.md)
- **[Project Requirements](PRD.md)**: Complete product requirements document
- **[Architecture Planning](docs/infrastructure-planning.md)**: Technical architecture decisions
- **[Project Tracking](ProjectProgress.md)**: Overall project status and timeline
