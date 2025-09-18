#!/usr/bin/env python3
"""
Update existing DynamoDB data with new regional branch IDs
Much faster than regenerating all training data
"""

import boto3
import json
from decimal import Decimal
from botocore.exceptions import ClientError

# Regional mapping for branch ID updates
BRANCH_ID_MAPPING = {
    # Hong Kong Island (HK)
    "hk-central": "hk-central-caine",
    "hk-causeway": "hk-causeway-hennessy",
    "hk-quarrybay": "hk-quarrybay-westlands",

    # Kowloon (KL)
    "hk-mongkok": "kl-mongkok-nathan",
    "hk-tsimshatsui": "kl-tsimshatsui-ashley",
    "hk-jordan": "kl-jordan-nathan",
    "hk-taikok": "kl-taikok-ivy",

    # New Territories (NT)
    "hk-shatin": "nt-shatin-fun",
    "hk-maonshan": "nt-maonshan-lee",
    "hk-tsuenwan": "nt-tsuenwan-lik",
    "hk-tinshui": "nt-tinshui-tin",
    "hk-fanling": "nt-fanling-green"
}

def update_current_state_table():
    """Update gym-pulse-current-state table with new branch IDs"""
    print("🔄 Updating current-state table...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-current-state')

    try:
        # Scan all items
        response = table.scan()
        items = response['Items']

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])

        print(f"Found {len(items)} items in current-state table")

        updates = 0
        with table.batch_writer() as batch:
            for item in items:
                machine_id = item['machineId']
                old_gym_id = item.get('gymId', '')

                # Extract branch ID from machine ID (e.g., "hk-central-leg-press-01" -> "hk-central")
                parts = machine_id.split('-')
                if len(parts) >= 2:
                    old_branch_id = f"{parts[0]}-{parts[1]}"

                    if old_branch_id in BRANCH_ID_MAPPING:
                        new_branch_id = BRANCH_ID_MAPPING[old_branch_id]
                        new_machine_id = machine_id.replace(old_branch_id, new_branch_id)

                        # Delete old item
                        batch.delete_item(Key={'machineId': machine_id})

                        # Create new item with updated IDs
                        new_item = item.copy()
                        new_item['machineId'] = new_machine_id
                        new_item['gymId'] = new_branch_id

                        batch.put_item(Item=new_item)
                        updates += 1

                        if updates % 50 == 0:
                            print(f"  Updated {updates} items...")

        print(f"✅ Updated {updates} items in current-state table")

    except ClientError as e:
        print(f"❌ Error updating current-state table: {e}")

def update_events_table():
    """Update gym-pulse-events table with new branch IDs"""
    print("🔄 Updating events table...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-events')

    try:
        # Scan all items
        response = table.scan()
        items = response['Items']

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])

        print(f"Found {len(items)} items in events table")

        updates = 0
        with table.batch_writer() as batch:
            for item in items:
                machine_id = item['machineId']
                old_gym_id = item.get('gymId', '')

                # Extract branch ID from machine ID
                parts = machine_id.split('-')
                if len(parts) >= 2:
                    old_branch_id = f"{parts[0]}-{parts[1]}"

                    if old_branch_id in BRANCH_ID_MAPPING:
                        new_branch_id = BRANCH_ID_MAPPING[old_branch_id]
                        new_machine_id = machine_id.replace(old_branch_id, new_branch_id)

                        # Delete old item
                        batch.delete_item(Key={
                            'machineId': machine_id,
                            'timestamp': item['timestamp']
                        })

                        # Create new item with updated IDs
                        new_item = item.copy()
                        new_item['machineId'] = new_machine_id
                        new_item['gymId'] = new_branch_id

                        batch.put_item(Item=new_item)
                        updates += 1

                        if updates % 100 == 0:
                            print(f"  Updated {updates} items...")

        print(f"✅ Updated {updates} items in events table")

    except ClientError as e:
        print(f"❌ Error updating events table: {e}")

def update_aggregates_table():
    """Update gym-pulse-aggregates table with new branch IDs"""
    print("🔄 Updating aggregates table...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-aggregates')

    try:
        # Scan all items
        response = table.scan()
        items = response['Items']

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])

        print(f"Found {len(items)} items in aggregates table")

        updates = 0
        with table.batch_writer() as batch:
            for item in items:
                gym_category_key = item['gymId_category']

                # Extract old branch ID from gym_category key (e.g., "hk-central_legs")
                if '_' in gym_category_key:
                    old_branch_id, category = gym_category_key.split('_', 1)

                    if old_branch_id in BRANCH_ID_MAPPING:
                        new_branch_id = BRANCH_ID_MAPPING[old_branch_id]
                        new_gym_category_key = f"{new_branch_id}_{category}"

                        # Delete old item
                        batch.delete_item(Key={
                            'gymId_category': gym_category_key,
                            'timestamp15min': item['timestamp15min']
                        })

                        # Create new item with updated key
                        new_item = item.copy()
                        new_item['gymId_category'] = new_gym_category_key
                        new_item['gymId'] = new_branch_id

                        batch.put_item(Item=new_item)
                        updates += 1

                        if updates % 100 == 0:
                            print(f"  Updated {updates} items...")

        print(f"✅ Updated {updates} items in aggregates table")

    except ClientError as e:
        print(f"❌ Error updating aggregates table: {e}")

def main():
    """Update all DynamoDB tables with new regional branch IDs"""
    print("🔄 Starting regional branch ID update...")
    print("This will update existing data with new HK/KL/NT prefixes")
    print("Much faster than regenerating all training data!\n")

    # Show mapping
    print("📋 Branch ID Mapping:")
    for old_id, new_id in BRANCH_ID_MAPPING.items():
        print(f"   {old_id} → {new_id}")
    print()

    # Update each table
    update_current_state_table()
    print()
    update_events_table()
    print()
    update_aggregates_table()

    print("\n✅ Regional branch ID update completed!")
    print("🎯 All data now uses HK/KL/NT regional organization")

if __name__ == "__main__":
    main()