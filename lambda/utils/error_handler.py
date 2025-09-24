"""
Error handling utilities for GymPulse Lambda functions
Provides decorators, logging, metrics, and error handling patterns
"""
import json
import logging
import time
import functools
from typing import Dict, Any, Optional, Union
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CloudWatch metrics client
cloudwatch = boto3.client('cloudwatch')

# Custom exceptions
class ValidationError(Exception):
    """Raised when input validation fails"""
    pass

class ResourceNotFoundError(Exception):
    """Raised when a required resource is not found"""
    pass

class DatabaseError(Exception):
    """Raised when database operations fail"""
    pass

def log_structured(level: str, message: str, **kwargs):
    """
    Log structured messages with additional context
    """
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'level': level,
        'message': message,
        **kwargs
    }
    
    if level.upper() == 'ERROR':
        logger.error(json.dumps(log_entry))
    elif level.upper() == 'WARNING':
        logger.warning(json.dumps(log_entry))
    else:
        logger.info(json.dumps(log_entry))

def send_metric(metric_name: str, value: float, unit: str = 'Count', namespace: str = 'GymPulse', dimensions: Dict[str, str] = None):
    """
    Send custom metric to CloudWatch with optional dimensions
    """
    try:
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }
        
        # Add dimensions if provided
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': key, 'Value': value} for key, value in dimensions.items()
            ]
        
        cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=[metric_data]
        )
    except Exception as e:
        logger.error(f"Failed to send metric {metric_name}: {e}")

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that all required fields are present in data
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

def safe_json_parse(json_string: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON string with error handling
    """
    try:
        return json.loads(json_string) if json_string else None
    except (json.JSONDecodeError, TypeError) as e:
        log_structured('error', 'JSON parse error', error=str(e), json_string=json_string[:100])
        return None

class CircuitBreaker:
    """Simple circuit breaker implementation"""
    
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
                raise Exception("Circuit breaker is OPEN")
        
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

# Global circuit breaker for DynamoDB operations
dynamodb_circuit_breaker = CircuitBreaker()

def api_handler(func):
    """
    Decorator for API Lambda functions with error handling and metrics
    """
    @functools.wraps(func)
    def wrapper(event, context):
        start_time = time.time()
        function_name = context.function_name if context else 'unknown'
        
        try:
            log_structured('info', 'API request started', 
                         function=function_name, 
                         event_keys=list(event.keys()) if event else [])
            
            result = func(event, context)
            
            # Send success metric
            send_metric(f'{function_name}_success', 1)
            send_metric(f'{function_name}_duration', (time.time() - start_time) * 1000, 'Milliseconds')
            
            log_structured('info', 'API request completed', 
                         function=function_name,
                         duration_ms=(time.time() - start_time) * 1000)
            
            return result
            
        except ValidationError as e:
            send_metric(f'{function_name}_validation_error', 1)
            log_structured('warning', 'Validation error', 
                         function=function_name, error=str(e))
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Validation error', 'message': str(e)})
            }
            
        except ResourceNotFoundError as e:
            send_metric(f'{function_name}_not_found_error', 1)
            log_structured('warning', 'Resource not found', 
                         function=function_name, error=str(e))
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Resource not found', 'message': str(e)})
            }
            
        except DatabaseError as e:
            send_metric(f'{function_name}_database_error', 1)
            log_structured('error', 'Database error', 
                         function=function_name, error=str(e))
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Database error', 'message': 'Internal server error'})
            }
            
        except Exception as e:
            send_metric(f'{function_name}_error', 1)
            log_structured('error', 'Unexpected error', 
                         function=function_name, error=str(e))
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Internal server error'})
            }
    
    return wrapper

def websocket_handler(func):
    """
    Decorator for WebSocket Lambda functions with error handling and metrics
    """
    @functools.wraps(func)
    def wrapper(event, context):
        start_time = time.time()
        function_name = context.function_name if context else 'unknown'
        connection_id = event.get('requestContext', {}).get('connectionId', 'unknown')
        
        try:
            log_structured('info', 'WebSocket request started', 
                         function=function_name,
                         connection_id=connection_id)
            
            result = func(event, context)
            
            # Send success metric
            send_metric(f'{function_name}_success', 1)
            send_metric(f'{function_name}_duration', (time.time() - start_time) * 1000, 'Milliseconds')
            
            log_structured('info', 'WebSocket request completed', 
                         function=function_name,
                         connection_id=connection_id,
                         duration_ms=(time.time() - start_time) * 1000)
            
            return result
            
        except Exception as e:
            send_metric(f'{function_name}_error', 1)
            log_structured('error', 'WebSocket error', 
                         function=function_name,
                         connection_id=connection_id,
                         error=str(e))
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal server error'})
            }
    
    return wrapper