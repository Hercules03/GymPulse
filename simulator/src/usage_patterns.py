"""
Usage Pattern Engine
Peak hour calculations and realistic session durations for gym machine simulation
"""
import random
import json
from datetime import datetime, time
from typing import Dict, Tuple, Any


class UsagePatterns:
    def __init__(self, config_path: str = "config/machines.json"):
        """Initialize usage patterns from configuration"""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.patterns = config['usage_patterns']
        self.peak_hours = self.patterns['peak_hours']
        self.timing = self.patterns['timing']
        self.noise = self.patterns['noise']
    
    def get_current_occupancy_rate(self, current_hour: int) -> float:
        """Get occupancy rate based on current hour"""
        # Morning peak: 6-9 AM
        if self.peak_hours['morning']['start'] <= current_hour < self.peak_hours['morning']['end']:
            return self.peak_hours['morning']['occupancy_rate']
        
        # Lunch peak: 12-1 PM
        elif self.peak_hours['lunch']['start'] <= current_hour < self.peak_hours['lunch']['end']:
            return self.peak_hours['lunch']['occupancy_rate']
        
        # Evening peak: 6-9 PM
        elif self.peak_hours['evening']['start'] <= current_hour < self.peak_hours['evening']['end']:
            return self.peak_hours['evening']['occupancy_rate']
        
        # Night hours: 10 PM - 6 AM
        elif current_hour >= 22 or current_hour < 6:
            return self.peak_hours['night']['occupancy_rate']
        
        # Off-peak hours
        else:
            return self.peak_hours['off_peak']['occupancy_rate']
    
    def should_machine_be_occupied(self, current_hour: int) -> bool:
        """Determine if machine should be occupied based on current time"""
        base_rate = self.get_current_occupancy_rate(current_hour)
        
        # Add some randomization (±20%)
        variation = random.uniform(-0.2, 0.2)
        actual_rate = max(0, min(1, base_rate + variation))
        
        return random.random() < actual_rate
    
    def get_occupied_duration(self) -> int:
        """Get realistic occupied duration in seconds (exercise sets)"""
        return random.randint(
            self.timing['occupied_duration']['min'],
            self.timing['occupied_duration']['max']
        )
    
    def get_rest_duration(self) -> int:
        """Get rest duration between sets in seconds"""
        return random.randint(
            self.timing['rest_duration']['min'],
            self.timing['rest_duration']['max']
        )
    
    def get_session_length(self) -> int:
        """Get total session length in seconds (15-45 minutes)"""
        return random.randint(
            self.timing['session_length']['min'],
            self.timing['session_length']['max']
        )
    
    def get_transition_time(self) -> int:
        """Get machine changeover time in seconds"""
        return random.randint(
            self.timing['transition_time']['min'],
            self.timing['transition_time']['max']
        )
    
    def should_inject_noise(self) -> Tuple[bool, str]:
        """Determine if noise should be injected and what type"""
        rand = random.random()
        
        if rand < self.noise['false_positive_rate']:
            return True, 'false_positive'
        elif rand < (self.noise['false_positive_rate'] + self.noise['missed_detection_rate']):
            return True, 'missed_detection'
        else:
            return False, 'none'
    
    def should_go_offline(self) -> bool:
        """Determine if device should simulate offline state"""
        return random.random() < self.noise['offline_frequency']
    
    def get_network_delay(self) -> int:
        """Get simulated network delay in seconds"""
        if random.random() < 0.1:  # 10% chance of delay
            return random.randint(5, self.noise['network_delay_max'])
        return 0
    
    def get_category_specific_patterns(self, category: str) -> Dict[str, Any]:
        """Get usage patterns specific to equipment category"""
        category_modifiers = {
            'legs': {
                'popularity_multiplier': 1.2,  # More popular
                'session_multiplier': 1.1,     # Slightly longer sessions
                'peak_shift': 0                # No peak time shift
            },
            'chest': {
                'popularity_multiplier': 1.3,  # Most popular
                'session_multiplier': 1.0,     # Standard sessions
                'peak_shift': -1               # Peak 1 hour earlier
            },
            'back': {
                'popularity_multiplier': 0.9,  # Less popular
                'session_multiplier': 0.9,     # Shorter sessions
                'peak_shift': 1                # Peak 1 hour later
            }
        }
        
        return category_modifiers.get(category, {
            'popularity_multiplier': 1.0,
            'session_multiplier': 1.0,
            'peak_shift': 0
        })
    
    def get_realistic_state_transition(self, current_state: str, current_hour: int, 
                                     category: str = 'legs') -> Tuple[str, int]:
        """
        Get next state and duration based on current state and realistic patterns
        Returns: (next_state, duration_seconds)
        """
        category_patterns = self.get_category_specific_patterns(category)
        should_be_occupied = self.should_machine_be_occupied(current_hour)
        
        # Apply category-specific popularity modifier
        should_be_occupied = (random.random() < 
                            (self.get_current_occupancy_rate(current_hour) * 
                             category_patterns['popularity_multiplier']))
        
        if current_state == 'free':
            if should_be_occupied:
                # Transition to occupied
                duration = int(self.get_occupied_duration() * 
                             category_patterns['session_multiplier'])
                return 'occupied', duration
            else:
                # Stay free, check again in 1-5 minutes
                return 'free', random.randint(60, 300)
        
        elif current_state == 'occupied':
            # Decide if user is done or just resting between sets
            if random.random() < 0.3:  # 30% chance user is done
                transition_time = self.get_transition_time()
                return 'free', transition_time
            else:
                # Rest between sets
                rest_time = self.get_rest_duration()
                return 'occupied', rest_time
        
        else:
            # Default: transition to free
            return 'free', random.randint(60, 180)