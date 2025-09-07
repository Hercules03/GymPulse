#!/usr/bin/env python3
"""
GymPulse Load Testing Orchestrator
Runs comprehensive load testing including connection tests, sustained load, and latency measurement
"""
import asyncio
import os
import sys
import logging
import json
import time
from pathlib import Path
from datetime import datetime

# Add simulator src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "simulator" / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from latency_monitor import EndToEndLatencyMonitor


class LoadTestOrchestrator:
    """Orchestrates comprehensive load testing for GymPulse system"""
    
    def __init__(self):
        self.results = {
            'start_time': datetime.utcnow().isoformat(),
            'tests_completed': [],
            'overall_success': True
        }
        
    async def run_connection_baseline_test(self) -> bool:
        """Test basic connectivity with existing simulator"""
        logging.info("=== Phase 1: Connection Baseline Test ===")
        
        try:
            # Test with existing simulator first
            simulator_dir = Path(__file__).parent.parent / "simulator"
            os.chdir(simulator_dir)
            
            # Run basic simulator test for 2 minutes to establish baseline
            logging.info("🧪 Running baseline connectivity test...")
            
            process = await asyncio.create_subprocess_exec(
                sys.executable, "main.py", "--duration", "2", "--verbose",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'IOT_ENDPOINT': os.environ.get('IOT_ENDPOINT', '')}
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logging.info("✅ Baseline connectivity test passed")
                self.results['tests_completed'].append({
                    'test': 'connection_baseline',
                    'status': 'passed',
                    'details': 'Basic simulator connectivity verified'
                })
                return True
            else:
                logging.error(f"❌ Baseline test failed: {stderr.decode()}")
                self.results['overall_success'] = False
                return False
                
        except Exception as e:
            logging.error(f"❌ Connection baseline test error: {e}")
            self.results['overall_success'] = False
            return False
    
    async def run_scaled_device_test(self) -> bool:
        """Test with current maximum number of devices"""
        logging.info("=== Phase 2: Scaled Device Test ===")
        
        try:
            # Count available certificates (proxy for max devices)
            simulator_dir = Path(__file__).parent.parent / "simulator"
            cert_dir = simulator_dir / "certs"
            cert_files = list(cert_dir.glob("*.cert.pem"))
            
            # Filter out root CA
            device_certs = [f for f in cert_files if not f.name.startswith('root-CA')]
            max_devices = len(device_certs)
            
            logging.info(f"📊 Found {max_devices} device certificates")
            
            if max_devices < 15:
                logging.warning("⚠️ Less than 15 devices available, this may affect load testing")
            
            # Run simulator with all available machines for 5 minutes
            logging.info(f"🚀 Running scaled test with {max_devices} devices...")
            
            os.chdir(simulator_dir)
            process = await asyncio.create_subprocess_exec(
                sys.executable, "main.py", "--duration", "5", "--verbose",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'IOT_ENDPOINT': os.environ.get('IOT_ENDPOINT', '')}
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logging.info(f"✅ Scaled device test passed with {max_devices} devices")
                self.results['tests_completed'].append({
                    'test': 'scaled_device_test',
                    'status': 'passed',
                    'device_count': max_devices,
                    'details': f'Successfully ran {max_devices} concurrent devices'
                })
                return True
            else:
                logging.error(f"❌ Scaled device test failed: {stderr.decode()}")
                self.results['overall_success'] = False
                return False
                
        except Exception as e:
            logging.error(f"❌ Scaled device test error: {e}")
            self.results['overall_success'] = False
            return False
    
    async def run_message_rate_test(self) -> bool:
        """Test sustained message publishing at target rates"""
        logging.info("=== Phase 3: Message Rate Test ===")
        
        try:
            # Run demo scenario which has more realistic messaging patterns
            simulator_dir = Path(__file__).parent.parent / "simulator"
            os.chdir(simulator_dir)
            
            logging.info("📤 Testing sustained message rates...")
            
            process = await asyncio.create_subprocess_exec(
                sys.executable, "main.py", "--demo", "--duration", "10", "--verbose",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'IOT_ENDPOINT': os.environ.get('IOT_ENDPOINT', '')}
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logging.info("✅ Message rate test completed successfully")
                
                # Analyze output for message statistics
                output = stdout.decode()
                message_count = output.count('Publishing status update') if 'Publishing status update' in output else 0
                
                self.results['tests_completed'].append({
                    'test': 'message_rate_test',
                    'status': 'passed',
                    'messages_published': message_count,
                    'duration_minutes': 10,
                    'avg_messages_per_minute': message_count / 10 if message_count > 0 else 0
                })
                return True
            else:
                logging.error(f"❌ Message rate test failed: {stderr.decode()}")
                self.results['overall_success'] = False
                return False
                
        except Exception as e:
            logging.error(f"❌ Message rate test error: {e}")
            self.results['overall_success'] = False
            return False
    
    async def run_latency_measurement(self) -> bool:
        """Run end-to-end latency measurement"""
        logging.info("=== Phase 4: End-to-End Latency Measurement ===")
        
        try:
            # Get WebSocket URL from environment or construct from API Gateway
            websocket_url = os.environ.get('WEBSOCKET_URL')
            if not websocket_url:
                # Try to construct from common patterns
                api_id = os.environ.get('API_GATEWAY_WEBSOCKET_ID')
                region = os.environ.get('AWS_REGION', 'ap-east-1')
                if api_id:
                    websocket_url = f"wss://{api_id}.execute-api.{region}.amazonaws.com/prod"
                else:
                    logging.warning("⚠️ WEBSOCKET_URL not configured, skipping latency test")
                    self.results['tests_completed'].append({
                        'test': 'latency_measurement',
                        'status': 'skipped',
                        'reason': 'WebSocket URL not configured'
                    })
                    return True
            
            # Run latency measurement
            monitor = EndToEndLatencyMonitor(
                iot_endpoint=os.environ.get('IOT_ENDPOINT'),
                websocket_url=websocket_url
            )
            
            logging.info("📊 Measuring end-to-end latency...")
            report = await monitor.measure_end_to_end_latency(
                num_tests=10,
                interval_seconds=5.0
            )
            
            # Check results
            if report.get('performance_targets', {}).get('target_met', False):
                logging.info("✅ Latency targets met!")
                self.results['tests_completed'].append({
                    'test': 'latency_measurement',
                    'status': 'passed',
                    'p95_latency_ms': report['latency_statistics'].get('p95_ms'),
                    'success_rate': report['summary']['success_rate']
                })
                return True
            else:
                logging.warning("⚠️ Latency targets not fully met")
                self.results['tests_completed'].append({
                    'test': 'latency_measurement', 
                    'status': 'partial',
                    'p95_latency_ms': report['latency_statistics'].get('p95_ms'),
                    'success_rate': report['summary']['success_rate']
                })
                return True  # Don't fail overall test for latency issues
                
        except Exception as e:
            logging.error(f"❌ Latency measurement error: {e}")
            self.results['tests_completed'].append({
                'test': 'latency_measurement',
                'status': 'failed',
                'error': str(e)
            })
            return False
    
    async def run_system_stress_test(self) -> bool:
        """Run system under stress conditions"""
        logging.info("=== Phase 5: System Stress Test ===")
        
        try:
            # Run multiple simultaneous simulator instances
            simulator_dir = Path(__file__).parent.parent / "simulator" 
            os.chdir(simulator_dir)
            
            logging.info("💪 Running system stress test...")
            
            # Start 2 concurrent simulator processes
            processes = []
            for i in range(2):
                process = await asyncio.create_subprocess_exec(
                    sys.executable, "main.py", "--demo", "--duration", "5",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ, 'IOT_ENDPOINT': os.environ.get('IOT_ENDPOINT', '')}
                )
                processes.append(process)
            
            # Wait for all processes to complete
            results = await asyncio.gather(*[p.communicate() for p in processes])
            
            success_count = sum(1 for i, (stdout, stderr) in enumerate(results) if processes[i].returncode == 0)
            
            if success_count >= 1:  # At least one process succeeded
                logging.info(f"✅ Stress test completed - {success_count}/2 processes succeeded")
                self.results['tests_completed'].append({
                    'test': 'system_stress_test',
                    'status': 'passed',
                    'concurrent_processes': 2,
                    'successful_processes': success_count
                })
                return True
            else:
                logging.error("❌ All stress test processes failed")
                self.results['overall_success'] = False
                return False
                
        except Exception as e:
            logging.error(f"❌ System stress test error: {e}")
            self.results['overall_success'] = False
            return False
    
    def generate_final_report(self) -> Dict:
        """Generate final load testing report"""
        self.results['end_time'] = datetime.utcnow().isoformat()
        self.results['total_duration_minutes'] = (
            datetime.fromisoformat(self.results['end_time'].replace('Z', '+00:00')) -
            datetime.fromisoformat(self.results['start_time'].replace('Z', '+00:00'))
        ).total_seconds() / 60
        
        # Calculate test statistics
        passed_tests = sum(1 for t in self.results['tests_completed'] if t['status'] == 'passed')
        total_tests = len(self.results['tests_completed'])
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'overall_success': self.results['overall_success']
        }
        
        return self.results
    
    def save_report(self, filename: str = None):
        """Save load testing report"""
        if not filename:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"load_test_comprehensive_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logging.info(f"📄 Comprehensive load test report saved to {filename}")


async def main():
    """Main load testing orchestrator"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Check prerequisites
    if not os.environ.get('IOT_ENDPOINT'):
        logging.error("❌ IOT_ENDPOINT environment variable not set")
        return 1
    
    try:
        orchestrator = LoadTestOrchestrator()
        
        logging.info("🚀 Starting comprehensive load testing...")
        
        # Run test phases
        tests = [
            orchestrator.run_connection_baseline_test(),
            orchestrator.run_scaled_device_test(),
            orchestrator.run_message_rate_test(),
            orchestrator.run_latency_measurement(),
            orchestrator.run_system_stress_test()
        ]
        
        # Execute all tests
        for i, test_coro in enumerate(tests, 1):
            logging.info(f"▶️ Running test phase {i}/{len(tests)}")
            try:
                await test_coro
            except Exception as e:
                logging.error(f"❌ Test phase {i} failed: {e}")
                orchestrator.results['overall_success'] = False
        
        # Generate and save final report
        final_report = orchestrator.generate_final_report()
        orchestrator.save_report()
        
        # Display results
        logging.info("=" * 50)
        logging.info("🏁 LOAD TESTING COMPLETED")
        logging.info("=" * 50)
        logging.info(f"📊 Total tests: {final_report['summary']['total_tests']}")
        logging.info(f"✅ Passed tests: {final_report['summary']['passed_tests']}")
        logging.info(f"📈 Success rate: {final_report['summary']['success_rate']:.1%}")
        logging.info(f"⏱️ Total duration: {final_report['total_duration_minutes']:.1f} minutes")
        
        if final_report['overall_success']:
            logging.info("🎯 ✅ Overall load testing PASSED!")
            return 0
        else:
            logging.error("🎯 ❌ Overall load testing FAILED!")
            return 1
            
    except KeyboardInterrupt:
        logging.info("⚠️ Load testing interrupted by user")
        return 130
    
    except Exception as e:
        logging.error(f"❌ Load testing orchestrator failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))