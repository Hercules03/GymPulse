## Phase 0: Repo and assistants
- Initialize a mono-repo (e.g., /infra for CDK, /backend for Lambdas, /frontend for web, /agent for chat tools) and decide to use Amazon Q Developer or Kiro to generate scaffolds, tests, and docs with recorded diffs for submission [3][4].  
- Prompt the assistant to create a high-level architecture README and CDK starter stack including placeholders for IoT Core, DynamoDB, API Gateway, Bedrock agent, and Location Service so it’s traceable that GenAI produced core artifacts [3][5].  

## Phase 1: Infrastructure as code
- Provision IoT Core via CDK: device policy, certificates pattern, and MQTT topics like org/{gymId}/machines/{machineId}/status with retained last state and optional device shadow for health [6][7].  
- Create storage and compute: a time-series table (e.g., DynamoDB or a PostgreSQL/Timescale option), and Lambdas for ingest/transform, aggregates, alerts, and chat tools handlers to enable low-latency updates and analytics [8].  
- Enable Amazon Location: create a Route Calculator resource and IAM permissions to compute ETA between user location and candidate branches using Route Matrix APIs [9][10].  
- Configure Bedrock agent runtime (Converse API) with tool-use enabled so the LLM can request function calls to availability and route tools deterministically [2][11].  
- Use Q Developer’s Console-to-Code to capture any console setup and emit CDK code for parity, committing PRs as hackathon evidence of GenAI-created infra [3].  

## Phase 2: Synthetic data and device simulation
- Choose AWS IoT Device Simulator to define a “gym-machine” template with occupied/free events and dwell timings, or implement a small simulator using AWS IoT Device SDK to publish to your MQTT topics during the demo [12][1].  
- Model realistic occupancy: 30–90s “occupied” sets, 60–180s “rest,” peaks by day/time, and occasional brief noise to mimic PIR-like detection characteristics [13][14].  
- Seed two branches and three categories (e.g., legs/chest/back) in the simulator so UI and chat can demonstrate cross-branch selection and category filtering convincingly [12][1].  

## Phase 3: Ingest, state, and aggregation
- Add an IoT Rule targeting a transform Lambda that converts raw messages into state transitions (occupied→free, free→occupied), updates current_state, and writes events to the time-series store for history and heatmaps [8].  
- Use retained MQTT messages for last-known state and a simple device shadow heartbeat to mark stale devices offline gracefully if no updates arrive within a threshold [6].  
- Precompute 15-minute aggregates per machine and by category/branch to drive heatmaps and light forecasting without high query cost at runtime [8].  

## Phase 4: APIs, streams, and alerts
- Implement REST endpoints: GET /branches (with coordinates and free counts by category), GET /branches/{id}/categories/{category}/machines, GET /machines/{id}/history?range=24h, and POST /alerts for notify-when-free [8].  
- Provide WebSocket/SSE endpoint to push current_state changes to the browser so tiles update in near-real-time during the demo without manual refresh [8].  
- Implement alert triggers on occupied→free transitions with quiet-hours support so participants can subscribe to target machine notifications in the demo [8].  

## Phase 5: Frontend web app
- Build a React/Vite UI: branch and category selectors, machine tiles with live status and last-change time, a 24-hour mini-heatmap per machine/category, and an alert button per machine [15].  
- Use browser Geolocation on consent to get user lat/lon and store it transiently for agent queries; fall back to typed location if denied to keep flows working [16].  
- Render a small “likely free in 30m” chip using a weekly-seasonality baseline from 15-minute bins so the MVP demonstrates predictive UX without heavy training [17][8].  

## Phase 6: Agentic chatbot with tool-use
- Define tool schemas for getAvailabilityByCategory(lat,lon,radius,category) and getRouteMatrix(userCoord, branchCoords), returning free counts and ETA matrices, respectively, to support deterministic function calls [2][10].  
- Implement getAvailabilityByCategory by querying your aggregates and current_state APIs, returning branch coordinates and per-category free counts in a strict JSON shape for the agent [8].  
- Implement getRouteMatrix with Amazon Location CalculateRouteMatrix and rank candidates by ETA then free counts so responses are both quick and practical for leg-day queries [9][18].  
- Wire the Bedrock Converse API with tool-use: the model plans, requests function calls, you execute tools, return results, and the model composes the final recommendation with a short reason and two alternates [2][11].  
- Integrate a simple chat UI: send user intent plus coordinates to the agent, display structured results (branch name, ETA, free count), and allow one-click navigation to the branch view in the app [2].  

## Phase 7: Forecasting chip (baseline)
- Compute for each machine/category the historical occupancy probability by weekday and 15-minute bin and expose a “likely free in 30m” boolean using a tuned threshold so it’s clear and actionable [17].  
- Expose this likelihood to both the tiles and the chatbot fallback path (“nothing free now → nearest likely free in 30m”) to keep the agent helpful under load [17].  

## Phase 8: Security, privacy, and compliance guardrails
- Enforce mutual TLS, least-privilege IoT policies, and scoped MQTT topics; do not collect PII in telemetry; store only anonymized occupancy events aligned with Hong Kong PDPO norms [6][19].  
- Follow GovCERT IoT practice guidance: device identity, signed updates, IAM boundaries for Bedrock/Location tools, and periodic security checks even in prototype form [20][2].  
- Show a brief privacy notice in the app for geolocation consent and explain that location is used only to compute ETA for this session’s recommendation [16].  

## Phase 9: Testing, QA, and observability
- Use the simulator to run a sustained test of 10–50 devices; verify end-to-end latency from publish to UI tile update and ensure P95 ≤ ~15s in the live demo environment [12][8].  
- Add unit tests for Lambdas and integration tests for tool-use chains; let Q Developer or Kiro generate initial tests and update stubs as requirements change for visible GenAI contribution [3][4].  
- Add basic metrics and logs: ingest message counts, tool-call success rate, agent response time, and alert trigger counts to support a confident demo walkthrough [8].  

## Phase 10: Demo script and submission assets
- Demo flow: show live tiles changing with the simulator, set a “notify when free,” then ask the chatbot “I want to do legs nearby” to receive a top pick with ETA and two alternates, then click through to the branch view [1][2].  
- Record evidence: capture Q Developer Console-to-Code or Kiro action logs and PRs that generated CDK stacks, Lambda handlers, test suites, and docs to satisfy judging requirements [3][5].  
- Include a short README section “How GenAI built this” with screenshots of the assistant sessions and commit links for transparent provenance in the repo [3][5].  

## Timeline (suggested 1–2 days)
- Morning Day 1: Infra CDK with Q/Kiro, IoT topics, storage, API Gateway, Bedrock agent, Location calculator, deploy and smoke test endpoints [3][9].  
- Afternoon Day 1: Simulator publishing events, ingest→state→aggregate Lambdas, and REST/WebSocket endpoints powering a basic tile grid [12][8].  
- Morning Day 2: Agent tool-use wiring to availability and route matrix, browser geolocation hookup, and ranked chat responses in UI [2][10].  
- Afternoon Day 2: Forecast chip, alerts, polishing UI/observability, and recording GenAI usage evidence clips and the final demo video [17][3].  

## Acceptance checklist
- Tiles refresh near-real-time from simulated events, with 24h heatmap and a small “likely free in 30m” chip per machine/category for clarity and actionability [8][17].  
- Chatbot answers “leg day nearby?” by calling availability and route matrix tools and returns a ranked list with ETA and free counts in under ~3 seconds P95 for the demo [2][9].  
- Repo contains CDK/IaC, Lambdas, tests, and docs generated materially by Amazon Q Developer or Kiro, with PRs/logs/screenshots proving GenAI’s contribution per hackathon rules [3][5].  

## Prompts to accelerate with assistants
- “Generate a CDK stack for AWS IoT Core topics/policies, DynamoDB time-series table, API Gateway + Lambdas, Bedrock agent (Converse) integration, and Amazon Location Route Calculator with least-privilege IAM” to get turnkey infra [3][9].  
- “Create Python Lambdas for: IoT transform (state transitions + aggregates), GET /branches, GET /machines/{id}/history, POST /alerts, and Bedrock tool handlers (availability, route matrix) with tests and OpenAPI spec” to speed backend [3][2].  
- “Scaffold a React/Vite app with WebSocket live tiles, 24h heatmap component, forecast chip, chat panel wired to Bedrock Converse tool-use, and geolocation consent flow” to bootstrap the frontend fast [3][16].  

This plan gets a complete, demo-ready MVP using **synthetic** telemetry, tool-using Bedrock chat for routing-based recommendations, and visible code/IaC/test generation by Q Developer or Kiro to meet hackathon criteria confidently. [1][2]