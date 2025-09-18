#!/usr/bin/env python3
"""
Fix regional prefixes by updating items individually to avoid duplicates
"""

import boto3
import time
from botocore.exceptions import ClientError

# Regional prefix mapping
MAPPING = {
    "hk-mongkok-nathan": "kl-mongkok-nathan",
    "hk-tsimshatsui-ashley": "kl-tsimshatsui-ashley",
    "hk-jordan-nathan": "kl-jordan-nathan",
    "hk-taikok-ivy": "kl-taikok-ivy",
    "hk-shatin-fun": "nt-shatin-fun",
    "hk-maonshan-lee": "nt-maonshan-lee",
    "hk-tsuenwan-lik": "nt-tsuenwan-lik",
    "hk-tinshui-tin": "nt-tinshui-tin",
    "hk-fanling-green": "nt-fanling-green"
}

def update_current_state_individual():
    """Update current-state table item by item"""
    print("🔄 Updating current-state table (individual updates)...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-current-state')

    total_updates = 0

    for old_id, new_id in MAPPING.items():
        print(f"  Processing {old_id} → {new_id}")

        try:
            # Scan for items with this gymId
            response = table.scan(
                FilterExpression='gymId = :gid',
                ExpressionAttributeValues={':gid': old_id}
            )

            items = response['Items']
            print(f"    Found {len(items)} items")

            # Update each item individually
            for i, item in enumerate(items):
                try:
                    # First, put the new item
                    new_item = item.copy()
                    new_item['gymId'] = new_id

                    table.put_item(Item=new_item)

                    # Then delete the old item
                    table.delete_item(Key={'machineId': item['machineId']})

                    total_updates += 1

                    if (i + 1) % 10 == 0:
                        print(f"      Updated {i + 1}/{len(items)} items")
                        time.sleep(0.1)  # Small delay to avoid throttling

                except ClientError as e:
                    print(f"      ❌ Error updating item {item['machineId']}: {e}")

        except ClientError as e:
            print(f"    ❌ Error scanning {old_id}: {e}")

    print(f"✅ Updated {total_updates} items in current-state table")

def verify_update():
    """Verify the update worked"""
    print("\n🔍 Verifying updates...")

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

        gym_ids = set(item['gymId'] for item in items)
        print(f"Current gymIds in database: {sorted(gym_ids)}")

        # Check for old IDs
        old_ids_remaining = [gid for gid in gym_ids if gid in MAPPING.keys()]
        if old_ids_remaining:
            print(f"⚠️  Old IDs still present: {old_ids_remaining}")
        else:
            print("✅ All old IDs successfully updated!")

    except Exception as e:
        print(f"❌ Error verifying: {e}")

if __name__ == "__main__":
    update_current_state_individual()
    verify_update()