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
    
    def get_current_occupancy_rate(self, current_hour: int, branch_id: str = None, equipment_type: str = None) -> float:
        """Get occupancy rate based on current hour with Hong Kong 247 Fitness patterns"""
        base_rate = 0.1  # Default night rate
        
        # Morning peak: 6-8 AM - moderate usage, cardio popular
        if self.peak_hours['morning']['start'] <= current_hour < self.peak_hours['morning']['end']:
            base_rate = self.peak_hours['morning']['occupancy_rate']
        
        # Lunch peak: 12-2 PM - business district boost
        elif self.peak_hours['lunch']['start'] <= current_hour < self.peak_hours['lunch']['end']:
            base_rate = self.peak_hours['lunch']['occupancy_rate']
            # Central business district has higher lunch traffic
            if branch_id == 'hk-central' and 'branch_differences' in self.patterns:
                base_rate *= self.patterns['branch_differences']['hk-central'].get('lunch_boost', 1.0)
        
        # Evening peak: 6-10 PM - highest demand, queues for popular equipment
        elif self.peak_hours['evening']['start'] <= current_hour < self.peak_hours['evening']['end']:
            base_rate = self.peak_hours['evening']['occupancy_rate']
        
        # Midday: 10 AM - 4 PM - mostly retirees and shift workers
        elif 'midday' in self.peak_hours and self.peak_hours['midday']['start'] <= current_hour < self.peak_hours['midday']['end']:
            base_rate = self.peak_hours['midday']['occupancy_rate']
        
        # Night hours: 10 PM - 6 AM - sparse usage, ideal for avoiding crowds
        elif current_hour >= 22 or current_hour < 6:
            base_rate = self.peak_hours['night']['occupancy_rate']
        
        # Apply equipment-specific multipliers based on Hong Kong preferences
        if equipment_type and 'equipment_preferences' in self.patterns:
            for category, equipment_map in self.patterns['equipment_preferences'].items():
                if equipment_type in equipment_map:
                    equipment_data = equipment_map[equipment_type]
                    # Apply base demand
                    base_rate *= equipment_data.get('base_demand', 1.0)
                    # Apply peak multiplier during evening hours
                    if self.peak_hours['evening']['start'] <= current_hour < self.peak_hours['evening']['end']:
                        base_rate *= equipment_data.get('peak_multiplier', 1.0)
                    break
        
        return min(0.95, max(0.05, base_rate))  # Cap between 5% and 95%
    
    def should_machine_be_occupied(self, current_hour: int, branch_id: str = None, equipment_type: str = None) -> bool:
        """Determine if machine should be occupied based on current time"""
        base_rate = self.get_current_occupancy_rate(current_hour, branch_id, equipment_type)

        # Add some natural randomization (±10% for realistic variation)
        variation = random.uniform(-0.10, 0.10)
        actual_rate = max(0.05, min(0.95, base_rate + variation))

        return random.random() < actual_rate
    
    def get_occupied_duration(self, equipment_type: str = None) -> int:
        """Get realistic occupied duration in seconds based on equipment type"""
        # Cardio machines have longer sessions (15-40 minutes)
        if equipment_type in ['rowing', 'treadmill', 'bike', 'elliptical']:
            if 'cardio_duration' in self.timing:
                return random.randint(
                    self.timing['cardio_duration']['min'],
                    self.timing['cardio_duration']['max']
                )
        
        # Strength machines have shorter sessions (8-15 minutes)
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
    
    def get_transition_time(self, current_hour: int = None) -> int:
        """Get machine changeover time in seconds based on peak hours"""
        if current_hour is None:
            current_hour = datetime.now().hour
        
        # During peak hours (6-10pm): 1-10 minutes between uses
        if self.peak_hours['evening']['start'] <= current_hour < self.peak_hours['evening']['end']:
            if 'peak_transition_time' in self.timing:
                return random.randint(
                    self.timing['peak_transition_time']['min'],
                    self.timing['peak_transition_time']['max']
                )
        
        # During lunch peak: moderate transition times
        elif self.peak_hours['lunch']['start'] <= current_hour < self.peak_hours['lunch']['end']:
            if 'peak_transition_time' in self.timing:
                return random.randint(
                    self.timing['peak_transition_time']['min'],
                    self.timing['peak_transition_time']['max']
                )
        
        # During off-peak hours: 15-60 minutes between uses
        elif (current_hour >= 22 or current_hour < 6 or 
              (10 <= current_hour < 18 and not (12 <= current_hour < 14))):
            if 'off_peak_transition_time' in self.timing:
                return random.randint(
                    self.timing['off_peak_transition_time']['min'],
                    self.timing['off_peak_transition_time']['max']
                )
        
        # Default to standard transition time
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
            max_delay = self.noise.get('network_delay_max', 30)
            if max_delay > 5:  # Only add delay if max is greater than minimum
                return random.randint(5, max_delay)
            else:
                return 0  # Skip delay if max is too small
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
                                     category: str = 'legs', branch_id: str = None, 
                                     equipment_type: str = None) -> Tuple[str, int]:
        """
        Get next state and duration based on current state and realistic Hong Kong patterns
        Returns: (next_state, duration_seconds)
        """
        category_patterns = self.get_category_specific_patterns(category)
        should_be_occupied = self.should_machine_be_occupied(current_hour, branch_id, equipment_type)
        
        if current_state == 'free':
            if should_be_occupied:
                # Transition to occupied - Hong Kong gym sessions are typically focused and efficient
                base_duration = self.get_occupied_duration(equipment_type)
                duration = int(base_duration * category_patterns['session_multiplier'])
                return 'occupied', duration
            else:
                # Stay free, check again using transition_time based on current hour
                transition_time = self.get_transition_time(current_hour)
                return 'free', transition_time
        
        elif current_state == 'occupied':
            # Hong Kong gym users tend to be efficient - shorter rest periods during peak hours
            peak_multiplier = 0.7 if self.peak_hours['evening']['start'] <= current_hour < self.peak_hours['evening']['end'] else 1.0
            
            # Decide if user is done or just resting between sets
            if random.random() < 0.35:  # 35% chance user is done (slightly higher turnover)
                transition_time = int(self.get_transition_time(current_hour) * peak_multiplier)
                return 'free', transition_time
            else:
                # Rest between sets - shorter during peak hours due to social pressure
                rest_time = int(self.get_rest_duration() * peak_multiplier)
                return 'occupied', rest_time
        
        else:
            # Default: transition to free
            return 'free', random.randint(60, 180)