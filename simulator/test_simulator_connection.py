#!/usr/bin/env python3
"""
Test script to validate simulator connection to AWS IoT Core
"""
import os
import sys
import json
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from machine_simulator import MachineSimulator

def load_machine_config():
    """Load a test machine configuration"""
    return {
        'machineId': 'leg-press-01',
        'name': 'Test Leg Press Machine 1',
        'category': 'legs'
    }

def load_gym_config():
    """Load test gym configuration"""
    return {
        'id': 'hk-central',
        'name': 'Central Branch',
        'coordinates': {'lat': 22.2819, 'lon': 114.1577}
    }

async def test_simulator_connection():
    """Test simulator connection and message publishing"""
    print("🧪 Testing Simulator Connection to AWS IoT Core...")
    
    # Load environment
    load_dotenv()
    
    # Get configuration
    endpoint = os.getenv('IOT_ENDPOINT')
    cert_path = os.getenv('DEVICE_CERT', 'certs/device.cert.pem')
    key_path = os.getenv('DEVICE_KEY', 'certs/device.private.key')
    ca_path = os.getenv('ROOT_CA', 'certs/root-CA.crt')
    
    # Verify files exist
    for file_path, name in [(cert_path, 'Device Certificate'), 
                           (key_path, 'Private Key'), 
                           (ca_path, 'Root CA')]:
        if not os.path.exists(file_path):
            print(f"❌ {name} not found at: {file_path}")
            return False
        print(f"✅ {name} found: {file_path}")
    
    print(f"📡 IoT Endpoint: {endpoint}")
    
    # Create simulator instance
    machine_config = load_machine_config()
    gym_config = load_gym_config()
    
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
        print(f"📤 Message {messages_sent}: {machine_id} -> {state}")
        print(f"   Topic: org/{gym_config['id']}/machines/{machine_id}/status")
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
        
        # Send test messages
        print("\n📨 Sending test messages...")
        
        # Initial state
        await simulator._publish_state_change('free')
        time.sleep(2)
        
        # State change to occupied
        await simulator._publish_state_change('occupied')
        time.sleep(2)
        
        # State change back to free
        await simulator._publish_state_change('free')
        time.sleep(1)
        
        print(f"\n✅ Test completed successfully! Sent {messages_sent} messages")
        
        # Clean up
        simulator.stop_simulation()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("🏋️  GymPulse Simulator Connection Test")
    print("=" * 60)
    
    # Run the test
    success = asyncio.run(test_simulator_connection())
    
    if success:
        print("\n🎉 All tests passed! Simulator is ready.")
        print("\nNext steps:")
        print("1. Complete AWS Console IoT setup (click 'Continue')")
        print("2. Run the full simulator with multiple machines")
        print("3. Test end-to-end data flow to frontend")
    else:
        print("\n❌ Tests failed. Check configuration and certificates.")
    
    return success

if __name__ == "__main__":
    main()