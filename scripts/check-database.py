#!/usr/bin/env python3
"""
GymPulse Database Inspector

Check data stored in DynamoDB tables for debugging and validation.
"""

import boto3
import json
from datetime import datetime, timezone
from tabulate import tabulate

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb', region_name='ap-east-1')
dynamodb_resource = boto3.resource('dynamodb', region_name='ap-east-1')

def format_dynamodb_item(item):
    """Convert DynamoDB item format to readable format"""
    result = {}
    for key, value in item.items():
        if 'S' in value:
            result[key] = value['S']
        elif 'N' in value:
            result[key] = int(value['N']) if value['N'].isdigit() else float(value['N'])
        elif 'BOOL' in value:
            result[key] = value['BOOL']
        elif 'M' in value:
            result[key] = format_dynamodb_item(value['M'])
        else:
            result[key] = str(value)
    return result

def check_current_state():
    """Check current machine states"""
    print("🔍 CURRENT MACHINE STATES")
    print("=" * 50)
    
    try:
        response = dynamodb.scan(
            TableName='gym-pulse-current-state',
            Limit=20
        )
        
        if response['Items']:
            items = [format_dynamodb_item(item) for item in response['Items']]
            headers = ['Machine ID', 'Status', 'Last Update', 'Gym ID', 'Category']
            table_data = []
            
            for item in items:
                timestamp = datetime.fromtimestamp(item.get('lastUpdate', 0), tz=timezone.utc)
                table_data.append([
                    item.get('machineId', 'N/A'),
                    item.get('status', 'N/A'),
                    timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                    item.get('gymId', 'N/A'),
                    item.get('category', 'N/A')
                ])
            
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
        else:
            print("❌ No current state data found. Is the simulator running?")
            
    except Exception as e:
        print(f"❌ Error checking current state: {e}")

def check_recent_events():
    """Check recent machine events"""
    print("\n🔍 RECENT MACHINE EVENTS")
    print("=" * 50)
    
    try:
        response = dynamodb.scan(
            TableName='gym-pulse-events',
            Limit=10
        )
        
        if response['Items']:
            items = [format_dynamodb_item(item) for item in response['Items']]
            # Sort by timestamp (most recent first)
            items.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            headers = ['Machine ID', 'Status', 'Timestamp', 'Transition']
            table_data = []
            
            for item in items[:10]:  # Show latest 10
                timestamp = datetime.fromtimestamp(item.get('timestamp', 0), tz=timezone.utc)
                table_data.append([
                    item.get('machineId', 'N/A'),
                    item.get('status', 'N/A'),
                    timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                    item.get('transition', 'N/A')
                ])
            
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
        else:
            print("❌ No event data found. Is the simulator running?")
            
    except Exception as e:
        print(f"❌ Error checking events: {e}")

def check_aggregates():
    """Check aggregation data"""
    print("\n🔍 AGGREGATION DATA")
    print("=" * 50)
    
    try:
        response = dynamodb.scan(
            TableName='gym-pulse-aggregates',
            Limit=10
        )
        
        if response['Items']:
            items = [format_dynamodb_item(item) for item in response['Items']]
            
            headers = ['Gym+Category', 'Timestamp', 'Occupancy %', 'Free Count', 'Total Count']
            table_data = []
            
            for item in items:
                timestamp = datetime.fromtimestamp(item.get('timestamp15min', 0), tz=timezone.utc)
                table_data.append([
                    item.get('gymId_category', 'N/A'),
                    timestamp.strftime('%Y-%m-%d %H:%M UTC'),
                    f"{item.get('occupancyRatio', 0):.1f}%",
                    item.get('freeCount', 0),
                    item.get('totalCount', 0)
                ])
            
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
        else:
            print("❌ No aggregation data found.")
            
    except Exception as e:
        print(f"❌ Error checking aggregates: {e}")

def check_alerts():
    """Check active alerts"""
    print("\n🔍 ACTIVE ALERTS")
    print("=" * 50)
    
    try:
        response = dynamodb.scan(
            TableName='gym-pulse-alerts',
            Limit=10
        )
        
        if response['Items']:
            items = [format_dynamodb_item(item) for item in response['Items']]
            
            headers = ['User ID', 'Machine ID', 'Active', 'Created At']
            table_data = []
            
            for item in items:
                created_at = datetime.fromtimestamp(item.get('createdAt', 0), tz=timezone.utc)
                table_data.append([
                    item.get('userId', 'N/A'),
                    item.get('machineId', 'N/A'),
                    '✅ Yes' if item.get('active', False) else '❌ No',
                    created_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                ])
            
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
        else:
            print("❌ No alerts found.")
            
    except Exception as e:
        print(f"❌ Error checking alerts: {e}")

def check_table_stats():
    """Check table statistics"""
    print("\n📊 TABLE STATISTICS")
    print("=" * 50)
    
    tables = [
        'gym-pulse-current-state',
        'gym-pulse-events', 
        'gym-pulse-aggregates',
        'gym-pulse-alerts'
    ]
    
    stats_data = []
    
    for table_name in tables:
        try:
            response = dynamodb.describe_table(TableName=table_name)
            table = response['Table']
            
            # Get item count
            scan_response = dynamodb.scan(
                TableName=table_name,
                Select='COUNT'
            )
            
            stats_data.append([
                table_name,
                scan_response['Count'],
                table['TableStatus'],
                f"{table['TableSizeBytes'] / 1024:.1f} KB" if table['TableSizeBytes'] > 0 else "0 KB"
            ])
            
        except Exception as e:
            stats_data.append([table_name, 'Error', f'Error: {str(e)[:30]}...', 'N/A'])
    
    headers = ['Table Name', 'Item Count', 'Status', 'Size']
    print(tabulate(stats_data, headers=headers, tablefmt='grid'))

def main():
    """Main function to check all database data"""
    print("🏋️ GymPulse Database Inspector")
    print("=" * 60)
    print(f"Checking DynamoDB tables in region: ap-east-1")
    print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    # Check all data
    check_table_stats()
    check_current_state()
    check_recent_events()
    check_aggregates()
    check_alerts()
    
    print("\n💡 TIPS:")
    print("- Start the simulator to see real-time data: cd simulator && python src/main.py")
    print("- Check AWS Console DynamoDB for visual data exploration")
    print("- Use 'aws dynamodb scan --table-name <table>' for direct CLI access")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Database inspection interrupted by user")
    except Exception as e:
        print(f"\n❌ Database inspection failed: {e}")