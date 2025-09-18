#!/usr/bin/env python3
"""
Generate realistic 247 Fitness machine configuration
Converts the realistic store data into the format expected by the simulator
"""
import json
import random
from typing import Dict, List, Any

def generate_machine_id(machine_type: str, store_id: str, index: int) -> str:
    """Generate unique machine ID"""
    # Remove hk- prefix and use short codes
    store_code = store_id.replace('hk-', '').replace('-', '')[:8]
    return f"{machine_type}-{store_code}-{index:02d}"

def distribute_machines_by_type(category: str, count: int, machine_types: List[Dict], store_id: str) -> List[Dict]:
    """Distribute machines within a category based on weights"""
    machines = []

    # Calculate weighted distribution
    total_weight = sum(mt['weight'] for mt in machine_types)

    # Generate machines based on weights
    type_counts = {}
    remaining = count

    for i, machine_type in enumerate(machine_types):
        if i == len(machine_types) - 1:  # Last type gets remaining
            type_count = remaining
        else:
            proportion = machine_type['weight'] / total_weight
            type_count = max(1, round(count * proportion))
            remaining -= type_count

        type_counts[machine_type['type']] = type_count

    # Create machine objects
    machine_index = 1
    for machine_type in machine_types:
        type_count = type_counts[machine_type['type']]
        for i in range(type_count):
            machine_id = generate_machine_id(machine_type['type'], store_id, machine_index)

            machines.append({
                "machineId": machine_id,
                "name": f"{machine_type['type'].replace('-', ' ').title()} {machine_index}",
                "category": category,
                "type": machine_type['type'],
                "demand_multiplier": machine_type['demand_multiplier']
            })
            machine_index += 1

    return machines

def generate_realistic_machines_config():
    """Generate realistic machines configuration from 247 Fitness data"""

    # Load realistic store configuration
    with open('config/realistic_247_stores.json', 'r') as f:
        realistic_config = json.load(f)

    # Generate machines for each branch
    branches = []

    for branch_data in realistic_config['branches']:
        print(f"Generating machines for {branch_data['name']} ({branch_data['total_machines']} machines)")

        branch_machines = []
        machine_distribution = branch_data['machine_distribution']
        machine_types = realistic_config['machine_types']

        # Generate machines for each category
        for category, count in machine_distribution.items():
            if count > 0 and category in machine_types:
                category_machines = distribute_machines_by_type(
                    category, count, machine_types[category], branch_data['id']
                )
                branch_machines.extend(category_machines)

        # Create branch object
        branch = {
            "id": branch_data['id'],
            "name": branch_data['name'],
            "district": branch_data['district'],
            "type": branch_data['type'],
            "size": branch_data['size'],
            "coordinates": branch_data['coordinates'],
            "peak_patterns": branch_data['peak_patterns'],
            "machines": branch_machines
        }

        branches.append(branch)
        print(f"  Generated {len(branch_machines)} machines")

    # Create usage patterns from realistic config
    usage_patterns = {
        "peak_hours": realistic_config['global_usage_patterns']['peak_hours'],
        "equipment_preferences": {},
        "branch_differences": {},
        "location_patterns": realistic_config['location_behavioral_patterns'],
        "timing": {
            "occupied_duration": {
                "min": 480,
                "max": 900,
                "description": "Strength machines: 8-15 minutes per session"
            },
            "cardio_duration": {
                "min": 900,
                "max": 2400,
                "description": "Cardio machines: 15-40 minutes per session"
            },
            "rest_duration": {
                "min": 60,
                "max": 600,
                "description": "Rest between sets: 1-10 minutes"
            },
            "session_length": {
                "min": 900,
                "max": 2700,
                "description": "Total session length: 15-45 minutes"
            },
            "transition_time": {
                "min": 120,
                "max": 1800,
                "description": "Machine changeover: 2-30 minutes"
            }
        },
        "noise": {
            "false_positive_rate": 0.02,
            "missed_detection_rate": 0.01,
            "network_delay_max": 30,
            "offline_frequency": 0.005
        }
    }

    # Generate equipment preferences from machine types
    for category, machine_types_list in realistic_config['machine_types'].items():
        usage_patterns["equipment_preferences"][category] = {}
        for machine_type in machine_types_list:
            usage_patterns["equipment_preferences"][category][machine_type['type']] = {
                "peak_multiplier": machine_type['demand_multiplier'],
                "base_demand": min(0.9, machine_type['demand_multiplier'] * 0.6),
                "description": f"Demand multiplier: {machine_type['demand_multiplier']}"
            }

    # Generate branch differences
    for branch in branches:
        patterns = branch['peak_patterns']
        usage_patterns["branch_differences"][branch['id']] = {
            "type": branch['type'],
            "lunch_boost": patterns.get('lunch_boost', 1.0),
            "morning_peak": patterns.get('morning_peak', 1.0),
            "evening_peak_start": patterns.get('evening_peak_start', 18),
            "evening_peak_end": patterns.get('evening_peak_end', 22),
            "weekend_factor": patterns.get('weekend_factor', 1.0),
            "description": f"{branch['type']} location patterns"
        }

    # Create final configuration
    final_config = {
        "branches": branches,
        "usage_patterns": usage_patterns
    }

    return final_config

def main():
    """Generate and save realistic machine configuration"""
    print("🏋️ Generating realistic 247 Fitness machine configuration...")

    config = generate_realistic_machines_config()

    # Save to machines.json
    with open('config/machines.json', 'w') as f:
        json.dump(config, f, indent=2)

    # Print summary
    total_machines = sum(len(branch['machines']) for branch in config['branches'])
    total_branches = len(config['branches'])

    print(f"\n✅ Generated configuration:")
    print(f"   📍 {total_branches} stores across Hong Kong")
    print(f"   🏋️ {total_machines} total machines")
    print(f"   📊 Realistic usage patterns by location type")
    print(f"   💾 Saved to config/machines.json")

    # Print breakdown by store type
    type_summary = {}
    for branch in config['branches']:
        branch_type = branch['type']
        if branch_type not in type_summary:
            type_summary[branch_type] = {'count': 0, 'machines': 0}
        type_summary[branch_type]['count'] += 1
        type_summary[branch_type]['machines'] += len(branch['machines'])

    print(f"\n📋 Store breakdown:")
    for store_type, data in type_summary.items():
        avg_machines = data['machines'] / data['count']
        print(f"   {store_type}: {data['count']} stores, avg {avg_machines:.0f} machines each")

if __name__ == "__main__":
    main()