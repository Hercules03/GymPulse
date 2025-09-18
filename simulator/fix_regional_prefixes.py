#!/usr/bin/env python3
"""
Fix regional prefixes in existing DynamoDB data
Convert hk-* branches to proper kl-* and nt-* prefixes
"""

import boto3
from decimal import Decimal
from botocore.exceptions import ClientError

# Regional prefix mapping - only branches that need updating
REGIONAL_PREFIX_MAPPING = {
    # Kowloon (KL) - should start with kl-
    "hk-mongkok-nathan": "kl-mongkok-nathan",
    "hk-tsimshatsui-ashley": "kl-tsimshatsui-ashley",
    "hk-jordan-nathan": "kl-jordan-nathan",
    "hk-taikok-ivy": "kl-taikok-ivy",

    # New Territories (NT) - should start with nt-
    "hk-shatin-fun": "nt-shatin-fun",
    "hk-maonshan-lee": "nt-maonshan-lee",
    "hk-tsuenwan-lik": "nt-tsuenwan-lik",
    "hk-tinshui-tin": "nt-tinshui-tin",
    "hk-fanling-green": "nt-fanling-green"
}

def update_current_state_table():
    """Update current-state table with correct regional prefixes"""
    print("🔄 Updating current-state table regional prefixes...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-current-state')

    updates = 0

    for old_gym_id, new_gym_id in REGIONAL_PREFIX_MAPPING.items():
        print(f"  Updating {old_gym_id} → {new_gym_id}")

        try:
            # Scan for items with this gymId
            response = table.scan(
                FilterExpression='gymId = :gym_id',
                ExpressionAttributeValues={':gym_id': old_gym_id}
            )

            items = response['Items']

            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = table.scan(
                    FilterExpression='gymId = :gym_id',
                    ExpressionAttributeValues={':gym_id': old_gym_id},
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response['Items'])

            print(f"    Found {len(items)} items to update")

            # Update each item
            with table.batch_writer() as batch:
                for item in items:
                    # Delete old item
                    batch.delete_item(Key={'machineId': item['machineId']})

                    # Create new item with updated gymId
                    new_item = item.copy()
                    new_item['gymId'] = new_gym_id

                    batch.put_item(Item=new_item)
                    updates += 1

        except ClientError as e:
            print(f"    ❌ Error updating {old_gym_id}: {e}")

    print(f"✅ Updated {updates} items in current-state table")

def update_events_table():
    """Update events table with correct regional prefixes"""
    print("\n🔄 Updating events table regional prefixes...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-events')

    updates = 0

    for old_gym_id, new_gym_id in REGIONAL_PREFIX_MAPPING.items():
        print(f"  Updating {old_gym_id} → {new_gym_id}")

        try:
            # Scan for items with this gymId
            response = table.scan(
                FilterExpression='gymId = :gym_id',
                ExpressionAttributeValues={':gym_id': old_gym_id}
            )

            items = response['Items']

            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = table.scan(
                    FilterExpression='gymId = :gym_id',
                    ExpressionAttributeValues={':gym_id': old_gym_id},
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response['Items'])

            print(f"    Found {len(items)} items to update")

            # Update each item
            with table.batch_writer() as batch:
                for item in items:
                    # Delete old item
                    batch.delete_item(Key={
                        'machineId': item['machineId'],
                        'timestamp': item['timestamp']
                    })

                    # Create new item with updated gymId
                    new_item = item.copy()
                    new_item['gymId'] = new_gym_id

                    batch.put_item(Item=new_item)
                    updates += 1

        except ClientError as e:
            print(f"    ❌ Error updating {old_gym_id}: {e}")

    print(f"✅ Updated {updates} items in events table")

def update_aggregates_table():
    """Update aggregates table with correct regional prefixes"""
    print("\n🔄 Updating aggregates table regional prefixes...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-aggregates')

    updates = 0

    for old_gym_id, new_gym_id in REGIONAL_PREFIX_MAPPING.items():
        print(f"  Updating {old_gym_id} → {new_gym_id}")

        try:
            # Scan for items where gymId_category starts with old_gym_id
            response = table.scan(
                FilterExpression='begins_with(gymId_category, :prefix)',
                ExpressionAttributeValues={':prefix': f'{old_gym_id}_'}
            )

            items = response['Items']

            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = table.scan(
                    FilterExpression='begins_with(gymId_category, :prefix)',
                    ExpressionAttributeValues={':prefix': f'{old_gym_id}_'},
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response['Items'])

            print(f"    Found {len(items)} items to update")

            # Update each item
            with table.batch_writer() as batch:
                for item in items:
                    old_gym_category = item['gymId_category']

                    # Replace old gymId with new one in the key
                    new_gym_category = old_gym_category.replace(old_gym_id, new_gym_id)

                    # Delete old item
                    batch.delete_item(Key={
                        'gymId_category': old_gym_category,
                        'timestamp15min': item['timestamp15min']
                    })

                    # Create new item with updated keys
                    new_item = item.copy()
                    new_item['gymId_category'] = new_gym_category
                    new_item['gymId'] = new_gym_id

                    batch.put_item(Item=new_item)
                    updates += 1

        except ClientError as e:
            print(f"    ❌ Error updating {old_gym_id}: {e}")

    print(f"✅ Updated {updates} items in aggregates table")

def main():
    """Fix regional prefixes in all DynamoDB tables"""
    print("🔄 Fixing regional prefixes in DynamoDB tables...")
    print("Converting hk-* to proper kl-* and nt-* prefixes\n")

    # Show what we're updating
    print("📋 Regional Prefix Updates:")
    print("  Kowloon (KL):")
    for old, new in REGIONAL_PREFIX_MAPPING.items():
        if new.startswith('kl-'):
            print(f"    {old} → {new}")

    print("  New Territories (NT):")
    for old, new in REGIONAL_PREFIX_MAPPING.items():
        if new.startswith('nt-'):
            print(f"    {old} → {new}")
    print()

    # Update tables
    update_current_state_table()
    update_events_table()
    update_aggregates_table()

    print("\n✅ Regional prefix update completed!")
    print("🎯 All branches now have correct HK/KL/NT regional organization")

if __name__ == "__main__":
    main()