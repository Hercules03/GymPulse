#!/usr/bin/env python3
"""
Test updating just one branch to verify the approach works
"""

import boto3
from botocore.exceptions import ClientError

def test_one_branch():
    """Test updating just one branch"""
    print("🔄 Testing update of one branch: hk-mongkok-nathan → kl-mongkok-nathan")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    table = dynamodb.Table('gym-pulse-current-state')

    old_id = "hk-mongkok-nathan"
    new_id = "kl-mongkok-nathan"

    try:
        # Get items for this branch
        response = table.scan(
            FilterExpression='gymId = :gid',
            ExpressionAttributeValues={':gid': old_id}
        )

        items = response['Items']
        print(f"Found {len(items)} items for {old_id}")

        if items:
            # Update just the first item as a test
            item = items[0]
            print(f"Testing with machine: {item['machineId']}")

            # Create new item
            new_item = item.copy()
            new_item['gymId'] = new_id

            # Put new item
            table.put_item(Item=new_item)
            print("✅ Successfully created new item")

            # Delete old item
            table.delete_item(Key={'machineId': item['machineId']})
            print("✅ Successfully deleted old item")

            print("✅ Test successful! One item updated.")

        else:
            print("No items found for this branch")

    except ClientError as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_one_branch()