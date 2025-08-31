"""
Centralized error handling and monitoring utilities
Provides structured logging, error categorization, and CloudWatch metrics
"""
import json
import logging
import time
import traceback
from functools import wraps
from typing import Dict, Any, Optional
import boto3


# Configure structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CloudWatch client for custom metrics
cloudwatch = boto3.client('cloudwatch')


class GymPulseError(Exception):
    """Base exception class for GymPulse-specific errors"""
    def __init__(self, message: str, error_code: str = None, status_code: int = 500):
        self.message = message
        self.error_code = error_code or 'INTERNAL_ERROR'
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(GymPulseError):
    """Raised when input validation fails"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message, 'VALIDATION_ERROR', 400)
        self.field = field


class ResourceNotFoundError(GymPulseError):
    """Raised when requested resource is not found"""
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} '{resource_id}' not found"
        super().__init__(message, 'RESOURCE_NOT_FOUND', 404)


class DatabaseError(GymPulseError):
    """Raised when database operations fail"""
    def __init__(self, message: str, operation: str = None):
        super().__init__(message, 'DATABASE_ERROR', 500)
        self.operation = operation


def log_structured(level: str, event_type: str, data: Dict[str, Any], 
                  correlation_id: str = None, duration: float = None):
    """
    Log structured JSON events for CloudWatch analysis
    """
    log_entry = {
        'timestamp': int(time.time() * 1000),  # Millisecond precision
        'level': level.upper(),
        'event_type': event_type,
        'data': data
    }
    
    if correlation_id:
        log_entry['correlation_id'] = correlation_id
    
    if duration:
        log_entry['duration_ms'] = round(duration * 1000, 2)
    
    logger.info(json.dumps(log_entry))


def send_metric(metric_name: str, value: float, unit: str = 'Count', 
                dimensions: Dict[str, str] = None, namespace: str = 'GymPulse'):
    """
    Send custom metrics to CloudWatch
    """
    try:
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': time.time()
        }
        
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]
        
        cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=[metric_data]
        )
    except Exception as e:
        logger.warning(f"Failed to send metric {metric_name}: {str(e)}")


def api_handler(func):
    """
    Decorator for API Lambda handlers with error handling and monitoring
    """
    @wraps(func)
    def wrapper(event, context):
        start_time = time.time()
        correlation_id = context.aws_request_id if context else None
        function_name = getattr(context, 'function_name', 'unknown') if context else 'unknown'
        
        # Extract basic request info
        method = event.get('httpMethod', 'UNKNOWN')
        path = event.get('path', 'unknown')
        
        log_structured('INFO', 'api_request_start', {
            'method': method,
            'path': path,
            'function': function_name
        }, correlation_id)
        
        try:
            # Execute the handler
            result = func(event, context)
            
            duration = time.time() - start_time
            status_code = result.get('statusCode', 500)
            
            # Log success
            log_structured('INFO', 'api_request_complete', {
                'method': method,
                'path': path,
                'status_code': status_code,
                'function': function_name
            }, correlation_id, duration)
            
            # Send metrics
            send_metric('APIRequest', 1, dimensions={
                'Method': method,
                'Path': path,
                'StatusCode': str(status_code),
                'Function': function_name
            })
            
            send_metric('APILatency', duration * 1000, 'Milliseconds', dimensions={
                'Method': method,
                'Path': path,
                'Function': function_name
            })
            
            if status_code >= 400:
                send_metric('APIError', 1, dimensions={
                    'Method': method,
                    'Path': path,
                    'StatusCode': str(status_code),
                    'Function': function_name
                })
            
            return result
            
        except GymPulseError as e:
            duration = time.time() - start_time
            
            # Log application error
            log_structured('ERROR', 'api_request_error', {
                'method': method,
                'path': path,
                'error_code': e.error_code,
                'error_message': e.message,
                'status_code': e.status_code,
                'function': function_name
            }, correlation_id, duration)
            
            # Send error metrics
            send_metric('APIError', 1, dimensions={
                'Method': method,
                'Path': path,
                'ErrorCode': e.error_code,
                'Function': function_name
            })
            
            return {
                'statusCode': e.status_code,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'X-Correlation-ID': correlation_id or 'unknown'
                },
                'body': json.dumps({
                    'error': e.message,
                    'error_code': e.error_code,
                    'correlation_id': correlation_id
                })
            }
            
        except Exception as e:
            duration = time.time() - start_time
            error_trace = traceback.format_exc()
            
            # Log unexpected error
            log_structured('ERROR', 'api_request_exception', {
                'method': method,
                'path': path,
                'error_message': str(e),
                'error_trace': error_trace,
                'function': function_name
            }, correlation_id, duration)
            
            # Send critical error metric
            send_metric('APIException', 1, dimensions={
                'Method': method,
                'Path': path,
                'Function': function_name
            })
            
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'X-Correlation-ID': correlation_id or 'unknown'
                },
                'body': json.dumps({
                    'error': 'Internal server error',
                    'error_code': 'INTERNAL_ERROR',
                    'correlation_id': correlation_id
                })
            }
    
    return wrapper


def websocket_handler(func):
    """
    Decorator for WebSocket Lambda handlers with error handling
    """
    @wraps(func)
    def wrapper(event, context):
        start_time = time.time()
        correlation_id = context.aws_request_id if context else None
        function_name = getattr(context, 'function_name', 'unknown') if context else 'unknown'
        
        route_key = event.get('routeKey', 'unknown')
        connection_id = event.get('requestContext', {}).get('connectionId', 'unknown')
        
        log_structured('INFO', 'websocket_request_start', {
            'route': route_key,
            'connection_id': connection_id[:8] + '...',  # Partial ID for privacy
            'function': function_name
        }, correlation_id)
        
        try:
            result = func(event, context)
            
            duration = time.time() - start_time
            status_code = result.get('statusCode', 200)
            
            log_structured('INFO', 'websocket_request_complete', {
                'route': route_key,
                'connection_id': connection_id[:8] + '...',
                'status_code': status_code,
                'function': function_name
            }, correlation_id, duration)
            
            # Send WebSocket metrics
            send_metric('WebSocketRequest', 1, dimensions={
                'Route': route_key,
                'StatusCode': str(status_code),
                'Function': function_name
            })
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            error_trace = traceback.format_exc()
            
            log_structured('ERROR', 'websocket_request_error', {
                'route': route_key,
                'connection_id': connection_id[:8] + '...',
                'error_message': str(e),
                'error_trace': error_trace,
                'function': function_name
            }, correlation_id, duration)
            
            send_metric('WebSocketError', 1, dimensions={
                'Route': route_key,
                'Function': function_name
            })
            
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Internal server error',
                    'correlation_id': correlation_id
                })
            }
    
    return wrapper


def validate_required_fields(data: Dict[str, Any], required_fields: list, 
                            field_types: Dict[str, type] = None) -> None:
    """
    Validate required fields in request data
    """
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValidationError(f"Field '{field}' is required", field)
        
        # Type validation if specified
        if field_types and field in field_types:
            expected_type = field_types[field]
            if not isinstance(data[field], expected_type):
                raise ValidationError(
                    f"Field '{field}' must be of type {expected_type.__name__}", 
                    field
                )


def safe_json_parse(json_string: str, field_name: str = 'body') -> Dict[str, Any]:
    """
    Safely parse JSON string with proper error handling
    """
    if not json_string:
        raise ValidationError(f"{field_name} cannot be empty")
    
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in {field_name}: {str(e)}")


# Circuit breaker pattern for external services
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise GymPulseError("Circuit breaker is OPEN", "SERVICE_UNAVAILABLE", 503)
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
            
            raise e


# Global circuit breaker instances
dynamodb_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
websocket_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)