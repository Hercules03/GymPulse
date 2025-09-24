#!/usr/bin/env python3
"""
Complete the remaining regional prefix updates
"""

import boto3
import time
from botocore.exceptions import ClientError

# Only update branches that still need it (from our previous check)
REMAINING_UPDATES = {
    "hk-fanling-green": "nt-fanling-green",     # 30 items
    "hk-maonshan-lee": "nt-maonshan-lee",       # 20 items
    "hk-tinshui-tin": "nt-tinshui-tin",         # 35 items
    "hk-tsuenwan-lik": "nt-tsuenwan-lik"        # 50 items
}

def complete_current_state_updates():
    """Complete the remaining regional prefix updates"""
    print("🔄 Completing remaining regional prefix updates...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-current-state')

    total_updated = 0

    for old_id, new_id in REMAINING_UPDATES.items():
        print(f"\n  Processing {old_id} → {new_id}")

        try:
            # Get all items for this branch
            response = table.scan(
                FilterExpression='gymId = :gid',
                ExpressionAttributeValues={':gid': old_id}
            )

            items = response['Items']
            print(f"    Found {len(items)} items to update")

            # Process in small batches to avoid timeouts
            batch_size = 10
            for i in range(0, len(items), batch_size):
                batch = items[i:i+batch_size]
                print(f"    Processing batch {i//batch_size + 1}/{(len(items)-1)//batch_size + 1}")

                for item in batch:
                    try:
                        # Create new item with updated gymId
                        new_item = item.copy()
                        new_item['gymId'] = new_id

                        # Put new item first
                        table.put_item(Item=new_item)

                        # Delete old item
                        table.delete_item(Key={'machineId': item['machineId']})

                        total_updated += 1

                    except ClientError as e:
                        print(f"      ❌ Error updating {item['machineId']}: {e}")

                # Small delay between batches to avoid throttling
                time.sleep(0.2)

        except ClientError as e:
            print(f"    ❌ Error processing {old_id}: {e}")

    print(f"\n✅ Completed! Updated {total_updated} items total")

def verify_completion():
    """Verify all regional updates are complete"""
    print("\n🔍 Verifying completion...")

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

        from collections import Counter
        gym_id_counts = Counter(item['gymId'] for item in items)

        print("Final gymId distribution:")
        hk_count = kl_count = nt_count = 0

        for gym_id, count in sorted(gym_id_counts.items()):
            prefix = gym_id.split('-')[0]
            if prefix == 'hk':
                region = "HK"
                hk_count += count
            elif prefix == 'kl':
                region = "KL"
                kl_count += count
            elif prefix == 'nt':
                region = "NT"
                nt_count += count
            else:
                region = "??"

            print(f"  {gym_id:<25} {count:>3} items [{region}]")

        print(f"\nRegional Summary:")
        print(f"  HK (Hong Kong Island): {hk_count} items")
        print(f"  KL (Kowloon):          {kl_count} items")
        print(f"  NT (New Territories):  {nt_count} items")
        print(f"  Total:                 {hk_count + kl_count + nt_count} items")

        # Check for any remaining old prefixes
        old_prefixes = [gid for gid in gym_id_counts.keys() if gid in REMAINING_UPDATES.keys()]
        if old_prefixes:
            print(f"\n⚠️  Still have old prefixes: {old_prefixes}")
        else:
            print(f"\n✅ All regional prefixes updated successfully!")

    except Exception as e:
        print(f"❌ Error verifying: {e}")

if __name__ == "__main__":
    complete_current_state_updates()
    verify_completion()