#!/usr/bin/env python3
"""
Simple MQTT publish test to verify IoT Core connectivity
"""
import json
import time
from awscrt import mqtt5, auth
from awsiot import mqtt5_client_builder

def test_simple_publish():
    # Configuration
    endpoint = "a2udl08tinypzz-ats.iot.ap-east-1.amazonaws.com"
    cert_path = "certs/leg-press-01.cert.pem"
    key_path = "certs/leg-press-01.private.key"
    ca_path = "certs/root-CA.crt"
    client_id = "leg-press-01"
    topic = "org/hk-central/machines/leg-press-01/status"

    print(f"Testing MQTT publish to IoT Core...")
    print(f"Endpoint: {endpoint}")
    print(f"Topic: {topic}")
    print(f"Client ID: {client_id}")

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

        print("Connecting to AWS IoT Core...")

        # Connect
        connection_future = client.start()
        if connection_future:
            connection_future.result(timeout=10)

        print("Connected! Waiting 2 seconds...")
        time.sleep(2)

        # Publish test message
        payload = {
            "machineId": "leg-press-01",
            "gymId": "hk-central",
            "status": "free",
            "timestamp": int(time.time()),
            "test": True
        }

        print(f"Publishing test message: {payload}")

        publish_request = mqtt5.PublishPacket(
            topic=topic,
            payload=json.dumps(payload).encode('utf-8'),
            qos=mqtt5.QoS.AT_MOST_ONCE,
            retain=True
        )

        publish_future = client.publish(publish_request)
        if publish_future:
            publish_future.result(timeout=10)

        print("✅ Message published successfully!")

        # Wait a moment before disconnecting
        time.sleep(2)

        # Disconnect
        client.stop()
        print("Disconnected.")

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True

if __name__ == "__main__":
    success = test_simple_publish()
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")