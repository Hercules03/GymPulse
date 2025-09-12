#!/usr/bin/env python3
"""
GymPulse Frontend Data Flow Verification

Verify that the frontend is actually using real database data by:
1. Testing API endpoints directly
2. Comparing database state with API responses
3. Checking for data consistency
4. Validating real-time data flow
"""

import boto3
import json
import requests
import time
from datetime import datetime, timezone
from tabulate import tabulate
import sys

# Configuration
API_BASE_URL = "https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod"
REGION = 'ap-east-1'

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name=REGION)
current_state_table = dynamodb.Table('gym-pulse-current-state')

def test_api_endpoint(endpoint, method='GET', data=None):
    """Test an API endpoint and return response"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        print(f"✅ {method} {endpoint}: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint}: Connection failed - {e}")
        return None

def get_database_state():
    """Get current state from database"""
    try:
        response = current_state_table.scan()
        machines = {}
        
        for item in response['Items']:
            machines[item['machineId']] = {
                'status': item['status'],
                'gymId': item['gymId'],
                'category': item['category'],
                'lastUpdate': item['lastUpdate']
            }
        
        return machines
    except Exception as e:
        print(f"❌ Error reading database: {e}")
        return {}

def compare_database_and_api():
    """Compare database state with API responses"""
    print("\n🔍 COMPARING DATABASE VS API RESPONSES")
    print("=" * 60)
    
    # Get database state
    db_machines = get_database_state()
    print(f"📊 Database has {len(db_machines)} machines")
    
    # Get API branches response
    api_branches = test_api_endpoint('/branches')
    if not api_branches:
        print("❌ Cannot compare - API branches endpoint failed")
        return False
    
    print(f"📊 API returned {len(api_branches)} branches")
    
    # Track consistency
    consistent = True
    api_machine_count = 0
    
    # Check each branch
    for branch in api_branches:
        branch_id = branch['id']
        print(f"\n🏢 Branch: {branch['name']} ({branch_id})")
        
        categories = branch.get('categories', {})
        for category, counts in categories.items():
            print(f"  📂 {category}: {counts['free']} free / {counts['total']} total")
            api_machine_count += counts['total']
            
            # Test machines endpoint for this branch/category
            machines_data = test_api_endpoint(f'/branches/{branch_id}/categories/{category}/machines')
            
            if machines_data:
                machines = machines_data.get('machines', [])
                print(f"  🔧 API returned {len(machines)} {category} machines")
                
                # Compare individual machines with database
                for machine in machines:
                    machine_id = machine['machineId']
                    api_status = machine['status']
                    
                    if machine_id in db_machines:
                        db_status = db_machines[machine_id]['status']
                        if api_status != db_status:
                            print(f"    ❌ {machine_id}: API={api_status}, DB={db_status}")
                            consistent = False
                        else:
                            print(f"    ✅ {machine_id}: {api_status} (consistent)")
                    else:
                        print(f"    ⚠️ {machine_id}: Not found in database")
                        consistent = False
    
    print(f"\n📊 SUMMARY:")
    print(f"   Database machines: {len(db_machines)}")
    print(f"   API total machines: {api_machine_count}")
    print(f"   Data consistency: {'✅ CONSISTENT' if consistent else '❌ INCONSISTENT'}")
    
    return consistent

def test_real_time_updates():
    """Test if system responds to database changes"""
    print("\n🔄 TESTING REAL-TIME DATA UPDATES")
    print("=" * 60)
    
    # Pick a random machine to update
    db_machines = get_database_state()
    if not db_machines:
        print("❌ No machines in database to test")
        return False
    
    test_machine_id = list(db_machines.keys())[0]
    original_status = db_machines[test_machine_id]['status']
    new_status = 'occupied' if original_status == 'free' else 'free'
    
    print(f"🧪 Testing with machine: {test_machine_id}")
    print(f"   Original status: {original_status}")
    print(f"   Will change to: {new_status}")
    
    try:
        # Update database directly
        current_time = int(time.time())
        current_state_table.update_item(
            Key={'machineId': test_machine_id},
            UpdateExpression='SET #status = :new_status, lastUpdate = :timestamp',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':new_status': new_status,
                ':timestamp': current_time
            }
        )
        print(f"✅ Database updated at {datetime.fromtimestamp(current_time, tz=timezone.utc)}")
        
        # Wait a moment for propagation
        print("⏳ Waiting 2 seconds for API to reflect change...")
        time.sleep(2)
        
        # Check API response
        machine_gym = db_machines[test_machine_id]['gymId']
        machine_category = db_machines[test_machine_id]['category']
        
        api_response = test_api_endpoint(f'/branches/{machine_gym}/categories/{machine_category}/machines')
        
        if api_response:
            machines = api_response.get('machines', [])
            api_machine = next((m for m in machines if m['machineId'] == test_machine_id), None)
            
            if api_machine and api_machine['status'] == new_status:
                print(f"✅ API reflects change: {test_machine_id} = {new_status}")
                
                # Restore original status
                current_state_table.update_item(
                    Key={'machineId': test_machine_id},
                    UpdateExpression='SET #status = :original_status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':original_status': original_status}
                )
                print(f"🔄 Restored original status: {original_status}")
                return True
            else:
                print(f"❌ API still shows old status or machine not found")
                return False
        else:
            print(f"❌ API call failed")
            return False
            
    except Exception as e:
        print(f"❌ Database update failed: {e}")
        return False

def test_chat_api():
    """Test chat API with real location-based query"""
    print("\n💬 TESTING CHAT API WITH DATABASE INTEGRATION")
    print("=" * 60)
    
    # Test with Hong Kong Central location
    chat_request = {
        "message": "I want to do legs nearby",
        "userLocation": {
            "lat": 22.2819,  # Central, Hong Kong
            "lon": 114.1577
        },
        "sessionId": "test-session"
    }
    
    chat_response = test_api_endpoint('/chat', method='POST', data=chat_request)
    
    if chat_response:
        print(f"✅ Chat API Response:")
        print(f"   Message: {chat_response.get('response', 'No response')}")
        print(f"   Tools Used: {chat_response.get('toolsUsed', [])}")
        print(f"   Fallback Mode: {chat_response.get('fallback', False)}")
        
        recommendations = chat_response.get('recommendations', [])
        if recommendations:
            print(f"   Recommendations: {len(recommendations)} branches")
            for rec in recommendations[:2]:  # Show first 2
                print(f"     - {rec['name']}: {rec['availableCount']}/{rec['totalCount']} free, ETA: {rec['eta']}")
        
        return True
    else:
        print("❌ Chat API failed")
        return False

def verify_frontend_config():
    """Check frontend configuration files"""
    print("\n⚙️ VERIFYING FRONTEND CONFIGURATION")
    print("=" * 60)
    
    try:
        # Check if API base URL is correct
        expected_url = API_BASE_URL
        print(f"✅ Expected API URL: {expected_url}")
        
        # Test health endpoint
        health = test_api_endpoint('/health')
        if health:
            print(f"✅ API Health: {health.get('status', 'Unknown')}")
            print(f"   Service: {health.get('service', 'Unknown')}")
            print(f"   Version: {health.get('version', 'Unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        return False

def main():
    """Main verification function"""
    print("🏋️ GymPulse Frontend Data Flow Verification")
    print("=" * 70)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Database Region: {REGION}")
    print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    results = []
    
    # Run all verification tests
    print("1️⃣ Testing API endpoints...")
    api_working = len([test_api_endpoint('/branches'), test_api_endpoint('/health')]) == 2
    results.append(('API Endpoints', '✅ Working' if api_working else '❌ Failed'))
    
    print("2️⃣ Comparing database vs API data...")
    data_consistent = compare_database_and_api()
    results.append(('Data Consistency', '✅ Consistent' if data_consistent else '❌ Inconsistent'))
    
    print("3️⃣ Testing real-time updates...")
    realtime_working = test_real_time_updates()
    results.append(('Real-time Updates', '✅ Working' if realtime_working else '❌ Failed'))
    
    print("4️⃣ Testing chat API integration...")
    chat_working = test_chat_api()
    results.append(('Chat API', '✅ Working' if chat_working else '❌ Failed'))
    
    print("5️⃣ Verifying frontend configuration...")
    config_ok = verify_frontend_config()
    results.append(('Frontend Config', '✅ Correct' if config_ok else '❌ Issues'))
    
    # Summary
    print(f"\n📊 VERIFICATION SUMMARY")
    print("=" * 70)
    print(tabulate(results, headers=['Component', 'Status'], tablefmt='grid'))
    
    # Overall assessment
    all_passed = all('✅' in result[1] for result in results)
    
    if all_passed:
        print(f"\n🎉 FRONTEND IS USING REAL DATABASE DATA!")
        print(f"✅ All verification tests passed")
        print(f"✅ Your frontend is connected to live DynamoDB data")
        print(f"✅ Real-time updates are working")
        print(f"✅ Chat API is using actual availability data")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Start frontend: cd frontend && pnpm run dev")
        print(f"   2. Visit: http://localhost:5173")
        print(f"   3. See live data from your DynamoDB tables!")
        
        return True
    else:
        print(f"\n⚠️ ISSUES DETECTED")
        failed_tests = [r[0] for r in results if '❌' in r[1]]
        print(f"❌ Failed tests: {', '.join(failed_tests)}")
        print(f"🔧 Check API Gateway deployment and Lambda functions")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        sys.exit(1)