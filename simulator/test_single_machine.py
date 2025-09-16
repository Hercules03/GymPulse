#!/usr/bin/env python3
"""
Test single machine with AWS CLI publishing
"""
import asyncio
import logging
import signal
import sys
from machine_simulator import MachineSimulator

def signal_handler(signum, frame):
    print("\nShutdown signal received")
    sys.exit(0)

async def test_single_machine():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    signal.signal(signal.SIGINT, signal_handler)

    # Machine configuration
    machine_config = {
        'machineId': 'leg-press-01',
        'name': 'Leg Press Machine 1',
        'category': 'legs',
        'type': 'leg-press'
    }

    gym_config = {
        'id': 'hk-central',
        'name': 'Central Branch',
        'coordinates': {'lat': 22.2819, 'lon': 114.1577}
    }

    # Certificate paths
    cert_path = "certs/leg-press-01.cert.pem"
    key_path = "certs/leg-press-01.private.key"
    ca_path = "certs/root-CA.crt"
    endpoint = "a2udl08tinypzz-ats.iot.ap-east-1.amazonaws.com"

    print("Starting single machine simulator test...")
    print(f"Machine: {machine_config['machineId']}")
    print(f"Using AWS CLI publishing method")

    # Create simulator
    simulator = MachineSimulator(
        machine_config=machine_config,
        gym_config=gym_config,
        cert_path=cert_path,
        key_path=key_path,
        ca_path=ca_path,
        endpoint=endpoint
    )

    try:
        # Start simulation
        await simulator.start_simulation()
    except KeyboardInterrupt:
        print("\nStopping simulation...")
        simulator.stop_simulation()
    except Exception as e:
        print(f"Error: {e}")
        simulator.stop_simulation()

if __name__ == "__main__":
    asyncio.run(test_single_machine())