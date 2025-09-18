#!/usr/bin/env python3
"""
Fast table recreation - much faster than item-by-item deletion
"""
import boto3
import time

def recreate_tables():
    """Delete and recreate DynamoDB tables"""
    print("🗑️  Recreating DynamoDB tables (fastest cleanup method)...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')

    tables_to_recreate = [
        {
            'name': 'gym-pulse-events',
            'partition_key': 'machineId',
            'sort_key': 'timestamp',
            'ttl_attribute': 'ttl'
        },
        {
            'name': 'gym-pulse-aggregates',
            'partition_key': 'gymId_category',
            'sort_key': 'timestamp15min',
            'ttl_attribute': 'ttl'
        }
    ]

    for table_config in tables_to_recreate:
        table_name = table_config['name']
        print(f"\n📋 Recreating {table_name}...")

        try:
            # Get existing table configuration
            table = dynamodb.Table(table_name)
            table_info = table.meta.client.describe_table(TableName=table_name)

            # Extract configuration
            key_schema = table_info['Table']['KeySchema']
            attribute_definitions = table_info['Table']['AttributeDefinitions']
            billing_mode = table_info['Table']['BillingMode']

            print(f"   🗑️  Deleting {table_name}...")
            table.delete()

            # Wait for deletion
            print(f"   ⏳ Waiting for deletion...")
            table.meta.client.get_waiter('table_not_exists').wait(TableName=table_name)

            print(f"   🏗️  Recreating {table_name}...")
            # Recreate table
            new_table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attribute_definitions,
                BillingMode=billing_mode
            )

            # Wait for table to be active
            print(f"   ⏳ Waiting for table to be active...")
            new_table.meta.client.get_waiter('table_exists').wait(TableName=table_name)

            # Re-enable TTL if it was configured
            if table_config.get('ttl_attribute'):
                print(f"   🕐 Re-enabling TTL...")
                new_table.meta.client.update_time_to_live(
                    TableName=table_name,
                    TimeToLiveSpecification={
                        'AttributeName': table_config['ttl_attribute'],
                        'Enabled': True
                    }
                )

            print(f"   ✅ {table_name} recreated successfully")

        except Exception as e:
            print(f"   ❌ Error with {table_name}: {e}")

    # Clear current state table (keep structure, just delete data)
    print(f"\n📋 Clearing gym-pulse-current-state...")
    try:
        current_state_table = dynamodb.Table('gym-pulse-current-state')

        # Scan and delete in batches
        response = current_state_table.scan()
        items = response.get('Items', [])

        if items:
            with current_state_table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(Key={'machineId': item['machineId']})
            print(f"   ✅ Cleared {len(items)} items from gym-pulse-current-state")
        else:
            print(f"   ✅ gym-pulse-current-state already empty")

    except Exception as e:
        print(f"   ❌ Error clearing current state: {e}")

    print(f"\n🎉 All tables recreated! Ready for fresh training data.")

if __name__ == "__main__":
    start_time = time.time()
    recreate_tables()
    duration = time.time() - start_time
    print(f"⏱️  Table recreation took {duration:.1f} seconds")