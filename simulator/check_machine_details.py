#!/usr/bin/env python3
"""
Check detailed machine ID patterns to understand current state
"""

import boto3

def check_machine_details():
    """Check detailed machine patterns"""
    print("🔍 Checking detailed machine ID patterns...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-current-state')

    try:
        # Get a few sample items from each branch
        response = table.scan(Limit=20)

        print("Sample machine records:")
        for item in response['Items']:
            machine_id = item.get('machineId', '')
            gym_id = item.get('gymId', '')
            print(f"  gymId: {gym_id:<20} | machineId: {machine_id}")

    except Exception as e:
        print(f"❌ Error: {e}")

def check_expected_vs_actual():
    """Compare expected regional IDs with actual data"""
    print("\n🔍 Checking if we need mapping updates...")

    # Expected new regional IDs from our config
    expected_branches = [
        'hk-central-caine', 'hk-causeway-hennessy', 'hk-quarrybay-westlands',
        'kl-mongkok-nathan', 'kl-tsimshatsui-ashley', 'kl-jordan-nathan', 'kl-taikok-ivy',
        'nt-shatin-fun', 'nt-maonshan-lee', 'nt-tsuenwan-lik', 'nt-tinshui-tin', 'nt-fanling-green'
    ]

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-current-state')

    try:
        # Get all unique gymIds
        response = table.scan(ProjectionExpression='gymId')
        items = response['Items']

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ProjectionExpression='gymId',
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response['Items'])

        actual_gym_ids = set(item['gymId'] for item in items)

        print(f"Expected branches: {len(expected_branches)}")
        print(f"Actual gymIds in DB: {len(actual_gym_ids)}")
        print(f"Actual gymIds: {sorted(actual_gym_ids)}")

        # Check which ones need regional prefix updates
        needs_update = []
        for gym_id in actual_gym_ids:
            if gym_id.startswith('hk-') and not any(gym_id.startswith(prefix) for prefix in ['hk-central', 'hk-causeway', 'hk-quarry']):
                # This is an old HK ID that should be converted to KL or NT
                needs_update.append(gym_id)

        if needs_update:
            print(f"\nBranches that need regional prefix updates: {needs_update}")
        else:
            print("\n✅ All branches already have correct regional prefixes!")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_machine_details()
    check_expected_vs_actual()