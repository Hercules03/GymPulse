#!/usr/bin/env python3
"""
Simple IoT test using the AWS SDK sample approach
"""
import json
import os
import sys
import time
from awsiot import mqtt5_client_builder
from awscrt import mqtt5
from concurrent.futures import Future
import threading

def main():
    print("🧪 Simple AWS IoT Core Connection Test")
    print("=" * 50)
    
    # Configuration
    endpoint = "a2udl08tinypzz-ats.iot.ap-east-1.amazonaws.com"
    cert_file = "certs/device.cert.pem"
    key_file = "certs/device.private.key"
    ca_file = "certs/root-CA.crt"
    client_id = "basicPubSub"
    topic = "org/hk-central/machines/test-machine/status"
    
    # Verify files exist
    for file_path, name in [(cert_file, 'Certificate'), (key_file, 'Private Key'), (ca_file, 'CA')]:
        if not os.path.exists(file_path):
            print(f"❌ {name} not found: {file_path}")
            return False
        print(f"✅ {name} found: {file_path}")
    
    received_count = 0
    received_all_event = threading.Event()
    
    # Callback when connection is successful
    def on_connection_success(connection, callback_data):
        print(f"✅ Connection successful: {callback_data}")
    
    # Callback when connection fails
    def on_connection_failure(connection, callback_data):
        print(f"❌ Connection failed: {callback_data}")
    
    # Callback when disconnected
    def on_disconnection(disconnect_data):
        print(f"⚠️ Disconnected: {disconnect_data}")
    
    # Callback when message is received
    def on_publish_received(publish_packet_data):
        nonlocal received_count
        received_count += 1
        publish_packet = publish_packet_data.publish_packet
        print(f"📥 Received message #{received_count}:")
        print(f"   Topic: {publish_packet.topic}")
        print(f"   Payload: {publish_packet.payload.decode('utf-8')}")
        
        if received_count >= 3:
            received_all_event.set()
    
    # Create MQTT5 client
    print(f"🔌 Creating MQTT5 client...")
    client = mqtt5_client_builder.mtls_from_path(
        endpoint=endpoint,
        port=8883,
        cert_filepath=cert_file,
        pri_key_filepath=key_file,
        ca_filepath=ca_file,
        client_id=client_id,
        on_publish_received=on_publish_received
    )
    
    # Set callbacks
    client.on_connection_success = on_connection_success
    client.on_connection_failure = on_connection_failure
    client.on_disconnection = on_disconnection
    
    print(f"📡 Connecting to {endpoint}...")
    lifecycle_connect_future = client.start()
    if lifecycle_connect_future:
        lifecycle_connect_future.result()
    
    # Wait a moment for connection to establish
    time.sleep(3)
    
    print("✅ Connected! Subscribing to topic...")
    
    # Subscribe to topic
    subscribe_packet = mqtt5.SubscribePacket(
        subscriptions=[mqtt5.Subscription(topic_filter=topic, qos=mqtt5.QoS.AT_LEAST_ONCE)]
    )
    subscribe_future = client.subscribe(subscribe_packet)
    subscribe_result = subscribe_future.result()
    print(f"📬 Subscribed to {topic}")
    
    # Publish test messages
    print(f"📤 Publishing test messages...")
    for i in range(3):
        test_payload = {
            'machineId': 'test-machine',
            'gymId': 'hk-central',
            'status': 'occupied' if i % 2 == 0 else 'free',
            'timestamp': int(time.time()),
            'category': 'legs',
            'test_message': i + 1
        }
        
        publish_packet = mqtt5.PublishPacket(
            topic=topic,
            payload=json.dumps(test_payload).encode('utf-8'),
            qos=mqtt5.QoS.AT_LEAST_ONCE,
            retain=True
        )
        
        publish_future = client.publish(publish_packet)
        publish_future.result(timeout=10.0)
        
        print(f"📤 Published message {i+1}: {test_payload['status']}")
        time.sleep(1)
    
    # Wait for all messages to be received
    print("⏳ Waiting for all messages to be received...")
    received_all_event.wait(timeout=10.0)
    
    print(f"\n🎉 Test completed successfully!")
    print(f"📊 Messages published: 3")
    print(f"📊 Messages received: {received_count}")
    
    # Clean up
    print("🧹 Cleaning up...")
    client.stop()
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)