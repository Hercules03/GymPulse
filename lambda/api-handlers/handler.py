"""
API Handler for REST endpoints
Handles branches, machines, history, and alerts endpoints
"""
import json
import boto3
import os
from boto3.dynamodb.conditions import Key


dynamodb = boto3.resource('dynamodb')
current_state_table = dynamodb.Table(os.environ['CURRENT_STATE_TABLE'])
events_table = dynamodb.Table(os.environ['EVENTS_TABLE'])
aggregates_table = dynamodb.Table(os.environ['AGGREGATES_TABLE'])
alerts_table = dynamodb.Table(os.environ['ALERTS_TABLE'])


def lambda_handler(event, context):
    """
    Handle REST API requests
    """
    try:
        path = event.get('path', '')
        method = event.get('httpMethod', 'GET')
        path_parameters = event.get('pathParameters') or {}
        
        print(f"API request: {method} {path}")
        
        # Route requests based on path and method
        if path == '/branches' and method == 'GET':
            return get_branches()
        elif path.startswith('/branches/') and path.endswith('/machines') and method == 'GET':
            branch_id = path_parameters.get('id')
            category = path_parameters.get('category')
            return get_machines(branch_id, category)
        elif path.startswith('/machines/') and path.endswith('/history') and method == 'GET':
            machine_id = path_parameters.get('id')
            return get_machine_history(machine_id)
        elif path == '/alerts' and method == 'POST':
            return create_alert(event)
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        print(f"API handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }


def get_branches():
    """
    Return list of branches with availability counts
    """
    # Mock data for now - replace with DynamoDB query
    branches = [
        {
            'id': 'hk-central',
            'name': 'Central Branch',
            'coordinates': {'lat': 22.2819, 'lon': 114.1577},
            'categories': {
                'legs': {'free': 3, 'total': 8},
                'chest': {'free': 5, 'total': 10},
                'back': {'free': 2, 'total': 6}
            }
        },
        {
            'id': 'hk-causeway',
            'name': 'Causeway Bay Branch',
            'coordinates': {'lat': 22.2783, 'lon': 114.1747},
            'categories': {
                'legs': {'free': 1, 'total': 6},
                'chest': {'free': 8, 'total': 12},
                'back': {'free': 4, 'total': 8}
            }
        }
    ]
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'branches': branches})
    }


def get_machines(branch_id, category):
    """
    Return machines for a branch and category
    """
    # TODO: Query current_state_table for machines
    machines = []
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'machines': machines})
    }


def get_machine_history(machine_id):
    """
    Return 24-hour history for a machine
    """
    # TODO: Query events_table and aggregates_table
    history = []
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'history': history})
    }


def create_alert(event):
    """
    Create alert subscription
    """
    # TODO: Parse request body and create alert in alerts_table
    return {
        'statusCode': 201,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Alert created successfully'})
    }