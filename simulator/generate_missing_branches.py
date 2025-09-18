#!/usr/bin/env python3
"""
Generate training data only for the missing 8 branches
Much faster than regenerating everything
"""

import boto3
import json
import random
from datetime import datetime, timedelta
from decimal import Decimal
import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from usage_patterns import UsagePatterns

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

def load_machines_for_missing_branches():
    """Load machine configuration for missing branches only"""
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

    print(f"Found {len(missing_machines)} machines across {len(MISSING_BRANCHES)} missing branches")

    # Group by branch for verification
    by_branch = {}
    for machine in missing_machines:
        branch = machine['gymId']
        if branch not in by_branch:
            by_branch[branch] = []
        by_branch[branch].append(machine)

    for branch in MISSING_BRANCHES:
        count = len(by_branch.get(branch, []))
        print(f"  {branch}: {count} machines")

    return missing_machines

def generate_training_data_for_missing():
    """Generate training data only for missing branches"""
    print("🔄 Generating training data for missing branches...")

    # Load configuration
    missing_machines = load_machines_for_missing_branches()
    usage_patterns = UsagePatterns('config/realistic_247_stores.json')

    # DynamoDB setup
    dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
    current_state_table = dynamodb.Table('gym-pulse-current-state')
    events_table = dynamodb.Table('gym-pulse-events')

    print(f"Starting training data generation for {len(missing_machines)} machines...")

    # Generate data for last 30 days (shorter period for speed)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    total_events = 0
    total_machines = len(missing_machines)

    for machine_idx, machine in enumerate(missing_machines):
        machine_id = machine['machineId']
        gym_id = machine['gymId']
        category = machine['category']

        print(f"Processing {machine_idx + 1}/{total_machines}: {machine_id} ({gym_id})")

        # Generate events for this machine
        current_date = start_date
        current_status = 'free'
        machine_events = 0

        while current_date < end_date:
            # Get occupancy rate for this time
            occupancy_rate = usage_patterns.get_current_occupancy_rate(
                current_date, gym_id, category
            )

            # Determine if status should change
            if random.random() < 0.1:  # 10% chance of status change each hour
                current_status = 'occupied' if current_status == 'free' else 'free'

                # Create event
                event_item = {
                    'machineId': machine_id,
                    'timestamp': int(current_date.timestamp()),
                    'status': current_status,
                    'gymId': gym_id,
                    'category': category,
                    'ttl': int((current_date + timedelta(days=30)).timestamp())
                }

                try:
                    events_table.put_item(Item=event_item)
                    machine_events += 1
                    total_events += 1
                except Exception as e:
                    print(f"    ❌ Error creating event: {e}")

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
            print(f"    ❌ Error creating current state: {e}")

        print(f"    Generated {machine_events} events")

        # Progress update every 50 machines
        if (machine_idx + 1) % 50 == 0:
            print(f"    Progress: {machine_idx + 1}/{total_machines} machines completed")

    print(f"\n✅ Training data generation completed!")
    print(f"    Generated {total_events} total events")
    print(f"    Created current state for {total_machines} machines")

def verify_missing_branches_added():
    """Verify that missing branches are now in the database"""
    print("\n🔍 Verifying missing branches were added...")

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

        print(f"Current branches in database:")
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

        print(f"\nRegional Summary:")
        print(f"  HK (Hong Kong Island): {hk_count} items")
        print(f"  KL (Kowloon):          {kl_count} items")
        print(f"  NT (New Territories):  {nt_count} items")
        print(f"  Total:                 {hk_count + kl_count + nt_count} items")

        # Check if we have all expected branches
        found_missing = [branch for branch in MISSING_BRANCHES if branch in gym_id_counts]
        still_missing = [branch for branch in MISSING_BRANCHES if branch not in gym_id_counts]

        if found_missing:
            print(f"\n✅ Successfully added {len(found_missing)} branches: {found_missing}")

        if still_missing:
            print(f"\n❌ Still missing {len(still_missing)} branches: {still_missing}")
        else:
            print(f"\n✅ All missing branches have been added!")

    except Exception as e:
        print(f"❌ Error verifying: {e}")

if __name__ == "__main__":
    generate_training_data_for_missing()
    verify_missing_branches_added()