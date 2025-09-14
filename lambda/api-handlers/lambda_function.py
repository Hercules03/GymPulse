import json
import boto3
import os
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
current_state_table = dynamodb.Table('gym-pulse-current-state')
aggregates_table = dynamodb.Table('gym-pulse-aggregates')

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
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept',
            'Access-Control-Max-Age': '86400'
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
        elif path.startswith('/machines/') and '/history' in path and http_method == 'GET':
            return handle_machine_history_request(event, context, cors_headers)
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
        # Get current machine states (for live status)
        response = current_state_table.scan()
        live_machines = {machine['machineId']: machine for machine in response['Items']}
        
        # Complete machine configuration from simulator config
        machine_config = {
            'hk-central': {
                'machines': [
                    {'machineId': 'leg-press-01', 'name': 'Leg Press Machine 1', 'category': 'legs', 'type': 'leg-press'},
                    {'machineId': 'leg-press-02', 'name': 'Leg Press Machine 2', 'category': 'legs', 'type': 'leg-press'},
                    {'machineId': 'squat-rack-01', 'name': 'Squat Rack 1', 'category': 'legs', 'type': 'squat-rack'},
                    {'machineId': 'calf-raise-01', 'name': 'Calf Raise Machine 1', 'category': 'legs', 'type': 'calf-raise'},
                    {'machineId': 'bench-press-01', 'name': 'Bench Press 1', 'category': 'chest', 'type': 'bench-press'},
                    {'machineId': 'bench-press-02', 'name': 'Bench Press 2', 'category': 'chest', 'type': 'bench-press'},
                    {'machineId': 'chest-fly-01', 'name': 'Chest Fly Machine 1', 'category': 'chest', 'type': 'chest-fly'},
                    {'machineId': 'lat-pulldown-01', 'name': 'Lat Pulldown 1', 'category': 'back', 'type': 'lat-pulldown'},
                    {'machineId': 'rowing-01', 'name': 'Rowing Machine 1', 'category': 'back', 'type': 'rowing'},
                    {'machineId': 'pull-up-01', 'name': 'Pull-up Station 1', 'category': 'back', 'type': 'pull-up'}
                ]
            },
            'hk-causeway': {
                'machines': [
                    {'machineId': 'leg-press-03', 'name': 'Leg Press Machine 3', 'category': 'legs', 'type': 'leg-press'},
                    {'machineId': 'squat-rack-02', 'name': 'Squat Rack 2', 'category': 'legs', 'type': 'squat-rack'},
                    {'machineId': 'leg-curl-01', 'name': 'Leg Curl Machine 1', 'category': 'legs', 'type': 'leg-curl'},
                    {'machineId': 'bench-press-03', 'name': 'Bench Press 3', 'category': 'chest', 'type': 'bench-press'},
                    {'machineId': 'incline-press-01', 'name': 'Incline Press 1', 'category': 'chest', 'type': 'incline-press'},
                    {'machineId': 'dips-01', 'name': 'Dips Station 1', 'category': 'chest', 'type': 'dips'},
                    {'machineId': 'lat-pulldown-02', 'name': 'Lat Pulldown 2', 'category': 'back', 'type': 'lat-pulldown'},
                    {'machineId': 'rowing-02', 'name': 'Rowing Machine 2', 'category': 'back', 'type': 'rowing'},
                    {'machineId': 't-bar-row-01', 'name': 'T-Bar Row 1', 'category': 'back', 'type': 't-bar-row'}
                ]
            }
        }
        
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
        
        # Count machines by branch and category using complete configuration
        for branch_id in branches.keys():
            categories = {'legs': {'free': 0, 'total': 0}, 
                         'chest': {'free': 0, 'total': 0}, 
                         'back': {'free': 0, 'total': 0}}
            
            # Use configured machines instead of only live machines
            if branch_id in machine_config:
                for machine_def in machine_config[branch_id]['machines']:
                    machine_id = machine_def['machineId']
                    category = machine_def['category']
                    
                    if category in categories:
                        categories[category]['total'] += 1
                        
                        # Check if machine is live and get its status
                        live_machine = live_machines.get(machine_id)
                        if live_machine and live_machine.get('status') == 'free':
                            categories[category]['free'] += 1
                        elif live_machine and live_machine.get('status') == 'occupied':
                            # Occupied - don't count as free
                            pass  
                        else:
                            # Machine not connected yet - assume available
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
        
        # Get current machine states (for live status)
        response = current_state_table.scan()
        live_machines = {machine['machineId']: machine for machine in response['Items']}
        
        # Complete machine configuration (same as in branches API)
        machine_config = {
            'hk-central': {
                'machines': [
                    {'machineId': 'leg-press-01', 'name': 'Leg Press Machine 1', 'category': 'legs', 'type': 'leg-press'},
                    {'machineId': 'leg-press-02', 'name': 'Leg Press Machine 2', 'category': 'legs', 'type': 'leg-press'},
                    {'machineId': 'squat-rack-01', 'name': 'Squat Rack 1', 'category': 'legs', 'type': 'squat-rack'},
                    {'machineId': 'calf-raise-01', 'name': 'Calf Raise Machine 1', 'category': 'legs', 'type': 'calf-raise'},
                    {'machineId': 'bench-press-01', 'name': 'Bench Press 1', 'category': 'chest', 'type': 'bench-press'},
                    {'machineId': 'bench-press-02', 'name': 'Bench Press 2', 'category': 'chest', 'type': 'bench-press'},
                    {'machineId': 'chest-fly-01', 'name': 'Chest Fly Machine 1', 'category': 'chest', 'type': 'chest-fly'},
                    {'machineId': 'lat-pulldown-01', 'name': 'Lat Pulldown 1', 'category': 'back', 'type': 'lat-pulldown'},
                    {'machineId': 'rowing-01', 'name': 'Rowing Machine 1', 'category': 'back', 'type': 'rowing'},
                    {'machineId': 'pull-up-01', 'name': 'Pull-up Station 1', 'category': 'back', 'type': 'pull-up'}
                ]
            },
            'hk-causeway': {
                'machines': [
                    {'machineId': 'leg-press-03', 'name': 'Leg Press Machine 3', 'category': 'legs', 'type': 'leg-press'},
                    {'machineId': 'squat-rack-02', 'name': 'Squat Rack 2', 'category': 'legs', 'type': 'squat-rack'},
                    {'machineId': 'leg-curl-01', 'name': 'Leg Curl Machine 1', 'category': 'legs', 'type': 'leg-curl'},
                    {'machineId': 'bench-press-03', 'name': 'Bench Press 3', 'category': 'chest', 'type': 'bench-press'},
                    {'machineId': 'incline-press-01', 'name': 'Incline Press 1', 'category': 'chest', 'type': 'incline-press'},
                    {'machineId': 'dips-01', 'name': 'Dips Station 1', 'category': 'chest', 'type': 'dips'},
                    {'machineId': 'lat-pulldown-02', 'name': 'Lat Pulldown 2', 'category': 'back', 'type': 'lat-pulldown'},
                    {'machineId': 'rowing-02', 'name': 'Rowing Machine 2', 'category': 'back', 'type': 'rowing'},
                    {'machineId': 't-bar-row-01', 'name': 'T-Bar Row 1', 'category': 'back', 'type': 't-bar-row'}
                ]
            }
        }
        
        # Filter machines by branch and category from configuration
        machine_list = []
        if branch_id in machine_config:
            for machine_def in machine_config[branch_id]['machines']:
                if machine_def['category'] == category:
                    machine_id = machine_def['machineId']
                    live_machine = live_machines.get(machine_id)
                    
                    # Determine status
                    if live_machine:
                        status = live_machine.get('status', 'unknown')
                        last_update = live_machine.get('lastUpdate')
                    else:
                        # Machine not connected yet - show as available
                        status = 'free'
                        last_update = None
                    
                    machine_list.append({
                        'machineId': machine_id,
                        'name': machine_def['name'],
                        'status': status,
                        'lastUpdate': last_update,
                        'category': category,
                        'gymId': branch_id,
                        'type': machine_def['type'],
                        'alertEligible': status == 'occupied'
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

def handle_machine_history_request(event, context, cors_headers):
    """
    Handle GET /machines/{machineId}/history - return usage history for heatmap
    """
    import time
    from datetime import datetime, timedelta
    
    try:
        # Extract machine ID from path
        path = event.get('path', '')
        # Path format: /machines/{machineId}/history
        path_parts = path.split('/')
        if len(path_parts) >= 3:
            machine_id = path_parts[2]
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', **cors_headers},
                'body': json.dumps({'error': 'Missing machine ID'})
            }
        
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        range_param = query_params.get('range', '24h')
        
        print(f"Fetching history for machine: {machine_id}, range: {range_param}")
        
        # Get machine info from current state to find category and gymId
        machine_response = current_state_table.get_item(Key={'machineId': machine_id})
        if 'Item' not in machine_response:
            # If machine not found, return empty usage data
            print(f"Machine {machine_id} not found in current state")
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', **cors_headers},
                'body': json.dumps({'usageData': [], 'machineId': machine_id})
            }
        
        machine = machine_response['Item']
        gym_id = machine.get('gymId')
        category = machine.get('category')
        
        if not gym_id or not category:
            print(f"Missing gymId or category for machine {machine_id}")
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', **cors_headers},
                'body': json.dumps({'usageData': [], 'machineId': machine_id})
            }
        
        # Calculate time range (last 24 hours in 15-minute intervals)
        current_time = int(time.time())
        start_time = current_time - (24 * 60 * 60)  # 24 hours ago
        
        # Query aggregates table for this gym/category combination
        gym_category_key = f"{gym_id}_{category}"
        
        response = aggregates_table.query(
            KeyConditionExpression='gymId_category = :gck AND timestamp15min BETWEEN :start AND :end',
            ExpressionAttributeValues={
                ':gck': gym_category_key,
                ':start': start_time,
                ':end': current_time
            },
            ScanIndexForward=True  # Sort by timestamp ascending
        )
        
        aggregates = response.get('Items', [])
        print(f"Found {len(aggregates)} aggregate records for {gym_category_key}")
        
        # Convert aggregates to hourly usage data for heatmap
        usage_data = []
        
        # Group aggregates by hour
        hourly_data = {}
        for aggregate in aggregates:
            timestamp = int(aggregate['timestamp15min'])
            hour = datetime.fromtimestamp(timestamp).hour
            occupancy_ratio = float(aggregate.get('occupancyRatio', 0))
            
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(occupancy_ratio)
        
        # Create usage data for all 24 hours
        current_hour = datetime.now().hour
        
        # Use machine-specific seed for consistent patterns
        import hashlib
        machine_seed = int(hashlib.md5(machine_id.encode()).hexdigest()[:8], 16) % 1000
        
        for hour in range(24):
            if hour in hourly_data:
                # Average the occupancy ratios for this hour (already in percentage 0-100)
                avg_usage_percentage = sum(hourly_data[hour]) / len(hourly_data[hour])
            else:
                # No aggregated data yet - use Hong Kong 247 Fitness patterns with machine-specific variation
                import random
                random.seed(machine_seed + hour)  # Consistent seed per machine per hour
                
                # Base patterns from Hong Kong 247 Fitness analysis
                base_usage = 5.0  # Default low usage
                if 6 <= hour < 9:  # Morning rush (6-9 AM): 60% busy
                    base_usage = 60.0 + random.uniform(-10, 10)
                elif 12 <= hour < 14:  # Lunch peak (12-2 PM): 45% busy
                    base_usage = 45.0 + random.uniform(-8, 8)
                elif 18 <= hour < 22:  # Evening peak (6-10 PM): 85% busy  
                    base_usage = 85.0 + random.uniform(-5, 5)
                elif 10 <= hour < 18:  # Off-peak daytime (10 AM-6 PM): 25% busy
                    base_usage = 25.0 + random.uniform(-5, 10)
                elif hour >= 22 or hour < 6:  # Night (10 PM-6 AM): 12% busy
                    base_usage = 12.0 + random.uniform(-3, 8)
                
                # Equipment-specific multipliers
                equipment_multiplier = 1.0
                if 'bench-press' in machine_id:
                    equipment_multiplier = 1.4  # Most popular
                elif 'squat-rack' in machine_id:
                    equipment_multiplier = 1.3  # Second most popular
                elif 'leg-press' in machine_id:
                    equipment_multiplier = 1.2
                elif 'calf-raise' in machine_id or 'pull-up' in machine_id:
                    equipment_multiplier = 0.8  # Less popular
                
                avg_usage_percentage = min(95.0, max(5.0, base_usage * equipment_multiplier))
            
            usage_data.append({
                'hour': hour,
                'day_of_week': datetime.now().weekday(),
                'usage_percentage': round(avg_usage_percentage, 1),
                'timestamp': datetime.now().isoformat(),
                'predicted_free_time': int((100 - avg_usage_percentage) * 60 / 100) if avg_usage_percentage < 100 else 0
            })
        
        result = {
            'usageData': usage_data,
            'machineId': machine_id,
            'gymId': gym_id,
            'category': category,
            'dataPoints': len(aggregates),
            'timeRange': f"{range_param} ({len(aggregates)} 15-min intervals)"
        }
        
        print(f"Returning {len(usage_data)} hourly usage points")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps(result, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error in handle_machine_history_request: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps({'error': f'Failed to retrieve machine history: {str(e)}'})
        }

def decimal_default(obj):
    """
    JSON serializer for objects not serializable by default json code
    """
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError
