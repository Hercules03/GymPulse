#!/usr/bin/env python3
"""
Test real state transitions using the working MQTT approach
"""
import json
import os
import time
from awsiot import mqtt5_client_builder
from awscrt import mqtt5
import threading

def test_real_state_transitions():
    print("🧪 Testing Real State Transitions...")
    
    # Configuration
    endpoint = "a2udl08tinypzz-ats.iot.ap-east-1.amazonaws.com"
    cert_file = "certs/device.cert.pem"
    key_file = "certs/device.private.key"
    ca_file = "certs/root-CA.crt"
    client_id = "basicPubSub"
    machine_id = "chest-press-01"
    topic = f"org/hk-central/machines/{machine_id}/status"
    
    # Connection callbacks
    def on_connection_success(connection, callback_data):
        print(f"✅ Connected successfully")
    
    def on_connection_failure(connection, callback_data):
        print(f"❌ Connection failed: {callback_data}")
    
    # Create MQTT5 client
    print(f"🔌 Creating MQTT5 client...")
    client = mqtt5_client_builder.mtls_from_path(
        endpoint=endpoint,
        port=8883,
        cert_filepath=cert_file,
        pri_key_filepath=key_file,
        ca_filepath=ca_file,
        client_id=client_id
    )
    
    # Set callbacks
    client.on_connection_success = on_connection_success
    client.on_connection_failure = on_connection_failure
    
    print(f"📡 Connecting to {endpoint}...")
    lifecycle_connect_future = client.start()
    if lifecycle_connect_future:
        lifecycle_connect_future.result()
    
    # Wait for connection
    time.sleep(3)
    
    print("✅ Connected! Sending state transitions...")
    
    # Test sequence: free -> occupied -> free -> occupied
    states = ['free', 'occupied', 'free', 'occupied']
    
    for i, status in enumerate(states):
        print(f"{i+1}️⃣ Publishing: {machine_id} -> {status}")
        
        payload = {
            'machineId': machine_id,
            'gymId': 'hk-central',
            'status': status,
            'timestamp': int(time.time()),
            'category': 'chest',
            'coordinates': {'lat': 22.2819, 'lon': 114.1577},
            'machine_name': 'Chest Press Machine 1'
        }
        
        publish_packet = mqtt5.PublishPacket(
            topic=topic,
            payload=json.dumps(payload).encode('utf-8'),
            qos=mqtt5.QoS.AT_LEAST_ONCE,
            retain=True
        )
        
        try:
            publish_future = client.publish(publish_packet)
            publish_future.result(timeout=10.0)
            print(f"   ✅ Published successfully: {status}")
            
            # Wait between transitions
            time.sleep(4)
            
        except Exception as e:
            print(f"   ❌ Failed to publish: {str(e)}")
    
    print(f"\n🎉 Test completed! Check:")
    print("1. AWS CloudWatch logs: /aws/lambda/gym-pulse-iot-ingest")
    print("2. DynamoDB table: gym-pulse-current-state")
    print("3. Your frontend WebSocket connection for real-time updates!")
    
    # Clean up
    client.stop()
    return True

def main():
    print("=" * 60)
    print("🏋️  Real State Transition Test")
    print("=" * 60)
    return test_real_state_transitions()

if __name__ == "__main__":
    main()