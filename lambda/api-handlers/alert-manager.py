"""
Alert Management Handler
Handles alert listing, cancellation, and cleanup operations
"""
import json
import boto3
import os
import time
from botocore.exceptions import ClientError


dynamodb = boto3.resource('dynamodb')
alerts_table = dynamodb.Table(os.environ['ALERTS_TABLE'])


def lambda_handler(event, context):
    """
    Handle alert management requests
    """
    try:
        path = event.get('path', '')
        method = event.get('httpMethod', 'GET')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        print(f"Alert management request: {method} {path}")
        
        # Route requests based on path and method
        if path == '/alerts' and method == 'GET':
            user_id = query_parameters.get('userId', 'anonymous')
            return list_user_alerts(user_id)
        elif path.startswith('/alerts/') and method == 'DELETE':
            alert_id = path_parameters.get('alertId')
            return cancel_alert(alert_id, event)
        elif path.startswith('/alerts/') and method == 'PUT':
            alert_id = path_parameters.get('alertId')
            return update_alert(alert_id, event)
        elif path == '/alerts/cleanup' and method == 'POST':
            return cleanup_expired_alerts()
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Alert management endpoint not found'})
            }
            
    except Exception as e:
        print(f"Alert management error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }


def list_user_alerts(user_id):
    """
    List active alerts for a user
    """
    try:
        print(f"Listing alerts for user: {user_id}")
        
        # Query alerts table for user's alerts
        response = alerts_table.query(
            KeyConditionExpression='userId = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        
        alerts = response.get('Items', [])
        active_alerts = []
        expired_alerts = []
        
        current_time = int(time.time())
        
        for alert in alerts:
            # Check if alert is expired
            expires_at = alert.get('expiresAt', 0)
            if expires_at > 0 and current_time > expires_at:
                expired_alerts.append(alert)
                continue
                
            # Format alert for response
            formatted_alert = {
                'alertId': alert.get('alertId'),
                'machineId': alert.get('machineId'),
                'gymId': alert.get('gymId'),
                'category': alert.get('category'),
                'active': alert.get('active', False),
                'createdAt': alert.get('createdAt'),
                'expiresAt': alert.get('expiresAt'),
                'quietHours': alert.get('quietHours', {}),
                'firedAt': alert.get('firedAt'),
                'machineName': alert.get('machineId', '').replace('-', ' ').title()
            }
            
            if alert.get('active', False):
                active_alerts.append(formatted_alert)
        
        # Clean up expired alerts asynchronously
        if expired_alerts:
            print(f"Found {len(expired_alerts)} expired alerts for cleanup")
            cleanup_alerts_list(expired_alerts)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({
                'userId': user_id,
                'activeAlerts': active_alerts,
                'totalActive': len(active_alerts),
                'expiredCleaned': len(expired_alerts)
            })
        }
        
    except Exception as e:
        print(f"Error listing alerts for user {user_id}: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Failed to list user alerts'})
        }


def cancel_alert(alert_id, event):
    """
    Cancel/deactivate a specific alert
    """
    try:
        if not alert_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Alert ID is required'})
            }
        
        # Parse request body for user validation
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except json.JSONDecodeError:
                pass
        
        user_id = body.get('userId', 'anonymous')
        
        # Find the alert by scanning (since we don't have alertId as primary key)
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
        
        # Verify user ownership (for demo, allow anonymous)
        if user_id != 'anonymous' and alert.get('userId') != user_id:
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Not authorized to cancel this alert'})
            }
        
        # Deactivate the alert
        try:
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
            
            print(f"Cancelled alert {alert_id} for user {user_id}")
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                },
                'body': json.dumps({
                    'message': 'Alert cancelled successfully',
                    'alertId': alert_id,
                    'machineId': alert['machineId']
                })
            }
            
        except ClientError as e:
            print(f"Error cancelling alert {alert_id}: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Failed to cancel alert'})
            }
        
    except Exception as e:
        print(f"Error in cancel_alert: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }


def update_alert(alert_id, event):
    """
    Update alert settings (quiet hours, etc.)
    """
    try:
        if not alert_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Alert ID is required'})
            }
        
        # Parse request body
        if not event.get('body'):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Request body is required'})
            }
        
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid JSON in request body'})
            }
        
        user_id = body.get('userId', 'anonymous')
        quiet_hours = body.get('quietHours')
        
        if not quiet_hours:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'quietHours is required for update'})
            }
        
        # Find and update the alert
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
        print(f"Error updating alert {alert_id}: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Failed to update alert'})
        }


def cleanup_expired_alerts():
    """
    Clean up expired and fired alerts
    """
    try:
        current_time = int(time.time())
        
        # Scan for expired or old fired alerts
        response = alerts_table.scan()
        all_alerts = response.get('Items', [])
        
        expired_count = 0
        old_fired_count = 0
        
        for alert in all_alerts:
            should_delete = False
            
            # Check if expired
            expires_at = alert.get('expiresAt', 0)
            if expires_at > 0 and current_time > expires_at:
                should_delete = True
                expired_count += 1
            
            # Check if fired more than 24 hours ago
            fired_at = alert.get('firedAt', 0)
            if fired_at > 0 and (current_time - fired_at) > (24 * 60 * 60):
                should_delete = True
                old_fired_count += 1
            
            if should_delete:
                try:
                    alerts_table.delete_item(
                        Key={
                            'userId': alert['userId'],
                            'machineId': alert['machineId']
                        }
                    )
                except Exception as e:
                    print(f"Error deleting alert {alert.get('alertId')}: {str(e)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({
                'message': 'Alert cleanup completed',
                'expiredCleaned': expired_count,
                'oldFiredCleaned': old_fired_count,
                'totalCleaned': expired_count + old_fired_count
            })
        }
        
    except Exception as e:
        print(f"Error in cleanup_expired_alerts: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Alert cleanup failed'})
        }


def cleanup_alerts_list(alerts_to_cleanup):
    """
    Helper function to clean up a specific list of alerts
    """
    try:
        for alert in alerts_to_cleanup:
            try:
                alerts_table.delete_item(
                    Key={
                        'userId': alert['userId'],
                        'machineId': alert['machineId']
                    }
                )
                print(f"Cleaned up expired alert: {alert.get('alertId')}")
            except Exception as e:
                print(f"Error cleaning up alert {alert.get('alertId')}: {str(e)}")
                
    except Exception as e:
        print(f"Error in cleanup_alerts_list: {str(e)}")