## Summary
- Build a web app that shows live per-machine availability by category across branches, plus a GenAI chatbot that answers “leg day nearby?” by fetching availability and routing to the closest branch with free machines and shortest ETA [2][3].  
- Use synthetic data via an AWS IoT simulator or MQTT publisher to power the full backend and UI during the hackathon, and use Amazon Q Developer or Kiro to generate infrastructure, code, tests, and docs for submission evidence [4][5].  

## Problem
- 24/7, multi-branch gyms in Hong Kong make it convenient to train anywhere, but members still arrive to find priority equipment occupied, wasting time and disrupting training plans [1][6].  
- Brand apps often show “how busy” at club level, but lack machine-level granularity and proactive guidance on where to go now for a specific body part [2][7].  

## Goals and KPIs
- Reduce “failed sessions” where a planned machine is unavailable on arrival, targeting ≥30% reduction in pilot metrics and ≥50% alert adoption by active users [2][7].  
- Technical KPIs: live status latency ≤ 15s P95 end-to-end; agent response (plan+tools) ≤ 3s P95; simulator sustaining 10–50 devices for demo without drops [8][3].  

## Users and use cases
- Members: check live availability by category and branch; tap “notify when free”; ask the chatbot “Leg day nearby?” to get the fastest branch with free leg machines and ETA [2][3].  
- Coaches: plan sessions around peak windows and machine alternatives; view heatmaps and short-horizon availability signals [2][9].  
- Operators: utilization analytics for layout, maintenance, and staffing, with privacy-preserving aggregates rather than PII [10][11].  

## Scope
- MVP: live per-machine status, branch and category views, favorites, alert-on-free, 24‑hour heatmap, baseline forecasting chip (“likely free in 30m”), and GenAI chatbot with tool-use for availability+routing [2][3].  
- Post-MVP: weekly forecast improvements, anomaly/downtime detection, operator dashboard, and optional booking for constrained stations with partner gyms [9][2].  

## Differentiation and landscape
- Existing brand apps expose occupancy at club level, validating demand for real-time signals but not per-machine granularity, which this product delivers [2][7].  
- Hong Kong’s 24/7, multi-branch context amplifies value of cross-branch discovery and ETA-based recommendations driven by machine availability [1][6].  

## Core features
- Live availability: per-machine occupied/free, aggregated by category and branch, with auto-refresh and low latency [8][2].  
- Discovery: branch list with distance/ETA and free counts per category; machine cards with last change and “notify when free” [2][12].  
- History: 24‑hour heatmaps per machine and category powered by 15‑minute aggregates from event streams [13][2].  
- Forecast: baseline weekly seasonality per 15‑minute bin; show a binary “likely free in 30m” chip with thresholds for demo [9][14].  
- Chatbot: agent that interprets “leg day nearby,” calls tools to fetch availability and route-matrix ETAs, and replies with the closest viable branch plus two alternates [3][12].  

## GenAI requirements
- Amazon Q Developer: generate CDK/IaC for IoT Core, APIs, Location Service, and Lambdas; create tests and docs; use Console‑to‑Code to convert console steps into code and submit PRs as evidence [5][15].  
- Kiro: author a repo-level spec; have Kiro generate multi-file code, tests, and docs for agent tools, back-end, and UI; include agent logs/diffs per hackathon rules [16][17].  

## Chatbot design (agentic)
- Intent parsing: detect category/body part and constraint “nearby,” then plan: get availability → compute ETAs → rank by ETA then free count → respond with justification and options [18][3].  
- Tool-use: implement tools getAvailabilityByCategory and getRouteMatrix with strict JSON schemas and bind them via Bedrock Converse API tool-use for deterministic calls [3][19].  
- Location: in browser, request Geolocation (on consent) and send lat/lon with the chat turn; if declined, accept text location and geocode before routing [20][12].  

## Tool schemas and logic
- Availability tool: inputs lat/lon, radius, and category; returns branches with free counts, coordinates, and optional short-horizon likelihood [13][9].  
- Route-matrix tool: inputs user coordinate and candidate branch coordinates; returns ETAs and distances using Amazon Location CalculateRouteMatrix [12][21].  
- Ranking: sort by ETA ascending, tie-breaker on free count and forecast likelihood, then format a concise answer with map-friendly metadata [12][3].  

## Data and synthetic telemetry
- Event model: machineId, timestamp, status ∈ {occupied, free}, and optional heartbeat for health; retained MQTT message for last-known state [8][22].  
- Aggregates: 15‑minute bins for occupancy ratios per machine and category to power heatmaps and the baseline forecast chip [13][9].  
- Synthetic generation: use AWS IoT Device Simulator or a small SDK publisher to simulate 10–50 devices with realistic sets (30–90s) and rests (60–180s), peak hours, and light noise for demo realism [4][23].  

## Sensing assumptions (for future real data)
- MVP sim uses PIR-like dynamics to reflect feasibility of low-power occupancy sensing on equipment, acknowledging PIR’s line-of-sight and stillness limits mitigated by placement and hold-times [24][25].  
- Future variants can fuse simple vibration or reed switches for stubborn stations to improve precision without introducing cameras or PII [25][10].  

## Architecture
- Devices/sim: MQTT publish occupied/free/heartbeat to scoped topics with TLS and retained messages for last state; device shadow for health [8][22].  
- Ingest/processing: IoT rule to a Lambda that maintains current_state, derives transitions, writes events and aggregates to a time-series table, and triggers alerts [13][8].  
- APIs: REST/GraphQL for status/history, WebSocket/SSE for live updates, and POST alert subscriptions; Bedrock agent endpoint for chat with tool-use [3][13].  
- Maps/routing: Amazon Location route calculator configured and called by the route-matrix tool to compute ETAs for candidate branches [12][26].  

## Public APIs (MVP)
- GET /branches: list branches with coordinates and aggregate free-by-category counts for quick scanning [13][2].  
- GET /branches/{id}/categories/{category}/machines: list machines with current status, last change, and alert eligibility [13][2].  
- GET /machines/{id}/history?range=24h: return 15‑minute bins for heatmap and a simple “likely free” flag for the next 30 minutes [13][9].  
- POST /alerts: create “notify when free” subscriptions that trigger on occupied→free transitions with quiet-hours control [2][13].  

## Non-functional requirements
- Latency: live state propagation ≤ 15s P95; chatbot answer including tool calls ≤ 3s P95 under demo loads [8][3].  
- Reliability: simulator runs sustained for demo; service handles disconnected devices gracefully with stale markers and heartbeats [13][8].  
- Scalability: horizontal scale to thousands of machines and multi-branch queries with route-matrix batches [12][13].  

## Security, privacy, and compliance
- Privacy-by-design: no cameras or audio; only machine occupancy events and aggregates; publish a clear notice and retain minimal data aligned to PCPD/PDPO expectations in Hong Kong [27][28].  
- IoT security: device identity, mutual TLS, least-privilege topic policies, signed OTA, and periodic assessments per GovCERT IoT guidance [10][8].  
- Data governance: if accounts are added, provide access/erasure and security controls per PCPD guidance notes [11][28].  

## Metrics and analytics
- Product: session success rate (find ≥1 target machine available), alert-to-use conversion, and time saved per week (survey) [2][7].  
- Forecast: precision/recall of “likely free in 30m” vs realized events; lift over seasonal baseline measured weekly [9][14].  
- Agent: tool-call success rate, average tool chain length, and turnaround time for “nearby leg day” queries [3][18].  

## Build plan (hackathon)
- Day 1 AM: generate CDK stacks and Lambdas with Amazon Q Developer or Kiro; deploy IoT Core topics, DynamoDB/time-series table, API Gateway, Bedrock agent, and Location calculator [5][12].  
- Day 1 PM: implement ingest/aggregator Lambda, seed simulator (IoT Device Simulator or SDK publisher), and wire live UI tiles with WebSocket/SSE [4][13].  
- Day 2 AM: implement chatbot with Bedrock Converse API tool-use and two tools (availability, route matrix), and wire browser Geolocation to chat turns [3][20].  
- Day 2 PM: add alert-on-free, heatmaps, baseline forecast chip, and polish UX; capture evidence clips showing Q/Kiro generating code/IaC/tests for submission [9][17].  

## Risks and mitigations
- Data realism: simulator may look synthetic; mitigate with realistic peaks, bursts, and brief false signals modeled on PIR studies [24][4].  
- Tool brittleness: agent might mis-call tools; mitigate with strict JSON schemas, validation, and guardrails in the tool handlers [3][18].  
- Routing quotas/costs: route-matrix calls can add up; cache recent ETAs and limit candidate branches per request [26][12].  

## Existing solutions to acknowledge
- Brand “how busy” features validate appetite for live occupancy but not machine granularity, supporting the differentiator of this product [2][7].  
- Device simulation on AWS is common and appropriate for hackathons, enabling realistic end-to-end demos without hardware [4][29].  

## Acceptance criteria
- Live tiles update within 15s of simulated events and show branch/category availability with machine-level detail under stable demo load [13][8].  
- Chatbot answers “leg day nearby?” with a ranked list including ETA and free counts by calling availability and route-matrix tools successfully [3][12].  
- Repo contains CDK/IaC, Lambdas, tests, and docs generated materially by Amazon Q Developer or Kiro, with PRs/logs as evidence for hackathon rules [5][17].  

## Appendix: key references
- Agentic tool-use via Bedrock Converse API and schema-based functions for deterministic planning and calls [3][19].  
- Amazon Location Route Matrix for fast ETA computation across user and multiple branches [12][21].  
- AWS IoT Device Simulator and SDKs for synthetic device events at scale during demos [4][23].  
- Privacy/security baselines for IoT and Hong Kong PDPO/PCPD guidance [10][28].  

This PRD centers on a machine-level availability **MVP** with an agentic **chatbot** that plans via tool-use and routing, powered by **synthetic** IoT telemetry and built demonstrably with Amazon Q Developer or Kiro to meet hackathon criteria [2][3].
