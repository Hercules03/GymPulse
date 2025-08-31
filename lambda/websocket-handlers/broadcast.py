"""
WebSocket Broadcast Handler
Sends real-time machine updates to subscribed connections
"""
import json
import boto3
import os
import time
from botocore.exceptions import ClientError


dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ['CONNECTIONS_TABLE'])

# API Gateway Management API client for posting messages to WebSocket connections
apigateway_management = None


def get_apigateway_client():
    """
    Get API Gateway Management API client with endpoint URL
    """
    global apigateway_management
    if not apigateway_management:
        endpoint_url = os.environ['WEBSOCKET_API_ENDPOINT']
        apigateway_management = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=endpoint_url
        )
    return apigateway_management


def lambda_handler(event, context):
    """
    Handle broadcasting machine updates to subscribed WebSocket connections
    This function can be called by:
    1. IoT ingest Lambda when machine state changes
    2. Alert system when alerts are fired
    3. Scheduled updates for heartbeat/keepalive
    """
    try:
        print(f"Received broadcast event: {json.dumps(event, default=str)}")
        
        # Parse the incoming message
        if 'Records' in event:
            # Called from DynamoDB Stream or SQS
            for record in event['Records']:
                if record['eventName'] in ['INSERT', 'MODIFY']:
                    # Process DynamoDB stream record
                    process_machine_update_from_stream(record)
        else:
            # Called directly with machine update data
            machine_update = event.get('machineUpdate')
            user_alert = event.get('userAlert')
            target_user_id = event.get('targetUserId')
            
            if machine_update:
                broadcast_machine_update(machine_update)
            elif user_alert and target_user_id:
                broadcast_user_alert(user_alert, target_user_id)
            else:
                print("No machine update or user alert data found in event")
                
        return {'statusCode': 200}
        
    except Exception as e:
        print(f"WebSocket broadcast error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


def process_machine_update_from_stream(record):
    """
    Process machine state change from DynamoDB stream
    """
    try:
        # Extract new image from DynamoDB stream record
        if 'dynamodb' in record and 'NewImage' in record['dynamodb']:
            new_image = record['dynamodb']['NewImage']
            
            machine_update = {
                'type': 'machine_update',
                'machineId': new_image.get('machineId', {}).get('S', ''),
                'gymId': new_image.get('gymId', {}).get('S', ''),
                'category': new_image.get('category', {}).get('S', ''),
                'status': new_image.get('status', {}).get('S', ''),
                'timestamp': int(new_image.get('lastUpdate', {}).get('N', 0)),
                'lastChange': int(new_image.get('lastChange', {}).get('N', 0))
            }
            
            broadcast_machine_update(machine_update)
        
    except Exception as e:
        print(f"Error processing DynamoDB stream record: {str(e)}")


def broadcast_machine_update(machine_update):
    """
    Broadcast machine update to all relevant WebSocket connections
    """
    try:
        # Get all active connections
        connections = get_subscribed_connections(machine_update)
        
        message_data = json.dumps(machine_update)
        successful_sends = 0
        failed_sends = 0
        stale_connections = []
        
        client = get_apigateway_client()
        
        for connection in connections:
            connection_id = connection['connectionId']
            try:
                # Send message to WebSocket connection
                client.post_to_connection(
                    ConnectionId=connection_id,
                    Data=message_data
                )
                successful_sends += 1
                
            except client.exceptions.GoneException:
                # Connection is stale, mark for removal
                print(f"Connection {connection_id} is stale, marking for removal")
                stale_connections.append(connection_id)
                failed_sends += 1
                
            except Exception as e:
                print(f"Failed to send to connection {connection_id}: {str(e)}")
                failed_sends += 1
        
        # Clean up stale connections
        cleanup_stale_connections(stale_connections)
        
        print(f"Broadcast complete: {successful_sends} successful, {failed_sends} failed, {len(stale_connections)} stale")
        
    except Exception as e:
        print(f"Error in broadcast_machine_update: {str(e)}")


def get_subscribed_connections(machine_update):
    """
    Get all connections that should receive this machine update
    """
    try:
        # Scan connections table for relevant subscriptions
        response = connections_table.scan()
        connections = response.get('Items', [])
        
        relevant_connections = []
        
        for connection in connections:
            subscriptions = connection.get('subscriptions', {})
            
            # Check if connection is interested in this update
            if is_connection_interested(subscriptions, machine_update):
                relevant_connections.append(connection)
        
        return relevant_connections
        
    except Exception as e:
        print(f"Error getting subscribed connections: {str(e)}")
        return []


def is_connection_interested(subscriptions, machine_update):
    """
    Determine if a connection should receive this machine update
    """
    try:
        machine_id = machine_update.get('machineId')
        gym_id = machine_update.get('gymId')
        category = machine_update.get('category')
        
        # Check specific machine subscription
        if machine_id in subscriptions.get('machines', []):
            return True
        
        # Check gym and category subscription
        if (gym_id in subscriptions.get('branches', []) and 
            category in subscriptions.get('categories', [])):
            return True
        
        # If no specific subscriptions, default to interested
        if (not subscriptions.get('machines') and
            not subscriptions.get('branches') and 
            not subscriptions.get('categories')):
            return True
            
        return False
        
    except Exception as e:
        print(f"Error checking connection interest: {str(e)}")
        return False


def broadcast_user_alert(alert_message, target_user_id):
    """
    Send alert notification to specific user's WebSocket connections
    """
    try:
        print(f"Broadcasting alert to user {target_user_id}: {alert_message.get('message', 'No message')}")
        
        # Get connections for the specific user
        user_connections = get_user_connections(target_user_id)
        
        message_data = json.dumps(alert_message)
        successful_sends = 0
        failed_sends = 0
        stale_connections = []
        
        client = get_apigateway_client()
        
        for connection in user_connections:
            connection_id = connection['connectionId']
            try:
                # Send alert to WebSocket connection
                client.post_to_connection(
                    ConnectionId=connection_id,
                    Data=message_data
                )
                successful_sends += 1
                print(f"Alert sent to connection {connection_id} for user {target_user_id}")
                
            except client.exceptions.GoneException:
                # Connection is stale, mark for removal
                print(f"Connection {connection_id} is stale, marking for removal")
                stale_connections.append(connection_id)
                failed_sends += 1
                
            except Exception as e:
                print(f"Failed to send alert to connection {connection_id}: {str(e)}")
                failed_sends += 1
        
        # Clean up stale connections
        cleanup_stale_connections(stale_connections)
        
        print(f"Alert broadcast to user {target_user_id} complete: {successful_sends} successful, {failed_sends} failed")
        
        if successful_sends == 0 and len(user_connections) > 0:
            print(f"Warning: No successful alert deliveries to user {target_user_id}, all connections may be stale")
        elif len(user_connections) == 0:
            print(f"Info: User {target_user_id} has no active WebSocket connections")
        
    except Exception as e:
        print(f"Error in broadcast_user_alert: {str(e)}")


def get_user_connections(user_id):
    """
    Get all active connections for a specific user
    """
    try:
        # Scan connections table for user's connections
        response = connections_table.scan(
            FilterExpression='userId = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        
        connections = response.get('Items', [])
        print(f"Found {len(connections)} active connections for user {user_id}")
        return connections
        
    except Exception as e:
        print(f"Error getting connections for user {user_id}: {str(e)}")
        return []


def cleanup_stale_connections(connection_ids):
    """
    Remove stale connections from the database
    """
    try:
        for connection_id in connection_ids:
            try:
                connections_table.delete_item(
                    Key={'connectionId': connection_id}
                )
                print(f"Removed stale connection: {connection_id}")
            except Exception as e:
                print(f"Error removing stale connection {connection_id}: {str(e)}")
                
    except Exception as e:
        print(f"Error in cleanup_stale_connections: {str(e)}")