"""
Simple WebSocket Broadcast Handler
Sends real-time updates to connected clients
"""
import json
import boto3
import os
from botocore.exceptions import ClientError

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Broadcast messages to WebSocket connections
    """
    try:
        # Get table name from environment (with fallback)
        table_name = os.environ.get('CONNECTIONS_TABLE', 'gym-pulse-connections')
        connections_table = dynamodb.Table(table_name)
        
        # Parse the message to broadcast
        if 'Records' in event:
            # Called from DynamoDB stream or other trigger
            message = {
                'type': 'machine_update',
                'data': 'Mock update for testing'
            }
        else:
            # Direct invocation
            message = event.get('message', {'type': 'test', 'data': 'Test message'})
        
        # Get WebSocket API endpoint
        websocket_endpoint = os.environ.get('WEBSOCKET_API_ENDPOINT', '')
        if not websocket_endpoint:
            print("No WebSocket endpoint configured")
            return {'statusCode': 200, 'body': 'No endpoint configured'}
            
        # Initialize API Gateway management client
        apigateway_client = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=websocket_endpoint.replace('wss://', 'https://')
        )
        
        # Get all connections
        response = connections_table.scan()
        connections = response.get('Items', [])
        
        # Broadcast to all connections
        for connection in connections:
            try:
                apigateway_client.post_to_connection(
                    ConnectionId=connection['connectionId'],
                    Data=json.dumps(message)
                )
                print(f"Message sent to {connection['connectionId']}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'GoneException':
                    # Connection is stale, remove it
                    connections_table.delete_item(
                        Key={'connectionId': connection['connectionId']}
                    )
                    print(f"Removed stale connection: {connection['connectionId']}")
                else:
                    print(f"Failed to send to {connection['connectionId']}: {e}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'Broadcasted to {len(connections)} connections'})
        }
        
    except Exception as e:
        print(f"Broadcast error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Broadcast failed'})
        }