"""
Structured logging system for GymPulse
Provides consistent, searchable logging across all Lambda functions
"""
import json
import logging
import time
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from enum import Enum


class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    """Event type enumeration for categorization"""
    IOT_MESSAGE = "iot_message"
    API_REQUEST = "api_request"
    WEBSOCKET_EVENT = "websocket_event"
    TOOL_CALL = "tool_call"
    ALERT_FIRED = "alert_fired"
    STATE_TRANSITION = "state_transition"
    SYSTEM_ERROR = "system_error"
    PERFORMANCE_METRIC = "performance_metric"
    DEVICE_HEALTH = "device_health"
    USER_ACTION = "user_action"


class StructuredLogger:
    """
    Structured logger for consistent logging across GymPulse system
    Outputs JSON formatted logs for easy parsing and searching
    """
    
    def __init__(self, 
                 component_name: str,
                 correlation_id: Optional[str] = None,
                 log_level: LogLevel = LogLevel.INFO):
        """
        Initialize structured logger
        
        Args:
            component_name: Name of the component using this logger
            correlation_id: Optional correlation ID for tracing requests
            log_level: Minimum log level to output
        """
        self.component_name = component_name
        self.correlation_id = correlation_id
        self.log_level = log_level
        
        # Configure Python logger
        self.logger = logging.getLogger(component_name)
        self.logger.setLevel(getattr(logging, log_level.value))
        
        # Remove existing handlers to avoid duplication
        self.logger.handlers = []
        
        # Add console handler with JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(self._create_json_formatter())
        self.logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _create_json_formatter(self) -> logging.Formatter:
        """Create JSON formatter for log records"""
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                # Create base log entry
                log_entry = {
                    'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                    'level': record.levelname,
                    'component': record.name,
                    'message': record.getMessage()
                }
                
                # Add correlation ID if available
                if hasattr(record, 'correlation_id') and record.correlation_id:
                    log_entry['correlationId'] = record.correlation_id
                
                # Add event type if available
                if hasattr(record, 'event_type'):
                    log_entry['eventType'] = record.event_type
                
                # Add additional fields if available
                if hasattr(record, 'extra_fields'):
                    log_entry.update(record.extra_fields)
                
                # Add exception information if present
                if record.exc_info:
                    log_entry['exception'] = {
                        'type': record.exc_info[0].__name__,
                        'message': str(record.exc_info[1]),
                        'traceback': traceback.format_exception(*record.exc_info)
                    }
                
                return json.dumps(log_entry, default=str, separators=(',', ':'))
        
        return JSONFormatter()
    
    def _log(self, 
             level: LogLevel,
             message: str,
             event_type: Optional[EventType] = None,
             correlation_id: Optional[str] = None,
             **extra_fields) -> None:
        """
        Internal logging method
        
        Args:
            level: Log level
            message: Log message
            event_type: Type of event being logged
            correlation_id: Correlation ID for request tracing
            **extra_fields: Additional fields to include in log
        """
        # Create log record
        python_level = getattr(logging, level.value)
        
        # Create extra data for the log record
        extra = {
            'correlation_id': correlation_id or self.correlation_id,
            'extra_fields': extra_fields
        }
        
        if event_type:
            extra['event_type'] = event_type.value
        
        # Log the message
        self.logger.log(python_level, message, extra=extra)
    
    def debug(self, message: str, event_type: Optional[EventType] = None, **extra_fields) -> None:
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, event_type, **extra_fields)
    
    def info(self, message: str, event_type: Optional[EventType] = None, **extra_fields) -> None:
        """Log info message"""
        self._log(LogLevel.INFO, message, event_type, **extra_fields)
    
    def warning(self, message: str, event_type: Optional[EventType] = None, **extra_fields) -> None:
        """Log warning message"""
        self._log(LogLevel.WARNING, message, event_type, **extra_fields)
    
    def error(self, message: str, event_type: Optional[EventType] = None, **extra_fields) -> None:
        """Log error message"""
        self._log(LogLevel.ERROR, message, event_type, **extra_fields)
    
    def critical(self, message: str, event_type: Optional[EventType] = None, **extra_fields) -> None:
        """Log critical message"""
        self._log(LogLevel.CRITICAL, message, event_type, **extra_fields)
    
    def log_iot_message(self,
                       machine_id: str,
                       status: str,
                       processing_time_ms: float,
                       success: bool = True,
                       error: Optional[str] = None) -> None:
        """
        Log IoT message processing
        
        Args:
            machine_id: Machine identifier
            status: Machine status
            processing_time_ms: Processing time in milliseconds
            success: Whether processing succeeded
            error: Error message if processing failed
        """
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"IoT message processed for {machine_id}: {status}"
        
        self._log(
            level=level,
            message=message,
            event_type=EventType.IOT_MESSAGE,
            machineId=machine_id,
            status=status,
            processingTimeMs=processing_time_ms,
            success=success,
            error=error
        )
    
    def log_api_request(self,
                       method: str,
                       endpoint: str,
                       status_code: int,
                       response_time_ms: float,
                       user_id: Optional[str] = None,
                       error: Optional[str] = None) -> None:
        """
        Log API request
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: Response status code
            response_time_ms: Response time in milliseconds
            user_id: Optional user identifier
            error: Error message if request failed
        """
        level = LogLevel.INFO if 200 <= status_code < 400 else LogLevel.ERROR
        message = f"{method} {endpoint} -> {status_code}"
        
        self._log(
            level=level,
            message=message,
            event_type=EventType.API_REQUEST,
            method=method,
            endpoint=endpoint,
            statusCode=status_code,
            responseTimeMs=response_time_ms,
            userId=user_id,
            error=error
        )
    
    def log_tool_call(self,
                     tool_name: str,
                     success: bool,
                     execution_time_ms: float,
                     input_params: Optional[Dict[str, Any]] = None,
                     output_size: Optional[int] = None,
                     error: Optional[str] = None) -> None:
        """
        Log chatbot tool call
        
        Args:
            tool_name: Name of the tool called
            success: Whether tool call succeeded
            execution_time_ms: Execution time in milliseconds
            input_params: Tool input parameters
            output_size: Size of output data
            error: Error message if tool call failed
        """
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Tool call {tool_name}: {'success' if success else 'failed'}"
        
        self._log(
            level=level,
            message=message,
            event_type=EventType.TOOL_CALL,
            toolName=tool_name,
            success=success,
            executionTimeMs=execution_time_ms,
            inputParams=input_params,
            outputSize=output_size,
            error=error
        )
    
    def log_alert_fired(self,
                       alert_id: str,
                       machine_id: str,
                       user_id: str,
                       delivery_success: bool,
                       delivery_method: str,
                       error: Optional[str] = None) -> None:
        """
        Log alert firing and delivery
        
        Args:
            alert_id: Alert identifier
            machine_id: Machine that triggered alert
            user_id: User who created alert
            delivery_success: Whether alert was delivered successfully
            delivery_method: Method used for delivery (websocket, email, etc.)
            error: Error message if delivery failed
        """
        level = LogLevel.INFO if delivery_success else LogLevel.WARNING
        message = f"Alert {alert_id} fired for {machine_id}"
        
        self._log(
            level=level,
            message=message,
            event_type=EventType.ALERT_FIRED,
            alertId=alert_id,
            machineId=machine_id,
            userId=user_id,
            deliverySuccess=delivery_success,
            deliveryMethod=delivery_method,
            error=error
        )
    
    def log_state_transition(self,
                           machine_id: str,
                           previous_status: Optional[str],
                           new_status: str,
                           transition_type: str,
                           gym_id: str) -> None:
        """
        Log machine state transition
        
        Args:
            machine_id: Machine identifier
            previous_status: Previous machine status
            new_status: New machine status
            transition_type: Type of transition (occupied, freed, no_change)
            gym_id: Gym identifier
        """
        message = f"State transition for {machine_id}: {previous_status} -> {new_status}"
        
        self._log(
            level=LogLevel.INFO,
            message=message,
            event_type=EventType.STATE_TRANSITION,
            machineId=machine_id,
            previousStatus=previous_status,
            newStatus=new_status,
            transitionType=transition_type,
            gymId=gym_id
        )
    
    def log_performance_metric(self,
                             metric_name: str,
                             value: float,
                             unit: str,
                             dimensions: Optional[Dict[str, str]] = None,
                             target_met: Optional[bool] = None) -> None:
        """
        Log performance metric
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Metric unit
            dimensions: Metric dimensions
            target_met: Whether performance target was met
        """
        message = f"Performance metric {metric_name}: {value} {unit}"
        
        self._log(
            level=LogLevel.INFO,
            message=message,
            event_type=EventType.PERFORMANCE_METRIC,
            metricName=metric_name,
            value=value,
            unit=unit,
            dimensions=dimensions,
            targetMet=target_met
        )
    
    def log_system_error(self,
                        error_type: str,
                        error_message: str,
                        component: str,
                        stack_trace: Optional[str] = None,
                        context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log system error with full context
        
        Args:
            error_type: Type of error
            error_message: Error message
            component: Component where error occurred
            stack_trace: Stack trace if available
            context: Additional context information
        """
        message = f"System error in {component}: {error_message}"
        
        extra_fields = {
            'errorType': error_type,
            'errorMessage': error_message,
            'component': component,
            'stackTrace': stack_trace,
            'context': context
        }
        
        self._log(
            level=LogLevel.ERROR,
            message=message,
            event_type=EventType.SYSTEM_ERROR,
            **extra_fields
        )
    
    def create_child_logger(self, correlation_id: str) -> 'StructuredLogger':
        """
        Create child logger with specific correlation ID
        
        Args:
            correlation_id: Correlation ID for request tracing
            
        Returns:
            New StructuredLogger instance with correlation ID
        """
        return StructuredLogger(
            component_name=self.component_name,
            correlation_id=correlation_id,
            log_level=self.log_level
        )


class ErrorTracker:
    """Error tracking and aggregation system"""
    
    def __init__(self, logger: StructuredLogger):
        """
        Initialize error tracker
        
        Args:
            logger: Structured logger instance
        """
        self.logger = logger
        self.error_counts = {}
        self.critical_errors = []
    
    def track_error(self,
                   error_type: str,
                   error_message: str,
                   component: str,
                   severity: str = "error",
                   context: Optional[Dict[str, Any]] = None) -> None:
        """
        Track an error occurrence
        
        Args:
            error_type: Type of error
            error_message: Error message
            component: Component where error occurred
            severity: Error severity (error, warning, critical)
            context: Additional context
        """
        # Log the error
        log_level = {
            'warning': LogLevel.WARNING,
            'error': LogLevel.ERROR,
            'critical': LogLevel.CRITICAL
        }.get(severity, LogLevel.ERROR)
        
        self.logger._log(
            level=log_level,
            message=f"Error tracked: {error_message}",
            event_type=EventType.SYSTEM_ERROR,
            errorType=error_type,
            component=component,
            severity=severity,
            context=context
        )
        
        # Track error count
        error_key = f"{component}:{error_type}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Track critical errors separately
        if severity == "critical":
            self.critical_errors.append({
                'timestamp': datetime.utcnow().isoformat(),
                'error_type': error_type,
                'message': error_message,
                'component': component,
                'context': context
            })
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of tracked errors
        
        Returns:
            Dictionary with error statistics
        """
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_types': len(self.error_counts),
            'critical_errors': len(self.critical_errors),
            'error_breakdown': self.error_counts,
            'recent_critical': self.critical_errors[-5:] if self.critical_errors else []
        }


# Example usage functions
def demo_structured_logging():
    """Demonstrate structured logging usage"""
    
    # Create logger for IoT ingest component
    logger = StructuredLogger("gym-pulse-iot-ingest", correlation_id="demo-123")
    
    # Log successful IoT message processing
    logger.log_iot_message(
        machine_id="leg-press-01",
        status="occupied",
        processing_time_ms=245.7,
        success=True
    )
    
    # Log API request
    logger.log_api_request(
        method="GET",
        endpoint="/branches",
        status_code=200,
        response_time_ms=156.3,
        user_id="user-456"
    )
    
    # Log tool call
    logger.log_tool_call(
        tool_name="getAvailabilityByCategory",
        success=True,
        execution_time_ms=892.1,
        input_params={"lat": 22.2819, "lon": 114.1577, "category": "legs"},
        output_size=3
    )
    
    # Log error
    logger.log_system_error(
        error_type="ValidationError",
        error_message="Invalid machine ID format",
        component="iot-ingest",
        context={"machineId": "invalid-id-123"}
    )
    
    print("Structured logging demo completed!")


if __name__ == '__main__':
    demo_structured_logging()