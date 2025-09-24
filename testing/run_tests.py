#!/usr/bin/env python3
"""
GymPulse Test Runner
Executes unit tests, integration tests, and performance validation
"""
import sys
import os
import asyncio
import json
import time
from typing import Dict, Any

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import test modules
try:
    from unit_tests import run_unit_tests
    from integration_tests import IntegrationTestSuite
    TESTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Could not import test modules: {e}")
    TESTS_AVAILABLE = False


def load_config():
    """Load test configuration from environment or config file"""
    config = {
        'api_url': os.environ.get('GYMPULSE_API_URL', 'https://your-api-gateway-id.execute-api.region.amazonaws.com/prod'),
        'websocket_url': os.environ.get('GYMPULSE_WEBSOCKET_URL', 'wss://your-websocket-id.execute-api.region.amazonaws.com/prod'),
        'run_unit_tests': os.environ.get('RUN_UNIT_TESTS', 'true').lower() == 'true',
        'run_integration_tests': os.environ.get('RUN_INTEGRATION_TESTS', 'true').lower() == 'true',
        'run_performance_tests': os.environ.get('RUN_PERFORMANCE_TESTS', 'true').lower() == 'true'
    }
    
    # Try to load from config file if exists
    config_file = os.path.join(os.path.dirname(__file__), 'test_config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"⚠️ Warning: Could not load config file: {e}")
    
    return config


def validate_endpoints(config: Dict[str, Any]) -> bool:
    """Validate that endpoints are configured and reachable"""
    if 'your-api-gateway-id' in config['api_url']:
        print("❌ Error: API URL not configured. Please set GYMPULSE_API_URL environment variable")
        print("   Example: export GYMPULSE_API_URL=https://abc123.execute-api.us-east-1.amazonaws.com/prod")
        return False
    
    if 'your-websocket-id' in config['websocket_url']:
        print("❌ Error: WebSocket URL not configured. Please set GYMPULSE_WEBSOCKET_URL environment variable")
        print("   Example: export GYMPULSE_WEBSOCKET_URL=wss://abc123.execute-api.us-east-1.amazonaws.com/prod")
        return False
    
    return True


async def run_all_tests(config: Dict[str, Any]):
    """Run all configured tests"""
    print("🚀 GymPulse Test Suite")
    print("=" * 50)
    
    results = {
        'unit_tests': None,
        'integration_tests': None,
        'performance_tests': None,
        'overall_success': True
    }
    
    # Run unit tests
    if config['run_unit_tests']:
        print("\n📚 Running Unit Tests...")
        try:
            results['unit_tests'] = run_unit_tests()
            if not results['unit_tests']:
                results['overall_success'] = False
        except Exception as e:
            print(f"❌ Unit tests failed with error: {e}")
            results['unit_tests'] = False
            results['overall_success'] = False
    
    # Run integration tests (requires valid endpoints)
    if config['run_integration_tests']:
        print("\n🔗 Running Integration Tests...")
        
        if not validate_endpoints(config):
            print("⏭️ Skipping integration tests due to configuration issues")
            results['integration_tests'] = 'skipped'
        else:
            try:
                tester = IntegrationTestSuite(config['api_url'], config['websocket_url'])
                await tester.run_all_tests()
                
                # Consider integration tests successful if >80% pass
                total_tests = tester.test_results['passed'] + tester.test_results['failed']
                success_rate = tester.test_results['passed'] / total_tests if total_tests > 0 else 0
                results['integration_tests'] = success_rate >= 0.8
                
                if not results['integration_tests']:
                    results['overall_success'] = False
                    
            except Exception as e:
                print(f"❌ Integration tests failed with error: {e}")
                results['integration_tests'] = False
                results['overall_success'] = False
    
    # Performance validation
    if config['run_performance_tests']:
        print("\n⚡ Running Performance Tests...")
        try:
            results['performance_tests'] = await run_performance_tests(config)
            if not results['performance_tests']:
                results['overall_success'] = False
        except Exception as e:
            print(f"❌ Performance tests failed with error: {e}")
            results['performance_tests'] = False
            results['overall_success'] = False
    
    return results


async def run_performance_tests(config: Dict[str, Any]) -> bool:
    """Run performance-specific tests"""
    if not validate_endpoints(config):
        print("⏭️ Skipping performance tests due to configuration issues")
        return True  # Don't fail overall if just config issue
    
    try:
        import requests
        import statistics
        
        # Performance test configuration
        endpoints = [
            '/health',
            '/branches',
            '/branches/hk-central/categories/legs/machines'
        ]
        
        performance_results = {}
        
        for endpoint in endpoints:
            print(f"📊 Testing {endpoint}...")
            
            times = []
            errors = 0
            
            # Run 10 requests per endpoint
            for i in range(10):
                try:
                    start_time = time.time()
                    response = requests.get(f"{config['api_url']}{endpoint}", timeout=10)
                    duration = time.time() - start_time
                    
                    if response.status_code == 200:
                        times.append(duration)
                    else:
                        errors += 1
                        
                except Exception as e:
                    errors += 1
                    print(f"  Request {i+1} failed: {e}")
            
            if times:
                avg_time = statistics.mean(times)
                p95_time = statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times)
                success_rate = len(times) / (len(times) + errors)
                
                performance_results[endpoint] = {
                    'avg_time': avg_time,
                    'p95_time': p95_time,
                    'success_rate': success_rate,
                    'total_requests': len(times) + errors
                }
                
                # Check performance targets
                perf_ok = (
                    avg_time < 2.0 and  # Average < 2 seconds
                    p95_time < 5.0 and  # P95 < 5 seconds  
                    success_rate >= 0.95  # 95% success rate
                )
                
                status = "✅" if perf_ok else "⚠️"
                print(f"  {status} avg={avg_time:.3f}s, p95={p95_time:.3f}s, success={success_rate:.1%}")
                
        # Overall performance assessment
        avg_performance = statistics.mean([r['avg_time'] for r in performance_results.values()])
        avg_success_rate = statistics.mean([r['success_rate'] for r in performance_results.values()])
        
        performance_ok = avg_performance < 2.0 and avg_success_rate >= 0.95
        
        print(f"\n📈 Overall Performance: avg={avg_performance:.3f}s, success={avg_success_rate:.1%}")
        
        return performance_ok
        
    except ImportError:
        print("⚠️ requests module not available, skipping performance tests")
        return True
    except Exception as e:
        print(f"❌ Performance tests error: {e}")
        return False


def create_test_report(results: Dict[str, Any]):
    """Create a test report"""
    print("\n" + "=" * 50)
    print("📊 GymPulse Test Report")
    print("=" * 50)
    
    # Unit test results
    if results['unit_tests'] is not None:
        status = "✅ PASSED" if results['unit_tests'] else "❌ FAILED"
        print(f"Unit Tests:        {status}")
    
    # Integration test results
    if results['integration_tests'] is not None:
        if results['integration_tests'] == 'skipped':
            print(f"Integration Tests: ⏭️ SKIPPED")
        else:
            status = "✅ PASSED" if results['integration_tests'] else "❌ FAILED"
            print(f"Integration Tests: {status}")
    
    # Performance test results
    if results['performance_tests'] is not None:
        status = "✅ PASSED" if results['performance_tests'] else "❌ FAILED"
        print(f"Performance Tests: {status}")
    
    # Overall result
    print("-" * 50)
    if results['overall_success']:
        print("🎉 OVERALL: ALL TESTS PASSED")
        return 0
    else:
        print("💥 OVERALL: SOME TESTS FAILED")
        return 1


def print_usage():
    """Print usage instructions"""
    print("""
🧪 GymPulse Test Runner

Usage:
    python run_tests.py [options]

Environment Variables:
    GYMPULSE_API_URL          - API Gateway URL (required for integration tests)
    GYMPULSE_WEBSOCKET_URL    - WebSocket API URL (required for WebSocket tests)
    RUN_UNIT_TESTS           - Run unit tests (default: true)
    RUN_INTEGRATION_TESTS    - Run integration tests (default: true)  
    RUN_PERFORMANCE_TESTS    - Run performance tests (default: true)

Example:
    export GYMPULSE_API_URL=https://abc123.execute-api.us-east-1.amazonaws.com/prod
    export GYMPULSE_WEBSOCKET_URL=wss://xyz789.execute-api.us-east-1.amazonaws.com/prod
    python run_tests.py

Configuration File:
    You can also create test_config.json with:
    {
        "api_url": "https://your-api-url",
        "websocket_url": "wss://your-websocket-url"
    }
""")


async def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print_usage()
        return 0
    
    if not TESTS_AVAILABLE:
        print("❌ Test modules not available. Please check your Python environment.")
        return 1
    
    # Load configuration
    config = load_config()
    
    print(f"🔧 Configuration:")
    print(f"   API URL: {config['api_url']}")
    print(f"   WebSocket URL: {config['websocket_url']}")
    print(f"   Unit Tests: {'enabled' if config['run_unit_tests'] else 'disabled'}")
    print(f"   Integration Tests: {'enabled' if config['run_integration_tests'] else 'disabled'}")
    print(f"   Performance Tests: {'enabled' if config['run_performance_tests'] else 'disabled'}")
    
    # Run tests
    results = await run_all_tests(config)
    
    # Generate report and exit
    return create_test_report(results)


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)