#!/usr/bin/env python3
"""
Test script to validate state transitions for real-time updates
"""
import json
import os
import sys
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from machine_simulator import MachineSimulator

async def test_state_transitions():
    """Test clear state transitions to trigger WebSocket updates"""
    print("🧪 Testing State Transitions for Real-Time Updates...")
    
    # Load environment
    load_dotenv()
    
    # Get configuration
    endpoint = os.getenv('IOT_ENDPOINT')
    cert_path = os.getenv('DEVICE_CERT', 'certs/device.cert.pem')
    key_path = os.getenv('DEVICE_KEY', 'certs/device.private.key')
    ca_path = os.getenv('ROOT_CA', 'certs/root-CA.crt')
    
    print(f"📡 IoT Endpoint: {endpoint}")
    
    # Create simulator instance for a different machine
    machine_config = {
        'machineId': 'bench-press-01',
        'name': 'Bench Press Machine 1',
        'category': 'chest'
    }
    
    gym_config = {
        'id': 'hk-central',
        'name': 'Central Branch',
        'coordinates': {'lat': 22.2819, 'lon': 114.1577}
    }
    
    simulator = MachineSimulator(
        machine_config=machine_config,
        gym_config=gym_config,
        cert_path=cert_path,
        key_path=key_path,
        ca_path=ca_path,
        endpoint=endpoint
    )
    
    # Track messages
    messages_sent = 0
    
    def on_state_change(machine_id, state, payload):
        nonlocal messages_sent
        messages_sent += 1
        print(f"📤 Transition {messages_sent}: {machine_id} -> {state}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    simulator.on_state_change = on_state_change
    
    try:
        # Test connection
        print("\n🔌 Connecting to AWS IoT Core...")
        connected = await simulator.connect()
        
        if not connected:
            print("❌ Failed to connect to AWS IoT Core")
            return False
        
        print("✅ Connected successfully!")
        
        # Send clear state transitions
        print("\n📨 Sending state transitions...")
        
        print("1️⃣ Setting machine to OCCUPIED...")
        await simulator._publish_state_change('occupied')
        time.sleep(3)
        
        print("2️⃣ Setting machine to FREE (should trigger alert processing)...")
        await simulator._publish_state_change('free')
        time.sleep(3)
        
        print("3️⃣ Setting machine to OCCUPIED again...")
        await simulator._publish_state_change('occupied')
        time.sleep(3)
        
        print("4️⃣ Setting machine back to FREE...")
        await simulator._publish_state_change('free')
        time.sleep(2)
        
        print(f"\n✅ Test completed! Sent {messages_sent} state transition messages")
        print("\nNow check:")
        print("1. AWS CloudWatch logs for Lambda processing")
        print("2. DynamoDB gym-pulse-current-state table for updates")
        print("3. Frontend for real-time WebSocket updates")
        
        # Clean up
        simulator.stop_simulation()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("🏋️  GymPulse State Transition Test")
    print("=" * 60)
    
    # Run the test
    success = asyncio.run(test_state_transitions())
    
    if success:
        print("\n🎉 State transition test completed!")
        print("Check your frontend to see if live updates are working.")
    else:
        print("\n❌ Test failed. Check configuration and certificates.")
    
    return success

if __name__ == "__main__":
    main()