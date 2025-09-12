#!/usr/bin/env python3

import boto3
import json
import time

def test_iot_pipeline():
    """Test the IoT pipeline by publishing a message"""
    
    # Create IoT data client
    iot_client = boto3.client('iot-data', region_name='ap-east-1')
    
    # Create test message
    test_message = {
        'machineId': 'leg-press-01',
        'gymId': 'hk-central',
        'status': 'occupied',
        'timestamp': int(time.time()),
        'category': 'legs'
    }
    
    topic = 'org/hk-central/machines/leg-press-01/status'
    
    print(f"Publishing message to topic: {topic}")
    print(f"Message: {json.dumps(test_message, indent=2)}")
    
    try:
        response = iot_client.publish(
            topic=topic,
            payload=json.dumps(test_message)
        )
        print(f"✅ Message published successfully!")
        print(f"Response: {response}")
        
        # Wait a moment for processing
        print("⏳ Waiting 10 seconds for message processing...")
        time.sleep(10)
        
        # Check DynamoDB for the record
        print("📊 Checking DynamoDB current-state table...")
        dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
        
        # Try to find the record in current-state table
        current_state_table = dynamodb.Table('gym-pulse-current-state')
        
        try:
            response = current_state_table.get_item(
                Key={'machineId': 'leg-press-01'}
            )
            
            if 'Item' in response:
                print("✅ Found record in current-state table!")
                print(json.dumps(response['Item'], indent=2, default=str))
            else:
                print("❌ No record found in current-state table")
                
        except Exception as e:
            print(f"❌ Error checking current-state table: {e}")
        
    except Exception as e:
        print(f"❌ Failed to publish message: {e}")

if __name__ == "__main__":
    test_iot_pipeline()