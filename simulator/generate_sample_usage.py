#!/usr/bin/env python3
"""
Generate sample historical usage data for heatmap testing
"""

import json
import math
import random
from datetime import datetime, timedelta

def generate_realistic_usage_pattern():
    """Generate realistic 24-hour usage pattern"""
    usage_data = []
    
    for hour in range(24):
        # Realistic gym usage patterns
        if 5 <= hour <= 9:  # Morning rush
            base_usage = 0.7 + (random.random() * 0.2)  # 70-90%
        elif 11 <= hour <= 14:  # Lunch time  
            base_usage = 0.5 + (random.random() * 0.3)  # 50-80%
        elif 17 <= hour <= 21:  # Evening peak
            base_usage = 0.8 + (random.random() * 0.2)  # 80-100%
        elif 22 <= hour <= 23 or 0 <= hour <= 4:  # Night/early morning
            base_usage = 0.1 + (random.random() * 0.2)  # 10-30%
        else:  # Other times
            base_usage = 0.3 + (random.random() * 0.3)  # 30-60%
        
        # Add some randomness but keep realistic
        usage = min(1.0, max(0.0, base_usage))
        
        usage_data.append({
            "hour": hour,
            "day_of_week": datetime.now().weekday(),
            "average_usage": round(usage, 2),
            "predicted_free_time": f"{60 - int(usage * 60)} min"
        })
    
    return usage_data

def create_machine_usage_sample():
    """Create sample usage data for testing"""
    
    sample_data = {
        "chest-press-01": generate_realistic_usage_pattern(),
        "leg-press-01": generate_realistic_usage_pattern(), 
        "lat-pulldown-01": generate_realistic_usage_pattern()
    }
    
    print("📊 Generated Sample Usage Data:")
    print("================================")
    
    for machine_id, usage in sample_data.items():
        peak_hour = max(usage, key=lambda x: x['average_usage'])
        low_hour = min(usage, key=lambda x: x['average_usage'])
        
        print(f"\n🏋️ {machine_id}:")
        print(f"  Peak: {peak_hour['hour']}:00 ({int(peak_hour['average_usage']*100)}% busy)")
        print(f"  Low:  {low_hour['hour']}:00 ({int(low_hour['average_usage']*100)}% busy)")
    
    # Save to file for frontend testing
    with open('sample_usage_data.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"\n💾 Saved to: sample_usage_data.json")
    print(f"📋 To test: Copy data to frontend MachineDetail component")
    
    return sample_data

if __name__ == "__main__":
    create_machine_usage_sample()