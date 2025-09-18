#!/usr/bin/env python3
"""
Simple approach to generate training data for missing 8 branches
Using basic patterns without complex usage calculations
"""

import boto3
import json
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Missing branches that need data generation
MISSING_BRANCHES = [
    'kl-jordan-nathan',     # 50 machines
    'kl-mongkok-nathan',    # 75 machines
    'kl-taikok-ivy',        # 45 machines
    'kl-tsimshatsui-ashley', # 65 machines
    'nt-fanling-green',     # 30 machines
    'nt-shatin-fun',        # 55 machines
    'nt-tinshui-tin',       # 35 machines
    'nt-tsuenwan-lik'       # 50 machines
]

def load_missing_machines():
    """Load machines for missing branches"""
    with open('config/machines.json', 'r') as f:
        config = json.load(f)

    missing_machines = []
    for branch in config['branches']:
        branch_id = branch['id']
        if branch_id in MISSING_BRANCHES:
            coordinates = branch['coordinates']
            for machine in branch['machines']:
                machine_data = {
                    'machineId': machine['machineId'],
                    'gymId': branch_id,
                    'category': machine['category'],
                    'coordinates': coordinates
                }
                missing_machines.append(machine_data)

    print(f"Found {len(missing_machines)} machines to generate data for")
    return missing_machines

def get_basic_occupancy_rate(hour, is_weekend=False):
    """Get basic occupancy rate by time of day"""
    if is_weekend:
        # Weekend pattern - more spread out
        if 8 <= hour <= 11:  # Morning
            return 0.6
        elif 14 <= hour <= 18:  # Afternoon
            return 0.7
        elif 19 <= hour <= 21:  # Evening
            return 0.5
        else:
            return 0.2
    else:
        # Weekday pattern
        if 6 <= hour <= 9:  # Morning rush
            return 0.6
        elif 12 <= hour <= 14:  # Lunch
            return 0.8
        elif 18 <= hour <= 21:  # Evening rush
            return 0.9
        else:
            return 0.3

def generate_simple_training_data():
    """Generate training data with simple patterns"""
    print("🔄 Generating training data for missing branches...")

    # Load machines
    missing_machines = load_missing_machines()

    # DynamoDB setup
    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    current_state_table = dynamodb.Table('gym-pulse-current-state')
    events_table = dynamodb.Table('gym-pulse-events')

    # Generate data for last 7 days (shorter for speed)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    total_events = 0
    batch_size = 25  # Process in batches for DynamoDB

    print(f"Generating data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    # Process machines in batches
    for batch_start in range(0, len(missing_machines), batch_size):
        batch_machines = missing_machines[batch_start:batch_start + batch_size]
        print(f"\nProcessing batch {batch_start//batch_size + 1}/{(len(missing_machines)-1)//batch_size + 1}")

        # Process each machine in the batch
        for machine in batch_machines:
            machine_id = machine['machineId']
            gym_id = machine['gymId']
            category = machine['category']

            print(f"  {machine_id}")

            # Generate some events for this machine
            current_date = start_date
            current_status = 'free'
            machine_events = 0

            while current_date < end_date:
                # Simple occupancy calculation
                hour = current_date.hour
                is_weekend = current_date.weekday() >= 5
                base_occupancy = get_basic_occupancy_rate(hour, is_weekend)

                # Add some randomness
                if random.random() < 0.15:  # 15% chance of status change each hour
                    # Determine new status based on occupancy rate
                    if current_status == 'free':
                        if random.random() < base_occupancy:
                            current_status = 'occupied'
                    else:  # currently occupied
                        if random.random() < 0.7:  # 70% chance to become free
                            current_status = 'free'

                    # Create event only if status changed
                    if machine_events < 50:  # Limit events per machine for speed
                        event_item = {
                            'machineId': machine_id,
                            'timestamp': int(current_date.timestamp()),
                            'status': current_status,
                            'gymId': gym_id,
                            'category': category,
                            'ttl': int((end_date + timedelta(days=30)).timestamp())
                        }

                        try:
                            events_table.put_item(Item=event_item)
                            machine_events += 1
                            total_events += 1
                        except Exception as e:
                            print(f"    Error creating event: {e}")

                # Move to next hour
                current_date += timedelta(hours=1)

            # Create current state for this machine
            current_state_item = {
                'machineId': machine_id,
                'status': current_status,
                'lastUpdate': int(end_date.timestamp()),
                'gymId': gym_id,
                'category': category,
                'coordinates': {
                    'lat': Decimal(str(machine['coordinates']['lat'])),
                    'lon': Decimal(str(machine['coordinates']['lon']))
                }
            }

            try:
                current_state_table.put_item(Item=current_state_item)
            except Exception as e:
                print(f"    Error creating current state: {e}")

        print(f"  Completed batch - {total_events} total events so far")

    print(f"\n✅ Training data generation completed!")
    print(f"   Generated {total_events} events")
    print(f"   Created current state for {len(missing_machines)} machines")

def verify_branches():
    """Verify all branches are now present"""
    print("\n🔍 Verifying all branches are present...")

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

        print(f"Branches in database: {len(gym_id_counts)}")

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

            print(f"  {gym_id:<25} {count:>3} items [{region}]")

        print(f"\nRegional Distribution:")
        print(f"  HK (Hong Kong Island): {hk_count} machines")
        print(f"  KL (Kowloon):          {kl_count} machines")
        print(f"  NT (New Territories):  {nt_count} machines")
        print(f"  Total:                 {hk_count + kl_count + nt_count} machines")

        # Check if we have all expected branches
        expected_branches = 12
        if len(gym_id_counts) >= expected_branches:
            print(f"\n✅ Success! All {len(gym_id_counts)} branches have data")
        else:
            print(f"\n⚠️  Only {len(gym_id_counts)}/{expected_branches} branches have data")

    except Exception as e:
        print(f"❌ Error verifying: {e}")

if __name__ == "__main__":
    generate_simple_training_data()
    verify_branches()