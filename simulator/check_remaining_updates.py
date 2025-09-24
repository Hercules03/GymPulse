#!/usr/bin/env python3
"""
Check what regional prefix updates are still needed
"""

import boto3
from collections import Counter

def check_remaining_updates():
    """Check current status and what needs updating"""
    print("🔍 Checking remaining regional prefix updates needed...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-current-state')

    try:
        # Get all gymIds
        response = table.scan(ProjectionExpression='gymId')
        items = response['Items']

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ProjectionExpression='gymId',
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response['Items'])

        gym_id_counts = Counter(item['gymId'] for item in items)

        print(f"Total items: {len(items)}")
        print(f"Unique gymIds: {len(gym_id_counts)}")
        print("\nCurrent gymId distribution:")
        for gym_id, count in sorted(gym_id_counts.items()):
            prefix = gym_id.split('-')[0]
            region = "HK" if prefix == "hk" else prefix.upper()
            print(f"  {gym_id:<25} {count:>3} items [{region}]")

        # Identify branches that still need updating (start with hk- but not Hong Kong Island)
        hk_island_branches = ['hk-central-caine', 'hk-causeway-hennessy', 'hk-quarrybay-westlands']

        needs_update = []
        for gym_id in gym_id_counts.keys():
            if gym_id.startswith('hk-') and gym_id not in hk_island_branches:
                needs_update.append(gym_id)

        if needs_update:
            print(f"\n🔄 Branches still needing regional prefix updates:")
            for branch in sorted(needs_update):
                print(f"  {branch} (has {gym_id_counts[branch]} items)")
        else:
            print("\n✅ All branches have correct regional prefixes!")

        # Check for any duplicates (old and new versions)
        print(f"\n🔍 Checking for duplicate branch processing...")
        base_names = {}
        for gym_id in gym_id_counts.keys():
            # Extract base name (without regional prefix)
            if gym_id.startswith('hk-'):
                base_name = gym_id[3:]  # Remove 'hk-'
            elif gym_id.startswith('kl-'):
                base_name = gym_id[3:]  # Remove 'kl-'
            elif gym_id.startswith('nt-'):
                base_name = gym_id[3:]  # Remove 'nt-'
            else:
                base_name = gym_id

            if base_name not in base_names:
                base_names[base_name] = []
            base_names[base_name].append(gym_id)

        duplicates = {k: v for k, v in base_names.items() if len(v) > 1}
        if duplicates:
            print(f"Found {len(duplicates)} branches with multiple regional versions:")
            for base_name, versions in duplicates.items():
                print(f"  {base_name}: {versions}")
        else:
            print("No duplicate regional versions found")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_remaining_updates()