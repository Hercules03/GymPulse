"""
Custom CloudWatch metrics for GymPulse system monitoring
Tracks end-to-end latency, device health, and performance targets
"""
import boto3
import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


class CustomMetrics:
    """Custom CloudWatch metrics publisher for GymPulse"""
    
    def __init__(self, region: str = 'ap-east-1'):
        """
        Initialize CloudWatch client
        
        Args:
            region: AWS region for CloudWatch
        """
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.namespace = 'GymPulse/Custom'
        self.region = region
    
    def publish_metric(self, 
                      metric_name: str, 
                      value: float, 
                      unit: str = 'Count',
                      dimensions: Optional[Dict[str, str]] = None,
                      timestamp: Optional[datetime] = None) -> None:
        """
        Publish a custom metric to CloudWatch
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: CloudWatch unit (Count, Seconds, Bytes, etc.)
            dimensions: Metric dimensions for filtering
            timestamp: Optional timestamp (defaults to now)
        """
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            if timestamp:
                metric_data['Timestamp'] = timestamp
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
            
            print(f"Published metric: {metric_name} = {value} {unit}")
            
        except Exception as e:
            print(f"Failed to publish metric {metric_name}: {e}")
    
    def publish_end_to_end_latency(self, 
                                  latency_ms: float, 
                                  machine_id: str,
                                  gym_id: str) -> None:
        """
        Publish end-to-end latency metric (MQTT to WebSocket)
        Target: P95 ≤ 15 seconds (15000ms)
        
        Args:
            latency_ms: Latency in milliseconds
            machine_id: Machine identifier
            gym_id: Gym identifier
        """
        self.publish_metric(
            metric_name='EndToEndLatency',
            value=latency_ms,
            unit='Milliseconds',
            dimensions={
                'MachineId': machine_id,
                'GymId': gym_id
            }
        )
        
        # Publish target compliance
        is_within_target = latency_ms <= 15000
        self.publish_metric(
            metric_name='LatencyWithinTarget',
            value=1.0 if is_within_target else 0.0,
            unit='Count',
            dimensions={
                'MachineId': machine_id,
                'GymId': gym_id
            }
        )
    
    def publish_chatbot_response_time(self, 
                                     response_time_ms: float,
                                     query_type: str,
                                     tools_used: List[str]) -> None:
        """
        Publish chatbot response time metric
        Target: P95 ≤ 3 seconds (3000ms)
        
        Args:
            response_time_ms: Response time in milliseconds
            query_type: Type of query (legs, chest, back, general)
            tools_used: List of tools called during request
        """
        self.publish_metric(
            metric_name='ChatbotResponseTime',
            value=response_time_ms,
            unit='Milliseconds',
            dimensions={
                'QueryType': query_type,
                'ToolsUsed': ','.join(tools_used)
            }
        )
        
        # Publish target compliance
        is_within_target = response_time_ms <= 3000
        self.publish_metric(
            metric_name='ChatbotWithinTarget',
            value=1.0 if is_within_target else 0.0,
            unit='Count',
            dimensions={
                'QueryType': query_type
            }
        )
    
    def publish_tool_call_metrics(self, 
                                 tool_name: str,
                                 success: bool,
                                 execution_time_ms: float,
                                 error_type: Optional[str] = None) -> None:
        """
        Publish tool call success rate and performance metrics
        
        Args:
            tool_name: Name of the tool (getAvailabilityByCategory, getRouteMatrix)
            success: Whether tool call succeeded
            execution_time_ms: Tool execution time in milliseconds
            error_type: Type of error if failed
        """
        # Tool success rate
        self.publish_metric(
            metric_name='ToolCallSuccessRate',
            value=1.0 if success else 0.0,
            unit='Count',
            dimensions={
                'ToolName': tool_name
            }
        )
        
        # Tool execution time
        metric_name = f'{tool_name.replace("get", "")}ToolLatency'
        self.publish_metric(
            metric_name=metric_name,
            value=execution_time_ms,
            unit='Milliseconds',
            dimensions={
                'ToolName': tool_name,
                'Success': str(success)
            }
        )
        
        # Error tracking
        if not success and error_type:
            self.publish_metric(
                metric_name='ToolCallErrors',
                value=1.0,
                unit='Count',
                dimensions={
                    'ToolName': tool_name,
                    'ErrorType': error_type
                }
            )
    
    def publish_device_health_metrics(self, 
                                     active_devices: int,
                                     offline_devices: int,
                                     message_throughput: int) -> None:
        """
        Publish IoT device health metrics
        
        Args:
            active_devices: Number of active devices
            offline_devices: Number of offline devices
            message_throughput: Messages per minute
        """
        self.publish_metric(
            metric_name='ActiveDevices',
            value=float(active_devices),
            unit='Count'
        )
        
        self.publish_metric(
            metric_name='DeviceOfflineCount',
            value=float(offline_devices),
            unit='Count'
        )
        
        self.publish_metric(
            metric_name='MessageThroughput',
            value=float(message_throughput),
            unit='Count/Minute'
        )
        
        # Device health ratio
        total_devices = active_devices + offline_devices
        if total_devices > 0:
            health_ratio = active_devices / total_devices
            self.publish_metric(
                metric_name='DeviceHealthRatio',
                value=health_ratio,
                unit='Percent'
            )
    
    def publish_alert_metrics(self, 
                             alerts_fired: int,
                             alerts_delivered: int,
                             alerts_failed: int) -> None:
        """
        Publish alert system metrics
        
        Args:
            alerts_fired: Number of alerts triggered
            alerts_delivered: Number of alerts successfully delivered
            alerts_failed: Number of failed alert deliveries
        """
        self.publish_metric(
            metric_name='AlertsFired',
            value=float(alerts_fired),
            unit='Count'
        )
        
        self.publish_metric(
            metric_name='AlertsDelivered',
            value=float(alerts_delivered),
            unit='Count'
        )
        
        self.publish_metric(
            metric_name='AlertsFailed',
            value=float(alerts_failed),
            unit='Count'
        )
        
        # Alert success rate
        if alerts_fired > 0:
            success_rate = alerts_delivered / alerts_fired
            self.publish_metric(
                metric_name='AlertSuccessRate',
                value=success_rate,
                unit='Percent'
            )
    
    def publish_websocket_metrics(self, 
                                 active_connections: int,
                                 messages_sent: int,
                                 connection_errors: int) -> None:
        """
        Publish WebSocket connection metrics
        
        Args:
            active_connections: Number of active WebSocket connections
            messages_sent: Number of messages broadcast
            connection_errors: Number of connection errors
        """
        self.publish_metric(
            metric_name='WebSocketConnections',
            value=float(active_connections),
            unit='Count'
        )
        
        self.publish_metric(
            metric_name='WebSocketMessagesSent',
            value=float(messages_sent),
            unit='Count'
        )
        
        self.publish_metric(
            metric_name='WebSocketErrors',
            value=float(connection_errors),
            unit='Count'
        )
    
    def publish_api_performance_metrics(self,
                                       endpoint: str,
                                       method: str,
                                       status_code: int,
                                       response_time_ms: float) -> None:
        """
        Publish API performance metrics
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: Response status code
            response_time_ms: Response time in milliseconds
        """
        # API response time
        self.publish_metric(
            metric_name='APIResponseTime',
            value=response_time_ms,
            unit='Milliseconds',
            dimensions={
                'Endpoint': endpoint,
                'Method': method,
                'StatusCode': str(status_code)
            }
        )
        
        # API success rate
        is_success = 200 <= status_code < 400
        self.publish_metric(
            metric_name='APISuccessRate',
            value=1.0 if is_success else 0.0,
            unit='Count',
            dimensions={
                'Endpoint': endpoint,
                'Method': method
            }
        )
    
    def create_performance_alarms(self) -> None:
        """
        Create CloudWatch alarms for performance targets
        """
        alarms = [
            {
                'AlarmName': 'GymPulse-EndToEndLatency-P95-High',
                'MetricName': 'EndToEndLatency',
                'Statistic': 'ExtendedStatistic',
                'ExtendedStatistic': 'p95',
                'Threshold': 15000.0,  # 15 seconds in ms
                'ComparisonOperator': 'GreaterThanThreshold',
                'AlarmDescription': 'End-to-end latency P95 exceeds 15 seconds',
                'TreatMissingData': 'notBreaching'
            },
            {
                'AlarmName': 'GymPulse-ChatbotResponseTime-P95-High',
                'MetricName': 'ChatbotResponseTime',
                'Statistic': 'ExtendedStatistic',
                'ExtendedStatistic': 'p95',
                'Threshold': 3000.0,  # 3 seconds in ms
                'ComparisonOperator': 'GreaterThanThreshold',
                'AlarmDescription': 'Chatbot response time P95 exceeds 3 seconds',
                'TreatMissingData': 'notBreaching'
            },
            {
                'AlarmName': 'GymPulse-DeviceHealthRatio-Low',
                'MetricName': 'DeviceHealthRatio',
                'Statistic': 'Average',
                'Threshold': 0.9,  # 90%
                'ComparisonOperator': 'LessThanThreshold',
                'AlarmDescription': 'Device health ratio below 90%',
                'TreatMissingData': 'breaching'
            },
            {
                'AlarmName': 'GymPulse-AlertSuccessRate-Low',
                'MetricName': 'AlertSuccessRate',
                'Statistic': 'Average',
                'Threshold': 0.95,  # 95%
                'ComparisonOperator': 'LessThanThreshold',
                'AlarmDescription': 'Alert success rate below 95%',
                'TreatMissingData': 'breaching'
            }
        ]
        
        for alarm_config in alarms:
            try:
                self.cloudwatch.put_metric_alarm(
                    AlarmName=alarm_config['AlarmName'],
                    ComparisonOperator=alarm_config['ComparisonOperator'],
                    EvaluationPeriods=2,
                    MetricName=alarm_config['MetricName'],
                    Namespace=self.namespace,
                    Period=300,  # 5 minutes
                    Statistic=alarm_config.get('Statistic', 'Average'),
                    ExtendedStatistic=alarm_config.get('ExtendedStatistic'),
                    Threshold=alarm_config['Threshold'],
                    ActionsEnabled=True,
                    AlarmDescription=alarm_config['AlarmDescription'],
                    TreatMissingData=alarm_config['TreatMissingData'],
                    Unit='Milliseconds' if 'Time' in alarm_config['MetricName'] or 'Latency' in alarm_config['MetricName'] else 'None'
                )
                
                print(f"Created alarm: {alarm_config['AlarmName']}")
                
            except Exception as e:
                print(f"Failed to create alarm {alarm_config['AlarmName']}: {e}")


def demo_metrics_collection():
    """
    Demo function showing how to collect and publish metrics
    """
    metrics = CustomMetrics()
    
    # Simulate end-to-end latency measurement
    metrics.publish_end_to_end_latency(
        latency_ms=8500.0,  # 8.5 seconds
        machine_id='leg-press-01',
        gym_id='hk-central'
    )
    
    # Simulate chatbot response time
    metrics.publish_chatbot_response_time(
        response_time_ms=2100.0,  # 2.1 seconds
        query_type='legs',
        tools_used=['getAvailabilityByCategory', 'getRouteMatrix']
    )
    
    # Simulate device health
    metrics.publish_device_health_metrics(
        active_devices=48,
        offline_devices=2,
        message_throughput=95  # messages per minute
    )
    
    # Simulate alert metrics
    metrics.publish_alert_metrics(
        alerts_fired=5,
        alerts_delivered=5,
        alerts_failed=0
    )
    
    print("Demo metrics published successfully!")


if __name__ == '__main__':
    # Run demo metrics collection
    demo_metrics_collection()
    
    # Create performance alarms
    metrics = CustomMetrics()
    metrics.create_performance_alarms()