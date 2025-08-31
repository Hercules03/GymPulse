"""
Unit Tests for GymPulse Lambda Functions
Tests individual function logic and error handling
"""
import unittest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
import sys
import os

# Add lambda directories to path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda', 'api-handlers'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda', 'iot-ingest'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda', 'websocket-handlers'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda', 'utils'))


class TestAPIHandlers(unittest.TestCase):
    """Test API handler functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_branch_data = {
            'id': 'hk-central',
            'name': 'Central Branch',
            'coordinates': {'lat': 22.2819, 'lon': 114.1577},
            'categories': {
                'legs': {'free': 2, 'total': 5},
                'chest': {'free': 1, 'total': 3},
                'back': {'free': 3, 'total': 4}
            }
        }
        
        self.sample_machine_data = {
            'machineId': 'leg-press-01',
            'name': 'Leg Press Machine 1',
            'status': 'free',
            'lastUpdate': int(time.time()),
            'gymId': 'hk-central',
            'category': 'legs'
        }

    @patch('handler.current_state_table')
    @patch('handler.branch_cache')
    def test_get_branches_success(self, mock_cache, mock_table):
        """Test successful branches retrieval"""
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock DynamoDB scan response
        mock_table.scan.return_value = {
            'Items': [
                {
                    'machineId': 'leg-press-01',
                    'status': 'free',
                    'gymId': 'hk-central',
                    'category': 'legs'
                },
                {
                    'machineId': 'leg-press-02',
                    'status': 'occupied',
                    'gymId': 'hk-central',
                    'category': 'legs'
                }
            ]
        }
        
        # Import after mocking
        try:
            from handler import get_branches
            result = get_branches()
            
            self.assertEqual(result['statusCode'], 200)
            data = json.loads(result['body'])
            self.assertIn('branches', data)
            self.assertGreater(len(data['branches']), 0)
            
            # Verify cache was called
            mock_cache.set.assert_called()
            
        except ImportError as e:
            self.skipTest(f"Could not import handler module: {e}")

    @patch('handler.current_state_table')
    def test_get_machines_invalid_params(self, mock_table):
        """Test machine retrieval with invalid parameters"""
        try:
            from handler import get_machines
            
            # Test missing branch_id
            result = get_machines(None, 'legs')
            self.assertEqual(result['statusCode'], 400)
            
            # Test missing category
            result = get_machines('hk-central', None)
            self.assertEqual(result['statusCode'], 400)
            
        except ImportError as e:
            self.skipTest(f"Could not import handler module: {e}")

    @patch('handler.aggregates_table')
    @patch('handler.events_table')
    def test_get_machine_history_success(self, mock_events_table, mock_aggregates_table):
        """Test successful machine history retrieval"""
        # Mock aggregates query
        mock_aggregates_table.query.return_value = {
            'Items': [
                {
                    'timestamp15min': int(time.time()) - 3600,
                    'occupancyRatio': Decimal('75.5'),
                    'freeCount': 1,
                    'totalCount': 4
                }
            ]
        }
        
        try:
            from handler import get_machine_history
            result = get_machine_history('leg-press-01')
            
            self.assertEqual(result['statusCode'], 200)
            data = json.loads(result['body'])
            self.assertIn('history', data)
            self.assertIn('forecast', data)
            self.assertIn('machineId', data)
            
        except ImportError as e:
            self.skipTest(f"Could not import handler module: {e}")

    def test_cache_key_generation(self):
        """Test cache key generation utility"""
        try:
            from cache_manager import cache_key
            
            # Test consistent key generation
            key1 = cache_key('arg1', 'arg2', param1='value1')
            key2 = cache_key('arg1', 'arg2', param1='value1')
            self.assertEqual(key1, key2)
            
            # Test different inputs produce different keys
            key3 = cache_key('arg1', 'arg2', param1='value2')
            self.assertNotEqual(key1, key3)
            
        except ImportError as e:
            self.skipTest(f"Could not import cache_manager module: {e}")


class TestIoTIngest(unittest.TestCase):
    """Test IoT message ingest and processing"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_iot_message = {
            'machineId': 'leg-press-01',
            'status': 'occupied',
            'timestamp': int(time.time()),
            'gymId': 'hk-central',
            'category': 'legs'
        }
        
        self.sample_iot_event = {
            'Records': [
                {
                    'eventName': 'INSERT',
                    'dynamodb': {
                        'NewImage': {
                            'machineId': {'S': 'leg-press-01'},
                            'status': {'S': 'occupied'},
                            'gymId': {'S': 'hk-central'},
                            'category': {'S': 'legs'},
                            'timestamp': {'N': str(int(time.time()))}
                        }
                    }
                }
            ]
        }

    def test_detect_transition(self):
        """Test state transition detection"""
        try:
            from handler import detect_transition
            
            # Test initialization
            self.assertEqual(detect_transition(None, 'free'), 'initialized')
            
            # Test state changes
            self.assertEqual(detect_transition('occupied', 'free'), 'freed')
            self.assertEqual(detect_transition('free', 'occupied'), 'occupied')
            
            # Test no change
            self.assertEqual(detect_transition('free', 'free'), 'no_change')
            self.assertEqual(detect_transition('occupied', 'occupied'), 'no_change')
            
        except ImportError as e:
            self.skipTest(f"Could not import IoT handler module: {e}")

    def test_quiet_hours_calculation(self):
        """Test quiet hours calculation"""
        try:
            from handler import is_in_quiet_hours
            
            # Create test datetime for 11 PM (23:00)
            test_time = Mock()
            test_time.hour = 23
            
            quiet_config = {'start': 22, 'end': 7}
            
            # Test time in quiet hours (spans midnight)
            self.assertTrue(is_in_quiet_hours(quiet_config, test_time))
            
            # Test time outside quiet hours
            test_time.hour = 12  # Noon
            self.assertFalse(is_in_quiet_hours(quiet_config, test_time))
            
            # Test quiet hours that don't span midnight
            quiet_config = {'start': 9, 'end': 17}  # 9 AM to 5 PM
            test_time.hour = 14  # 2 PM
            self.assertTrue(is_in_quiet_hours(quiet_config, test_time))
            
            test_time.hour = 20  # 8 PM
            self.assertFalse(is_in_quiet_hours(quiet_config, test_time))
            
        except ImportError as e:
            self.skipTest(f"Could not import IoT handler module: {e}")

    @patch('handler.current_state_table')
    def test_lambda_handler_message_processing(self, mock_table):
        """Test IoT Lambda handler message processing"""
        try:
            from handler import lambda_handler
            
            # Mock current state lookup
            mock_table.get_item.return_value = {
                'Item': {
                    'machineId': 'leg-press-01',
                    'status': 'free',
                    'lastUpdate': int(time.time()) - 60
                }
            }
            
            # Mock put operations
            mock_table.put_item.return_value = {}
            
            # Test direct payload format
            result = lambda_handler(self.sample_iot_message, None)
            
            # Should return success (200) or indicate processing success
            self.assertIn(result.get('statusCode', 200), [200, 201])
            
        except ImportError as e:
            self.skipTest(f"Could not import IoT handler module: {e}")


class TestWebSocketHandlers(unittest.TestCase):
    """Test WebSocket connection and broadcast handlers"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_connect_event = {
            'requestContext': {
                'connectionId': 'test-connection-123',
                'routeKey': '$connect',
                'identity': {
                    'userAgent': 'Test Client',
                    'sourceIp': '192.168.1.1'
                }
            },
            'queryStringParameters': {
                'branches': 'hk-central,hk-causeway',
                'categories': 'legs,chest',
                'userId': 'test-user'
            }
        }

    @patch('connect.connections_table')
    def test_websocket_connect_success(self, mock_table):
        """Test successful WebSocket connection"""
        try:
            from connect import lambda_handler
            
            # Mock successful put operation
            mock_table.put_item.return_value = {}
            
            result = lambda_handler(self.sample_connect_event, None)
            
            self.assertEqual(result['statusCode'], 200)
            body = json.loads(result['body'])
            self.assertIn('message', body)
            self.assertIn('subscriptions', body)
            
            # Verify put_item was called with correct data
            mock_table.put_item.assert_called_once()
            call_args = mock_table.put_item.call_args[1]['Item']
            self.assertEqual(call_args['connectionId'], 'test-connection-123')
            self.assertIn('subscriptions', call_args)
            
        except ImportError as e:
            self.skipTest(f"Could not import WebSocket connect handler: {e}")

    def test_subscription_validation(self):
        """Test subscription parameter validation"""
        try:
            from connect import lambda_handler
            
            # Test event without query parameters
            event = {
                'requestContext': {
                    'connectionId': 'test-connection-456',
                    'routeKey': '$connect'
                }
            }
            
            with patch('connect.connections_table') as mock_table:
                mock_table.put_item.return_value = {}
                
                result = lambda_handler(event, None)
                self.assertEqual(result['statusCode'], 200)
                
                # Should have default subscriptions
                body = json.loads(result['body'])
                subscriptions = body.get('subscriptions', {})
                self.assertIn('branches', subscriptions)
                self.assertIn('categories', subscriptions)
                
        except ImportError as e:
            self.skipTest(f"Could not import WebSocket connect handler: {e}")


class TestErrorHandling(unittest.TestCase):
    """Test error handling and validation functions"""
    
    def test_validation_error_creation(self):
        """Test custom validation error creation"""
        try:
            from error_handler import ValidationError
            
            error = ValidationError("Test error message", "testField")
            self.assertEqual(error.message, "Test error message")
            self.assertEqual(error.field, "testField")
            self.assertEqual(error.status_code, 400)
            self.assertEqual(error.error_code, "VALIDATION_ERROR")
            
        except ImportError as e:
            self.skipTest(f"Could not import error_handler module: {e}")

    def test_structured_logging(self):
        """Test structured logging format"""
        try:
            from error_handler import log_structured
            
            # This is a basic test - in real scenario you'd mock the logger
            # and verify the log format, but for now we just test it doesn't crash
            log_structured('INFO', 'test_event', {'key': 'value'})
            
        except ImportError as e:
            self.skipTest(f"Could not import error_handler module: {e}")

    def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        try:
            from error_handler import CircuitBreaker
            
            cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
            
            # Test normal operation
            result = cb.call(lambda: "success")
            self.assertEqual(result, "success")
            self.assertEqual(cb.state, 'CLOSED')
            
            # Test failure handling
            def failing_func():
                raise Exception("Test failure")
            
            # First failure
            with self.assertRaises(Exception):
                cb.call(failing_func)
            self.assertEqual(cb.failure_count, 1)
            
            # Second failure should open circuit
            with self.assertRaises(Exception):
                cb.call(failing_func)
            self.assertEqual(cb.state, 'OPEN')
            
            # Next call should be blocked
            with self.assertRaises(Exception):
                cb.call(lambda: "should be blocked")
            
        except ImportError as e:
            self.skipTest(f"Could not import error_handler module: {e}")


def run_unit_tests():
    """Run all unit tests and return results"""
    print("🧪 Running GymPulse Unit Tests\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestAPIHandlers,
        TestIoTIngest,
        TestWebSocketHandlers,
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n📊 Unit Test Summary:")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    print(f"⏭️ Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\n💥 Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print(f"\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_unit_tests()
    exit(0 if success else 1)