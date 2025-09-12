import json
import boto3
import os
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
current_state_table = dynamodb.Table('gym-pulse-current-state')

def lambda_handler(event, context):
    """
    AWS Lambda handler for GymPulse API requests
    """
    try:
        # Debug: Print the entire event
        print("=== DEBUG EVENT ===")
        print(f"Full event: {json.dumps(event)}")
        print(f"HTTP Method: {event.get('httpMethod')}")
        print(f"Path: {event.get('path')}")
        print(f"Resource: {event.get('resource')}")
        print("===================")
        
        # Extract HTTP method and path
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        print(f"API Request: {http_method} {path}")
        
        # Add CORS headers to all responses
        cors_headers = {
            'Access-Control-Allow-Origin': 'http://localhost:3000',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
        
        # Handle CORS preflight requests
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        # Route requests
        if path == '/branches' and http_method == 'GET':
            return handle_branches_request(event, context, cors_headers)
        elif path.startswith('/branches/') and path.endswith('/machines') and http_method == 'GET':
            return handle_machines_request(event, context, cors_headers)
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    **cors_headers
                },
                'body': json.dumps({'error': 'Endpoint not found'})
            }
    
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        # Create default CORS headers in case of early exception
        cors_headers = {
            'Access-Control-Allow-Origin': 'http://localhost:3000',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps({'error': 'Internal server error'})
        }

def handle_branches_request(event, context, cors_headers):
    """
    Handle GET /branches - return all branches with machine counts
    """
    try:
        # Scan current state table for all machines
        response = current_state_table.scan()
        machines = response['Items']
        
        # Branch configuration
        branches = {
            'hk-central': {
                'id': 'hk-central',
                'name': 'Central Branch',
                'coordinates': {'lat': 22.2819, 'lon': 114.1577}
            },
            'hk-causeway': {
                'id': 'hk-causeway', 
                'name': 'Causeway Bay Branch',
                'coordinates': {'lat': 22.2783, 'lon': 114.1747}
            }
        }
        
        # Count machines by branch and category
        for branch_id in branches.keys():
            categories = {'legs': {'free': 0, 'total': 0}, 
                         'chest': {'free': 0, 'total': 0}, 
                         'back': {'free': 0, 'total': 0}}
            
            branch_machines = [m for m in machines if m.get('gymId') == branch_id]
            
            for machine in branch_machines:
                category = machine.get('category', 'other')
                if category in categories:
                    categories[category]['total'] += 1
                    if machine.get('status') == 'free':
                        categories[category]['free'] += 1
            
            branches[branch_id]['categories'] = categories
        
        result = list(branches.values())
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps(result, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error in handle_branches_request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps({'error': f'Failed to retrieve branches: {str(e)}'})
        }

def handle_machines_request(event, context, cors_headers):
    """
    Handle GET /branches/{branchId}/categories/{category}/machines
    """
    try:
        # Extract path parameters
        path_params = event.get('pathParameters') or {}
        branch_id = path_params.get('branchId')
        category = path_params.get('category')
        
        # Scan for machines matching branch and category
        response = current_state_table.scan(
            FilterExpression='gymId = :gym_id AND category = :cat',
            ExpressionAttributeValues={
                ':gym_id': branch_id,
                ':cat': category
            }
        )
        
        machines = response['Items']
        
        # Format machine data
        machine_list = []
        for machine in machines:
            machine_list.append({
                'machineId': machine.get('machineId'),
                'name': machine.get('name', machine.get('machineId')),
                'status': machine.get('status'),
                'lastUpdate': machine.get('lastUpdate'),
                'category': machine.get('category'),
                'gymId': machine.get('gymId'),
                'alertEligible': machine.get('status') == 'occupied'
            })
        
        result = {
            'machines': machine_list,
            'branchId': branch_id,
            'category': category,
            'totalCount': len(machine_list),
            'freeCount': len([m for m in machine_list if m['status'] == 'free']),
            'occupiedCount': len([m for m in machine_list if m['status'] == 'occupied'])
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps(result, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error in handle_machines_request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps({'error': f'Failed to retrieve machines: {str(e)}'})
        }

def decimal_default(obj):
    """
    JSON serializer for objects not serializable by default json code
    """
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError
