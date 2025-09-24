#!/usr/bin/env python3
"""
Fast cleanup script with progress indicators
"""
import boto3
import time
from datetime import datetime

def fast_cleanup():
    """Clean up DynamoDB tables with progress indicators"""
    print("🧹 Fast DynamoDB Cleanup Starting...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')

    tables_to_clean = [
        ('gym-pulse-events', 'machineId', 'timestamp'),
        ('gym-pulse-aggregates', 'gymId_category', 'timestamp15min'),
        ('gym-pulse-current-state', 'machineId', None)
    ]

    total_deleted = 0

    for table_name, partition_key, sort_key in tables_to_clean:
        print(f"\n📋 Cleaning {table_name}...")
        table = dynamodb.Table(table_name)

        deleted_count = 0

        while True:
            # Scan with minimal data, handle reserved keywords
            scan_kwargs = {}
            expression_attribute_names = {}
            projection_parts = []

            # Handle partition key
            if partition_key == 'timestamp':
                expression_attribute_names['#pk'] = partition_key
                projection_parts.append('#pk')
            else:
                projection_parts.append(partition_key)

            # Handle sort key
            if sort_key:
                if sort_key == 'timestamp':
                    expression_attribute_names['#sk'] = sort_key
                    projection_parts.append('#sk')
                else:
                    projection_parts.append(sort_key)

            scan_kwargs['ProjectionExpression'] = ', '.join(projection_parts)
            if expression_attribute_names:
                scan_kwargs['ExpressionAttributeNames'] = expression_attribute_names

            response = table.scan(**scan_kwargs)
            items = response.get('Items', [])

            if not items:
                break

            # Delete in batches of 25
            with table.batch_writer() as batch:
                for item in items:
                    key = {partition_key: item[partition_key]}
                    if sort_key and sort_key in item:
                        key[sort_key] = item[sort_key]

                    batch.delete_item(Key=key)
                    deleted_count += 1

                    if deleted_count % 100 == 0:
                        print(f"   Deleted {deleted_count} items...")

            # Handle pagination
            if 'LastEvaluatedKey' not in response:
                break

        print(f"   ✅ Deleted {deleted_count} items from {table_name}")
        total_deleted += deleted_count

    print(f"\n🎉 Cleanup complete! Total items deleted: {total_deleted}")
    return total_deleted

if __name__ == "__main__":
    start_time = time.time()
    deleted = fast_cleanup()
    duration = time.time() - start_time
    print(f"⏱️  Cleanup took {duration:.1f} seconds")