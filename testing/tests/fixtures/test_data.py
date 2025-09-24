"""
Test fixtures and sample data for GymPulse testing
"""
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any


class TestDataFixtures:
    """Test data fixtures for GymPulse system"""
    
    @staticmethod
    def sample_iot_message(machine_id: str = "leg-press-01", 
                          status: str = "occupied",
                          gym_id: str = "hk-central") -> Dict[str, Any]:
        """Generate sample IoT message"""
        return {
            "machineId": machine_id,
            "gymId": gym_id,
            "status": status,
            "timestamp": int(time.time()),
            "category": "legs"
        }
    
    @staticmethod
    def sample_lambda_event(message: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate sample Lambda event from IoT Core"""
        if message is None:
            message = TestDataFixtures.sample_iot_message()
            
        return {
            "Records": [
                {
                    "eventSource": "aws:iot",
                    "eventName": "MessageReceived",
                    "eventVersion": "1.0",
                    "eventSourceARN": "arn:aws:iot:ap-east-1:123456789012:topic/org/+/machines/+/status",
                    "awsRegion": "ap-east-1",
                    "eventTime": datetime.utcnow().isoformat(),
                    "requestParameters": {},
                    "responseElements": {},
                    "messageId": f"test-message-{int(time.time())}",
                    "body": json.dumps(message)
                }
            ]
        }
    
    @staticmethod
    def sample_current_state_record(machine_id: str = "leg-press-01") -> Dict[str, Any]:
        """Generate sample current state DynamoDB record"""
        return {
            "machineId": {"S": machine_id},
            "status": {"S": "occupied"},
            "lastUpdate": {"N": str(int(time.time()))},
            "gymId": {"S": "hk-central"},
            "category": {"S": "legs"}
        }
    
    @staticmethod
    def sample_api_gateway_event(path: str = "/branches",
                                method: str = "GET",
                                body: str = None) -> Dict[str, Any]:
        """Generate sample API Gateway event"""
        return {
            "resource": path,
            "path": path,
            "httpMethod": method,
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "test-agent"
            },
            "multiValueHeaders": {},
            "queryStringParameters": {},
            "multiValueQueryStringParameters": {},
            "pathParameters": {},
            "stageVariables": {},
            "requestContext": {
                "requestId": f"test-request-{int(time.time())}",
                "stage": "test",
                "resourceId": "test",
                "httpMethod": method,
                "resourcePath": path,
                "accountId": "123456789012",
                "apiId": "test-api",
                "identity": {
                    "sourceIp": "127.0.0.1",
                    "userAgent": "test-agent"
                }
            },
            "body": body,
            "isBase64Encoded": False
        }
    
    @staticmethod
    def sample_websocket_event(action: str = "$connect") -> Dict[str, Any]:
        """Generate sample WebSocket event"""
        return {
            "requestContext": {
                "connectionId": f"test-connection-{int(time.time())}",
                "eventType": action,
                "requestId": f"test-request-{int(time.time())}",
                "stage": "test",
                "connectedAt": int(time.time()) * 1000,
                "identity": {
                    "sourceIp": "127.0.0.1",
                    "userAgent": "test-agent"
                }
            }
        }
    
    @staticmethod
    def sample_bedrock_chat_request() -> Dict[str, Any]:
        """Generate sample Bedrock chat request"""
        return {
            "message": "I want to do legs nearby",
            "userLocation": {
                "lat": 22.2819,
                "lon": 114.1577
            },
            "sessionId": "test-session"
        }
    
    @staticmethod
    def sample_availability_tool_input() -> Dict[str, Any]:
        """Generate sample availability tool input"""
        return {
            "lat": 22.2819,
            "lon": 114.1577,
            "radius": 5,
            "category": "legs"
        }
    
    @staticmethod
    def sample_route_matrix_input() -> Dict[str, Any]:
        """Generate sample route matrix tool input"""
        return {
            "userCoord": {
                "lat": 22.2819,
                "lon": 114.1577
            },
            "branchCoords": [
                {
                    "branchId": "hk-central",
                    "lat": 22.2819,
                    "lon": 114.1577
                },
                {
                    "branchId": "hk-causeway",
                    "lat": 22.2783,
                    "lon": 114.1747
                }
            ]
        }
    
    @staticmethod
    def sample_machine_inventory() -> List[Dict[str, Any]]:
        """Generate sample machine inventory"""
        return [
            {
                "machineId": "leg-press-01",
                "name": "Leg Press Machine 1",
                "category": "legs",
                "gymId": "hk-central",
                "status": "free"
            },
            {
                "machineId": "bench-press-01", 
                "name": "Bench Press 1",
                "category": "chest",
                "gymId": "hk-central",
                "status": "occupied"
            },
            {
                "machineId": "lat-pulldown-01",
                "name": "Lat Pulldown 1", 
                "category": "back",
                "gymId": "hk-causeway",
                "status": "free"
            }
        ]
    
    @staticmethod
    def sample_aggregates_data() -> List[Dict[str, Any]]:
        """Generate sample aggregates data for heatmaps"""
        base_timestamp = int(time.time())
        data = []
        
        # Generate 24 hours of 15-minute intervals
        for hour in range(24):
            for quarter in range(0, 60, 15):
                timestamp = base_timestamp - (24 - hour) * 3600 - quarter * 60
                
                # Simulate realistic occupancy patterns
                if 6 <= hour <= 9 or 18 <= hour <= 21:  # Peak hours
                    occupancy = 70 + (hour % 3) * 5  # 70-85%
                elif 12 <= hour <= 13:  # Lunch
                    occupancy = 60
                else:  # Off-peak
                    occupancy = 20 + (hour % 4) * 5  # 20-35%
                
                data.append({
                    "gymId_category": "hk-central_legs",
                    "timestamp15min": timestamp,
                    "occupancyRatio": occupancy,
                    "freeCount": max(1, int(10 * (100 - occupancy) / 100)),
                    "totalCount": 10
                })
        
        return data


class MockResponses:
    """Mock responses for external services"""
    
    @staticmethod
    def dynamodb_success_response():
        """Mock successful DynamoDB response"""
        return {
            "ResponseMetadata": {
                "RequestId": "test-request",
                "HTTPStatusCode": 200
            }
        }
    
    @staticmethod
    def bedrock_converse_response():
        """Mock Bedrock Converse API response"""
        return {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "text": "I found some available leg equipment near you. The Central Branch has 3 free leg machines with a 5-minute travel time."
                        }
                    ]
                }
            },
            "usage": {
                "inputTokens": 100,
                "outputTokens": 50,
                "totalTokens": 150
            },
            "metrics": {
                "latencyMs": 1500
            }
        }
    
    @staticmethod
    def location_route_matrix_response():
        """Mock Amazon Location Service route matrix response"""
        return {
            "RouteMatrix": [
                [
                    {
                        "DurationSeconds": 300,  # 5 minutes
                        "Distance": 2.5
                    },
                    {
                        "DurationSeconds": 600,  # 10 minutes  
                        "Distance": 4.8
                    }
                ]
            ]
        }
    
    @staticmethod
    def iot_publish_response():
        """Mock IoT Core publish response"""
        return {
            "ResponseMetadata": {
                "RequestId": "test-iot-request",
                "HTTPStatusCode": 200
            }
        }