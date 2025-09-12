"""
Simple WebSocket Disconnect Handler
Manages WebSocket connection cleanup
"""
import json
import boto3
import os
from botocore.exceptions import ClientError

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Handle WebSocket disconnection requests
    """
    try:
        connection_id = event['requestContext']['connectionId']
        
        # Get table name from environment (with fallback)
        table_name = os.environ.get('CONNECTIONS_TABLE', 'gym-pulse-connections')
        connections_table = dynamodb.Table(table_name)
        
        # Remove connection from table
        connections_table.delete_item(
            Key={'connectionId': connection_id}
        )
        
        print(f"WebSocket disconnected: {connection_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Disconnected successfully'})
        }
        
    except Exception as e:
        print(f"Disconnection error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Disconnection failed'})
        }