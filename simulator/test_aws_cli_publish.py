#!/usr/bin/env python3
"""
Test publishing via AWS CLI to confirm it works
"""
import json
import subprocess
import time

def test_aws_cli_publish():
    topic = "org/hk-central/machines/leg-press-01/status"
    payload = {
        "machineId": "leg-press-01",
        "gymId": "hk-central",
        "status": "occupied",
        "timestamp": int(time.time())
    }

    print(f"Publishing via AWS CLI to: {topic}")
    print(f"Payload: {payload}")

    try:
        # Convert payload to JSON string and then base64
        json_payload = json.dumps(payload)
        import base64
        b64_payload = base64.b64encode(json_payload.encode()).decode()

        # Use AWS CLI to publish
        cmd = [
            "aws", "iot-data", "publish",
            "--topic", topic,
            "--payload", b64_payload
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ AWS CLI publish successful!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ AWS CLI publish failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

if __name__ == "__main__":
    test_aws_cli_publish()