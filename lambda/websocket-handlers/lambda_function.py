"""
Simple WebSocket Connect Handler
Manages WebSocket connection establishment
"""
import json
import boto3
import os
import time
from botocore.exceptions import ClientError

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Handle WebSocket connection requests
    """
    try:
        connection_id = event['requestContext']['connectionId']
        
        # Get table name from environment (with fallback)
        table_name = os.environ.get('CONNECTIONS_TABLE', 'gym-pulse-connections')
        connections_table = dynamodb.Table(table_name)
        
        # Parse query parameters for subscriptions
        query_params = event.get('queryStringParameters') or {}

        # Debug logging
        print(f"Event: {json.dumps(event, default=str)}")
        print(f"Query parameters: {query_params}")

        # Store connection with subscription preferences
        connections_table.put_item(
            Item={
                'connectionId': connection_id,
                'timestamp': int(time.time()),
                'ttl': int(time.time()) + 7200,  # 2 hours TTL
                'branches': query_params.get('branches', '').split(',') if query_params.get('branches') else [],
                'categories': query_params.get('categories', '').split(',') if query_params.get('categories') else [],
                'machines': query_params.get('machines', '').split(',') if query_params.get('machines') else [],
                'userId': query_params.get('userId', 'anonymous')
            }
        )
        
        print(f"WebSocket connected: {connection_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Connected successfully'})
        }
        
    except Exception as e:
        print(f"Connection error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Connection failed'})
        }