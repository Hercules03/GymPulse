#!/usr/bin/env python3
"""
Simple regional prefix fix - update one table at a time
"""

import boto3
import sys
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

def update_current_state():
    """Update just current-state table first"""
    print("🔄 Updating current-state table...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-current-state')

    updates = 0

    for old_id, new_id in MAPPING.items():
        print(f"  Updating {old_id} → {new_id}")

        try:
            # Query items with this gymId (limited scan)
            response = table.scan(
                FilterExpression='gymId = :gid',
                ExpressionAttributeValues={':gid': old_id},
                Limit=100  # Process in smaller batches
            )

            items = response['Items']
            print(f"    Found {len(items)} items")

            # Update in batches
            with table.batch_writer() as batch:
                for item in items:
                    # Delete old
                    batch.delete_item(Key={'machineId': item['machineId']})

                    # Create new with updated gymId
                    new_item = item.copy()
                    new_item['gymId'] = new_id
                    batch.put_item(Item=new_item)

                    updates += 1

        except ClientError as e:
            print(f"    ❌ Error: {e}")

    print(f"✅ Updated {updates} items")

if __name__ == "__main__":
    update_current_state()