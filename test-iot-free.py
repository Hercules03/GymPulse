#!/usr/bin/env python3

import boto3
import json
import time

def test_iot_free_transition():
    """Test the IoT pipeline with a free status transition"""
    
    # Create IoT data client
    iot_client = boto3.client('iot-data', region_name='ap-east-1')
    
    # Create test message with FREE status
    test_message = {
        'machineId': 'leg-press-01',
        'gymId': 'hk-central',
        'status': 'free',  # Changed to free to trigger state transition
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
        
        # Wait for processing
        print("⏳ Waiting 15 seconds for message processing...")
        time.sleep(15)
        
        # Check DynamoDB for the record
        print("📊 Checking DynamoDB current-state table...")
        dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
        
        # Check current-state table
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
            
        # Also check if events were recorded
        print("\n📊 Checking DynamoDB events table...")
        try:
            events_table = dynamodb.Table('gym-pulse-events')
            response = events_table.query(
                KeyConditionExpression='machineId = :machineId',
                ExpressionAttributeValues={':machineId': 'leg-press-01'},
                ScanIndexForward=False,  # Get newest first
                Limit=5
            )
            
            if response['Items']:
                print("✅ Found events in events table!")
                for item in response['Items']:
                    print(json.dumps(item, indent=2, default=str))
            else:
                print("❌ No events found in events table")
        
        except Exception as e:
            print(f"❌ Error checking events table: {e}")
        
    except Exception as e:
        print(f"❌ Failed to publish message: {e}")

if __name__ == "__main__":
    test_iot_free_transition()