"""
IoT Message Ingest Handler with Performance Optimization
Processes MQTT messages and updates DynamoDB tables
Includes cache invalidation and performance monitoring
"""
import json
import boto3
import os
import sys
import traceback
from datetime import datetime
from decimal import Decimal

# Add utils directory to Python path
sys.path.append('/opt/python/lib/python3.9/site-packages')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.cache_manager import CacheInvalidationStrategy, cache_metrics, db_pool
    from utils.error_handler import log_structured, send_metric
    CACHE_AVAILABLE = True
except ImportError:
    print("Cache management utilities not available, continuing without caching")
    CACHE_AVAILABLE = False


# Initialize DynamoDB resource and Lambda client
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Use the existing table names from the deployed environment
try:
    machine_state_table = dynamodb.Table(os.environ.get('MACHINE_STATE_TABLE', 'gym-machine-states'))  # Time-series table
    aggregates_table = dynamodb.Table(os.environ.get('AGGREGATES_TABLE', 'gym-aggregates'))
    # Try the current state table for latest machine status
    current_state_table = dynamodb.Table('gym-pulse-current-state')
    # Also try the new table names if they exist
    events_table = dynamodb.Table(os.environ.get('EVENTS_TABLE', 'gym-pulse-events'))
    alerts_table = dynamodb.Table(os.environ.get('ALERTS_TABLE', 'gym-pulse-alerts'))
    print("Initialized all DynamoDB tables successfully")
except Exception as e:
    print(f"Warning: Could not initialize all tables: {e}")


def detect_transition(previous_state, new_state):
    """
    Detect state transitions between machine states
    Returns: 'initialized', 'freed', 'occupied', or 'no_change'
    """
    if previous_state is None:
        return 'initialized'
    elif previous_state != new_state:
        return 'freed' if new_state == 'free' else 'occupied'
    else:
        return 'no_change'


def broadcast_to_websocket_clients(message):
    """
    Broadcast real-time update to WebSocket clients via broadcast Lambda
    """
    try:
        print(f"Broadcasting to WebSocket clients: {json.dumps(message)}")
        
        # Call the WebSocket broadcast Lambda function
        broadcast_function_name = os.environ.get('WEBSOCKET_BROADCAST_FUNCTION', 'gym-pulse-websocket-broadcast')
        
        payload = {
            'machineUpdate': message
        }
        
        try:
            response = lambda_client.invoke(
                FunctionName=broadcast_function_name,
                InvocationType='Event',  # Asynchronous invocation
                Payload=json.dumps(payload)
            )
            
            print(f"Successfully invoked broadcast function: {response['StatusCode']}")
            return True
            
        except Exception as e:
            print(f"Error invoking broadcast function: {str(e)}")
            # Don't fail the main process if WebSocket broadcast fails
            return False
        
    except Exception as e:
        print(f"Error in broadcast_to_websocket_clients: {str(e)}")
        return False


def is_in_quiet_hours(quiet_hours_config, current_timestamp):
    """
    Check if current time falls within quiet hours
    """
    try:
        current_time = datetime.fromtimestamp(current_timestamp)
        current_hour = current_time.hour
        
        start = quiet_hours_config.get('start', 22)  # 10 PM default
        end = quiet_hours_config.get('end', 7)       # 7 AM default
        
        if start > end:  # Spans midnight (e.g., 10 PM to 7 AM)
            return current_hour >= start or current_hour < end
        else:
            return start <= current_hour < end
    except Exception as e:
        print(f"Error checking quiet hours: {e}")
        return False  # Default to allowing alerts


def process_alerts_for_machine(machine_id, status, timestamp):
    """
    Process alerts for machine state changes to 'free'
    """
    try:
        print(f"Processing alerts for machine {machine_id} status change to {status}")
        
        # Query active alerts for this machine using scan (temporary until GSI permissions are fixed)
        response = alerts_table.scan(
            FilterExpression='machineId = :machineId AND #active = :active',
            ExpressionAttributeNames={
                '#active': 'active'
            },
            ExpressionAttributeValues={
                ':machineId': machine_id,
                ':active': True
            }
        )
        
        alerts = response.get('Items', [])
        print(f"Found {len(alerts)} active alerts for machine {machine_id}")
        
        for alert in alerts:
            try:
                # Check quiet hours configuration
                quiet_hours = alert.get('quietHours', {})
                if is_in_quiet_hours(quiet_hours, timestamp):
                    print(f"Alert {alert.get('alertId', 'unknown')} suppressed due to quiet hours")
                    continue
                
                # Fire the alert
                fire_alert(alert, machine_id, status, timestamp)
                
                # Mark alert as fired and deactivate
                deactivate_alert(alert)
                
            except Exception as e:
                print(f"Error processing individual alert {alert.get('alertId', 'unknown')}: {e}")
        
    except Exception as e:
        print(f"Error querying alerts for machine {machine_id}: {e}")


def fire_alert(alert, machine_id, status, timestamp):
    """
    Fire an alert notification via WebSocket and other channels
    """
    try:
        user_id = alert.get('userId', 'unknown')
        alert_id = alert.get('alertId', 'unknown')
        gym_id = alert.get('gymId', 'unknown')
        category = alert.get('category', 'unknown')
        
        # Prepare alert notification message
        alert_message = {
            'type': 'machine_alert',
            'alertId': alert_id,
            'userId': user_id,
            'machineId': machine_id,
            'gymId': gym_id,
            'category': category,
            'status': status,
            'timestamp': int(timestamp),
            'message': f"Machine {machine_id.replace('-', ' ').title()} is now {status}!",
            'firedAt': int(timestamp),
            'notificationTitle': f"Equipment Available! 🎉",
            'notificationBody': f"{machine_id.replace('-', ' ').title()} in {gym_id} ({category}) is now free!"
        }
        
        print(f"Firing alert {alert_id} for user {user_id}: {json.dumps(alert_message)}")
        
        # Send WebSocket notification to user if connected
        try:
            broadcast_alert_to_user(alert_message, user_id)
        except Exception as e:
            print(f"Error sending WebSocket alert to user {user_id}: {str(e)}")
        
        # TODO: Send push notification via SNS/mobile when implemented
        # TODO: Send email notification when implemented
        # TODO: Send SMS notification when implemented
        
        return True
        
    except Exception as e:
        print(f"Error firing alert: {e}")
        return False


def broadcast_alert_to_user(alert_message, user_id):
    """
    Send alert notification via WebSocket broadcast function
    """
    try:
        broadcast_function_name = os.environ.get('WEBSOCKET_BROADCAST_FUNCTION', 'gym-pulse-websocket-broadcast')
        
        # Create a user-specific alert payload
        payload = {
            'userAlert': alert_message,
            'targetUserId': user_id
        }
        
        response = lambda_client.invoke(
            FunctionName=broadcast_function_name,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(payload)
        )
        
        print(f"Successfully sent alert to user {user_id} via WebSocket: {response['StatusCode']}")
        return True
        
    except Exception as e:
        print(f"Error broadcasting alert to user {user_id}: {str(e)}")
        return False


def deactivate_alert(alert):
    """
    Deactivate an alert after it has been fired
    """
    try:
        alerts_table.update_item(
            Key={
                'userId': alert['userId'],
                'machineId': alert['machineId']
            },
            UpdateExpression='SET #active = :active, firedAt = :firedAt',
            ExpressionAttributeNames={
                '#active': 'active'
            },
            ExpressionAttributeValues={
                ':active': False,
                ':firedAt': int(datetime.now().timestamp())
            }
        )
        print(f"Deactivated alert for user {alert['userId']} on machine {alert['machineId']}")
        
    except Exception as e:
        print(f"Error deactivating alert: {e}")


def get_15min_window_start(timestamp):
    """
    Get the 15-minute window start time for aggregation
    """
    dt = datetime.fromtimestamp(timestamp)
    # Round down to nearest 15-minute boundary
    minute = (dt.minute // 15) * 15
    window_start = dt.replace(minute=minute, second=0, microsecond=0)
    return int(window_start.timestamp())


def update_15min_aggregates(machine_id, gym_id, category, timestamp):
    """
    Update 15-minute aggregation data for heatmaps and forecasting
    """
    try:
        window_start = get_15min_window_start(timestamp)
        window_end = window_start + (15 * 60)  # 15 minutes later
        
        print(f"Updating 15min aggregate for {machine_id} in window {window_start}-{window_end}")
        
        # Composite key for aggregates: gymId#category
        aggregate_key = f"{gym_id}#{category}"
        
        # Query events in the current 15-minute window
        occupancy_ratio = calculate_window_occupancy_ratio(machine_id, window_start, window_end)
        
        # Update or create aggregate record using existing gym-aggregates table schema (pk/sk)
        try:
            # Try to update existing aggregate
            response = aggregates_table.update_item(
                Key={
                    'pk': aggregate_key,  # Using existing pk field
                    'sk': f"window#{window_start}"  # Using existing sk field
                },
                UpdateExpression='SET occupancyRatio = :ratio, lastUpdated = :updated, machineCount = if_not_exists(machineCount, :zero) + :one, totalSamples = if_not_exists(totalSamples, :zero) + :one',
                ExpressionAttributeValues={
                    ':ratio': Decimal(str(occupancy_ratio)),
                    ':updated': int(timestamp),
                    ':zero': 0,
                    ':one': 1
                },
                ReturnValues='ALL_NEW'
            )
            print(f"Updated aggregate for {aggregate_key} at {window_start}: {occupancy_ratio}% occupancy")
            
        except Exception as e:
            print(f"Error updating aggregate, creating new: {e}")
            # Create new aggregate record
            aggregates_table.put_item(
                Item={
                    'pk': aggregate_key,  # Using existing pk field
                    'sk': f"window#{window_start}",  # Using existing sk field
                    'timestamp15min': window_start,
                    'occupancyRatio': Decimal(str(occupancy_ratio)),
                    'gymId': gym_id,
                    'category': category,
                    'machineCount': 1,
                    'totalSamples': 1,
                    'lastUpdated': int(timestamp),
                    'ttl': window_start + (90 * 24 * 3600)  # 90 days TTL
                }
            )
            print(f"Created new aggregate for {aggregate_key} at {window_start}: {occupancy_ratio}% occupancy")
        
    except Exception as e:
        print(f"Error in update_15min_aggregates: {e}")


def calculate_window_occupancy_ratio(machine_id, window_start, window_end):
    """
    Calculate occupancy ratio for a machine within a 15-minute window
    """
    try:
        # Get current machine state
        current_response = current_state_table.get_item(
            Key={'machineId': machine_id}
        )
        
        current_state = None
        if 'Item' in current_response:
            current_state = current_response['Item'].get('status', 'free')
        
        # Query events within the window
        window_events = []
        try:
            response = events_table.query(
                KeyConditionExpression='machineId = :machineId AND #ts BETWEEN :start AND :end',
                ExpressionAttributeNames={
                    '#ts': 'timestamp'
                },
                ExpressionAttributeValues={
                    ':machineId': machine_id,
                    ':start': window_start,
                    ':end': window_end
                },
                ScanIndexForward=True  # Sort by timestamp ascending
            )
            window_events = response.get('Items', [])
        except Exception as e:
            print(f"Error querying events for occupancy calculation: {e}")
        
        # Calculate occupied time within the window
        window_duration = window_end - window_start
        occupied_time = 0
        
        if not window_events:
            # No events in window, use current state for entire window
            if current_state == 'occupied':
                occupied_time = window_duration
        else:
            # Process events to calculate occupied time
            last_timestamp = window_start
            last_status = 'free'  # Assume free at window start
            
            # Check if we need to know the state before the window
            if window_events:
                first_event_time = int(window_events[0]['timestamp'])
                if first_event_time > window_start:
                    # There's a gap at the beginning, use current state or make assumption
                    if current_state:
                        last_status = current_state if len(window_events) % 2 == 1 else 'free'
            
            for event in window_events:
                event_time = int(event['timestamp'])
                event_status = event['status']
                
                # Add occupied time if the last status was occupied
                if last_status == 'occupied':
                    occupied_time += event_time - last_timestamp
                
                last_timestamp = event_time
                last_status = event_status
            
            # Handle remaining time after last event
            if last_status == 'occupied':
                occupied_time += window_end - last_timestamp
        
        # Calculate occupancy ratio as percentage
        occupancy_ratio = (occupied_time / window_duration) * 100.0
        occupancy_ratio = min(100.0, max(0.0, occupancy_ratio))  # Clamp to 0-100%
        
        print(f"Occupancy calculation for {machine_id}: {occupied_time}s/{window_duration}s = {occupancy_ratio:.1f}%")
        return round(occupancy_ratio, 1)
        
    except Exception as e:
        print(f"Error calculating occupancy ratio: {e}")
        return 0.0  # Default to 0% on error


def lambda_handler(event, context):
    """
    Process IoT message from MQTT topic
    Fixed to handle the actual IoT Rule event format
    """
    try:
        print(f"Received IoT event: {json.dumps(event)}")
        
        # Handle different event formats
        # IoT Rule sends the payload directly, not wrapped
        if isinstance(event, dict):
            if 'machineId' in event:
                # Direct payload format
                payload = event
                topic = event.get('topic', 'unknown')
            elif 'payload' in event:
                # Wrapped payload format
                payload = json.loads(event.get('payload', '{}')) if isinstance(event.get('payload'), str) else event.get('payload', {})
                topic = event.get('topic', 'unknown')
            else:
                # Try to parse as stringified JSON
                if isinstance(event, str):
                    payload = json.loads(event)
                else:
                    payload = event
                topic = payload.get('topic', 'unknown')
        else:
            raise ValueError(f"Unexpected event format: {type(event)}")
        
        # Extract machine data
        machine_id = payload.get('machineId')
        status = payload.get('status')  # 'occupied' or 'free'
        timestamp = payload.get('timestamp', int(datetime.now().timestamp()))
        gym_id = payload.get('gymId', 'unknown')
        category = payload.get('category', 'unknown')
        
        print(f"Parsed: machineId={machine_id}, status={status}, gymId={gym_id}, category={category}")
        
        if not machine_id or not status:
            raise ValueError("Missing machineId or status in payload")
        
        # Get previous state to detect transitions
        previous_state = None
        transition_type = None
        try:
            response = current_state_table.get_item(
                Key={'machineId': machine_id}
            )
            if 'Item' in response:
                previous_state = response['Item'].get('status')
                print(f"Previous state for {machine_id}: {previous_state}")
            else:
                print(f"First-time registration for machine {machine_id}")
        except Exception as e:
            print(f"Could not query previous state: {e}")
        
        # Detect state transition
        transition_type = detect_transition(previous_state, status)
        print(f"State transition for {machine_id}: {transition_type}")
        
        # Timestamp validation (prevent out-of-order messages)
        current_time = int(datetime.now().timestamp())
        if previous_state and abs(int(timestamp) - current_time) > 300:  # 5 minute tolerance
            print(f"Warning: Message timestamp {timestamp} is >5 minutes from current time {current_time}")
            # Use current time if timestamp is too old/future
            timestamp = current_time
        
        # Only process if this is a real transition or new machine
        if transition_type in ['initialized', 'freed', 'occupied']:
            print(f"Processing {transition_type} transition for {machine_id}")
        elif transition_type == 'no_change':
            print(f"No state change for {machine_id}, updating timestamp only")
        
        # Write to time-series machine state table (with composite key)
        machine_state_table.put_item(
            Item={
                'machineId': machine_id,
                'timestamp': int(timestamp),  # This is the sort key
                'status': status,
                'gymId': gym_id,
                'category': category,
                'topic': topic
            }
        )
        print(f"Recorded state event for {machine_id} at {timestamp}")
        
        # Update current state table with latest status
        try:
            current_state_table.put_item(
                Item={
                    'machineId': machine_id,
                    'status': status,
                    'lastUpdate': int(timestamp),
                    'gymId': gym_id,
                    'category': category,
                    'topic': topic
                }
            )
            print(f"Updated current state for {machine_id}")
            
            # Invalidate caches when machine state changes
            if CACHE_AVAILABLE and transition_type != 'no_change':
                CacheInvalidationStrategy.on_machine_update(machine_id, gym_id, category)
                cache_metrics.invalidate()
                log_structured('DEBUG', 'cache_invalidated', {
                    'machine_id': machine_id,
                    'gym_id': gym_id,
                    'category': category,
                    'transition': transition_type
                })
                
                # Send cache invalidation metric
                send_metric('CacheInvalidation', 1, dimensions={
                    'Trigger': 'MachineStateChange',
                    'GymId': gym_id,
                    'Category': category
                })
                
        except Exception as e:
            print(f"Could not write to current state table: {e}")
        
        # Try to write to events table if it exists (only for real transitions)
        try:
            if transition_type != 'no_change':  # Only record actual state changes
                events_table.put_item(
                    Item={
                        'machineId': machine_id,
                        'timestamp': int(timestamp),
                        'status': status,
                        'transition': transition_type,
                        'gymId': gym_id,
                        'category': category,
                        'ttl': int(timestamp) + (30 * 24 * 3600)  # 30 days TTL
                    }
                )
                print(f"Recorded {transition_type} event for {machine_id}")
            else:
                print(f"Skipped recording no-change event for {machine_id}")
        except Exception as e:
            print(f"Could not write to events table: {e}")
        
        # Send real-time WebSocket notification for state transitions
        if transition_type in ['initialized', 'freed', 'occupied']:
            websocket_message = {
                'type': 'machine_update',
                'machineId': machine_id,
                'gymId': gym_id,
                'category': category,
                'status': status,
                'timestamp': int(timestamp),
                'lastChange': int(timestamp),
                'transition': transition_type
            }
            print(f"WebSocket notification prepared: {json.dumps(websocket_message)}")
            # TODO: Send to actual WebSocket connections when API is ready
            broadcast_to_websocket_clients(websocket_message)
        
        # Process alerts for occupied→free transitions
        if transition_type == 'freed':  # Machine became free
            try:
                process_alerts_for_machine(machine_id, status, timestamp)
            except Exception as e:
                print(f"Error processing alerts for {machine_id}: {e}")
        
        # Update 15-minute aggregates for heatmaps and forecasting
        if transition_type in ['initialized', 'freed', 'occupied']:  # Only for real state changes
            try:
                update_15min_aggregates(machine_id, gym_id, category, timestamp)
            except Exception as e:
                print(f"Error updating aggregates for {machine_id}: {e}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'IoT message processed successfully',
                'machineId': machine_id,
                'status': status,
                'timestamp': timestamp
            })
        }
        
    except Exception as e:
        error_msg = f"Error processing IoT message: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'event_received': str(event)
            })
        }