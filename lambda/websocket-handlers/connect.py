"""
WebSocket Connect Handler with comprehensive error handling and monitoring
Manages WebSocket connection establishment and subscription management
"""
import json
import boto3
import os
import sys
import time
from botocore.exceptions import ClientError

# Add utils directory to Python path
sys.path.append('/opt/python/lib/python3.9/site-packages')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.error_handler import (
    websocket_handler, log_structured, send_metric,
    ValidationError, DatabaseError, dynamodb_circuit_breaker
)

# Initialize AWS resources
try:
    dynamodb = boto3.resource('dynamodb')
    connections_table = dynamodb.Table(os.environ['CONNECTIONS_TABLE'])
except Exception as e:
    log_structured('ERROR', 'websocket_init_error', {
        'error': str(e),
        'missing_env_vars': [var for var in ['CONNECTIONS_TABLE'] if var not in os.environ]
    })
    raise


@websocket_handler
def lambda_handler(event, context):
    """
    Handle WebSocket $connect route
    Store connection info and subscription preferences
    """
    # Extract connection information
    request_context = event.get('requestContext', {})
    connection_id = request_context.get('connectionId')
    route_key = request_context.get('routeKey', '$connect')
    
    if not connection_id:
        raise ValidationError("Missing connection ID in request context")
    
    log_structured('INFO', 'websocket_connect_attempt', {
        'connection_id': connection_id[:8] + '...',  # Partial ID for privacy
        'route_key': route_key
    })
    
    # Extract query parameters for subscription preferences
    query_params = event.get('queryStringParameters', {}) or {}
    
    # Parse and validate subscriptions
    valid_branches = ['hk-central', 'hk-causeway']
    valid_categories = ['legs', 'chest', 'back']
    
    # Default subscription preferences with validation
    raw_branches = query_params.get('branches', '').split(',') if query_params.get('branches') else valid_branches
    raw_categories = query_params.get('categories', '').split(',') if query_params.get('categories') else valid_categories
    raw_machines = query_params.get('machines', '').split(',') if query_params.get('machines') else []
    
    # Validate and filter subscriptions
    subscriptions = {
        'branches': [b for b in raw_branches if b in valid_branches],
        'categories': [c for c in raw_categories if c in valid_categories],
        'machines': [m for m in raw_machines if m and len(m) > 2]  # Basic machine ID validation
    }
    
    # Ensure at least one subscription exists
    if not any(subscriptions.values()):
        subscriptions = {
            'branches': valid_branches,
            'categories': valid_categories,
            'machines': []
        }
        log_structured('WARNING', 'empty_subscriptions_default', {
            'connection_id': connection_id[:8] + '...',
            'default_applied': True
        })
    
    # Store connection in DynamoDB with circuit breaker
    current_time = int(time.time())
    connection_item = {
        'connectionId': connection_id,
        'connectedAt': current_time,
        'ttl': current_time + (24 * 60 * 60),  # Expire after 24 hours
        'subscriptions': subscriptions,
        'userId': query_params.get('userId', 'anonymous'),
        'userAgent': request_context.get('identity', {}).get('userAgent', 'unknown'),
        'sourceIp': request_context.get('identity', {}).get('sourceIp', 'unknown')
    }
    
    try:
        def store_connection():
            return connections_table.put_item(Item=connection_item)
        
        dynamodb_circuit_breaker.call(store_connection)
        
        log_structured('INFO', 'websocket_connect_success', {
            'connection_id': connection_id[:8] + '...',
            'subscriptions': {k: len(v) for k, v in subscriptions.items()},
            'user_id': connection_item['userId']
        })
        
        # Send connection metrics
        send_metric('WebSocketConnection', 1, dimensions={
            'Status': 'Connected',
            'UserType': 'Anonymous' if connection_item['userId'] == 'anonymous' else 'Identified'
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Connected successfully',
                'connectionId': connection_id,
                'subscriptions': subscriptions,
                'ttl': connection_item['ttl']
            })
        }
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        log_structured('ERROR', 'websocket_connect_db_error', {
            'connection_id': connection_id[:8] + '...',
            'error_code': error_code,
            'error_message': str(e)
        })
        
        send_metric('WebSocketConnectionError', 1, dimensions={
            'ErrorType': 'Database',
            'ErrorCode': error_code
        })
        
        raise DatabaseError(f"Failed to store connection: {error_code}")
        
    except Exception as e:
        log_structured('ERROR', 'websocket_connect_error', {
            'connection_id': connection_id[:8] + '...',
            'error_message': str(e)
        })
        
        send_metric('WebSocketConnectionError', 1, dimensions={
            'ErrorType': 'Unknown'
        })
        
        raise