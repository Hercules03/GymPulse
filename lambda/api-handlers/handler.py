"""
API Handler for REST endpoints with comprehensive error handling and monitoring
Handles branches, machines, history, and alerts endpoints
"""
import json
import boto3
import os
import sys
import time
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Add utils directory to Python path
sys.path.append('/opt/python/lib/python3.9/site-packages')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.error_handler import (
    api_handler, log_structured, send_metric, 
    ValidationError, ResourceNotFoundError, DatabaseError,
    validate_required_fields, safe_json_parse, dynamodb_circuit_breaker
)
from utils.cache_manager import (
    cached, branch_cache, machine_cache, aggregates_cache,
    CacheInvalidationStrategy, cache_metrics, db_pool
)

# Initialize AWS resources with connection pooling
try:
    current_state_table = db_pool.get_table(os.environ['CURRENT_STATE_TABLE'])
    events_table = db_pool.get_table(os.environ['EVENTS_TABLE'])
    aggregates_table = db_pool.get_table(os.environ['AGGREGATES_TABLE'])
    alerts_table = db_pool.get_table(os.environ['ALERTS_TABLE'])
except Exception as e:
    log_structured('ERROR', 'initialization_error', {
        'error': str(e),
        'missing_env_vars': [var for var in ['CURRENT_STATE_TABLE', 'EVENTS_TABLE', 'AGGREGATES_TABLE', 'ALERTS_TABLE'] 
                            if var not in os.environ]
    })
    raise


@api_handler
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
        elif path == '/alerts' and method == 'GET':
            return list_alerts(event)
        elif path.startswith('/alerts/') and method == 'DELETE':
            alert_id = path_parameters.get('alertId')
            return cancel_alert(alert_id, event)
        elif path.startswith('/alerts/') and method == 'PUT':
            alert_id = path_parameters.get('alertId')
            return update_alert(alert_id, event)
        elif path == '/health' and method == 'GET':
            return health_check()
        elif path.startswith('/forecast/'):
            # Delegate to forecast handler
            from forecast import lambda_handler as forecast_handler
            return forecast_handler(event, context)
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


@cached(ttl=30, cache_instance=branch_cache)  # Cache for 30 seconds
def get_branches():
    """
    Return list of branches with availability counts
    Query current_state table for real-time machine availability
    """
    # Branch definitions (could be moved to environment variables)
    branch_configs = [
        {
            'id': 'hk-central',
            'name': 'Central Branch',
            'coordinates': {'lat': 22.2819, 'lon': 114.1577}
        },
        {
            'id': 'hk-causeway', 
            'name': 'Causeway Bay Branch',
            'coordinates': {'lat': 22.2783, 'lon': 114.1747}
        }
    ]
    
    categories = ['legs', 'chest', 'back']
    branches = []
    query_errors = []
    
    for branch_config in branch_configs:
        branch_id = branch_config['id']
        branch_data = {
            'id': branch_id,
            'name': branch_config['name'],
            'coordinates': branch_config['coordinates'],
            'categories': {}
        }
        
        # Query current state for each category with circuit breaker
        for category in categories:
            try:
                def query_category():
                    return current_state_table.scan(
                        FilterExpression='gymId = :gym_id AND category = :category',
                        ExpressionAttributeValues={
                            ':gym_id': branch_id,
                            ':category': category
                        }
                    )
                
                response = dynamodb_circuit_breaker.call(query_category)
                machines = response.get('Items', [])
                total_count = len(machines)
                free_count = sum(1 for m in machines if m.get('status') == 'free')
                
                branch_data['categories'][category] = {
                    'free': free_count,
                    'total': total_count
                }
                
                # Log successful query
                log_structured('DEBUG', 'category_query_success', {
                    'branch_id': branch_id,
                    'category': category,
                    'total_machines': total_count,
                    'free_machines': free_count
                })
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                query_errors.append(f"{branch_id}/{category}: {error_code}")
                
                log_structured('ERROR', 'dynamodb_query_error', {
                    'branch_id': branch_id,
                    'category': category,
                    'error_code': error_code,
                    'error_message': str(e)
                })
                
                # Send error metric
                send_metric('DatabaseQueryError', 1, dimensions={
                    'Table': 'current_state',
                    'Operation': 'scan',
                    'ErrorCode': error_code
                })
                
                # Fallback to zero counts
                branch_data['categories'][category] = {'free': 0, 'total': 0}
                
            except Exception as e:
                query_errors.append(f"{branch_id}/{category}: {str(e)}")
                log_structured('ERROR', 'category_query_exception', {
                    'branch_id': branch_id,
                    'category': category,
                    'error_message': str(e)
                })
                
                # Fallback to zero counts
                branch_data['categories'][category] = {'free': 0, 'total': 0}
        
        branches.append(branch_data)
    
    # Send success metric
    send_metric('BranchesRequested', len(branches))
    
    response_body = {'branches': branches}
    if query_errors:
        response_body['warnings'] = f"Some data may be stale due to query errors: {len(query_errors)} errors"
        log_structured('WARNING', 'partial_branch_data', {
            'total_errors': len(query_errors),
            'error_details': query_errors
        })
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Cache-Control': 'max-age=30'  # Cache for 30 seconds
        },
        'body': json.dumps(response_body)
    }


@cached(ttl=15, cache_instance=machine_cache)  # Cache for 15 seconds
def get_machines(branch_id, category):
    """
    Return machines for a branch and category with current status and metadata
    """
    try:
        if not branch_id or not category:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Branch ID and category are required'})
            }
        
        # Query current_state table for machines in this branch and category
        response = current_state_table.scan(
            FilterExpression='gymId = :gym_id AND category = :category',
            ExpressionAttributeValues={
                ':gym_id': branch_id,
                ':category': category
            }
        )
        
        machines = []
        for item in response.get('Items', []):
            machine = {
                'machineId': item.get('machineId'),
                'name': item.get('name', item.get('machineId', '').replace('-', ' ').title()),
                'status': item.get('status', 'unknown'),
                'lastUpdate': item.get('lastUpdate'),
                'lastChange': item.get('lastChange'),
                'category': item.get('category'),
                'gymId': item.get('gymId'),
                'coordinates': item.get('coordinates', {}),
                'alertEligible': item.get('status') == 'occupied'  # Can only set alerts for occupied machines
            }
            
            # Add forecast data for this machine
            try:
                forecast = calculate_simple_forecast([], machine['machineId'])
                machine['forecast'] = forecast
            except Exception as e:
                print(f"Failed to get forecast for {machine['machineId']}: {str(e)}")
                machine['forecast'] = {
                    'likelyFreeIn30m': False,
                    'classification': 'error',
                    'display_text': 'Forecast unavailable',
                    'show_to_user': False
                }
            
            machines.append(machine)
        
        # Sort machines by ID for consistent ordering
        machines.sort(key=lambda x: x.get('machineId', ''))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({
                'machines': machines,
                'branchId': branch_id,
                'category': category,
                'totalCount': len(machines),
                'freeCount': sum(1 for m in machines if m['status'] == 'free'),
                'occupiedCount': sum(1 for m in machines if m['status'] == 'occupied')
            })
        }
        
    except Exception as e:
        print(f"Error in get_machines for branch {branch_id}, category {category}: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Failed to fetch machines'})
        }


@cached(ttl=300, cache_instance=aggregates_cache)  # Cache for 5 minutes
def get_machine_history(machine_id):
    """
    Return 24-hour history for a machine from aggregates table
    Query 15-minute bins for heatmap rendering
    """
    import time
    from datetime import datetime, timedelta
    
    try:
        if not machine_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Machine ID is required'})
            }
        
        # Calculate 24-hour window
        end_time = int(time.time())
        start_time = end_time - (24 * 60 * 60)  # 24 hours ago
        
        # Query aggregates table for 15-minute bins
        try:
            response = aggregates_table.query(
                KeyConditionExpression=Key('machineId').eq(machine_id) & 
                                     Key('timestamp15min').between(start_time, end_time)
            )
            
            history_data = response.get('Items', [])
            
        except Exception as e:
            print(f"Error querying aggregates for machine {machine_id}: {str(e)}")
            # Fallback: try events table for recent data
            try:
                response = events_table.query(
                    KeyConditionExpression=Key('machineId').eq(machine_id) & 
                                         Key('timestamp').between(start_time, end_time)
                )
                # Convert events to simple aggregated format
                events = response.get('Items', [])
                history_data = process_events_to_history(events)
            except Exception as e2:
                print(f"Fallback query also failed: {str(e2)}")
                history_data = []
        
        # Format history for frontend consumption
        history_bins = []
        for item in history_data:
            bin_data = {
                'timestamp': item.get('timestamp15min') or item.get('timestamp'),
                'occupancyRatio': item.get('occupancyRatio', 0),
                'freeCount': item.get('freeCount', 0),
                'totalCount': item.get('totalCount', 1),
                'status': item.get('status', 'unknown')
            }
            history_bins.append(bin_data)
        
        # Sort by timestamp
        history_bins.sort(key=lambda x: x['timestamp'])
        
        # Query current state for real-time status
        current_status = None
        try:
            response = current_state_table.get_item(Key={'machineId': machine_id})
            if 'Item' in response:
                current_item = response['Item']
                current_status = {
                    'status': current_item.get('status', 'unknown'),
                    'lastUpdate': current_item.get('lastUpdate', 0),
                    'gymId': current_item.get('gymId', ''),
                    'category': current_item.get('category', ''),
                    'name': current_item.get('name', machine_id),
                    'alertEligible': current_item.get('status') == 'occupied'
                }
        except Exception as e:
            print(f"Error querying current state for machine {machine_id}: {str(e)}")
            # Provide fallback current status
            current_status = {
                'status': 'unknown',
                'lastUpdate': 0,
                'gymId': '',
                'category': '',
                'name': machine_id,
                'alertEligible': False
            }
        
        # Calculate simple forecast for "likely free in 30m"
        forecast = calculate_simple_forecast(history_bins, machine_id)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({
                'machineId': machine_id,
                'currentStatus': current_status,  # Add current status information
                'history': history_bins,
                'timeRange': {
                    'start': start_time,
                    'end': end_time,
                    'duration': '24h'
                },
                'forecast': forecast,
                'totalBins': len(history_bins)
            })
        }
        
    except Exception as e:
        print(f"Error in get_machine_history for machine {machine_id}: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Failed to fetch machine history'})
        }


def process_events_to_history(events):
    """
    Convert events to aggregated 15-minute bins for history display
    """
    if not events:
        return []
    
    # Group events by 15-minute bins
    bins = {}
    for event in events:
        timestamp = event.get('timestamp', 0)
        bin_timestamp = (timestamp // 900) * 900  # Round to 15-minute intervals
        
        if bin_timestamp not in bins:
            bins[bin_timestamp] = {
                'timestamp15min': bin_timestamp,
                'events': [],
                'occupancyRatio': 0,
                'freeCount': 0,
                'totalCount': 1
            }
        
        bins[bin_timestamp]['events'].append(event)
        
        # Simple calculation - just use last status in bin
        if event.get('status') == 'free':
            bins[bin_timestamp]['freeCount'] = 1
            bins[bin_timestamp]['occupancyRatio'] = 0
        else:
            bins[bin_timestamp]['freeCount'] = 0
            bins[bin_timestamp]['occupancyRatio'] = 100
    
    return list(bins.values())


def calculate_simple_forecast(history_bins, machine_id):
    """
    Calculate forecast for "likely free in 30m" using enhanced seasonality model
    Falls back to simple heuristic if enhanced forecasting unavailable
    """
    try:
        # Try to use enhanced forecasting
        from .forecast_integration import get_enhanced_forecast
        enhanced_forecast = get_enhanced_forecast(machine_id)
        
        # Convert enhanced format to legacy format for compatibility
        return {
            'likelyFreeIn30m': enhanced_forecast.get('likelyFreeIn30m', False),
            'classification': enhanced_forecast.get('classification', 'unavailable'),
            'display_text': enhanced_forecast.get('display_text', ''),
            'color': enhanced_forecast.get('color', 'gray'),
            'confidence': enhanced_forecast.get('confidence', 'low'),
            'confidence_text': enhanced_forecast.get('confidence_text', ''),
            'show_to_user': enhanced_forecast.get('show_to_user', False),
            'reason': enhanced_forecast.get('reason', 'Forecast based on historical patterns'),
            'metadata': enhanced_forecast.get('metadata', {})
        }
    except ImportError:
        # Fall back to simple heuristic
        return calculate_simple_forecast_fallback(history_bins, machine_id)
    except Exception as e:
        print(f"Enhanced forecast failed for {machine_id}: {str(e)}")
        return calculate_simple_forecast_fallback(history_bins, machine_id)


def calculate_simple_forecast_fallback(history_bins, machine_id):
    """
    Fallback forecast calculation using simple heuristics
    """
    if not history_bins or len(history_bins) < 4:
        return {
            'likelyFreeIn30m': False,
            'classification': 'insufficient_data',
            'display_text': 'Insufficient data',
            'color': 'gray',
            'confidence': 'low',
            'show_to_user': False,
            'reason': 'Insufficient historical data (need at least 1 hour)',
            'metadata': {'sample_size': len(history_bins)}
        }
    
    # Look at recent trend (last 4 bins = 1 hour)
    recent_bins = history_bins[-4:]
    free_ratio = sum(1 for bin in recent_bins if bin['occupancyRatio'] < 50) / len(recent_bins)
    
    # Simple heuristic
    likely_free = free_ratio > 0.6
    confidence = 'high' if free_ratio > 0.8 or free_ratio < 0.2 else 'medium'
    
    if likely_free:
        classification = 'likely_free'
        display_text = 'Likely free in 30m'
        color = 'green'
    elif free_ratio > 0.3:
        classification = 'possibly_free'
        display_text = 'Possibly free in 30m'
        color = 'yellow'
    else:
        classification = 'unlikely_free'
        display_text = 'Unlikely free in 30m'
        color = 'red'
    
    return {
        'likelyFreeIn30m': likely_free,
        'classification': classification,
        'display_text': display_text,
        'color': color,
        'confidence': confidence,
        'show_to_user': True,
        'reason': f"Based on recent {len(recent_bins)}h pattern ({free_ratio:.0%} free time)",
        'metadata': {
            'free_ratio': free_ratio,
            'sample_size': len(recent_bins),
            'reliable': len(recent_bins) >= 4
        }
    }


def create_alert(event):
    """
    Create alert subscription for "notify when free" functionality
    """
    import uuid
    
    # Parse and validate request body
    body = safe_json_parse(event.get('body', ''))
    
    # Validate required fields
    validate_required_fields(body, ['machineId'], {
        'machineId': str
    })
    
    machine_id = body['machineId']
    user_id = body.get('userId', 'anonymous')  # Default for demo
    
    # Validate machine_id format (basic check)
    if not machine_id or len(machine_id) < 3:
        raise ValidationError("machineId must be at least 3 characters long")
        
        # Validate machine exists and is currently occupied
        try:
            machine_response = current_state_table.get_item(
                Key={'machineId': machine_id}
            )
            
            if 'Item' not in machine_response:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Machine not found'})
                }
            
            machine = machine_response['Item']
            if machine.get('status') != 'occupied':
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'Can only set alerts for occupied machines',
                        'currentStatus': machine.get('status')
                    })
                }
        
        except Exception as e:
            print(f"Error validating machine {machine_id}: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Failed to validate machine'})
            }
        
        # Parse quiet hours configuration
        quiet_hours = body.get('quietHours', {})
        if not quiet_hours:
            quiet_hours = {'start': 22, 'end': 7}  # Default 10 PM to 7 AM
        
        # Generate alert
        alert_id = str(uuid.uuid4())
        current_time = int(time.time())
        
        alert_item = {
            'alertId': alert_id,
            'userId': user_id,
            'machineId': machine_id,
            'active': True,
            'quietHours': quiet_hours,
            'createdAt': current_time,
            'expiresAt': current_time + (24 * 60 * 60),  # Expire after 24 hours
            'machineStatus': machine.get('status'),
            'gymId': machine.get('gymId'),
            'category': machine.get('category')
        }
        
        # Create alert in alerts table
        try:
            alerts_table.put_item(Item=alert_item)
            
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                },
                'body': json.dumps({
                    'alertId': alert_id,
                    'message': 'Alert created successfully',
                    'machineId': machine_id,
                    'userId': user_id,
                    'quietHours': quiet_hours,
                    'expiresAt': alert_item['expiresAt'],
                    'estimatedNotification': 'You will be notified when this machine becomes free'
                })
            }
            
        except Exception as e:
            print(f"Error creating alert: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Failed to create alert'})
            }
            
    except Exception as e:
        print(f"Error in create_alert: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }


def list_alerts(event):
    """
    List active alerts for a user
    """
    try:
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('userId', 'anonymous')
        
        print(f"Listing alerts for user: {user_id}")
        
        # Query alerts for user
        response = alerts_table.query(
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        
        alerts = response.get('Items', [])
        active_alerts = []
        
        current_time = int(time.time())
        
        for alert in alerts:
            # Only return active, non-expired alerts
            expires_at = alert.get('expiresAt', 0)
            if alert.get('active', False) and (expires_at == 0 or current_time < expires_at):
                active_alerts.append({
                    'alertId': alert.get('alertId'),
                    'machineId': alert.get('machineId'),
                    'gymId': alert.get('gymId'),
                    'category': alert.get('category'),
                    'createdAt': alert.get('createdAt'),
                    'expiresAt': alert.get('expiresAt'),
                    'quietHours': alert.get('quietHours', {}),
                    'machineName': alert.get('machineId', '').replace('-', ' ').title()
                })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({
                'userId': user_id,
                'alerts': active_alerts,
                'count': len(active_alerts)
            })
        }
        
    except Exception as e:
        print(f"Error listing alerts: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Failed to list alerts'})
        }


def cancel_alert(alert_id, event):
    """
    Cancel a specific alert
    """
    try:
        if not alert_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Alert ID is required'})
            }
        
        # Find alert by scanning (temporary solution)
        response = alerts_table.scan(
            FilterExpression='alertId = :alert_id',
            ExpressionAttributeValues={':alert_id': alert_id}
        )
        
        alerts = response.get('Items', [])
        if not alerts:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Alert not found'})
            }
        
        alert = alerts[0]
        
        # Deactivate the alert
        alerts_table.update_item(
            Key={
                'userId': alert['userId'],
                'machineId': alert['machineId']
            },
            UpdateExpression='SET #active = :active, cancelledAt = :cancelled',
            ExpressionAttributeNames={'#active': 'active'},
            ExpressionAttributeValues={
                ':active': False,
                ':cancelled': int(time.time())
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({
                'message': 'Alert cancelled successfully',
                'alertId': alert_id
            })
        }
        
    except Exception as e:
        print(f"Error cancelling alert: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Failed to cancel alert'})
        }


def update_alert(alert_id, event):
    """
    Update alert settings
    """
    try:
        if not alert_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Alert ID is required'})
            }
        
        # Parse request body
        try:
            body = json.loads(event['body']) if event.get('body') else {}
        except (json.JSONDecodeError, TypeError):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid JSON in request body'})
            }
        
        quiet_hours = body.get('quietHours')
        if not quiet_hours:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'quietHours is required'})
            }
        
        # Find and update alert
        response = alerts_table.scan(
            FilterExpression='alertId = :alert_id',
            ExpressionAttributeValues={':alert_id': alert_id}
        )
        
        alerts = response.get('Items', [])
        if not alerts:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Alert not found'})
            }
        
        alert = alerts[0]
        
        # Update the alert
        alerts_table.update_item(
            Key={
                'userId': alert['userId'],
                'machineId': alert['machineId']
            },
            UpdateExpression='SET quietHours = :quiet_hours, updatedAt = :updated',
            ExpressionAttributeValues={
                ':quiet_hours': quiet_hours,
                ':updated': int(time.time())
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({
                'message': 'Alert updated successfully',
                'alertId': alert_id,
                'quietHours': quiet_hours
            })
        }
        
    except Exception as e:
        print(f"Error updating alert: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Failed to update alert'})
        }


def health_check():
    """
    Health check endpoint
    """
    import time
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
        },
        'body': json.dumps({
            'status': 'healthy',
            'service': 'gym-pulse-api',
            'timestamp': int(time.time()),
            'version': '1.0.0'
        })
    }