"""
IoT Message Ingest Handler
Processes MQTT messages and updates DynamoDB tables
"""
import json
import boto3
import os
from decimal import Decimal
from datetime import datetime


dynamodb = boto3.resource('dynamodb')
current_state_table = dynamodb.Table(os.environ['CURRENT_STATE_TABLE'])
events_table = dynamodb.Table(os.environ['EVENTS_TABLE'])
aggregates_table = dynamodb.Table(os.environ['AGGREGATES_TABLE'])
alerts_table = dynamodb.Table(os.environ['ALERTS_TABLE'])


def lambda_handler(event, context):
    """
    Process IoT message from MQTT topic
    """
    try:
        print(f"Received IoT event: {json.dumps(event)}")
        
        # Parse IoT message
        topic = event.get('topic', '')
        payload = json.loads(event.get('payload', '{}'))
        
        machine_id = payload.get('machineId')
        status = payload.get('status')  # 'occupied' or 'free'
        timestamp = int(datetime.now().timestamp())
        gym_id = payload.get('gymId', 'unknown')
        category = payload.get('category', 'unknown')
        
        if not machine_id or not status:
            raise ValueError("Missing machineId or status in payload")
        
        # Update current state
        current_state_table.put_item(
            Item={
                'machineId': machine_id,
                'status': status,
                'lastUpdate': timestamp,
                'gymId': gym_id,
                'category': category
            }
        )
        
        # Write event to time-series table
        events_table.put_item(
            Item={
                'machineId': machine_id,
                'timestamp': timestamp,
                'status': status,
                'gymId': gym_id,
                'category': category,
                'ttl': timestamp + (30 * 24 * 3600)  # 30 days TTL
            }
        )
        
        # TODO: Update aggregates for heatmaps
        # TODO: Trigger alerts if status changed to 'free'
        # TODO: Send WebSocket notification
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'IoT message processed successfully',
                'machineId': machine_id,
                'status': status
            })
        }
        
    except Exception as e:
        print(f"Error processing IoT message: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }