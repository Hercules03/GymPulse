#!/usr/bin/env python3
"""
Simple table recreation using CDK-like definitions
"""
import boto3
import time

def recreate_tables():
    """Delete and recreate DynamoDB tables with simple definitions"""
    print("🗑️  Recreating DynamoDB tables...")

    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')

    tables_to_recreate = ['gym-pulse-events', 'gym-pulse-aggregates']

    for table_name in tables_to_recreate:
        print(f"\n📋 Processing {table_name}...")

        try:
            # Delete existing table
            table = dynamodb.Table(table_name)
            print(f"   🗑️  Deleting {table_name}...")
            table.delete()

            # Wait for deletion
            print(f"   ⏳ Waiting for deletion...")
            table.meta.client.get_waiter('table_not_exists').wait(TableName=table_name)
            print(f"   ✅ {table_name} deleted")

        except Exception as e:
            if 'ResourceNotFoundException' in str(e):
                print(f"   ℹ️  {table_name} doesn't exist, will create new")
            else:
                print(f"   ❌ Error deleting {table_name}: {e}")

        # Create new table based on name
        if table_name == 'gym-pulse-events':
            print(f"   🏗️  Creating {table_name}...")
            new_table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'machineId', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'machineId', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'N'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )

        elif table_name == 'gym-pulse-aggregates':
            print(f"   🏗️  Creating {table_name}...")
            new_table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'gymId_category', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp15min', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'gymId_category', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp15min', 'AttributeType': 'N'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )

        # Wait for table to be active
        print(f"   ⏳ Waiting for {table_name} to be active...")
        new_table.meta.client.get_waiter('table_exists').wait(TableName=table_name)

        # Enable TTL
        print(f"   🕐 Enabling TTL...")
        new_table.meta.client.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                'AttributeName': 'ttl',
                'Enabled': True
            }
        )

        print(f"   ✅ {table_name} recreated successfully")

    print(f"\n🎉 All tables recreated! Ready for fresh training data.")

if __name__ == "__main__":
    start_time = time.time()
    recreate_tables()
    duration = time.time() - start_time
    print(f"⏱️  Table recreation took {duration:.1f} seconds")