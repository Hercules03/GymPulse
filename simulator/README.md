# GymPulse IoT Device Simulator

A realistic gym equipment simulator for the GymPulse system that generates synthetic telemetry data with peak hour patterns, noise injection, and realistic usage cycles.

## Features

- **15 Simulated Machines** across 2 Hong Kong branches (Central, Causeway Bay)
- **3 Equipment Categories**: legs, chest, back
- **Realistic Usage Patterns**: Peak hours, session durations, rest periods
- **Noise Injection**: False positives, missed detections, network delays
- **MQTT Integration**: AWS IoT Core with retained messages and QoS 1

## Installation

```bash
cd simulator
uv sync  # Install dependencies
```

## Configuration

Machine inventory and usage patterns are configured in `config/machines.json`:

- **Branches**: Central (9 machines) and Causeway Bay (9 machines) 
- **Peak Hours**: Morning (6-9 AM), Lunch (12-1 PM), Evening (6-9 PM)
- **Timing**: 30-90s occupied, 60-180s rest, 15-45min sessions
- **Noise**: 5% false positives, 3% missed detections

## Usage

### Create Test Certificates
```bash
uv run python main.py --create-certs
```

### Run Demo Scenario (5 minutes)
```bash
uv run python main.py --demo --duration 5
```

### Run Specific Machines
```bash
uv run python main.py --machines leg-press-01 bench-press-01 --duration 10
```

### Full Simulation (60 minutes)
```bash
uv run python main.py --duration 60
```

### Command Line Options

- `--config` - Configuration file path (default: config/machines.json)
- `--cert-dir` - Certificate directory (default: certs)
- `--endpoint` - AWS IoT endpoint (or set IOT_ENDPOINT env var)
- `--duration` - Simulation duration in minutes (default: 60)
- `--machines` - Specific machine IDs to simulate
- `--demo` - Run demo scenario with preset patterns
- `--create-certs` - Create test certificate placeholders
- `--status` - Show simulation status
- `--verbose` - Enable verbose logging

## Message Format

```json
{
  "machineId": "leg-press-01",
  "gymId": "hk-central", 
  "status": "occupied",
  "timestamp": 1634567890,
  "category": "legs",
  "coordinates": {"lat": 22.2819, "lon": 114.1577},
  "machine_name": "Leg Press Machine 1"
}
```

## MQTT Topics

Messages are published to: `org/{gymId}/machines/{machineId}/status`

Examples:
- `org/hk-central/machines/leg-press-01/status`
- `org/hk-causeway/machines/bench-press-03/status`

## Peak Hour Simulation

The simulator models realistic gym usage patterns:

- **Morning Peak (6-9 AM)**: 70% occupancy rate
- **Lunch Peak (12-1 PM)**: 60% occupancy rate  
- **Evening Peak (6-9 PM)**: 85% occupancy rate
- **Off-Peak (2-5 PM)**: 30% occupancy rate
- **Night (10 PM-6 AM)**: 10% occupancy rate

## Category-Specific Patterns

- **Legs**: 20% more popular, slightly longer sessions
- **Chest**: 30% more popular, peak 1 hour earlier
- **Back**: 10% less popular, shorter sessions, peak 1 hour later

## Noise Injection

To simulate real-world sensor limitations:

- **False Positives**: 5% brief incorrect occupancy signals
- **Missed Detections**: 3% of actual state changes not reported
- **Network Delays**: 10% chance of 5-30 second delays
- **Device Offline**: 2% chance of 2-5 minute offline periods

## Architecture

```
src/
├── usage_patterns.py    # Peak hours and timing logic
├── machine_simulator.py # Individual machine simulation
└── gym_simulator.py     # Coordinator for all machines

config/
└── machines.json        # Machine inventory and patterns

certs/                   # IoT device certificates
```

## Development

The simulator is built with:
- **Python 3.13** with `uv` package management
- **AWS IoT Device SDK** for MQTT connectivity
- **Faker** for realistic data generation
- **Asyncio** for concurrent machine simulation

## Production Deployment

For production use:

1. Replace test certificates with real AWS IoT certificates
2. Set `IOT_ENDPOINT` environment variable
3. Configure IAM policies for device MQTT publishing
4. Adjust usage patterns for your specific gym data
5. Enable CloudWatch logging and monitoring

## Demo Integration

The simulator is designed to work with the GymPulse demo flow:

1. Start simulator before demo
2. Show live tile updates from MQTT messages
3. Test "notify when free" alerts
4. Query chatbot: "I want to do legs nearby"
5. Navigate to branch view with real data