#!/usr/bin/env python3
"""
Fast Synthetic Training Data Generator
Generates realistic historical data for ML forecasting training
"""
import json
import time
import random
import boto3
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

from src.usage_patterns import UsagePatterns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TrainingDataGenerator:
    def __init__(self, config_path: str = "config/machines.json"):
        """Initialize training data generator"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.usage_patterns = UsagePatterns(config_path)

        # AWS clients
        self.dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
        self.current_state_table = self.dynamodb.Table('gym-pulse-current-state')
        self.events_table = self.dynamodb.Table('gym-pulse-events')
        self.aggregates_table = self.dynamodb.Table('gym-pulse-aggregates')

        # DynamoDB client for batch operations
        self.dynamodb_client = boto3.client('dynamodb', region_name='ap-east-1')

        # Generate machine list
        self.machines = []
        for branch in self.config['branches']:
            for machine in branch['machines']:
                self.machines.append({
                    'machine_id': machine['machineId'],
                    'gym_id': branch['id'],
                    'category': machine['category'],
                    'type': machine['type'],
                    'name': machine['name']
                })

        logger.info(f"Initialized generator for {len(self.machines)} machines")

    def cleanup_existing_data(self) -> None:
        """Delete all existing data from DynamoDB tables"""
        logger.info("🧹 Starting cleanup of existing bad data...")

        # Cleanup events table
        self.cleanup_table_data('gym-pulse-events', 'machineId', 'timestamp')

        # Cleanup aggregates table
        self.cleanup_table_data('gym-pulse-aggregates', 'gymId_category', 'timestamp15min')

        # Cleanup current state table
        self.cleanup_table_data('gym-pulse-current-state', 'machineId')

        logger.info("✅ Cleanup complete - all bad data removed")

    def cleanup_table_data(self, table_name: str, partition_key: str, sort_key: str = None) -> None:
        """Delete all items from a DynamoDB table"""
        table = self.dynamodb.Table(table_name)

        logger.info(f"Cleaning up table: {table_name}")

        # Scan and delete in batches
        scan_kwargs = {}

        # Handle reserved keywords by using ExpressionAttributeNames
        if sort_key:
            if sort_key == 'timestamp' or partition_key == 'timestamp':
                # Use ExpressionAttributeNames for reserved keywords
                expression_attribute_names = {}
                projection_parts = []

                if partition_key == 'timestamp':
                    expression_attribute_names['#pk'] = partition_key
                    projection_parts.append('#pk')
                else:
                    projection_parts.append(partition_key)

                if sort_key == 'timestamp':
                    expression_attribute_names['#sk'] = sort_key
                    projection_parts.append('#sk')
                else:
                    projection_parts.append(sort_key)

                scan_kwargs['ProjectionExpression'] = ', '.join(projection_parts)
                scan_kwargs['ExpressionAttributeNames'] = expression_attribute_names
            else:
                scan_kwargs['ProjectionExpression'] = f"{partition_key}, {sort_key}"
        else:
            if partition_key == 'timestamp':
                scan_kwargs['ProjectionExpression'] = '#pk'
                scan_kwargs['ExpressionAttributeNames'] = {'#pk': partition_key}
            else:
                scan_kwargs['ProjectionExpression'] = partition_key

        items_deleted = 0

        while True:
            response = table.scan(**scan_kwargs)
            items = response.get('Items', [])

            if not items:
                break

            # Delete items in batches of 25 (DynamoDB limit)
            with table.batch_writer() as batch:
                for item in items:
                    key = {partition_key: item[partition_key]}
                    if sort_key and sort_key in item:
                        key[sort_key] = item[sort_key]

                    batch.delete_item(Key=key)
                    items_deleted += 1

            # Handle pagination
            if 'LastEvaluatedKey' in response:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            else:
                break

            if items_deleted % 100 == 0:
                logger.info(f"  Deleted {items_deleted} items from {table_name}")

        logger.info(f"  ✅ Deleted {items_deleted} total items from {table_name}")

    def generate_machine_variation_factor(self, machine_type: str, machine_id: str) -> float:
        """Generate consistent variation factor per machine to avoid identical patterns"""
        # Use machine_id hash to create consistent but varied factors
        hash_val = hash(machine_id) % 100
        base_variation = (hash_val - 50) / 500  # ±10% variation

        # Add type-specific variations
        type_variations = {
            'squat-rack': 0.15,      # More popular, higher variation
            'bench-press': 0.12,     # Popular equipment
            'leg-press': 0.08,       # Steady demand
            'rowing': 0.05,          # Cardio, less variation
            'calf-raise': -0.05,     # Less popular
            'chest-fly': 0.03,       # Moderate demand
            'lat-pulldown': 0.06,    # Steady back exercise
            'pull-up': 0.10,         # Popular but intimidating
            'leg-curl': 0.04         # Moderate legs exercise
        }

        type_factor = type_variations.get(machine_type, 0.0)
        return base_variation + type_factor

    def get_seasonal_factor(self, target_date: datetime) -> float:
        """Get seasonal variation factor for realistic yearly patterns"""
        month = target_date.month
        day_of_year = target_date.timetuple().tm_yday

        # New Year Resolution effect (Jan-Feb)
        if month <= 2:
            resolution_factor = 0.3 * (3 - month) / 2  # Decreases from Jan to Feb
        else:
            resolution_factor = 0.0

        # Summer body prep (Apr-Jun)
        if 4 <= month <= 6:
            summer_prep = 0.2 * (month - 3) / 3
        else:
            summer_prep = 0.0

        # Holiday season decrease (Dec)
        if month == 12:
            holiday_factor = -0.15 * (day_of_year - 335) / 30  # Decreases toward Christmas
        else:
            holiday_factor = 0.0

        # Weekend vs weekday
        weekend_factor = -0.1 if target_date.weekday() >= 5 else 0.0

        return resolution_factor + summer_prep + holiday_factor + weekend_factor

    def generate_day_data(self, machine: Dict[str, Any], target_date: datetime) -> List[Dict[str, Any]]:
        """Generate realistic data for one machine for one day"""
        events = []
        current_time = target_date.replace(hour=0, minute=0, second=0)
        end_time = current_time + timedelta(days=1)

        # Get machine-specific variation factor and seasonal adjustments
        variation_factor = self.generate_machine_variation_factor(machine['type'], machine['machine_id'])
        seasonal_factor = self.get_seasonal_factor(target_date)

        current_state = 'free'

        # Generate events throughout the day
        while current_time < end_time:
            hour = current_time.hour

            # Get base occupancy rate and apply machine variation + seasonal patterns
            base_rate = self.usage_patterns.get_current_occupancy_rate(
                hour, machine['gym_id'], machine['type']
            )
            adjusted_rate = max(0.05, min(0.95, base_rate + variation_factor + seasonal_factor))

            # Determine if state should change
            should_be_occupied = random.random() < adjusted_rate
            target_state = 'occupied' if should_be_occupied else 'free'

            # Generate state change if needed
            if current_state != target_state:
                event = {
                    'machineId': machine['machine_id'],
                    'timestamp': int(current_time.timestamp()),
                    'status': target_state,
                    'gymId': machine['gym_id'],
                    'category': machine['category'],
                    'transition': f"{current_state}→{target_state}",
                    'ttl': int((current_time + timedelta(days=30)).timestamp())
                }
                events.append(event)
                current_state = target_state

            # Move to next time interval (15 minutes for granularity)
            current_time += timedelta(minutes=random.randint(5, 25))

        return events

    def batch_write_events(self, events: List[Dict[str, Any]]) -> None:
        """Write events to DynamoDB in batches"""
        batch_size = 25  # DynamoDB batch limit

        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]

            with self.events_table.batch_writer() as batch_writer:
                for event in batch:
                    batch_writer.put_item(Item=event)

    def generate_aggregates(self, machine_id: str, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate 15-minute aggregates from events"""
        aggregates = []

        # Group events by 15-minute windows
        time_windows = {}
        for event in events:
            timestamp = event['timestamp']
            # Round to 15-minute window
            window_start = (timestamp // 900) * 900

            if window_start not in time_windows:
                time_windows[window_start] = []
            time_windows[window_start].append(event)

        # Calculate occupancy ratio for each window
        for window_start, window_events in time_windows.items():
            window_end = window_start + 900  # 15 minutes

            # Calculate time spent occupied in this window
            occupied_time = 0
            current_state = 'free'
            last_time = window_start

            for event in sorted(window_events, key=lambda x: x['timestamp']):
                if current_state == 'occupied':
                    occupied_time += event['timestamp'] - last_time
                current_state = event['status']
                last_time = event['timestamp']

            # Handle end of window
            if current_state == 'occupied':
                occupied_time += window_end - last_time

            occupancy_ratio = (occupied_time / 900) * 100  # Percentage

            # Get machine info
            machine = next(m for m in self.machines if m['machine_id'] == machine_id)

            aggregate = {
                'gymId_category': f"{machine['gym_id']}_{machine['category']}",
                'timestamp15min': window_start,
                'machineId': machine_id,
                'occupancyRatio': Decimal(str(round(occupancy_ratio, 1))),
                'freeCount': 1 if occupancy_ratio < 50 else 0,
                'totalCount': 1,
                'ttl': int((datetime.fromtimestamp(window_start) + timedelta(days=90)).timestamp())
            }
            aggregates.append(aggregate)

        return aggregates

    def batch_write_aggregates(self, aggregates: List[Dict[str, Any]]) -> None:
        """Write aggregates to DynamoDB in batches"""
        batch_size = 25

        for i in range(0, len(aggregates), batch_size):
            batch = aggregates[i:i + batch_size]

            with self.aggregates_table.batch_writer() as batch_writer:
                for aggregate in batch:
                    batch_writer.put_item(Item=aggregate)

    def update_current_state(self, machine: Dict[str, Any]) -> None:
        """Update current state table with latest realistic state"""
        current_hour = datetime.now().hour
        variation_factor = self.generate_machine_variation_factor(machine['type'], machine['machine_id'])

        base_rate = self.usage_patterns.get_current_occupancy_rate(
            current_hour, machine['gym_id'], machine['type']
        )
        adjusted_rate = max(0.05, min(0.95, base_rate + variation_factor))

        current_status = 'occupied' if random.random() < adjusted_rate else 'free'

        # Find the branch coordinates from config
        branch_coords = {'lat': Decimal('22.2819'), 'lon': Decimal('114.1577')}  # Default to Central
        for branch in self.config['branches']:
            if branch['id'] == machine['gym_id']:
                branch_coords = {
                    'lat': Decimal(str(branch['coordinates']['lat'])),
                    'lon': Decimal(str(branch['coordinates']['lon']))
                }
                break

        self.current_state_table.put_item(Item={
            'machineId': machine['machine_id'],
            'status': current_status,
            'lastUpdate': int(time.time()),
            'gymId': machine['gym_id'],
            'category': machine['category'],
            'coordinates': branch_coords
        })

    def generate_training_data(self, days: int = 30, max_workers: int = 8) -> None:
        """Generate realistic training data for all machines"""
        logger.info(f"Starting generation of {days} days of training data for {len(self.machines)} machines")

        end_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=days)

        total_tasks = len(self.machines) * days
        completed_tasks = 0

        # Process machines in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            # Submit all tasks
            for machine in self.machines:
                for day_offset in range(days):
                    target_date = start_date + timedelta(days=day_offset)
                    future = executor.submit(self.process_machine_day, machine, target_date)
                    futures.append(future)

            # Process completed tasks
            for future in as_completed(futures):
                try:
                    result = future.result()
                    completed_tasks += 1

                    if completed_tasks % 50 == 0:
                        progress = (completed_tasks / total_tasks) * 100
                        logger.info(f"Progress: {completed_tasks}/{total_tasks} ({progress:.1f}%)")

                except Exception as e:
                    logger.error(f"Task failed: {e}")

        # Update current state for all machines
        logger.info("Updating current state for all machines...")
        for machine in self.machines:
            self.update_current_state(machine)

        logger.info(f"Training data generation complete! Generated {completed_tasks} machine-days of data")

    def process_machine_day(self, machine: Dict[str, Any], target_date: datetime) -> Dict[str, Any]:
        """Process one machine for one day"""
        # Generate events
        events = self.generate_day_data(machine, target_date)

        # Write events to DynamoDB
        if events:
            self.batch_write_events(events)

            # Generate and write aggregates
            aggregates = self.generate_aggregates(machine['machine_id'], events)
            if aggregates:
                self.batch_write_aggregates(aggregates)

        return {
            'machine_id': machine['machine_id'],
            'date': target_date.date(),
            'events_count': len(events)
        }

def main():
    """Main function to generate training data"""
    generator = TrainingDataGenerator()

    print("🚀 GymPulse Training Data Generator")
    print("This will populate DynamoDB with realistic synthetic data for ML forecasting")
    print(f"📊 {len(generator.machines)} machines across {len(generator.config['branches'])} branches")

    # Ask about cleanup
    cleanup = input("\n🧹 Delete existing bad data first? (recommended: y/n): ") or "y"

    days = int(input("How many days of historical data to generate? (default: 365 for 1 year): ") or "365")
    workers = int(input("Number of parallel workers? (default: 16 for faster processing): ") or "16")

    print(f"\n📋 Summary:")
    print(f"   - Cleanup existing data: {'Yes' if cleanup.lower() == 'y' else 'No'}")
    print(f"   - Generate {days} days of data")
    print(f"   - For {len(generator.machines)} machines")
    print(f"   - Total: {days * len(generator.machines)} machine-days")

    confirm = input(f"\n⚠️  Continue with above plan? (y/n): ")
    if confirm.lower() != 'y':
        print("❌ Cancelled")
        return

    start_time = time.time()

    # Cleanup existing data if requested
    if cleanup.lower() == 'y':
        generator.cleanup_existing_data()

    # Generate new realistic data
    generator.generate_training_data(days=days, max_workers=workers)

    duration = time.time() - start_time

    print(f"\n✅ Complete! Generated training data in {duration:.1f} seconds")
    print("🧠 Your ML forecasting should now have realistic data to learn from!")
    print("\n🔄 Next steps:")
    print("   1. Restart your ML forecasting Lambda to pick up new data")
    print("   2. Check machine detail pages - heatmaps should now be different per machine")
    print("   3. Verify peak hours now match realistic patterns (Evening: 18-22, not 1-4 AM)")

if __name__ == "__main__":
    main()