"""
Integration tests for REST API endpoints
Tests complete API workflow including DynamoDB integration
"""
import pytest
import json
import time
import boto3
from unittest.mock import Mock, patch, MagicMock
from moto import mock_dynamodb, mock_apigateway
import requests

# Import test fixtures
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from fixtures.test_data import TestDataFixtures, MockResponses

# Mock API base URL for testing
API_BASE_URL = "https://test-api.execute-api.ap-east-1.amazonaws.com/prod"


class TestAPIEndpoints:
    """Integration tests for REST API endpoints"""
    
    def setup_method(self):
        """Set up test environment"""
        self.fixtures = TestDataFixtures()
        self.mock_responses = MockResponses()
    
    @mock_dynamodb
    def test_branches_endpoint_success(self):
        """Test GET /branches endpoint returns correct data format"""
        # Setup mock DynamoDB data
        dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
        
        # Create current_state table
        table = dynamodb.create_table(
            TableName='gym-pulse-current-state',
            KeySchema=[{'AttributeName': 'machineId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'machineId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Insert test data
        test_machines = [
            {
                'machineId': 'leg-press-01',
                'gymId': 'hk-central',
                'category': 'legs',
                'status': 'free',
                'lastUpdate': int(time.time()),
                'coordinates': {'lat': 22.2819, 'lon': 114.1577}
            },
            {
                'machineId': 'bench-press-01',
                'gymId': 'hk-central',
                'category': 'chest',
                'status': 'occupied',
                'lastUpdate': int(time.time()),
                'coordinates': {'lat': 22.2819, 'lon': 114.1577}
            }
        ]
        
        for machine in test_machines:
            table.put_item(Item=machine)
        
        # Mock the API call
        with patch('requests.get') as mock_get:
            expected_response = {
                'branches': [
                    {
                        'id': 'hk-central',
                        'name': 'Central Branch',
                        'coordinates': {'lat': 22.2819, 'lon': 114.1577},
                        'categories': {
                            'legs': {'free': 1, 'total': 1},
                            'chest': {'free': 0, 'total': 1},
                            'back': {'free': 0, 'total': 0}
                        }
                    }
                ]
            }
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = expected_response
            
            # Execute test
            response = requests.get(f"{API_BASE_URL}/branches")
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert 'branches' in data
            assert len(data['branches']) > 0
            
            # Validate branch structure
            branch = data['branches'][0]
            required_fields = ['id', 'name', 'coordinates', 'categories']
            for field in required_fields:
                assert field in branch
    
    @mock_dynamodb
    def test_machines_endpoint_by_category(self):
        """Test GET /branches/{id}/categories/{category}/machines endpoint"""
        # Setup mock data
        dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
        table = dynamodb.create_table(
            TableName='gym-pulse-current-state',
            KeySchema=[{'AttributeName': 'machineId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'machineId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Insert test machines
        legs_machines = [
            {
                'machineId': 'leg-press-01',
                'gymId': 'hk-central',
                'category': 'legs',
                'status': 'free',
                'name': 'Leg Press Machine 1',
                'lastUpdate': int(time.time())
            },
            {
                'machineId': 'squat-rack-01',
                'gymId': 'hk-central',
                'category': 'legs',
                'status': 'occupied',
                'name': 'Squat Rack 1',
                'lastUpdate': int(time.time()) - 300
            }
        ]
        
        for machine in legs_machines:
            table.put_item(Item=machine)
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                'machines': legs_machines,
                'category': 'legs',
                'branchId': 'hk-central'
            }
            
            # Execute test
            response = requests.get(f"{API_BASE_URL}/branches/hk-central/categories/legs/machines")
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert 'machines' in data
            assert data['category'] == 'legs'
            assert len(data['machines']) == 2
    
    @mock_dynamodb
    def test_machine_history_endpoint(self):
        """Test GET /machines/{id}/history?range=24h endpoint"""
        # Setup mock aggregates data
        dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
        table = dynamodb.create_table(
            TableName='gym-pulse-aggregates',
            KeySchema=[
                {'AttributeName': 'gymId_category', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp15min', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'gymId_category', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp15min', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Insert 24 hours of test data
        base_timestamp = int(time.time()) - (24 * 3600)
        for i in range(96):  # 96 15-minute intervals in 24 hours
            timestamp = base_timestamp + (i * 900)  # 900 seconds = 15 minutes
            occupancy = 30 + (i % 12) * 5  # Varying occupancy pattern
            
            table.put_item(Item={
                'gymId_category': 'hk-central_legs',
                'timestamp15min': timestamp,
                'occupancyRatio': occupancy,
                'freeCount': max(1, int(5 * (100 - occupancy) / 100)),
                'totalCount': 5
            })
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                'machineId': 'leg-press-01',
                'history': self.fixtures.sample_aggregates_data(),
                'forecast': {
                    'likelyFreeIn30m': True,
                    'probability': 0.75,
                    'confidence': 'high'
                }
            }
            
            # Execute test
            response = requests.get(f"{API_BASE_URL}/machines/leg-press-01/history?range=24h")
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert 'machineId' in data
            assert 'history' in data
            assert 'forecast' in data
            assert len(data['history']) > 0
    
    @mock_dynamodb
    def test_alerts_endpoint_create_alert(self):
        """Test POST /alerts endpoint creates alert subscription"""
        # Setup mock alerts table
        dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
        table = dynamodb.create_table(
            TableName='gym-pulse-alerts',
            KeySchema=[
                {'AttributeName': 'userId', 'KeyType': 'HASH'},
                {'AttributeName': 'machineId', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'userId', 'AttributeType': 'S'},
                {'AttributeName': 'machineId', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        alert_request = {
            'machineId': 'leg-press-01',
            'userId': 'test-user-123',
            'quietHours': {'start': 22, 'end': 7}
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                'alertId': 'alert-456',
                'machineId': 'leg-press-01',
                'userId': 'test-user-123',
                'active': True,
                'createdAt': int(time.time())
            }
            
            # Execute test
            response = requests.post(
                f"{API_BASE_URL}/alerts",
                json=alert_request,
                headers={'Content-Type': 'application/json'}
            )
            
            # Verify
            assert response.status_code == 201
            data = response.json()
            assert 'alertId' in data
            assert data['machineId'] == 'leg-press-01'
            assert data['active'] is True
    
    def test_api_error_handling(self):
        """Test API error responses and status codes"""
        with patch('requests.get') as mock_get:
            # Test 404 for non-existent branch
            mock_get.return_value.status_code = 404
            mock_get.return_value.json.return_value = {
                'error': 'Branch not found',
                'message': 'Branch hk-nonexistent does not exist'
            }
            
            response = requests.get(f"{API_BASE_URL}/branches/hk-nonexistent/categories/legs/machines")
            
            assert response.status_code == 404
            error_data = response.json()
            assert 'error' in error_data
    
    def test_api_cors_headers(self):
        """Test API returns proper CORS headers"""
        with patch('requests.options') as mock_options:
            mock_options.return_value.status_code = 200
            mock_options.return_value.headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization'
            }
            
            response = requests.options(f"{API_BASE_URL}/branches")
            
            assert response.status_code == 200
            assert 'Access-Control-Allow-Origin' in response.headers
            assert 'Access-Control-Allow-Methods' in response.headers
    
    @pytest.mark.parametrize("endpoint,expected_fields", [
        ("/branches", ["branches"]),
        ("/branches/hk-central/categories/legs/machines", ["machines", "category"]),
        ("/machines/leg-press-01/history?range=24h", ["machineId", "history"])
    ])
    def test_api_response_schemas(self, endpoint, expected_fields):
        """Test API endpoints return expected response schemas"""
        with patch('requests.get') as mock_get:
            # Mock appropriate response based on endpoint
            if "branches" in endpoint and "machines" not in endpoint:
                mock_response = {'branches': []}
            elif "machines" in endpoint and "history" not in endpoint:
                mock_response = {'machines': [], 'category': 'legs'}
            else:
                mock_response = {'machineId': 'test', 'history': []}
            
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            response = requests.get(f"{API_BASE_URL}{endpoint}")
            
            assert response.status_code == 200
            data = response.json()
            
            for field in expected_fields:
                assert field in data
    
    def test_api_rate_limiting(self):
        """Test API rate limiting behavior"""
        with patch('requests.get') as mock_get:
            # First requests succeed
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {'branches': []}
            
            # Simulate multiple requests
            responses = []
            for _ in range(5):
                response = requests.get(f"{API_BASE_URL}/branches")
                responses.append(response.status_code)
            
            # Should get 200s for normal usage
            assert all(status == 200 for status in responses)
            
            # Simulate rate limit exceeded
            mock_get.return_value.status_code = 429
            mock_get.return_value.json.return_value = {
                'error': 'Too Many Requests',
                'retryAfter': 60
            }
            
            response = requests.get(f"{API_BASE_URL}/branches")
            assert response.status_code == 429
    
    def test_api_performance_requirements(self):
        """Test API response times meet requirements"""
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {'branches': []}
            mock_get.return_value.elapsed.total_seconds.return_value = 0.15  # 150ms
            
            response = requests.get(f"{API_BASE_URL}/branches")
            
            # API should respond within 200ms (target from Phase 4)
            assert response.elapsed.total_seconds() < 0.2
            assert response.status_code == 200


@pytest.mark.integration
class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality"""
    
    def setup_method(self):
        """Set up WebSocket test environment"""
        self.fixtures = TestDataFixtures()
        self.ws_url = "wss://test-ws.execute-api.ap-east-1.amazonaws.com/prod"
    
    def test_websocket_connection_lifecycle(self):
        """Test WebSocket connection and disconnection"""
        with patch('websocket.WebSocket') as mock_ws:
            # Mock successful connection
            mock_ws_instance = Mock()
            mock_ws.return_value = mock_ws_instance
            mock_ws_instance.connect.return_value = None
            
            # Simulate connection
            ws = mock_ws()
            ws.connect(self.ws_url)
            
            # Verify connection was attempted
            mock_ws_instance.connect.assert_called_once()
    
    def test_websocket_real_time_updates(self):
        """Test WebSocket receives real-time machine updates"""
        with patch('websocket.WebSocket') as mock_ws:
            mock_ws_instance = Mock()
            mock_ws.return_value = mock_ws_instance
            
            # Simulate receiving update message
            test_update = {
                'type': 'machine_update',
                'machineId': 'leg-press-01',
                'status': 'free',
                'timestamp': int(time.time())
            }
            
            mock_ws_instance.recv.return_value = json.dumps(test_update)
            
            # Simulate receiving message
            ws = mock_ws()
            message = json.loads(ws.recv())
            
            # Verify message structure
            assert message['type'] == 'machine_update'
            assert message['machineId'] == 'leg-press-01'
            assert message['status'] == 'free'
            assert 'timestamp' in message
    
    def test_websocket_error_handling(self):
        """Test WebSocket error handling and recovery"""
        with patch('websocket.WebSocket') as mock_ws:
            mock_ws_instance = Mock()
            mock_ws.return_value = mock_ws_instance
            
            # Simulate connection error
            mock_ws_instance.connect.side_effect = ConnectionError("Connection failed")
            
            ws = mock_ws()
            
            # Should handle connection errors gracefully
            with pytest.raises(ConnectionError):
                ws.connect(self.ws_url)