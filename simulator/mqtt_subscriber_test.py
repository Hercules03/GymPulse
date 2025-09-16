#!/usr/bin/env python3
"""
MQTT Subscriber to test if messages are actually being received
"""
import json
import time
import threading
from awscrt import mqtt5, auth
from awsiot import mqtt5_client_builder

def test_mqtt_subscription():
    # Configuration
    endpoint = "a2udl08tinypzz-ats.iot.ap-east-1.amazonaws.com"
    cert_path = "certs/device.cert.pem"
    key_path = "certs/device.private.key"
    ca_path = "certs/root-CA.crt"
    client_id = "test-subscriber"
    topic = "org/hk-central/machines/leg-press-01/status"

    print(f"Testing MQTT subscription to IoT Core...")
    print(f"Endpoint: {endpoint}")
    print(f"Topic: {topic}")
    print(f"Client ID: {client_id}")

    received_messages = []

    def on_message_received(publish_packet_data):
        try:
            payload = json.loads(publish_packet_data.publish_packet.payload.decode('utf-8'))
            print(f"📨 Received message: {payload}")
            received_messages.append(payload)
        except Exception as e:
            print(f"Error processing message: {e}")
            print(f"Raw payload: {publish_packet_data.publish_packet.payload}")

    def on_connection_success(connection, callback_data):
        print(f"✅ Connected successfully!")

    def on_connection_failure(connection, callback_data):
        print(f"❌ Connection failed: {callback_data}")

    try:
        # Create MQTT client
        client = mqtt5_client_builder.mtls_from_path(
            endpoint=endpoint,
            port=8883,
            cert_filepath=cert_path,
            pri_key_filepath=key_path,
            ca_filepath=ca_path,
            client_id=client_id
        )

        # Set callbacks
        client.on_connection_success = on_connection_success
        client.on_connection_failure = on_connection_failure
        client.on_publish_received = on_message_received

        print("Connecting to AWS IoT Core...")

        # Connect
        connection_future = client.start()
        if connection_future:
            connection_future.result(timeout=10)

        print("Connected! Subscribing to topic...")
        time.sleep(1)

        # Subscribe to topic
        subscribe_request = mqtt5.SubscribePacket(
            subscriptions=[
                mqtt5.Subscription(
                    topic_filter=topic,
                    qos=mqtt5.QoS.AT_MOST_ONCE
                )
            ]
        )

        subscribe_future = client.subscribe(subscribe_request)
        if subscribe_future:
            subscribe_result = subscribe_future.result(timeout=10)
            print(f"Subscription result: {subscribe_result}")

        print(f"📡 Listening for messages on {topic}...")
        print("Press Ctrl+C to stop")

        # Keep listening
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping subscription...")

        print(f"Total messages received: {len(received_messages)}")

        # Disconnect
        client.stop()
        print("Disconnected.")

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return len(received_messages) > 0

if __name__ == "__main__":
    test_mqtt_subscription()