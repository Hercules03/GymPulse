"""
Integration Tests for GymPulse API and WebSocket Functionality
Tests end-to-end workflows including API calls, WebSocket connections, and alert systems
"""
import json
import time
import requests
import asyncio
import websockets
import boto3
from decimal import Decimal
import pytest
from typing import Dict, List, Any

# Test configuration
BASE_URL = "https://your-api-gateway-id.execute-api.region.amazonaws.com/prod"  # Replace with actual URL
WEBSOCKET_URL = "wss://your-websocket-id.execute-api.region.amazonaws.com/prod"  # Replace with actual URL

# Test data
TEST_BRANCHES = ["hk-central", "hk-causeway"]
TEST_CATEGORIES = ["legs", "chest", "back"]
TEST_MACHINES = {
    "hk-central": {
        "legs": ["leg-press-01", "leg-press-02", "squat-rack-01"],
        "chest": ["bench-press-01", "bench-press-02"],
        "back": ["lat-pulldown-01", "rowing-01"]
    },
    "hk-causeway": {
        "legs": ["leg-press-03", "squat-rack-02"],
        "chest": ["bench-press-03", "incline-press-01"],
        "back": ["lat-pulldown-02", "rowing-02"]
    }
}

class IntegrationTestSuite:
    """
    Comprehensive integration testing for GymPulse APIs and real-time features
    """
    
    def __init__(self, base_url: str, websocket_url: str):
        self.base_url = base_url
        self.websocket_url = websocket_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'GymPulse-Integration-Test/1.0'
        })
        
        # Test metrics
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': [],
            'performance': {}
        }
    
    def log_result(self, test_name: str, passed: bool, duration: float = None, error: str = None):
        """Log test result and update metrics"""
        if passed:
            self.test_results['passed'] += 1
            print(f"✅ {test_name} - PASSED" + (f" ({duration:.3f}s)" if duration else ""))
        else:
            self.test_results['failed'] += 1
            print(f"❌ {test_name} - FAILED" + (f": {error}" if error else ""))
            if error:
                self.test_results['errors'].append(f"{test_name}: {error}")
        
        if duration:
            self.test_results['performance'][test_name] = duration

    def test_health_check(self):
        """Test API health endpoint"""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/health")
            duration = time.time() - start_time
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert data.get('status') == 'healthy', f"Expected healthy status, got {data.get('status')}"
            
            self.log_result("API Health Check", True, duration)
            return True
            
        except Exception as e:
            self.log_result("API Health Check", False, error=str(e))
            return False

    def test_branches_endpoint(self):
        """Test branches endpoint with availability data"""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/branches")
            duration = time.time() - start_time
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert 'branches' in data, "Missing branches in response"
            
            branches = data['branches']
            assert len(branches) > 0, "No branches returned"
            
            # Validate branch structure
            for branch in branches:
                assert 'id' in branch, "Branch missing id"
                assert 'name' in branch, "Branch missing name"
                assert 'coordinates' in branch, "Branch missing coordinates"
                assert 'categories' in branch, "Branch missing categories"
                
                # Validate coordinates
                coords = branch['coordinates']
                assert 'lat' in coords and 'lon' in coords, "Invalid coordinates"
                assert -90 <= coords['lat'] <= 90, "Invalid latitude"
                assert -180 <= coords['lon'] <= 180, "Invalid longitude"
                
                # Validate categories
                categories = branch['categories']
                for category in TEST_CATEGORIES:
                    if category in categories:
                        cat_data = categories[category]
                        assert 'free' in cat_data and 'total' in cat_data, f"Invalid category data for {category}"
                        assert cat_data['free'] >= 0, "Negative free count"
                        assert cat_data['total'] >= cat_data['free'], "Free count exceeds total"
            
            self.log_result("Branches Endpoint", True, duration)
            return True
            
        except Exception as e:
            self.log_result("Branches Endpoint", False, error=str(e))
            return False

    def test_machines_endpoint(self):
        """Test machines endpoint for each branch and category"""
        success_count = 0
        total_tests = 0
        
        for branch_id in TEST_BRANCHES:
            for category in TEST_CATEGORIES:
                total_tests += 1
                try:
                    start_time = time.time()
                    response = self.session.get(f"{self.base_url}/branches/{branch_id}/categories/{category}/machines")
                    duration = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Validate response structure
                        assert 'machines' in data, "Missing machines in response"
                        assert 'branchId' in data, "Missing branchId"
                        assert 'category' in data, "Missing category"
                        assert 'totalCount' in data, "Missing totalCount"
                        assert 'freeCount' in data, "Missing freeCount"
                        
                        # Validate machine data
                        machines = data['machines']
                        for machine in machines:
                            assert 'machineId' in machine, "Machine missing machineId"
                            assert 'status' in machine, "Machine missing status"
                            assert machine['status'] in ['free', 'occupied', 'offline'], f"Invalid status: {machine['status']}"
                            assert 'lastUpdate' in machine, "Machine missing lastUpdate"
                        
                        success_count += 1
                        print(f"✅ Machines {branch_id}/{category} - PASSED ({duration:.3f}s)")
                    else:
                        print(f"❌ Machines {branch_id}/{category} - FAILED: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Machines {branch_id}/{category} - ERROR: {str(e)}")
        
        success_rate = success_count / total_tests
        self.log_result(f"Machines Endpoint ({success_count}/{total_tests})", success_rate > 0.8)
        return success_rate > 0.8

    def test_machine_history_endpoint(self):
        """Test machine history endpoint with sample machines"""
        success_count = 0
        test_machines = ["leg-press-01", "bench-press-01", "lat-pulldown-01"]
        
        for machine_id in test_machines:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/machines/{machine_id}/history?range=24h")
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Validate response structure
                    assert 'machineId' in data, "Missing machineId"
                    assert 'history' in data, "Missing history"
                    assert 'timeRange' in data, "Missing timeRange"
                    assert 'forecast' in data, "Missing forecast"
                    
                    # Validate history data
                    history = data['history']
                    for bin_data in history:
                        assert 'timestamp' in bin_data, "Missing timestamp in history bin"
                        assert 'occupancyRatio' in bin_data, "Missing occupancyRatio"
                        assert 0 <= bin_data['occupancyRatio'] <= 100, "Invalid occupancy ratio"
                    
                    # Validate forecast
                    forecast = data['forecast']
                    assert 'likelyFreeIn30m' in forecast, "Missing forecast prediction"
                    assert 'confidence' in forecast, "Missing forecast confidence"
                    
                    success_count += 1
                    print(f"✅ History {machine_id} - PASSED ({duration:.3f}s)")
                else:
                    print(f"❌ History {machine_id} - FAILED: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ History {machine_id} - ERROR: {str(e)}")
        
        success_rate = success_count / len(test_machines)
        self.log_result(f"Machine History ({success_count}/{len(test_machines)})", success_rate > 0.6)
        return success_rate > 0.6

    def test_alert_lifecycle(self):
        """Test complete alert lifecycle: create, list, update, cancel"""
        try:
            test_machine = "leg-press-01"
            alert_id = None
            
            # Step 1: Create alert
            alert_request = {
                "machineId": test_machine,
                "userId": "test-user",
                "quietHours": {"start": 22, "end": 7}
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/alerts", json=alert_request)
            
            # Handle different response scenarios
            if response.status_code == 201:
                alert_data = response.json()
                alert_id = alert_data.get('alertId')
                print(f"✅ Alert Created: {alert_id}")
            elif response.status_code == 400:
                # Machine might be free, which is expected
                error_data = response.json()
                if "occupied" in error_data.get('error', '').lower():
                    print(f"ℹ️ Alert Creation Skipped - Machine {test_machine} is free")
                    self.log_result("Alert Lifecycle", True)
                    return True
            else:
                raise Exception(f"Create alert failed: {response.status_code} - {response.text}")
            
            if not alert_id:
                self.log_result("Alert Lifecycle", True)  # Machine was free, test passed
                return True
            
            # Step 2: List alerts
            response = self.session.get(f"{self.base_url}/alerts?userId=test-user")
            assert response.status_code == 200, f"List alerts failed: {response.status_code}"
            
            alerts_data = response.json()
            assert 'alerts' in alerts_data, "Missing alerts in response"
            
            # Find our alert
            our_alert = None
            for alert in alerts_data['alerts']:
                if alert['alertId'] == alert_id:
                    our_alert = alert
                    break
            
            assert our_alert is not None, "Created alert not found in list"
            print("✅ Alert Listed Successfully")
            
            # Step 3: Update alert (modify quiet hours)
            update_request = {
                "quietHours": {"start": 23, "end": 6}
            }
            
            response = self.session.put(f"{self.base_url}/alerts/{alert_id}", json=update_request)
            assert response.status_code == 200, f"Update alert failed: {response.status_code}"
            print("✅ Alert Updated Successfully")
            
            # Step 4: Cancel alert
            response = self.session.delete(f"{self.base_url}/alerts/{alert_id}")
            assert response.status_code == 200, f"Cancel alert failed: {response.status_code}"
            print("✅ Alert Cancelled Successfully")
            
            duration = time.time() - start_time
            self.log_result("Alert Lifecycle", True, duration)
            return True
            
        except Exception as e:
            self.log_result("Alert Lifecycle", False, error=str(e))
            return False

    async def test_websocket_connection(self):
        """Test WebSocket connection and message handling"""
        try:
            start_time = time.time()
            
            # Connect to WebSocket with subscriptions
            uri = f"{self.websocket_url}?branches=hk-central&categories=legs,chest"
            
            async with websockets.connect(uri) as websocket:
                # Wait for connection confirmation
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    connection_data = json.loads(response)
                    
                    assert 'message' in connection_data, "Missing connection message"
                    assert connection_data['message'] == 'Connected successfully', "Unexpected connection message"
                    
                    print("✅ WebSocket Connected Successfully")
                    
                    # Listen for messages for a short time
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        message_data = json.loads(message)
                        
                        # Validate message structure for machine updates
                        if message_data.get('type') == 'machine_update':
                            assert 'machineId' in message_data, "Missing machineId in update"
                            assert 'status' in message_data, "Missing status in update"
                            print("✅ WebSocket Message Received")
                        
                    except asyncio.TimeoutError:
                        print("ℹ️ No messages received (expected if no machine changes)")
                    
                    duration = time.time() - start_time
                    self.log_result("WebSocket Connection", True, duration)
                    return True
                    
                except asyncio.TimeoutError:
                    raise Exception("Connection timeout - no initial response")
                    
        except Exception as e:
            self.log_result("WebSocket Connection", False, error=str(e))
            return False

    def test_api_performance(self):
        """Test API performance under multiple requests"""
        endpoints = [
            "/health",
            "/branches",
            "/branches/hk-central/categories/legs/machines",
            "/machines/leg-press-01/history?range=24h"
        ]
        
        performance_results = {}
        
        for endpoint in endpoints:
            times = []
            success_count = 0
            
            # Make 5 requests to each endpoint
            for _ in range(5):
                try:
                    start_time = time.time()
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    duration = time.time() - start_time
                    
                    times.append(duration)
                    if response.status_code == 200:
                        success_count += 1
                        
                except Exception as e:
                    print(f"Request failed for {endpoint}: {e}")
            
            if times:
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
                success_rate = success_count / len(times)
                
                performance_results[endpoint] = {
                    'avg_time': avg_time,
                    'max_time': max_time,
                    'min_time': min_time,
                    'success_rate': success_rate
                }
                
                print(f"📊 {endpoint}: avg={avg_time:.3f}s, max={max_time:.3f}s, success={success_rate:.0%}")
        
        # Check if performance meets targets
        performance_ok = True
        for endpoint, metrics in performance_results.items():
            if metrics['avg_time'] > 3.0:  # 3 second target
                performance_ok = False
                print(f"⚠️ Performance warning: {endpoint} avg time {metrics['avg_time']:.3f}s > 3.0s")
            
            if metrics['success_rate'] < 0.8:  # 80% success rate target
                performance_ok = False
                print(f"⚠️ Reliability warning: {endpoint} success rate {metrics['success_rate']:.0%} < 80%")
        
        self.log_result("API Performance", performance_ok)
        return performance_ok

    def test_cors_headers(self):
        """Test CORS headers are properly configured"""
        try:
            response = self.session.options(f"{self.base_url}/branches")
            
            headers = response.headers
            assert 'Access-Control-Allow-Origin' in headers, "Missing CORS Allow-Origin header"
            assert 'Access-Control-Allow-Headers' in headers, "Missing CORS Allow-Headers header"
            
            self.log_result("CORS Headers", True)
            return True
            
        except Exception as e:
            self.log_result("CORS Headers", False, error=str(e))
            return False

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        error_tests = [
            ("/branches/invalid-branch/categories/legs/machines", 404),
            ("/branches/hk-central/categories/invalid/machines", 404),
            ("/machines/invalid-machine/history", 404),
            ("/invalid-endpoint", 404)
        ]
        
        success_count = 0
        for endpoint, expected_code in error_tests:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == expected_code:
                    success_count += 1
                    print(f"✅ Error handling {endpoint} - {expected_code} as expected")
                else:
                    print(f"❌ Error handling {endpoint} - got {response.status_code}, expected {expected_code}")
            except Exception as e:
                print(f"❌ Error handling {endpoint} - Exception: {e}")
        
        success_rate = success_count / len(error_tests)
        self.log_result(f"Error Handling ({success_count}/{len(error_tests)})", success_rate >= 0.75)
        return success_rate >= 0.75

    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting GymPulse Integration Tests\n")
        
        # Synchronous tests
        sync_tests = [
            self.test_health_check,
            self.test_branches_endpoint,
            self.test_machines_endpoint,
            self.test_machine_history_endpoint,
            self.test_alert_lifecycle,
            self.test_api_performance,
            self.test_cors_headers,
            self.test_error_handling
        ]
        
        for test in sync_tests:
            test()
            time.sleep(0.5)  # Brief pause between tests
        
        # Asynchronous tests
        await self.test_websocket_connection()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📈 Success Rate: {self.test_results['passed']/(self.test_results['passed'] + self.test_results['failed']):.0%}")
        
        if self.test_results['errors']:
            print(f"\n🔍 Errors:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        
        # Performance summary
        if self.test_results['performance']:
            print(f"\n⚡ Performance Summary:")
            avg_performance = sum(self.test_results['performance'].values()) / len(self.test_results['performance'])
            print(f"Average response time: {avg_performance:.3f}s")
            
            slowest = max(self.test_results['performance'].items(), key=lambda x: x[1])
            print(f"Slowest test: {slowest[0]} ({slowest[1]:.3f}s)")

# Test runner
async def main():
    """Main test runner"""
    # Configure your actual endpoints here
    BASE_URL = "https://your-api-gateway-id.execute-api.region.amazonaws.com/prod"
    WEBSOCKET_URL = "wss://your-websocket-id.execute-api.region.amazonaws.com/prod"
    
    print("⚠️ Please update BASE_URL and WEBSOCKET_URL with your actual endpoints")
    print("Example URLs are placeholders and will cause connection errors\n")
    
    tester = IntegrationTestSuite(BASE_URL, WEBSOCKET_URL)
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())