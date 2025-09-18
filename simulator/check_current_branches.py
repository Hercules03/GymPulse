#!/usr/bin/env python3
"""
Check what branch IDs currently exist in the database
"""

import boto3
from collections import Counter

def check_current_state_branches():
    """Check branch IDs in current-state table"""
    print("🔍 Checking current-state table...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-current-state')

    try:
        # Scan table and collect branch IDs
        response = table.scan(
            ProjectionExpression='machineId, gymId',
            Limit=100  # Just sample first 100 items
        )

        gym_ids = []
        machine_prefixes = []

        for item in response['Items']:
            gym_id = item.get('gymId', '')
            machine_id = item.get('machineId', '')

            gym_ids.append(gym_id)

            # Extract branch prefix from machine ID
            parts = machine_id.split('-')
            if len(parts) >= 2:
                prefix = f"{parts[0]}-{parts[1]}"
                machine_prefixes.append(prefix)

        print(f"Sample of {len(gym_ids)} items:")
        print("GymId distribution:", dict(Counter(gym_ids).most_common(10)))
        print("Machine ID prefixes:", dict(Counter(machine_prefixes).most_common(10)))

    except Exception as e:
        print(f"❌ Error: {e}")

def check_aggregates_branches():
    """Check branch IDs in aggregates table"""
    print("\n🔍 Checking aggregates table...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-aggregates')

    try:
        # Scan table and collect gym_category keys
        response = table.scan(
            ProjectionExpression='gymId_category',
            Limit=50  # Just sample
        )

        gym_categories = []

        for item in response['Items']:
            gym_category = item.get('gymId_category', '')
            gym_categories.append(gym_category)

        print(f"Sample of {len(gym_categories)} items:")
        print("GymId_category distribution:", dict(Counter(gym_categories).most_common(10)))

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_current_state_branches()
    check_aggregates_branches()