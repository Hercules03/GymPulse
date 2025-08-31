"""
WebSocket Disconnect Handler
Manages WebSocket connection cleanup
"""
import json
import boto3
import os
from botocore.exceptions import ClientError


dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ['CONNECTIONS_TABLE'])


def lambda_handler(event, context):
    """
    Handle WebSocket $disconnect route
    Clean up connection and subscription data
    """
    try:
        connection_id = event['requestContext']['connectionId']
        route_key = event['requestContext']['routeKey']
        
        print(f"WebSocket connection closing: {connection_id} on route {route_key}")
        
        # Remove connection from DynamoDB
        try:
            response = connections_table.delete_item(
                Key={'connectionId': connection_id},
                ReturnValues='ALL_OLD'
            )
            
            deleted_item = response.get('Attributes', {})
            if deleted_item:
                print(f"Connection {connection_id} removed. Was connected since: {deleted_item.get('connectedAt')}")
                print(f"Had subscriptions: {deleted_item.get('subscriptions', {})}")
            else:
                print(f"Connection {connection_id} was not found in database (possibly expired)")
                
        except ClientError as e:
            print(f"Error removing connection {connection_id}: {str(e)}")
            # Don't fail the disconnect if we can't clean up - connection might already be expired
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Disconnected successfully',
                'connectionId': connection_id
            })
        }
        
    except Exception as e:
        print(f"WebSocket disconnect error: {str(e)}")
        return {
            'statusCode': 200  # Return 200 even on error to avoid connection state issues
        }