#!/usr/bin/env python3
"""
Comprehensive verification of DynamoDB data after training generation
Check regional distribution, data completeness, and API functionality
"""

import boto3
import json
import requests
from collections import Counter, defaultdict
from datetime import datetime, timedelta

def check_current_state_table():
    """Verify current-state table has all branches with correct regional distribution"""
    print("🔍 Checking current-state table...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-current-state')

    try:
        response = table.scan()
        items = response['Items']

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])

        print(f"✅ Total machines in current-state: {len(items)}")

        # Analyze by region and branch
        gym_counts = Counter(item['gymId'] for item in items)
        category_counts = Counter(item['category'] for item in items)

        print(f"\n📊 Regional Distribution:")
        hk_count = kl_count = nt_count = 0

        for gym_id, count in sorted(gym_counts.items()):
            prefix = gym_id.split('-')[0]
            if prefix == 'hk':
                region = "🇭🇰 HK"
                hk_count += count
            elif prefix == 'kl':
                region = "🏙️  KL"
                kl_count += count
            elif prefix == 'nt':
                region = "🏔️  NT"
                nt_count += count
            else:
                region = "❓ ??"

            print(f"   {gym_id:<25} {count:>3} machines [{region}]")

        print(f"\n📈 Regional Summary:")
        print(f"   🇭🇰 HK (Hong Kong Island): {hk_count:>3} machines")
        print(f"   🏙️  KL (Kowloon):          {kl_count:>3} machines")
        print(f"   🏔️  NT (New Territories):  {nt_count:>3} machines")
        print(f"   📍 Total:                  {hk_count + kl_count + nt_count:>3} machines")

        expected_total = 655
        if hk_count + kl_count + nt_count == expected_total:
            print(f"   ✅ Perfect! Matches expected {expected_total} machines")
        else:
            print(f"   ⚠️  Expected {expected_total} machines, got {hk_count + kl_count + nt_count}")

        print(f"\n🏷️  Category Distribution:")
        for category, count in sorted(category_counts.items()):
            percentage = (count / len(items)) * 100
            print(f"   {category:<12} {count:>3} machines ({percentage:.1f}%)")

        return len(gym_counts) == 12, hk_count + kl_count + nt_count == expected_total

    except Exception as e:
        print(f"❌ Error checking current-state: {e}")
        return False, False

def check_events_table():
    """Verify events table has historical data"""
    print(f"\n🔍 Checking events table...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-events')

    try:
        # Sample scan to check data exists
        response = table.scan(Limit=100)
        sample_items = response['Items']

        if sample_items:
            print(f"✅ Events table has data - sample of {len(sample_items)} items checked")

            # Check date range
            timestamps = [item['timestamp'] for item in sample_items]
            min_time = datetime.fromtimestamp(min(timestamps))
            max_time = datetime.fromtimestamp(max(timestamps))

            print(f"   📅 Data range: {min_time.strftime('%Y-%m-%d')} to {max_time.strftime('%Y-%m-%d')}")

            # Check branches in events
            event_gyms = set(item['gymId'] for item in sample_items)
            print(f"   🏢 Sample branches in events: {len(event_gyms)} different branches")

            return True
        else:
            print(f"❌ Events table is empty")
            return False

    except Exception as e:
        print(f"❌ Error checking events: {e}")
        return False

def check_api_response():
    """Verify API returns all 12 branches with data"""
    print(f"\n🔍 Checking API /branches endpoint...")

    try:
        response = requests.get("https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod/branches")

        if response.status_code == 200:
            data = response.json()
            branches = data.get('branches', [])

            print(f"✅ API Response successful - {len(branches)} branches returned")

            if len(branches) == 12:
                print(f"✅ Perfect! All 12 branches returned by API")
            else:
                print(f"⚠️  Expected 12 branches, API returned {len(branches)}")

            # Check regional distribution in API
            hk_branches = kl_branches = nt_branches = 0
            total_machines_api = 0

            print(f"\n📊 API Regional Distribution:")
            for branch in sorted(branches, key=lambda x: x['id']):
                branch_id = branch['id']
                categories = branch.get('categories', {})
                total_machines = sum(cat.get('total', 0) for cat in categories.values())
                free_machines = sum(cat.get('free', 0) for cat in categories.values())

                prefix = branch_id.split('-')[0]
                if prefix == 'hk':
                    region = "🇭🇰 HK"
                    hk_branches += 1
                elif prefix == 'kl':
                    region = "🏙️  KL"
                    kl_branches += 1
                elif prefix == 'nt':
                    region = "🏔️  NT"
                    nt_branches += 1
                else:
                    region = "❓ ??"

                total_machines_api += total_machines
                print(f"   {branch_id:<25} {total_machines:>3} machines ({free_machines:>3} free) [{region}]")

            print(f"\n📈 API Regional Summary:")
            print(f"   🇭🇰 HK: {hk_branches} branches")
            print(f"   🏙️  KL: {kl_branches} branches")
            print(f"   🏔️  NT: {nt_branches} branches")
            print(f"   📍 Total: {total_machines_api} machines across {len(branches)} branches")

            expected_distribution = (3, 4, 5)  # HK, KL, NT
            actual_distribution = (hk_branches, kl_branches, nt_branches)

            if actual_distribution == expected_distribution:
                print(f"   ✅ Perfect regional distribution: HK=3, KL=4, NT=5")
                return True
            else:
                print(f"   ⚠️  Expected HK=3, KL=4, NT=5, got HK={hk_branches}, KL={kl_branches}, NT={nt_branches}")
                return False

        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error checking API: {e}")
        return False

def test_chatbot_regional_queries():
    """Test chatbot with regional queries"""
    print(f"\n🔍 Testing chatbot with regional queries...")

    test_queries = [
        {
            "message": "I want to do legs nearby",
            "location": {"lat": 22.2819, "lon": 114.1577},  # Central (HK)
            "expected_region": "HK"
        },
        {
            "message": "chest workout nearby",
            "location": {"lat": 22.3193, "lon": 114.1694},  # Mongkok (KL)
            "expected_region": "KL"
        },
        {
            "message": "back exercises nearby",
            "location": {"lat": 22.3808, "lon": 114.1861},  # Shatin (NT)
            "expected_region": "NT"
        }
    ]

    chatbot_url = "https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod/chat"

    for i, test_case in enumerate(test_queries, 1):
        try:
            print(f"\n   Test {i}: {test_case['message']} (expecting {test_case['expected_region']} region)")

            payload = {
                "message": test_case["message"],
                "location": test_case["location"],
                "sessionId": f"test-{i}"
            }

            response = requests.post(chatbot_url, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                tools_used = data.get('toolsUsed', [])

                print(f"     ✅ Chatbot responded successfully")
                print(f"     🔧 Tools used: {tools_used}")
                print(f"     💬 Response: {response_text[:100]}...")

                # Check if response mentions regional branches
                if any(region in response_text.lower() for region in ['hk-', 'kl-', 'nt-']):
                    print(f"     ✅ Response includes regional branch IDs")
                else:
                    print(f"     ⚠️  Response doesn't clearly mention regional branches")

            else:
                print(f"     ❌ Chatbot error: {response.status_code}")

        except Exception as e:
            print(f"     ❌ Error testing chatbot: {e}")

def main():
    """Run comprehensive verification"""
    print("🔍 COMPREHENSIVE DATA VERIFICATION")
    print("=" * 50)

    # Check all components
    current_state_ok, machine_count_ok = check_current_state_table()
    events_ok = check_events_table()
    api_ok = check_api_response()

    print(f"\n" + "=" * 50)
    print(f"📋 VERIFICATION SUMMARY:")
    print(f"   ✅ Current State Table: {'✓' if current_state_ok else '✗'} (12 branches)")
    print(f"   ✅ Machine Count: {'✓' if machine_count_ok else '✗'} (655 machines)")
    print(f"   ✅ Events Table: {'✓' if events_ok else '✗'} (historical data)")
    print(f"   ✅ API Response: {'✓' if api_ok else '✗'} (regional distribution)")

    all_checks_passed = current_state_ok and machine_count_ok and events_ok and api_ok

    if all_checks_passed:
        print(f"\n🎉 ALL CHECKS PASSED!")
        print(f"✅ Complete regional organization (HK/KL/NT) is working perfectly!")
        print(f"✅ All 12 branches with 655 machines are operational!")
        print(f"✅ Frontend should now show all branches with proper regional distribution!")

        # Test chatbot
        test_chatbot_regional_queries()

    else:
        print(f"\n⚠️  Some checks failed - please review the issues above")

    return all_checks_passed

if __name__ == "__main__":
    main()