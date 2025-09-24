#!/usr/bin/env python3
"""
GymPulse Test Data Populator

Directly populate DynamoDB tables with realistic test data for demo purposes.
This bypasses IoT Core and certificates for quick database testing.
"""

import boto3
import json
import time
import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')

# Table references
current_state_table = dynamodb.Table('gym-pulse-current-state')
events_table = dynamodb.Table('gym-pulse-events')
aggregates_table = dynamodb.Table('gym-pulse-aggregates')
alerts_table = dynamodb.Table('gym-pulse-alerts')

# Machine configuration
MACHINES = [
    # Central Branch
    {'id': 'leg-press-01', 'gym': 'hk-central', 'category': 'legs', 'name': 'Leg Press 1'},
    {'id': 'leg-press-02', 'gym': 'hk-central', 'category': 'legs', 'name': 'Leg Press 2'},
    {'id': 'squat-rack-01', 'gym': 'hk-central', 'category': 'legs', 'name': 'Squat Rack 1'},
    {'id': 'calf-raise-01', 'gym': 'hk-central', 'category': 'legs', 'name': 'Calf Raise'},
    {'id': 'bench-press-01', 'gym': 'hk-central', 'category': 'chest', 'name': 'Bench Press 1'},
    {'id': 'bench-press-02', 'gym': 'hk-central', 'category': 'chest', 'name': 'Bench Press 2'},
    {'id': 'chest-fly-01', 'gym': 'hk-central', 'category': 'chest', 'name': 'Chest Fly'},
    {'id': 'lat-pulldown-01', 'gym': 'hk-central', 'category': 'back', 'name': 'Lat Pulldown 1'},
    {'id': 'rowing-01', 'gym': 'hk-central', 'category': 'back', 'name': 'Rowing 1'},
    {'id': 'pull-up-01', 'gym': 'hk-central', 'category': 'back', 'name': 'Pull Up Station'},
    
    # Causeway Bay Branch  
    {'id': 'leg-press-03', 'gym': 'hk-causeway', 'category': 'legs', 'name': 'Leg Press 3'},
    {'id': 'squat-rack-02', 'gym': 'hk-causeway', 'category': 'legs', 'name': 'Squat Rack 2'},
    {'id': 'leg-curl-01', 'gym': 'hk-causeway', 'category': 'legs', 'name': 'Leg Curl'},
    {'id': 'bench-press-03', 'gym': 'hk-causeway', 'category': 'chest', 'name': 'Bench Press 3'},
    {'id': 'incline-press-01', 'gym': 'hk-causeway', 'category': 'chest', 'name': 'Incline Press'},
    {'id': 'dips-01', 'gym': 'hk-causeway', 'category': 'chest', 'name': 'Dips Station'},
    {'id': 'lat-pulldown-02', 'gym': 'hk-causeway', 'category': 'back', 'name': 'Lat Pulldown 2'},
    {'id': 'rowing-02', 'gym': 'hk-causeway', 'category': 'back', 'name': 'Rowing 2'},
    {'id': 't-bar-row-01', 'gym': 'hk-causeway', 'category': 'back', 'name': 'T-Bar Row'}
]

# Branch coordinates
BRANCH_COORDS = {
    'hk-central': {'lat': 22.2819, 'lon': 114.1577},
    'hk-causeway': {'lat': 22.2783, 'lon': 114.1747}
}

def populate_current_state():
    """Populate current machine states"""
    print("🔄 Populating current machine states...")
    
    current_time = int(time.time())
    items = []
    
    for machine in MACHINES:
        # Random current status (70% free, 30% occupied for demo)
        status = 'free' if random.random() > 0.3 else 'occupied'
        last_change = current_time - random.randint(60, 1800)  # Changed 1-30 min ago
        
        coords = BRANCH_COORDS[machine['gym']]
        
        item = {
            'machineId': machine['id'],
            'status': status,
            'lastUpdate': current_time,
            'lastChange': last_change,
            'gymId': machine['gym'],
            'category': machine['category'],
            'name': machine['name'],
            'coordinates': {
                'lat': Decimal(str(coords['lat'])),
                'lon': Decimal(str(coords['lon']))
            }
        }
        items.append(item)
    
    # Batch write
    with current_state_table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)
    
    print(f"✅ Added {len(items)} machine states")

def populate_events():
    """Populate recent machine events"""
    print("🔄 Populating machine events...")
    
    current_time = int(time.time())
    events = []
    
    # Generate events for last 24 hours
    for machine in MACHINES:
        # Generate 5-15 state changes per machine over 24 hours
        num_events = random.randint(5, 15)
        
        for i in range(num_events):
            # Events spread over last 24 hours
            event_time = current_time - random.randint(0, 86400)  # 24 hours
            status = 'occupied' if i % 2 == 0 else 'free'
            transition = 'occupied' if status == 'occupied' else 'freed'
            
            # Add TTL (30 days from now)
            ttl = current_time + (30 * 24 * 3600)
            
            event = {
                'machineId': machine['id'],
                'timestamp': event_time,
                'status': status,
                'transition': transition,
                'gymId': machine['gym'],
                'category': machine['category'],
                'ttl': ttl
            }
            events.append(event)
    
    # Sort by timestamp
    events.sort(key=lambda x: x['timestamp'])
    
    # Batch write
    with events_table.batch_writer() as batch:
        for event in events:
            batch.put_item(Item=event)
    
    print(f"✅ Added {len(events)} historical events")

def populate_aggregates():
    """Populate aggregation data for heatmaps"""
    print("🔄 Populating aggregation data...")
    
    current_time = int(time.time())
    aggregates = []
    
    # Generate aggregates for last 7 days, every 15 minutes
    for gym_id in ['hk-central', 'hk-causeway']:
        for category in ['legs', 'chest', 'back']:
            
            # Count machines in this gym+category
            total_machines = len([m for m in MACHINES if m['gym'] == gym_id and m['category'] == category])
            
            # Generate 15-minute bins for last 7 days
            for day in range(7):
                for hour in range(24):
                    for minute in [0, 15, 30, 45]:
                        
                        # Calculate timestamp for this bin
                        bin_time = current_time - (day * 86400) - (hour * 3600) - (minute * 60)
                        bin_time = bin_time - (bin_time % 900)  # Round to 15-minute boundary
                        
                        # Realistic occupancy patterns
                        # Peak hours: 7-9 AM (70%), 12-1 PM (60%), 6-9 PM (80%)
                        if 7 <= hour <= 9:
                            base_occupancy = 0.7
                        elif 12 <= hour <= 13:
                            base_occupancy = 0.6
                        elif 18 <= hour <= 21:
                            base_occupancy = 0.8
                        elif 22 <= hour or hour <= 6:
                            base_occupancy = 0.1  # Night
                        else:
                            base_occupancy = 0.3  # Off-peak
                        
                        # Add some randomness
                        occupancy_ratio = max(0, min(100, base_occupancy * 100 + random.uniform(-15, 15)))
                        free_count = int(total_machines * (1 - occupancy_ratio / 100))
                        
                        # Add TTL (90 days from now)
                        ttl = current_time + (90 * 24 * 3600)
                        
                        aggregate = {
                            'gymId_category': f"{gym_id}_{category}",
                            'timestamp15min': bin_time,
                            'occupancyRatio': Decimal(str(round(occupancy_ratio, 1))),
                            'freeCount': free_count,
                            'totalCount': total_machines,
                            'gymId': gym_id,
                            'category': category,
                            'ttl': ttl
                        }
                        aggregates.append(aggregate)
    
    # Batch write
    with aggregates_table.batch_writer() as batch:
        for aggregate in aggregates:
            batch.put_item(Item=aggregate)
    
    print(f"✅ Added {len(aggregates)} aggregation records")

def populate_sample_alerts():
    """Create a few sample alerts"""
    print("🔄 Creating sample alerts...")
    
    current_time = int(time.time())
    alerts = []
    
    # Create 3-5 sample alerts
    sample_machines = random.sample(MACHINES, 4)
    
    for i, machine in enumerate(sample_machines):
        alert = {
            'userId': f'demo-user-{i+1}',
            'machineId': machine['id'],
            'active': True,
            'createdAt': current_time - random.randint(3600, 86400),  # 1-24 hours ago
            'quietHours': {
                'start': 22,
                'end': 7
            },
            'gymId': machine['gym'],
            'category': machine['category']
        }
        alerts.append(alert)
    
    # Batch write
    with alerts_table.batch_writer() as batch:
        for alert in alerts:
            batch.put_item(Item=alert)
    
    print(f"✅ Added {len(alerts)} sample alerts")

def main():
    """Populate all tables with test data"""
    print("🏋️ GymPulse Test Data Populator")
    print("=" * 50)
    print(f"Populating DynamoDB tables in region: ap-east-1")
    print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    try:
        # Clear existing data first
        print("🗑️  Clearing existing data...")
        
        # Clear current state
        scan = current_state_table.scan()
        with current_state_table.batch_writer() as batch:
            for item in scan['Items']:
                batch.delete_item(Key={'machineId': item['machineId']})
        
        # Clear events (scan and delete in batches)
        scan = events_table.scan()
        with events_table.batch_writer() as batch:
            for item in scan['Items']:
                batch.delete_item(Key={'machineId': item['machineId'], 'timestamp': item['timestamp']})
        
        # Clear aggregates
        scan = aggregates_table.scan()
        with aggregates_table.batch_writer() as batch:
            for item in scan['Items']:
                batch.delete_item(Key={'gymId_category': item['gymId_category'], 'timestamp15min': item['timestamp15min']})
        
        # Clear alerts
        scan = alerts_table.scan()
        with alerts_table.batch_writer() as batch:
            for item in scan['Items']:
                batch.delete_item(Key={'userId': item['userId'], 'machineId': item['machineId']})
        
        print("✅ Cleared existing data\n")
        
        # Populate with fresh test data
        populate_current_state()
        populate_events()
        populate_aggregates()
        populate_sample_alerts()
        
        print(f"\n🎉 Test data population complete!")
        print(f"📊 Check data with: python3 scripts/check-database.py")
        print(f"🌐 View in AWS Console: https://ap-east-1.console.aws.amazon.com/dynamodbv2")
        
    except Exception as e:
        print(f"❌ Error populating test data: {e}")
        raise

if __name__ == "__main__":
    main()