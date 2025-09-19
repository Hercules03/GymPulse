# GymPulse

🏋️‍♂️ **Real-time gym equipment availability tracker with AI-powered recommendations**

A hackathon project that delivers machine-level availability insights, cross-branch discovery, and intelligent routing recommendations powered by AWS IoT, ML forecasting, and Google Gemini AI.

![GymPulse Architecture](docs/demo-assets/architecture-overview.md)

## 📸 Screenshots

### 🏢 Branch Overview Dashboard
![Branch Dashboard](docs/screenshots/branch-dashboard.png)
*Real-time availability overview across Hong Kong gym branches with live status updates and category filtering*

### 🏋️‍♂️ Machine Detail View
![Machine Detail](docs/screenshots/machine-detail.png)
*Individual machine status with 24-hour heatmap, ML forecast chip, and alert subscription options*

### 🤖 AI Chat Assistant
![AI Chat Interface](docs/screenshots/ai-chat-conversation.png)
*Gemini-powered conversational assistant providing location-aware gym recommendations with ETA calculations*

### 📊 ML Forecasting & Analytics
![ML Forecasting](docs/screenshots/ml-forecasting-dashboard.png)
*Advanced ML analytics showing peak hours detection, anomaly flagging, and confidence-scored predictions*

### 📱 Real-Time Updates
![Real-Time Updates](docs/screenshots/realtime-websocket-demo.png)
*WebSocket-powered live tile updates demonstrating <15s latency from IoT device to browser*

### 🔔 Alert Management
![Alert Management](docs/screenshots/alert-subscription-ui.png)
*Smart alert subscription interface with quiet hours configuration and real-time notification preferences*

### 🗺️ Location & ETA Integration
![Location Integration](docs/screenshots/location-eta-integration.png)
*Browser geolocation integration with Google Maps API showing accurate walking/transit times for Hong Kong*

### 📈 CloudWatch Monitoring
![AWS Monitoring](docs/screenshots/aws-cloudwatch-dashboard.png)
*AWS CloudWatch dashboard showing real-time system metrics, Lambda performance, and DynamoDB throughput*

### 🔧 IoT Device Simulation
![IoT Simulation](docs/screenshots/iot-simulator-console.png)
*Python-based device simulator console showing realistic usage patterns across multiple gym branches*

### 📊 Performance Analytics
![Performance Dashboard](docs/screenshots/performance-analytics.png)
*Comprehensive performance metrics showing P95 latency targets, success rates, and system health indicators*

## 🚀 Live Demo

- **Frontend**: React + Vite with real-time WebSocket updates
- **Backend**: AWS CDK infrastructure with Lambda functions and DynamoDB
- **AI Chat**: Google Gemini-powered conversational assistant with tool-use capabilities
- **Data**: IoT device simulation with realistic usage patterns across Hong Kong gym branches

## ✨ Key Features

### 📱 Real-Time Availability
- **Live status updates**: Machine-level occupied/free status with <15s latency
- **Branch overview**: Cross-location availability with distance and ETA
- **Category filtering**: Legs, chest, back equipment organized by workout type
- **WebSocket integration**: Real-time tile updates without manual refresh

### 🤖 AI-Powered Chat Assistant
- **Natural language queries**: "Looking for leg day nearby?" → intelligent recommendations
- **Tool-use architecture**: Gemini AI calls availability and route-matrix functions
- **Location-aware**: Browser geolocation with Google Maps API for accurate ETAs
- **Multi-option responses**: Top recommendation plus alternatives with reasoning

### 📊 ML Forecasting & Analytics
- **24-hour heatmaps**: Historical usage patterns with ML-enhanced predictions
- **"Likely free in 30m" chips**: AI confidence scoring for future availability
- **Peak hours detection**: Automated identification of busy periods per branch
- **Anomaly detection**: Unusual patterns flagged with severity scoring

### 🔔 Smart Alerts
- **Notify when free**: Subscribe to occupied→free transitions
- **Quiet hours support**: Configurable notification windows
- **Multi-channel delivery**: Real-time WebSocket + future SMS/email integration

## 🏗️ Architecture

### Infrastructure (AWS CDK)
```
AWS IoT Core → Lambda (Ingest) → DynamoDB → Lambda (API) → React Frontend
     ↓              ↓              ↓            ↓
Device Shadow → WebSocket ← Aggregates → Gemini Chat
     ↓              ↓              ↓            ↓
Certificates → Monitoring ← Forecasting → Location Service
```

### Core Components

#### Backend Services
- **IoT Ingest**: Real-time device message processing with state transitions
- **API Handler**: REST endpoints with ML forecasting integration
- **WebSocket Handler**: Real-time browser notifications
- **Chat Engine**: Gemini AI with tool-use for availability queries
- **ML Forecast Engine**: 4-model ensemble with confidence scoring

#### Frontend Application
- **Branch Dashboard**: Live availability tiles with heatmaps
- **Machine Detail**: Individual machine history and forecast chips
- **Chat Interface**: Conversational AI with geolocation integration
- **Alert Management**: Subscription and notification preferences

#### Device Simulation
- **Realistic Patterns**: Peak hours, session durations, noise modeling
- **Multiple Branches**: Hong Kong locations with distance/ETA calculations
- **Scalable Testing**: 10-50 concurrent devices for load validation

## 🛠️ Tech Stack

### Frontend
- **React 18** + **Vite** - Modern development with fast HMR
- **TypeScript** - Type safety and developer experience
- **Tailwind CSS** - Utility-first styling with responsive design
- **Framer Motion** - Smooth animations and transitions
- **React Router** - Client-side routing and navigation

### Backend & Infrastructure
- **AWS CDK (Python)** - Infrastructure as Code with least-privilege IAM
- **AWS Lambda** - Serverless compute with reserved concurrency
- **DynamoDB** - NoSQL storage with time-series data optimization
- **IoT Core** - MQTT messaging with device policies and certificates
- **API Gateway** - REST + WebSocket APIs with rate limiting
- **CloudWatch** - Monitoring, alerting, and observability

### AI & ML
- **Google Gemini 2.0 Flash** - Conversational AI with function calling
- **NumPy** - Time series analysis and statistical modeling
- **Custom ML Engine** - 4-model ensemble (seasonal, pattern, trend, context)
- **Anomaly Detection** - Statistical outlier identification with severity scoring

### External Integrations
- **Google Maps API** - Accurate walking/transit times for Hong Kong
- **Amazon Location Service** - Route calculation and distance matrix (backup)

## 📋 Prerequisites

### Development Environment
- **Node.js 18+** with npm/yarn package manager
- **Python 3.10+** with `uv` package manager
- **AWS CLI** configured with appropriate permissions
- **AWS CDK v2** for infrastructure deployment

### AWS Services Required
- IoT Core, Lambda, DynamoDB, API Gateway, CloudWatch
- IAM permissions for resource creation and management
- Optional: Amazon Location Service, Amazon Bedrock

### API Keys (Optional Enhancements)
- **Google Maps API** - For accurate Hong Kong walking times
- **Google Gemini API** - For Singapore Lambda deployment

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd GymPulse
```

### 2. Install Dependencies
```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Configure Environment
```bash
# Set AWS region for Hong Kong East (ap-east-1)
export AWS_DEFAULT_REGION=ap-east-1
export CDK_DEFAULT_REGION=ap-east-1

# Optional: Set API keys for enhanced features
export GOOGLE_MAPS_API_KEY=your_google_maps_key
export GEMINI_API_KEY=your_gemini_api_key
```

### 4. Deploy Infrastructure
```bash
# Deploy AWS infrastructure
cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/ap-east-1
cdk deploy
```

### 5. Start Device Simulation
```bash
# Run IoT device simulator
cd simulator
python src/gym_simulator.py config/machines.json
```

### 6. Launch Frontend
```bash
# Start development server
cd frontend
npm run dev
```

### 7. Access Application
- **Frontend**: http://localhost:5173
- **API Docs**: Check CDK output for API Gateway URL
- **WebSocket**: Real-time updates automatically connected

## 📊 Usage Examples

### Basic Availability Check
1. Navigate to **Branches** page
2. View real-time availability counts per category
3. Click branch to see detailed machine status
4. Enable alerts for occupied machines

### AI Chat Assistant
1. Click floating chat button
2. Grant location permission when prompted
3. Ask: *"Looking for leg equipment nearby?"*
4. Receive ETA-ranked recommendations with reasoning

### Historical Analysis
1. Select specific machine from branch view
2. View 24-hour heatmap with ML predictions
3. Check "Likely free in 30m" forecast chip
4. Review AI insights and anomaly detection

## 🏗️ Development Phases

This project follows a structured 11-phase development approach:

### ✅ Completed Phases
- **Phase 0**: Repository setup and AI assistant integration
- **Phase 1**: AWS CDK infrastructure deployment (4.5 hours)
- **Phase 2**: IoT device simulation with Python SDK (4.5 hours)

### 🔄 Current Work
- **Phase 3**: Ingest pipeline and state aggregation
- **Phase 4**: REST APIs and WebSocket streaming
- **Phase 5**: Frontend React application

### 📋 Upcoming Phases
- **Phase 6**: AI chatbot with tool-use capabilities
- **Phase 7**: ML forecasting and prediction chips
- **Phase 8**: Security, privacy, and compliance
- **Phase 9**: Testing, QA, and observability
- **Phase 10**: Demo preparation and hackathon submission

*See [ProjectProgress.md](docs/phases/ProjectProgress.md) for detailed tracking*

## 🤖 AI-Generated Development

This project leverages AI assistance for accelerated development:

### Code Generation
- **AWS CDK Stacks**: Infrastructure as Code with security best practices
- **Lambda Functions**: API handlers, WebSocket, and IoT processing
- **React Components**: UI components with TypeScript and accessibility
- **ML Algorithms**: Forecasting models and statistical analysis

### Documentation
- **API Specifications**: OpenAPI/Swagger documentation
- **Architecture Diagrams**: System design and data flow
- **Phase Planning**: Detailed development roadmaps
- **Testing Strategies**: Unit, integration, and load testing

### Evidence & Attribution
All AI-generated code includes proper attribution and commit history for hackathon transparency requirements.

## 📁 Project Structure

```
GymPulse/
├── frontend/                  # React + Vite frontend application
│   ├── src/
│   │   ├── components/       # UI components (chat, dashboard, machine)
│   │   ├── pages/           # Route pages (branches, dashboard, machines)
│   │   ├── services/        # API integration and WebSocket
│   │   └── utils/           # Utility functions and helpers
│   ├── package.json         # Frontend dependencies
│   └── vite.config.ts       # Vite configuration
├── gym_pulse/               # AWS CDK infrastructure code
│   ├── gym_pulse_stack.py   # Main CDK stack definition
│   └── security/           # Security-focused stack components
├── lambda/                  # Lambda function implementations
│   ├── api-handlers/        # REST API and ML forecasting
│   ├── bedrock-tools/       # AI chat and tool functions
│   ├── iot-ingest/         # IoT message processing
│   └── websocket-handlers/ # Real-time WebSocket communication
├── simulator/               # IoT device simulation
│   ├── src/                # Simulation logic and patterns
│   ├── config/             # Machine and branch configurations
│   └── certs/              # Device certificates (generated)
├── testing/                 # Test suites and validation
├── docs/                   # Project documentation
│   ├── phases/             # Development phase tracking
│   ├── project/            # PRD, plans, and architecture
│   └── ai-evidence/        # AI usage documentation
├── app.py                  # CDK application entry point
├── cdk.json               # CDK configuration
└── requirements.txt       # Python dependencies
```

## 🧪 Testing

### Load Testing
```bash
# Test with 10-50 concurrent devices
cd simulator
python load_test.py --machines 50 --duration 300
```

### API Testing
```bash
# Test REST endpoints
cd testing
python run_tests.py --integration
```

### Frontend Testing
```bash
# Run frontend tests
cd frontend
npm test
```

## 📈 Performance Metrics

### Target KPIs
- **Live status latency**: ≤15s P95 end-to-end
- **Chat response time**: ≤3s P95 including tool calls
- **Simulator capacity**: 10-50 devices sustained without drops
- **Failed session reduction**: ≥30% through better availability insights

### Monitoring
- **CloudWatch Dashboard**: Real-time metrics and alarms
- **Lambda Performance**: Invocation count, duration, errors
- **DynamoDB Metrics**: Read/write capacity, throttling
- **WebSocket Connections**: Active connections, message rates

## 🔒 Security & Privacy

### Privacy-by-Design
- **No PII collection**: Only anonymized occupancy events
- **Minimal data retention**: Aggregated patterns, not individual usage
- **Hong Kong PDPO compliance**: Clear privacy notice and consent flows
- **Geolocation consent**: Optional browser location with transparent usage

### IoT Security
- **Mutual TLS**: Device certificates and encryption
- **Least-privilege policies**: Scoped MQTT topics and permissions
- **Device identity**: Individual certificates per machine
- **Secure communication**: All data encrypted in transit

## 🤝 Contributing

This is a hackathon project developed with AI assistance. For transparency:

1. **AI Usage**: Major code components generated with Amazon Q Developer/Kiro
2. **Human Review**: All AI output reviewed and integrated by human developers
3. **Attribution**: Clear commit messages indicating AI vs. human contributions
4. **Documentation**: Comprehensive evidence of AI assistance for judging

## 📄 License

This project is developed for hackathon submission. See competition guidelines for usage and distribution terms.

## 🏆 Hackathon Evidence

### AI-Generated Components
- ✅ AWS CDK infrastructure (100% AI-generated with human review)
- ✅ Lambda function templates (80% AI-generated, 20% customization)
- ✅ React component scaffolding (70% AI-generated, 30% styling)
- ✅ ML forecasting algorithms (90% AI-generated with domain tuning)

### Evidence Documentation
- **Commit History**: Tagged commits showing AI vs. human contributions
- **Screenshots**: AI assistant conversations and code generation
- **PRs/Logs**: Development workflow with AI tools
- **README Section**: "How GenAI built this" with transparent attribution

---

Built with ❤️ and 🤖 AI assistance for the hackathon challenge