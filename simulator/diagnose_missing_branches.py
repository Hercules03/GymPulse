#!/usr/bin/env python3
"""
Diagnose why we're missing so many branches after the regional update
"""

import boto3
import json
from collections import Counter

def check_expected_vs_actual():
    """Compare what we expect vs what's in the database"""
    print("🔍 Diagnosing missing branches...")

    # Load the expected configuration
    with open('config/realistic_247_stores.json', 'r') as f:
        config = json.load(f)

    expected_branches = {}
    total_expected_machines = 0

    for branch in config['branches']:
        branch_id = branch['id']
        total_machines = branch['total_machines']
        region = branch['region']
        expected_branches[branch_id] = {
            'region': region,
            'total_machines': total_machines
        }
        total_expected_machines += total_machines

    print(f"Expected from config:")
    print(f"  Total branches: {len(expected_branches)}")
    print(f"  Total machines: {total_expected_machines}")

    hk_branches = [b for b, info in expected_branches.items() if info['region'] == 'HK']
    kl_branches = [b for b, info in expected_branches.items() if info['region'] == 'KL']
    nt_branches = [b for b, info in expected_branches.items() if info['region'] == 'NT']

    print(f"  HK branches: {len(hk_branches)} - {hk_branches}")
    print(f"  KL branches: {len(kl_branches)} - {kl_branches}")
    print(f"  NT branches: {len(nt_branches)} - {nt_branches}")

    # Check what's actually in the database
    print(f"\nActual in database:")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-current-state')

    try:
        response = table.scan(ProjectionExpression='gymId')
        items = response['Items']

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ProjectionExpression='gymId',
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response['Items'])

        actual_gym_ids = Counter(item['gymId'] for item in items)

        print(f"  Total items in DB: {len(items)}")
        print(f"  Unique branches in DB: {len(actual_gym_ids)}")

        for gym_id, count in sorted(actual_gym_ids.items()):
            prefix = gym_id.split('-')[0]
            region = "HK" if prefix == "hk" else prefix.upper()
            expected_count = expected_branches.get(gym_id, {}).get('total_machines', 'UNKNOWN')
            status = "✅" if count == expected_count else "❌"
            print(f"    {gym_id:<25} {count:>3} items [{region}] (expected: {expected_count}) {status}")

        # Check what's missing
        missing_branches = set(expected_branches.keys()) - set(actual_gym_ids.keys())
        if missing_branches:
            print(f"\n❌ Missing branches ({len(missing_branches)}):")
            for branch in sorted(missing_branches):
                info = expected_branches[branch]
                print(f"    {branch} ({info['region']}) - {info['total_machines']} machines")
        else:
            print(f"\n✅ All expected branches are present!")

    except Exception as e:
        print(f"❌ Error checking database: {e}")

def check_other_tables():
    """Check if the missing data is in other tables"""
    print(f"\n🔍 Checking events table for missing branches...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    events_table = dynamodb.Table('gym-pulse-events')

    try:
        # Check a small sample of events table
        response = events_table.scan(
            ProjectionExpression='gymId',
            Limit=50
        )

        events_gym_ids = set(item['gymId'] for item in response['Items'])
        print(f"Sample gym IDs in events table: {sorted(events_gym_ids)}")

    except Exception as e:
        print(f"❌ Error checking events table: {e}")

if __name__ == "__main__":
    check_expected_vs_actual()
    check_other_tables()