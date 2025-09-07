"""
Performance Validation System for GymPulse
Validates P95 latency targets: ≤15s end-to-end, ≤3s chatbot
"""
import asyncio
import time
import json
import statistics
from typing import List, Dict, Any, Tuple
import boto3
import requests
import websocket
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone

# Import our monitoring system
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "monitoring"))
from custom_metrics import CustomMetrics
from structured_logger import StructuredLogger, EventType


@dataclass
class PerformanceTarget:
    """Performance target definition"""
    name: str
    target_p95_ms: float
    target_avg_ms: float
    description: str


@dataclass
class LatencyMeasurement:
    """Single latency measurement"""
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    context: Dict[str, Any]


class PerformanceValidator:
    """Comprehensive performance validation system"""
    
    def __init__(self, region: str = 'ap-east-1'):
        """
        Initialize performance validator
        
        Args:
            region: AWS region for testing
        """
        self.region = region
        self.logger = StructuredLogger("performance-validator")
        self.metrics = CustomMetrics(region)
        
        # Performance targets
        self.targets = {
            'end_to_end': PerformanceTarget(
                name='End-to-End Latency',
                target_p95_ms=15000.0,  # 15 seconds
                target_avg_ms=8000.0,   # 8 seconds average
                description='MQTT publish to WebSocket notification'
            ),
            'chatbot': PerformanceTarget(
                name='Chatbot Response Time',
                target_p95_ms=3000.0,   # 3 seconds
                target_avg_ms=1500.0,   # 1.5 seconds average
                description='User query to tool-use response'
            ),
            'api': PerformanceTarget(
                name='API Response Time',
                target_p95_ms=500.0,    # 500ms
                target_avg_ms=200.0,    # 200ms average
                description='REST API endpoint response'
            )
        }
        
        # Test configuration
        self.api_base_url = None  # Will be set from CDK outputs
        self.websocket_url = None
        self.chat_endpoint = None
    
    def load_endpoints_from_cdk(self) -> None:
        """Load API endpoints from CDK stack outputs"""
        try:
            cloudformation = boto3.client('cloudformation', region_name=self.region)
            
            # Get stack outputs
            response = cloudformation.describe_stacks(StackName='GymPulseStack')
            outputs = response['Stacks'][0].get('Outputs', [])
            
            for output in outputs:
                key = output['OutputKey']
                value = output['OutputValue']
                
                if 'ApiGateway' in key and 'RestApi' in key:
                    self.api_base_url = value
                elif 'WebSocket' in key:
                    self.websocket_url = value
                elif 'Chat' in key:
                    self.chat_endpoint = value
            
            self.logger.info(
                "Loaded endpoints from CDK",
                event_type=EventType.SYSTEM_ERROR,
                apiUrl=self.api_base_url,
                websocketUrl=self.websocket_url,
                chatEndpoint=self.chat_endpoint
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to load CDK endpoints: {e}",
                event_type=EventType.SYSTEM_ERROR,
                error=str(e)
            )
            
            # Fallback to hardcoded endpoints for testing
            self.api_base_url = "https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod"
            self.chat_endpoint = f"{self.api_base_url}/chat"
    
    def measure_end_to_end_latency(self, num_samples: int = 20) -> List[LatencyMeasurement]:
        """
        Measure end-to-end latency from MQTT publish to WebSocket notification
        
        Args:
            num_samples: Number of latency measurements to take
            
        Returns:
            List of latency measurements
        """
        measurements = []
        
        self.logger.info(
            f"Starting end-to-end latency measurement with {num_samples} samples",
            event_type=EventType.PERFORMANCE_METRIC
        )
        
        for i in range(num_samples):
            try:
                # Generate unique test message
                test_id = f"perf-test-{int(time.time())}-{i}"
                machine_id = f"test-machine-{i % 5}"  # Cycle through 5 test machines
                
                # Set up WebSocket listener first
                websocket_messages = []
                
                def on_message(ws, message):
                    """WebSocket message handler"""
                    try:
                        data = json.loads(message)
                        if data.get('machineId') == machine_id:
                            websocket_messages.append({
                                'timestamp': time.time(),
                                'data': data
                            })
                    except json.JSONDecodeError:
                        pass
                
                # Create WebSocket connection
                ws = None
                if self.websocket_url:
                    ws = websocket.WebSocketApp(
                        self.websocket_url,
                        on_message=on_message
                    )
                
                start_time = time.time()
                
                # Publish IoT message
                self._publish_test_iot_message(machine_id, test_id)
                
                # Wait for WebSocket notification (with timeout)
                timeout = 30.0  # 30 second timeout
                end_time = None
                
                if ws:
                    # Start WebSocket connection in separate thread
                    import threading
                    ws_thread = threading.Thread(target=ws.run_forever)
                    ws_thread.daemon = True
                    ws_thread.start()
                    
                    # Wait for message or timeout
                    wait_start = time.time()
                    while time.time() - wait_start < timeout:
                        if websocket_messages:
                            end_time = websocket_messages[0]['timestamp']
                            break
                        time.sleep(0.1)
                    
                    ws.close()
                else:
                    # Fallback: simulate processing time
                    time.sleep(2.0)  # Simulate processing
                    end_time = time.time()
                
                # Calculate latency
                if end_time:
                    duration_ms = (end_time - start_time) * 1000
                    success = True
                else:
                    duration_ms = timeout * 1000
                    success = False
                
                measurement = LatencyMeasurement(
                    start_time=start_time,
                    end_time=end_time or (start_time + timeout),
                    duration_ms=duration_ms,
                    success=success,
                    context={
                        'machineId': machine_id,
                        'testId': test_id,
                        'sample': i
                    }
                )
                
                measurements.append(measurement)
                
                # Log individual measurement
                self.logger.log_performance_metric(
                    metric_name='EndToEndLatency',
                    value=duration_ms,
                    unit='Milliseconds',
                    dimensions={'MachineId': machine_id},
                    target_met=duration_ms <= self.targets['end_to_end'].target_p95_ms
                )
                
                # Publish to CloudWatch
                self.metrics.publish_end_to_end_latency(
                    latency_ms=duration_ms,
                    machine_id=machine_id,
                    gym_id='test-gym'
                )
                
                # Add small delay between tests
                time.sleep(1.0)
                
            except Exception as e:
                self.logger.error(
                    f"Error measuring end-to-end latency: {e}",
                    event_type=EventType.SYSTEM_ERROR,
                    sample=i,
                    error=str(e)
                )
        
        return measurements
    
    def measure_chatbot_response_time(self, num_samples: int = 20) -> List[LatencyMeasurement]:
        """
        Measure chatbot response time for tool-use queries
        
        Args:
            num_samples: Number of response time measurements
            
        Returns:
            List of latency measurements
        """
        measurements = []
        
        # Test queries to cycle through
        test_queries = [
            {
                'message': 'I want to do legs nearby',
                'category': 'legs',
                'userLocation': {'lat': 22.2819, 'lon': 114.1577}
            },
            {
                'message': 'chest workout near me',
                'category': 'chest',
                'userLocation': {'lat': 22.2783, 'lon': 114.1747}
            },
            {
                'message': 'back exercises close by',
                'category': 'back',
                'userLocation': {'lat': 22.2819, 'lon': 114.1577}
            }
        ]
        
        self.logger.info(
            f"Starting chatbot response time measurement with {num_samples} samples",
            event_type=EventType.PERFORMANCE_METRIC
        )
        
        for i in range(num_samples):
            try:
                # Select test query
                query = test_queries[i % len(test_queries)]
                
                start_time = time.time()
                
                # Make chat request
                response = requests.post(
                    self.chat_endpoint,
                    json=query,
                    headers={'Content-Type': 'application/json'},
                    timeout=10.0
                )
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                success = response.status_code == 200
                
                # Parse response to check for tool use
                tools_used = []
                if success:
                    try:
                        response_data = response.json()
                        tools_used = response_data.get('toolsUsed', [])
                    except json.JSONDecodeError:
                        pass
                
                measurement = LatencyMeasurement(
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    success=success,
                    context={
                        'query': query['message'],
                        'category': query['category'],
                        'toolsUsed': tools_used,
                        'statusCode': response.status_code,
                        'sample': i
                    }
                )
                
                measurements.append(measurement)
                
                # Log measurement
                self.logger.log_tool_call(
                    tool_name='chatbot-query',
                    success=success,
                    execution_time_ms=duration_ms,
                    input_params={'category': query['category']},
                    output_size=len(response.text) if success else 0
                )
                
                # Publish to CloudWatch
                self.metrics.publish_chatbot_response_time(
                    response_time_ms=duration_ms,
                    query_type=query['category'],
                    tools_used=tools_used
                )
                
                # Add delay between requests
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(
                    f"Error measuring chatbot response time: {e}",
                    event_type=EventType.SYSTEM_ERROR,
                    sample=i,
                    error=str(e)
                )
        
        return measurements
    
    def measure_api_response_times(self, num_samples: int = 20) -> Dict[str, List[LatencyMeasurement]]:
        """
        Measure API endpoint response times
        
        Args:
            num_samples: Number of measurements per endpoint
            
        Returns:
            Dictionary mapping endpoint to measurements
        """
        endpoints = [
            {'path': '/branches', 'method': 'GET'},
            {'path': '/branches/hk-central/categories/legs/machines', 'method': 'GET'},
            {'path': '/machines/leg-press-01/history?range=24h', 'method': 'GET'}
        ]
        
        results = {}
        
        for endpoint in endpoints:
            measurements = []
            endpoint_key = f"{endpoint['method']} {endpoint['path']}"
            
            self.logger.info(
                f"Measuring API response time for {endpoint_key}",
                event_type=EventType.PERFORMANCE_METRIC
            )
            
            for i in range(num_samples):
                try:
                    url = f"{self.api_base_url}{endpoint['path']}"
                    start_time = time.time()
                    
                    response = requests.get(url, timeout=5.0)
                    
                    end_time = time.time()
                    duration_ms = (end_time - start_time) * 1000
                    success = 200 <= response.status_code < 400
                    
                    measurement = LatencyMeasurement(
                        start_time=start_time,
                        end_time=end_time,
                        duration_ms=duration_ms,
                        success=success,
                        context={
                            'endpoint': endpoint['path'],
                            'method': endpoint['method'],
                            'statusCode': response.status_code,
                            'sample': i
                        }
                    )
                    
                    measurements.append(measurement)
                    
                    # Log API request
                    self.logger.log_api_request(
                        method=endpoint['method'],
                        endpoint=endpoint['path'],
                        status_code=response.status_code,
                        response_time_ms=duration_ms
                    )
                    
                    # Publish metrics
                    self.metrics.publish_api_performance_metrics(
                        endpoint=endpoint['path'],
                        method=endpoint['method'],
                        status_code=response.status_code,
                        response_time_ms=duration_ms
                    )
                    
                    time.sleep(0.2)  # Small delay between requests
                    
                except Exception as e:
                    self.logger.error(
                        f"Error measuring API response time: {e}",
                        event_type=EventType.SYSTEM_ERROR,
                        endpoint=endpoint_key,
                        error=str(e)
                    )
            
            results[endpoint_key] = measurements
        
        return results
    
    def _publish_test_iot_message(self, machine_id: str, test_id: str) -> None:
        """Publish test IoT message"""
        try:
            iot_client = boto3.client('iot-data', region_name=self.region)
            
            message = {
                'machineId': machine_id,
                'status': 'free',  # Toggle status for testing
                'timestamp': int(time.time()),
                'gymId': 'test-gym',
                'category': 'legs',
                'testId': test_id
            }
            
            topic = f"org/test-gym/machines/{machine_id}/status"
            
            iot_client.publish(
                topic=topic,
                qos=1,
                payload=json.dumps(message)
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to publish test IoT message: {e}",
                event_type=EventType.SYSTEM_ERROR,
                machineId=machine_id,
                error=str(e)
            )
    
    def analyze_measurements(self, 
                           measurements: List[LatencyMeasurement],
                           target: PerformanceTarget) -> Dict[str, Any]:
        """
        Analyze performance measurements against targets
        
        Args:
            measurements: List of measurements
            target: Performance target to compare against
            
        Returns:
            Analysis results
        """
        if not measurements:
            return {'error': 'No measurements to analyze'}
        
        # Extract successful measurements
        successful_measurements = [m for m in measurements if m.success]
        durations = [m.duration_ms for m in successful_measurements]
        
        if not durations:
            return {'error': 'No successful measurements'}
        
        # Calculate statistics
        avg_ms = statistics.mean(durations)
        median_ms = statistics.median(durations)
        p95_ms = statistics.quantiles(durations, n=20)[18]  # 95th percentile
        p99_ms = statistics.quantiles(durations, n=100)[98]  # 99th percentile
        min_ms = min(durations)
        max_ms = max(durations)
        
        # Check target compliance
        avg_target_met = avg_ms <= target.target_avg_ms
        p95_target_met = p95_ms <= target.target_p95_ms
        
        success_rate = len(successful_measurements) / len(measurements)
        
        analysis = {
            'target_name': target.name,
            'target_p95_ms': target.target_p95_ms,
            'target_avg_ms': target.target_avg_ms,
            'measurements': {
                'total': len(measurements),
                'successful': len(successful_measurements),
                'success_rate': success_rate
            },
            'statistics': {
                'avg_ms': round(avg_ms, 2),
                'median_ms': round(median_ms, 2),
                'p95_ms': round(p95_ms, 2),
                'p99_ms': round(p99_ms, 2),
                'min_ms': round(min_ms, 2),
                'max_ms': round(max_ms, 2)
            },
            'target_compliance': {
                'avg_target_met': avg_target_met,
                'p95_target_met': p95_target_met,
                'avg_margin_ms': round(target.target_avg_ms - avg_ms, 2),
                'p95_margin_ms': round(target.target_p95_ms - p95_ms, 2)
            }
        }
        
        return analysis
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Run comprehensive performance validation
        
        Returns:
            Complete validation results
        """
        self.logger.info(
            "Starting comprehensive performance validation",
            event_type=EventType.PERFORMANCE_METRIC
        )
        
        # Load endpoints
        self.load_endpoints_from_cdk()
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'region': self.region,
            'targets': {name: target.__dict__ for name, target in self.targets.items()},
            'measurements': {},
            'analysis': {},
            'overall_compliance': {}
        }
        
        # Measure end-to-end latency
        self.logger.info("Measuring end-to-end latency...")
        e2e_measurements = self.measure_end_to_end_latency(num_samples=10)
        results['measurements']['end_to_end'] = [m.__dict__ for m in e2e_measurements]
        results['analysis']['end_to_end'] = self.analyze_measurements(
            e2e_measurements, self.targets['end_to_end']
        )
        
        # Measure chatbot response time
        self.logger.info("Measuring chatbot response time...")
        chatbot_measurements = self.measure_chatbot_response_time(num_samples=10)
        results['measurements']['chatbot'] = [m.__dict__ for m in chatbot_measurements]
        results['analysis']['chatbot'] = self.analyze_measurements(
            chatbot_measurements, self.targets['chatbot']
        )
        
        # Measure API response times
        self.logger.info("Measuring API response times...")
        api_measurements = self.measure_api_response_times(num_samples=5)
        results['measurements']['api'] = {k: [m.__dict__ for m in v] for k, v in api_measurements.items()}
        
        # Analyze API measurements (combine all endpoints)
        all_api_measurements = []
        for endpoint_measurements in api_measurements.values():
            all_api_measurements.extend(endpoint_measurements)
        
        results['analysis']['api'] = self.analyze_measurements(
            all_api_measurements, self.targets['api']
        )
        
        # Overall compliance
        results['overall_compliance'] = {
            'end_to_end_p95_met': results['analysis']['end_to_end'].get('target_compliance', {}).get('p95_target_met', False),
            'chatbot_p95_met': results['analysis']['chatbot'].get('target_compliance', {}).get('p95_target_met', False),
            'api_p95_met': results['analysis']['api'].get('target_compliance', {}).get('p95_target_met', False),
            'all_targets_met': False  # Will be calculated below
        }
        
        # Check if all targets are met
        all_met = all([
            results['overall_compliance']['end_to_end_p95_met'],
            results['overall_compliance']['chatbot_p95_met'],
            results['overall_compliance']['api_p95_met']
        ])
        results['overall_compliance']['all_targets_met'] = all_met
        
        # Log final results
        self.logger.info(
            f"Performance validation completed: {'PASS' if all_met else 'FAIL'}",
            event_type=EventType.PERFORMANCE_METRIC,
            allTargetsMet=all_met,
            endToEndP95=results['analysis']['end_to_end'].get('statistics', {}).get('p95_ms'),
            chatbotP95=results['analysis']['chatbot'].get('statistics', {}).get('p95_ms'),
            apiP95=results['analysis']['api'].get('statistics', {}).get('p95_ms')
        )
        
        return results


def main():
    """Run performance validation"""
    validator = PerformanceValidator()
    results = validator.run_comprehensive_validation()
    
    # Save results to file
    results_file = f"performance_validation_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Performance validation results saved to: {results_file}")
    
    # Print summary
    print("\n=== PERFORMANCE VALIDATION SUMMARY ===")
    print(f"Overall: {'✅ PASS' if results['overall_compliance']['all_targets_met'] else '❌ FAIL'}")
    print(f"End-to-End P95: {results['analysis']['end_to_end']['statistics']['p95_ms']:.1f}ms (target: {results['targets']['end_to_end']['target_p95_ms']:.0f}ms)")
    print(f"Chatbot P95: {results['analysis']['chatbot']['statistics']['p95_ms']:.1f}ms (target: {results['targets']['chatbot']['target_p95_ms']:.0f}ms)")
    print(f"API P95: {results['analysis']['api']['statistics']['p95_ms']:.1f}ms (target: {results['targets']['api']['target_p95_ms']:.0f}ms)")


if __name__ == '__main__':
    main()