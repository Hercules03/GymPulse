#!/usr/bin/env python3
"""
GymPulse Load Testing Script
Scales up to 50 concurrent devices for sustained load testing
"""
import asyncio
import json
import logging
import time
import sys
import os
import random
import statistics
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from machine_simulator import MachineSimulator
from usage_patterns import UsagePatterns


class LoadTestRunner:
    """Manages load testing with 50 concurrent devices"""
    
    def __init__(self, config_path: str = "load-test-config.json"):
        self.config_path = config_path
        self.simulators: List[MachineSimulator] = []
        self.performance_metrics = {
            'connection_times': [],
            'publish_latencies': [],
            'connection_failures': 0,
            'publish_failures': 0,
            'messages_sent': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Load configuration
        self.load_config()
        
    def load_config(self):
        """Load load testing configuration"""
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
            
        self.target_devices = self.config['load_test']['target_devices']
        self.test_duration = self.config['load_test']['test_duration_minutes']
        self.message_rate = self.config['load_test']['message_rate_per_device']
        
    def generate_machine_inventory(self) -> List[Dict[str, Any]]:
        """Generate 50 machine configurations dynamically"""
        machines = []
        machine_counter = 1
        
        for branch in self.config['branches']:
            branch_machines = branch['load_test_machines']
            
            for i in range(branch_machines):
                # Distribute machines across categories
                category = self._get_weighted_category()
                machine_type = random.choice(self.config['machine_types'][category]['types'])
                
                machine = {
                    'machineId': f"{machine_type}-{machine_counter:03d}",
                    'name': f"{machine_type.replace('-', ' ').title()} {machine_counter}",
                    'category': category,
                    'type': machine_type,
                    'gymId': branch['id'],
                    'coordinates': branch['coordinates']
                }
                machines.append(machine)
                machine_counter += 1
                
        return machines
    
    def _get_weighted_category(self) -> str:
        """Get category based on weights"""
        categories = list(self.config['machine_types'].keys())
        weights = [self.config['machine_types'][cat]['weight'] for cat in categories]
        return random.choices(categories, weights=weights)[0]
    
    async def setup_simulators(self) -> bool:
        """Set up 50 concurrent machine simulators"""
        logging.info(f"🏗️ Setting up {self.target_devices} concurrent simulators...")
        
        machines = self.generate_machine_inventory()
        
        # Create simulators for each machine
        for i, machine in enumerate(machines):
            try:
                simulator = MachineSimulator(
                    machine_id=machine['machineId'],
                    gym_id=machine['gymId'],
                    category=machine['category'],
                    endpoint=os.environ.get('IOT_ENDPOINT'),
                    cert_path=f"certs/{machine['machineId']}.cert.pem",
                    key_path=f"certs/{machine['machineId']}.private.key",
                    ca_path="certs/root-CA.crt"
                )
                
                # Configure realistic usage patterns
                patterns = UsagePatterns(machine['category'])
                simulator.set_usage_patterns(patterns)
                
                self.simulators.append(simulator)
                
            except Exception as e:
                logging.error(f"❌ Failed to create simulator for {machine['machineId']}: {e}")
                return False
        
        logging.info(f"✅ Created {len(self.simulators)} simulators")
        return True
    
    async def run_connection_test(self) -> Dict[str, Any]:
        """Test connection establishment for all devices"""
        logging.info("🔌 Testing connection establishment...")
        
        connection_results = {
            'successful': 0,
            'failed': 0,
            'connection_times': [],
            'errors': []
        }
        
        # Connect all simulators with timing
        connection_tasks = []
        for simulator in self.simulators:
            task = self._connect_with_timing(simulator)
            connection_tasks.append(task)
        
        # Execute connections with controlled ramp-up
        ramp_up_time = self.config['load_test']['ramp_up_time_seconds']
        batch_size = 10  # Connect 10 devices at a time
        
        for i in range(0, len(connection_tasks), batch_size):
            batch = connection_tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    connection_results['failed'] += 1
                    connection_results['errors'].append(str(result))
                else:
                    connection_results['successful'] += 1
                    connection_results['connection_times'].append(result)
            
            # Wait between batches for ramp-up
            if i + batch_size < len(connection_tasks):
                await asyncio.sleep(ramp_up_time / (len(connection_tasks) // batch_size))
        
        # Calculate connection statistics
        if connection_results['connection_times']:
            avg_time = statistics.mean(connection_results['connection_times'])
            p95_time = statistics.quantiles(connection_results['connection_times'], n=20)[18]  # 95th percentile
            
            logging.info(f"📊 Connection Results:")
            logging.info(f"  ✅ Successful: {connection_results['successful']}")
            logging.info(f"  ❌ Failed: {connection_results['failed']}")
            logging.info(f"  ⏱️ Average time: {avg_time:.2f}ms")
            logging.info(f"  📈 P95 time: {p95_time:.2f}ms")
        
        return connection_results
    
    async def _connect_with_timing(self, simulator: MachineSimulator) -> float:
        """Connect simulator with timing measurement"""
        start_time = time.perf_counter()
        
        try:
            await simulator.connect()
            end_time = time.perf_counter()
            return (end_time - start_time) * 1000  # Convert to milliseconds
        except Exception as e:
            raise Exception(f"Connection failed for {simulator.machine_id}: {e}")
    
    async def run_sustained_load_test(self) -> Dict[str, Any]:
        """Run sustained load test for specified duration"""
        logging.info(f"🚀 Starting sustained load test for {self.test_duration} minutes...")
        
        self.performance_metrics['start_time'] = datetime.utcnow()
        
        # Start all simulators
        simulation_tasks = []
        for simulator in self.simulators:
            task = self._run_simulator_with_metrics(simulator)
            simulation_tasks.append(task)
        
        # Run for test duration
        try:
            await asyncio.wait_for(
                asyncio.gather(*simulation_tasks, return_exceptions=True),
                timeout=self.test_duration * 60
            )
        except asyncio.TimeoutError:
            logging.info("⏰ Test duration reached, stopping simulators...")
        
        self.performance_metrics['end_time'] = datetime.utcnow()
        
        # Stop all simulators
        await self._stop_all_simulators()
        
        return self._generate_performance_report()
    
    async def _run_simulator_with_metrics(self, simulator: MachineSimulator):
        """Run simulator with performance metric collection"""
        try:
            while True:
                # Publish message with timing
                start_time = time.perf_counter()
                
                try:
                    await simulator.publish_status_update()
                    end_time = time.perf_counter()
                    
                    # Record metrics
                    latency = (end_time - start_time) * 1000
                    self.performance_metrics['publish_latencies'].append(latency)
                    self.performance_metrics['messages_sent'] += 1
                    
                except Exception as e:
                    self.performance_metrics['publish_failures'] += 1
                    logging.debug(f"Publish failed for {simulator.machine_id}: {e}")
                
                # Wait between messages (1-2 per minute as specified)
                await asyncio.sleep(random.randint(
                    self.message_rate['min_interval_seconds'],
                    self.message_rate['max_interval_seconds']
                ))
                
        except asyncio.CancelledError:
            logging.debug(f"Simulator {simulator.machine_id} cancelled")
    
    async def _stop_all_simulators(self):
        """Stop all simulators gracefully"""
        logging.info("🛑 Stopping all simulators...")
        
        stop_tasks = []
        for simulator in self.simulators:
            if hasattr(simulator, 'disconnect'):
                task = simulator.disconnect()
                stop_tasks.append(task)
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
    
    def _generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        metrics = self.performance_metrics
        
        # Calculate duration
        if metrics['start_time'] and metrics['end_time']:
            duration = (metrics['end_time'] - metrics['start_time']).total_seconds()
        else:
            duration = self.test_duration * 60
        
        # Calculate message rate
        messages_per_second = metrics['messages_sent'] / duration if duration > 0 else 0
        
        # Calculate latency statistics
        latency_stats = {}
        if metrics['publish_latencies']:
            latencies = metrics['publish_latencies']
            latency_stats = {
                'avg_ms': statistics.mean(latencies),
                'p50_ms': statistics.median(latencies),
                'p95_ms': statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies),
                'p99_ms': statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else max(latencies),
                'max_ms': max(latencies),
                'min_ms': min(latencies)
            }
        
        # Calculate success rates
        total_attempts = metrics['messages_sent'] + metrics['publish_failures']
        success_rate = metrics['messages_sent'] / total_attempts if total_attempts > 0 else 0
        
        report = {
            'test_summary': {
                'target_devices': self.target_devices,
                'actual_devices': len(self.simulators),
                'duration_seconds': duration,
                'test_completed': datetime.utcnow().isoformat()
            },
            'performance': {
                'messages_sent': metrics['messages_sent'],
                'messages_failed': metrics['publish_failures'],
                'success_rate': success_rate,
                'messages_per_second': messages_per_second,
                'target_met': success_rate >= self.config['performance_targets']['message_success_rate']
            },
            'latency': latency_stats,
            'targets_vs_actual': {
                'target_success_rate': self.config['performance_targets']['message_success_rate'],
                'actual_success_rate': success_rate,
                'target_msg_per_min': self.config['performance_targets']['target_messages_per_minute'],
                'actual_msg_per_min': messages_per_second * 60
            }
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save performance report to file"""
        if not filename:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"load_test_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logging.info(f"📄 Performance report saved to {filename}")


async def main():
    """Main load testing function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Check for IoT endpoint
    if not os.environ.get('IOT_ENDPOINT'):
        logging.error("❌ IOT_ENDPOINT environment variable not set")
        return 1
    
    try:
        # Create load test runner
        runner = LoadTestRunner()
        
        # Setup simulators
        if not await runner.setup_simulators():
            logging.error("❌ Failed to setup simulators")
            return 1
        
        # Run connection test
        logging.info("=== Phase 1: Connection Testing ===")
        connection_results = await runner.run_connection_test()
        
        if connection_results['successful'] < runner.target_devices * 0.9:
            logging.error(f"❌ Too many connection failures: {connection_results['failed']}")
            return 1
        
        # Run sustained load test
        logging.info("=== Phase 2: Sustained Load Testing ===")
        performance_report = await runner.run_sustained_load_test()
        
        # Save and display results
        runner.save_report(performance_report)
        
        logging.info("=== Load Test Results ===")
        logging.info(f"📊 Devices: {performance_report['test_summary']['actual_devices']}")
        logging.info(f"⏱️ Duration: {performance_report['test_summary']['duration_seconds']:.1f}s")
        logging.info(f"📤 Messages sent: {performance_report['performance']['messages_sent']}")
        logging.info(f"✅ Success rate: {performance_report['performance']['success_rate']:.3f}")
        logging.info(f"📈 Msg/sec: {performance_report['performance']['messages_per_second']:.2f}")
        
        if 'latency' in performance_report and performance_report['latency']:
            logging.info(f"⚡ P95 latency: {performance_report['latency']['p95_ms']:.2f}ms")
        
        # Check if targets were met
        if performance_report['performance']['target_met']:
            logging.info("🎯 ✅ All performance targets met!")
            return 0
        else:
            logging.warning("🎯 ⚠️ Some performance targets not met")
            return 2
    
    except KeyboardInterrupt:
        logging.info("⚠️ Load test interrupted by user")
        return 130
    
    except Exception as e:
        logging.error(f"❌ Load test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))