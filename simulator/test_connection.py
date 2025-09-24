#!/usr/bin/env python3
"""
Test AWS IoT Core connection with real certificates
"""
import json
import time
import os
from awsiot import mqtt_connection_builder
from awscrt import mqtt
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Configuration
    endpoint = "a2udl08tinypzz-ats.iot.ap-east-1.amazonaws.com"
    cert_path = "certs/device.cert.pem"
    key_path = "certs/device.private.key"
    ca_path = "certs/root-CA.crt"
    client_id = "gym-pulse-test-device"
    topic = "org/hk-central/machines/test-machine/status"
    
    # Check if certificate files exist
    for path in [cert_path, key_path, ca_path]:
        if not os.path.exists(path):
            logger.error(f"Certificate file not found: {path}")
            return False
    
    logger.info("Starting IoT Core connection test...")
    
    # Build MQTT connection
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        cert_filepath=cert_path,
        pri_key_filepath=key_path,
        ca_filepath=ca_path,
        client_id=client_id,
        clean_session=False,
        keep_alive_secs=30
    )
    
    logger.info("Connecting to AWS IoT Core...")
    
    # Connect
    connect_future = mqtt_connection.connect()
    connect_future.result()
    logger.info("Connected successfully!")
    
    # Publish test message
    test_message = {
        "machineId": "test-machine",
        "gymId": "hk-central",
        "status": "free",
        "timestamp": int(time.time()),
        "category": "legs",
        "test": True
    }
    
    logger.info(f"Publishing test message to {topic}...")
    publish_future = mqtt_connection.publish(
        topic=topic,
        payload=json.dumps(test_message),
        qos=mqtt.QoS.AT_LEAST_ONCE
    )
    publish_future.result()
    logger.info("Message published successfully!")
    
    # Wait a bit
    time.sleep(2)
    
    # Disconnect
    logger.info("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    logger.info("Disconnected successfully!")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("✅ IoT Core connection test PASSED!")
        else:
            print("❌ IoT Core connection test FAILED!")
    except Exception as e:
        print(f"❌ IoT Core connection test FAILED: {e}")
        logger.error(f"Connection test failed: {e}")