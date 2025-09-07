#!/usr/bin/env python3
"""
End-to-End Latency Measurement System
Measures latency from MQTT publish to UI tile update via WebSocket
"""
import asyncio
import json
import time
import boto3
import websockets
import statistics
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class LatencyMeasurement:
    """Single latency measurement result"""
    test_id: str
    mqtt_publish_time: float
    websocket_receive_time: Optional[float]
    end_to_end_latency_ms: Optional[float]
    success: bool
    error_message: Optional[str] = None


class EndToEndLatencyMonitor:
    """Monitors end-to-end latency from IoT to WebSocket"""
    
    def __init__(self, 
                 iot_endpoint: str,
                 websocket_url: str,
                 aws_region: str = 'ap-east-1'):
        self.iot_endpoint = iot_endpoint
        self.websocket_url = websocket_url
        self.aws_region = aws_region
        
        # Initialize AWS clients
        self.iot_client = boto3.client('iot-data', region_name=aws_region)
        
        # Measurement tracking
        self.measurements: List[LatencyMeasurement] = []
        self.pending_messages: Dict[str, float] = {}
        
        # WebSocket connection
        self.websocket = None
        
    async def connect_websocket(self) -> bool:
        """Connect to WebSocket endpoint"""
        try:
            logging.info(f"🔌 Connecting to WebSocket: {self.websocket_url}")
            self.websocket = await websockets.connect(self.websocket_url)
            logging.info("✅ WebSocket connected successfully")
            return True
            
        except Exception as e:
            logging.error(f"❌ WebSocket connection failed: {e}")
            return False
    
    async def disconnect_websocket(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            logging.info("🔌 WebSocket disconnected")
    
    async def measure_end_to_end_latency(self, 
                                       machine_id: str = "test-machine-01",
                                       num_tests: int = 10,
                                       interval_seconds: float = 5.0) -> Dict[str, Any]:
        """
        Measure end-to-end latency from MQTT publish to WebSocket receive
        
        Args:
            machine_id: Machine ID to use for testing
            num_tests: Number of latency measurements to take
            interval_seconds: Interval between measurements
            
        Returns:
            Dictionary containing latency statistics and results
        """
        logging.info(f"🚀 Starting end-to-end latency measurement...")
        logging.info(f"📊 Tests: {num_tests}, Interval: {interval_seconds}s")
        
        # Connect to WebSocket
        if not await self.connect_websocket():
            return {'error': 'Failed to connect to WebSocket'}
        
        # Start WebSocket listener
        listener_task = asyncio.create_task(self._websocket_listener())
        
        try:
            # Run latency tests
            for i in range(num_tests):
                test_id = f"latency-test-{int(time.time())}-{i:03d}"
                
                logging.info(f"📤 Test {i+1}/{num_tests}: {test_id}")
                
                # Publish MQTT message with timing
                await self._publish_test_message(machine_id, test_id)
                
                # Wait for next test
                if i < num_tests - 1:
                    await asyncio.sleep(interval_seconds)
            
            # Wait for remaining responses (timeout after 30s)
            await asyncio.sleep(30)
            
        finally:
            # Stop WebSocket listener
            listener_task.cancel()
            await self.disconnect_websocket()
        
        # Generate latency report
        return self._generate_latency_report()
    
    async def _publish_test_message(self, machine_id: str, test_id: str):
        """Publish test message to MQTT topic"""
        publish_time = time.perf_counter()
        
        test_message = {
            'machineId': machine_id,
            'status': 'free' if int(time.time()) % 2 == 0 else 'occupied',
            'timestamp': int(time.time()),
            'testId': test_id,
            'latencyTest': True
        }
        
        topic = f"org/hk-central/machines/{machine_id}/status"
        
        try:
            # Publish via AWS IoT
            self.iot_client.publish(
                topic=topic,
                payload=json.dumps(test_message),
                qos=1  # At least once delivery
            )
            
            # Record publish time
            self.pending_messages[test_id] = publish_time
            
            logging.debug(f"📤 Published: {test_id} at {publish_time}")
            
        except Exception as e:
            # Record failed measurement
            measurement = LatencyMeasurement(
                test_id=test_id,
                mqtt_publish_time=publish_time,
                websocket_receive_time=None,
                end_to_end_latency_ms=None,
                success=False,
                error_message=f"MQTT publish failed: {e}"
            )
            self.measurements.append(measurement)
            logging.error(f"❌ MQTT publish failed for {test_id}: {e}")
    
    async def _websocket_listener(self):
        """Listen for WebSocket messages and measure receive times"""
        try:
            while True:
                # Receive WebSocket message
                message = await self.websocket.recv()
                receive_time = time.perf_counter()
                
                try:
                    data = json.loads(message)
                    
                    # Check if this is a test message
                    if (data.get('type') == 'machine_update' and 
                        'testId' in data and 
                        data.get('latencyTest')):
                        
                        test_id = data['testId']
                        
                        if test_id in self.pending_messages:
                            publish_time = self.pending_messages[test_id]
                            latency_ms = (receive_time - publish_time) * 1000
                            
                            # Record successful measurement
                            measurement = LatencyMeasurement(
                                test_id=test_id,
                                mqtt_publish_time=publish_time,
                                websocket_receive_time=receive_time,
                                end_to_end_latency_ms=latency_ms,
                                success=True
                            )
                            self.measurements.append(measurement)
                            
                            # Remove from pending
                            del self.pending_messages[test_id]
                            
                            logging.info(f"📥 Received: {test_id} - Latency: {latency_ms:.2f}ms")
                        
                except json.JSONDecodeError:
                    logging.debug("Received non-JSON WebSocket message")
                
        except asyncio.CancelledError:
            logging.debug("WebSocket listener cancelled")
        except Exception as e:
            logging.error(f"❌ WebSocket listener error: {e}")
    
    def _generate_latency_report(self) -> Dict[str, Any]:
        """Generate comprehensive latency report"""
        successful_measurements = [m for m in self.measurements if m.success]
        failed_measurements = [m for m in self.measurements if not m.success]
        
        # Handle pending (timed out) measurements
        for test_id, publish_time in self.pending_messages.items():
            timeout_measurement = LatencyMeasurement(
                test_id=test_id,
                mqtt_publish_time=publish_time,
                websocket_receive_time=None,
                end_to_end_latency_ms=None,
                success=False,
                error_message="Timeout - no WebSocket response received"
            )
            failed_measurements.append(timeout_measurement)
        
        total_tests = len(self.measurements) + len(self.pending_messages)
        success_rate = len(successful_measurements) / total_tests if total_tests > 0 else 0
        
        # Calculate latency statistics
        latency_stats = {}
        if successful_measurements:
            latencies = [m.end_to_end_latency_ms for m in successful_measurements]
            
            latency_stats = {
                'count': len(latencies),
                'avg_ms': statistics.mean(latencies),
                'median_ms': statistics.median(latencies),
                'min_ms': min(latencies),
                'max_ms': max(latencies),
                'std_dev_ms': statistics.stdev(latencies) if len(latencies) > 1 else 0,
            }
            
            # Calculate percentiles
            if len(latencies) >= 10:
                sorted_latencies = sorted(latencies)
                latency_stats.update({
                    'p95_ms': sorted_latencies[int(len(sorted_latencies) * 0.95)],
                    'p99_ms': sorted_latencies[int(len(sorted_latencies) * 0.99)]
                })
        
        # Generate report
        report = {
            'summary': {
                'total_tests': total_tests,
                'successful': len(successful_measurements),
                'failed': len(failed_measurements),
                'timed_out': len(self.pending_messages),
                'success_rate': success_rate,
                'timestamp': datetime.utcnow().isoformat()
            },
            'latency_statistics': latency_stats,
            'performance_targets': {
                'target_p95_ms': 15000,  # 15 seconds as per Phase 9
                'actual_p95_ms': latency_stats.get('p95_ms'),
                'target_met': (latency_stats.get('p95_ms', float('inf')) <= 15000) if latency_stats else False
            },
            'failures': [
                {
                    'test_id': m.test_id,
                    'error': m.error_message
                } for m in failed_measurements
            ]
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save latency report to file"""
        if not filename:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"latency_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logging.info(f"📄 Latency report saved to {filename}")


async def continuous_monitoring(monitor: EndToEndLatencyMonitor, 
                              duration_minutes: int = 30,
                              test_interval_seconds: int = 60):
    """
    Run continuous latency monitoring for specified duration
    """
    logging.info(f"🔄 Starting continuous monitoring for {duration_minutes} minutes")
    
    end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
    test_count = 0
    
    while datetime.utcnow() < end_time:
        test_count += 1
        logging.info(f"🔍 Continuous test #{test_count}")
        
        # Single latency measurement
        report = await monitor.measure_end_to_end_latency(
            num_tests=1,
            interval_seconds=0
        )
        
        # Log current latency if successful
        if (report.get('latency_statistics') and 
            report['latency_statistics'].get('avg_ms')):
            latency = report['latency_statistics']['avg_ms']
            logging.info(f"⚡ Current latency: {latency:.2f}ms")
        
        # Wait for next test
        await asyncio.sleep(test_interval_seconds)
    
    logging.info("✅ Continuous monitoring completed")


async def main():
    """Main latency monitoring function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Get configuration from environment
    iot_endpoint = os.environ.get('IOT_ENDPOINT')
    websocket_url = os.environ.get('WEBSOCKET_URL', 'wss://your-websocket-api.execute-api.region.amazonaws.com/prod')
    
    if not iot_endpoint:
        logging.error("❌ IOT_ENDPOINT environment variable not set")
        return 1
    
    try:
        # Create latency monitor
        monitor = EndToEndLatencyMonitor(iot_endpoint, websocket_url)
        
        # Run latency measurement
        logging.info("=== End-to-End Latency Testing ===")
        report = await monitor.measure_end_to_end_latency(
            num_tests=20,  # Increased for better statistics
            interval_seconds=3.0
        )
        
        # Save and display results
        monitor.save_report(report)
        
        logging.info("=== Latency Test Results ===")
        logging.info(f"📊 Total tests: {report['summary']['total_tests']}")
        logging.info(f"✅ Success rate: {report['summary']['success_rate']:.3f}")
        
        if report['latency_statistics']:
            stats = report['latency_statistics']
            logging.info(f"⚡ Average latency: {stats['avg_ms']:.2f}ms")
            logging.info(f"📈 P95 latency: {stats.get('p95_ms', 'N/A')}ms")
            logging.info(f"🎯 Target met: {report['performance_targets']['target_met']}")
        
        if report['summary']['failed'] > 0:
            logging.warning(f"⚠️ {report['summary']['failed']} tests failed")
        
        return 0 if report['performance_targets']['target_met'] else 2
        
    except KeyboardInterrupt:
        logging.info("⚠️ Latency monitoring interrupted by user")
        return 130
    
    except Exception as e:
        logging.error(f"❌ Latency monitoring failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))