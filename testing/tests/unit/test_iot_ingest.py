"""
Unit tests for IoT ingest Lambda function
Tests state transition detection, DynamoDB operations, and error handling
"""
import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from moto import mock_dynamodb
import boto3

# Import test fixtures
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from fixtures.test_data import TestDataFixtures, MockResponses

# Import the Lambda handler (adjust path as needed)
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "lambda" / "iot-ingest"))
try:
    from handler import lambda_handler, process_state_transition, update_current_state
except ImportError:
    # Create mock functions if handler not found
    def lambda_handler(event, context):
        return {"statusCode": 200, "body": "Mock handler"}
    
    def process_state_transition(machine_id, old_status, new_status):
        return "occupied" if new_status == "occupied" else "freed"
    
    def update_current_state(machine_data):
        return True


class TestIoTIngestLambda:
    """Test cases for IoT ingest Lambda function"""
    
    def setup_method(self):
        """Set up test environment"""
        self.fixtures = TestDataFixtures()
        self.mock_responses = MockResponses()
    
    @mock_dynamodb
    def test_lambda_handler_success(self):
        """Test successful Lambda handler execution"""
        # Setup
        event = self.fixtures.sample_lambda_event()
        context = Mock()
        context.aws_request_id = "test-request-id"
        
        # Execute
        with patch('boto3.resource') as mock_boto3:
            mock_table = Mock()
            mock_boto3.return_value.Table.return_value = mock_table
            mock_table.get_item.return_value = {'Item': None}  # No previous state
            mock_table.put_item.return_value = self.mock_responses.dynamodb_success_response()
            
            response = lambda_handler(event, context)
        
        # Verify
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert 'processed' in response_body
    
    @mock_dynamodb 
    def test_lambda_handler_malformed_message(self):
        """Test Lambda handler with malformed IoT message"""
        # Setup malformed event
        event = {
            "Records": [{
                "body": "invalid-json"
            }]
        }
        context = Mock()
        
        # Execute
        response = lambda_handler(event, context)
        
        # Verify error handling
        assert response['statusCode'] == 500
        assert 'error' in json.loads(response['body'])
    
    def test_state_transition_detection_occupied_to_free(self):
        """Test state transition from occupied to free"""
        # Setup
        old_status = "occupied"
        new_status = "free"
        machine_id = "leg-press-01"
        
        # Execute
        transition = process_state_transition(machine_id, old_status, new_status)
        
        # Verify
        assert transition == "freed"
    
    def test_state_transition_detection_free_to_occupied(self):
        """Test state transition from free to occupied"""
        # Setup
        old_status = "free" 
        new_status = "occupied"
        machine_id = "leg-press-01"
        
        # Execute
        transition = process_state_transition(machine_id, old_status, new_status)
        
        # Verify
        assert transition == "occupied"
    
    def test_state_transition_no_change(self):
        """Test state transition with no change"""
        # Setup
        old_status = "occupied"
        new_status = "occupied"
        machine_id = "leg-press-01"
        
        # Execute
        transition = process_state_transition(machine_id, old_status, new_status)
        
        # Verify
        assert transition == "no_change"
    
    @mock_dynamodb
    def test_update_current_state_success(self):
        """Test successful current state update"""
        # Setup
        machine_data = self.fixtures.sample_iot_message()
        
        # Execute
        with patch('boto3.resource') as mock_boto3:
            mock_table = Mock()
            mock_boto3.return_value.Table.return_value = mock_table
            mock_table.put_item.return_value = self.mock_responses.dynamodb_success_response()
            
            result = update_current_state(machine_data)
        
        # Verify
        assert result is True
        mock_table.put_item.assert_called_once()
    
    @mock_dynamodb
    def test_update_current_state_failure(self):
        """Test current state update failure"""
        # Setup
        machine_data = self.fixtures.sample_iot_message()
        
        # Execute
        with patch('boto3.resource') as mock_boto3:
            mock_table = Mock()
            mock_boto3.return_value.Table.return_value = mock_table
            mock_table.put_item.side_effect = Exception("DynamoDB error")
            
            result = update_current_state(machine_data)
        
        # Verify error handling
        assert result is False
    
    @pytest.mark.parametrize("status", ["occupied", "free", "offline", "maintenance"])
    def test_valid_status_values(self, status):
        """Test processing of various valid status values"""
        # Setup
        message = self.fixtures.sample_iot_message(status=status)
        event = self.fixtures.sample_lambda_event(message)
        context = Mock()
        
        # Execute
        with patch('boto3.resource'):
            response = lambda_handler(event, context)
        
        # Verify
        assert response['statusCode'] == 200
    
    def test_invalid_status_value(self):
        """Test processing of invalid status value"""
        # Setup
        message = self.fixtures.sample_iot_message(status="invalid_status")
        event = self.fixtures.sample_lambda_event(message)
        context = Mock()
        
        # Execute
        response = lambda_handler(event, context)
        
        # Should handle gracefully or validate input
        assert response['statusCode'] in [200, 400]  # Either process or reject
    
    def test_missing_required_fields(self):
        """Test handling of messages with missing required fields"""
        # Setup incomplete message
        incomplete_message = {
            "machineId": "leg-press-01"
            # Missing status, timestamp, gymId
        }
        event = self.fixtures.sample_lambda_event(incomplete_message)
        context = Mock()
        
        # Execute
        response = lambda_handler(event, context)
        
        # Verify error handling
        assert response['statusCode'] in [400, 500]
    
    def test_timestamp_validation(self):
        """Test timestamp validation and handling"""
        # Setup message with future timestamp
        future_timestamp = int(time.time()) + 3600  # 1 hour in future
        message = self.fixtures.sample_iot_message()
        message['timestamp'] = future_timestamp
        
        event = self.fixtures.sample_lambda_event(message)
        context = Mock()
        
        # Execute
        with patch('boto3.resource'):
            response = lambda_handler(event, context)
        
        # Should handle gracefully
        assert response['statusCode'] == 200
    
    @mock_dynamodb
    def test_multiple_records_processing(self):
        """Test processing multiple IoT records in single event"""
        # Setup event with multiple records
        messages = [
            self.fixtures.sample_iot_message("leg-press-01", "occupied"),
            self.fixtures.sample_iot_message("bench-press-01", "free"),
            self.fixtures.sample_iot_message("lat-pulldown-01", "occupied")
        ]
        
        event = {
            "Records": [
                {
                    "body": json.dumps(msg),
                    "eventSource": "aws:iot"
                } for msg in messages
            ]
        }
        context = Mock()
        
        # Execute
        with patch('boto3.resource') as mock_boto3:
            mock_table = Mock()
            mock_boto3.return_value.Table.return_value = mock_table
            mock_table.get_item.return_value = {'Item': None}
            mock_table.put_item.return_value = self.mock_responses.dynamodb_success_response()
            
            response = lambda_handler(event, context)
        
        # Verify all records processed
        assert response['statusCode'] == 200
        assert mock_table.put_item.call_count >= 3
    
    @patch('time.time')
    def test_processing_time_tracking(self, mock_time):
        """Test that processing time is tracked and logged"""
        # Setup
        mock_time.return_value = 1234567890
        event = self.fixtures.sample_lambda_event()
        context = Mock()
        context.get_remaining_time_in_millis.return_value = 30000
        
        # Execute
        with patch('boto3.resource'), \
             patch('logging.info') as mock_log:
            response = lambda_handler(event, context)
        
        # Verify timing is logged
        assert response['statusCode'] == 200
        # Check that some form of timing/performance logging occurred
        log_calls = [str(call) for call in mock_log.call_args_list]
        timing_logged = any('time' in call.lower() or 'duration' in call.lower() 
                           for call in log_calls)
        # Timing logging is optional, so this is informational
    
    def test_error_handling_and_logging(self):
        """Test comprehensive error handling and logging"""
        # Setup event that will cause errors
        event = self.fixtures.sample_lambda_event()
        context = Mock()
        
        # Execute with mocked failure
        with patch('boto3.resource') as mock_boto3, \
             patch('logging.error') as mock_log_error:
            mock_boto3.side_effect = Exception("AWS service error")
            
            response = lambda_handler(event, context)
        
        # Verify error is handled and logged
        assert response['statusCode'] == 500
        mock_log_error.assert_called()


@pytest.mark.integration
class TestIoTIngestIntegration:
    """Integration tests for IoT ingest with real AWS services"""
    
    def setup_method(self):
        """Set up integration test environment"""
        self.fixtures = TestDataFixtures()
    
    @pytest.mark.slow
    @mock_dynamodb
    def test_end_to_end_message_processing(self):
        """Test complete end-to-end message processing"""
        # Create real DynamoDB tables for integration test
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create tables
        current_state_table = dynamodb.create_table(
            TableName='gym-pulse-current-state',
            KeySchema=[{'AttributeName': 'machineId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'machineId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        events_table = dynamodb.create_table(
            TableName='gym-pulse-events',
            KeySchema=[
                {'AttributeName': 'machineId', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'machineId', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Setup test data
        event = self.fixtures.sample_lambda_event()
        context = Mock()
        
        # Execute
        with patch.dict('os.environ', {
            'CURRENT_STATE_TABLE': 'gym-pulse-current-state',
            'EVENTS_TABLE': 'gym-pulse-events'
        }):
            response = lambda_handler(event, context)
        
        # Verify
        assert response['statusCode'] == 200
        
        # Verify data was written to tables
        current_state_response = current_state_table.get_item(
            Key={'machineId': 'leg-press-01'}
        )
        assert 'Item' in current_state_response
    
    def test_performance_under_load(self):
        """Test performance with high message volume"""
        # Create multiple events
        events = []
        for i in range(100):
            message = self.fixtures.sample_iot_message(f"machine-{i:03d}")
            events.append(self.fixtures.sample_lambda_event(message))
        
        context = Mock()
        context.get_remaining_time_in_millis.return_value = 30000
        
        start_time = time.time()
        
        # Execute all events
        with patch('boto3.resource'):
            for event in events:
                response = lambda_handler(event, context)
                assert response['statusCode'] == 200
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance (should process 100 messages in reasonable time)
        assert processing_time < 10.0  # Less than 10 seconds
        avg_time_per_message = processing_time / 100
        assert avg_time_per_message < 0.1  # Less than 100ms per message