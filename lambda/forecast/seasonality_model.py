"""
Weekly Seasonality Model for Machine Availability Forecasting

Calculates baseline weekly patterns and probability predictions.
"""
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .data_processor import HistoricalDataProcessor


class SeasonalityModel:
    def __init__(self):
        self.data_processor = HistoricalDataProcessor()
        self.min_sample_size = 5  # Minimum samples needed for reliable prediction
        self.confidence_threshold = 0.6  # Minimum confidence for showing prediction
    
    def calculate_free_probability(self, patterns: Dict, current_time: datetime, 
                                 forecast_minutes: int = 30) -> Dict:
        """
        Calculate probability machine will be free in specified minutes
        
        Args:
            patterns: Historical patterns from data_processor
            current_time: Current timestamp
            forecast_minutes: Minutes ahead to forecast (default 30)
            
        Returns:
            Dict with probability, confidence, and metadata
        """
        if 'patterns' not in patterns:
            return self._default_prediction('no_patterns')
        
        target_time = current_time + timedelta(minutes=forecast_minutes)
        weekday = target_time.weekday()
        hour = target_time.hour
        minute_slot = (target_time.minute // 15) * 15
        
        time_key = f"{weekday}_{hour:02d}_{minute_slot:02d}"
        
        pattern_data = patterns['patterns']
        
        if time_key in pattern_data:
            pattern = pattern_data[time_key]
            sample_size = pattern['sample_size']
            avg_occupancy = pattern['avg_occupancy']
            std_dev = pattern.get('std_dev', 0)
            
            # Calculate free probability (inverse of occupancy)
            free_probability = max(0.0, min(1.0, 1.0 - (avg_occupancy / 100.0)))
            
            # Calculate confidence based on sample size and consistency
            confidence = self._calculate_confidence(sample_size, std_dev)
            confidence_level = self._get_confidence_level(confidence)
            
            return {
                'probability': free_probability,
                'confidence': confidence,
                'confidence_level': confidence_level,
                'sample_size': sample_size,
                'avg_occupancy': avg_occupancy,
                'std_dev': std_dev,
                'time_slot': time_key,
                'forecast_time': target_time.isoformat(),
                'reliable': sample_size >= self.min_sample_size and confidence >= self.confidence_threshold
            }
        
        # Try to find nearby time slots if exact match not found
        nearby_prediction = self._find_nearby_slot_prediction(
            pattern_data, weekday, hour, minute_slot
        )
        
        if nearby_prediction:
            nearby_prediction['time_slot'] = f"nearby_{time_key}"
            nearby_prediction['forecast_time'] = target_time.isoformat()
            return nearby_prediction
        
        return self._default_prediction('insufficient_data', target_time)
    
    def generate_baseline_weekly_pattern(self, machine_id: str, days_back: int = 21) -> Dict:
        """
        Generate baseline weekly pattern for a machine
        
        Args:
            machine_id: Machine to analyze
            days_back: Days of historical data (default 21 for 3 weeks)
            
        Returns:
            Dict with weekly pattern and statistics
        """
        patterns = self.data_processor.analyze_occupancy_patterns(machine_id, days_back)
        
        if 'error' in patterns:
            return patterns
        
        # Organize patterns by day of week and time
        weekly_pattern = {}
        for day in range(7):  # Monday = 0, Sunday = 6
            weekly_pattern[day] = {}
            for hour in range(24):
                weekly_pattern[day][hour] = {}
                for minute_slot in [0, 15, 30, 45]:
                    time_key = f"{day}_{hour:02d}_{minute_slot:02d}"
                    if time_key in patterns.get('patterns', {}):
                        pattern = patterns['patterns'][time_key]
                        weekly_pattern[day][hour][minute_slot] = {
                            'free_probability': max(0.0, 1.0 - (pattern['avg_occupancy'] / 100.0)),
                            'avg_occupancy': pattern['avg_occupancy'],
                            'confidence': self._calculate_confidence(
                                pattern['sample_size'], 
                                pattern.get('std_dev', 0)
                            ),
                            'sample_size': pattern['sample_size']
                        }
                    else:
                        weekly_pattern[day][hour][minute_slot] = {
                            'free_probability': 0.5,  # Default uncertainty
                            'avg_occupancy': 50.0,
                            'confidence': 0.0,
                            'sample_size': 0
                        }
        
        # Calculate overall statistics
        all_probabilities = []
        reliable_predictions = 0
        total_slots = 0
        
        for day_data in weekly_pattern.values():
            for hour_data in day_data.values():
                for slot_data in hour_data.values():
                    total_slots += 1
                    if slot_data['sample_size'] >= self.min_sample_size:
                        all_probabilities.append(slot_data['free_probability'])
                        reliable_predictions += 1
        
        return {
            'machineId': machine_id,
            'weekly_pattern': weekly_pattern,
            'statistics': {
                'total_time_slots': total_slots,
                'reliable_predictions': reliable_predictions,
                'reliability_percentage': (reliable_predictions / total_slots) * 100 if total_slots > 0 else 0,
                'avg_free_probability': sum(all_probabilities) / len(all_probabilities) if all_probabilities else 0.5,
                'data_quality': self.data_processor.assess_data_quality(patterns)
            },
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def get_category_forecast(self, gym_id: str, category: str, 
                            current_time: datetime, forecast_minutes: int = 30) -> Dict:
        """
        Get forecast for entire category at a gym
        
        Args:
            gym_id: Gym branch ID
            category: Equipment category
            current_time: Current timestamp
            forecast_minutes: Minutes ahead to forecast
            
        Returns:
            Dict with category-level forecast
        """
        patterns = self.data_processor.analyze_category_patterns(gym_id, category)
        
        if 'error' in patterns:
            return {
                'gymId': gym_id,
                'category': category,
                'forecast': self._default_prediction('analysis_error'),
                'error': patterns['error']
            }
        
        forecast = self.calculate_free_probability(patterns, current_time, forecast_minutes)
        
        return {
            'gymId': gym_id,
            'category': category,
            'forecast': forecast,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _calculate_confidence(self, sample_size: int, std_dev: float) -> float:
        """
        Calculate confidence score based on sample size and variability
        
        Args:
            sample_size: Number of historical samples
            std_dev: Standard deviation of occupancy values
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence from sample size
        size_confidence = min(1.0, sample_size / 20.0)  # Max confidence at 20+ samples
        
        # Consistency confidence (lower std_dev = higher confidence)
        # Normalize std_dev to 0-1 scale (assume max reasonable std_dev is 30)
        consistency_confidence = max(0.0, 1.0 - (std_dev / 30.0))
        
        # Weighted combination
        return (size_confidence * 0.7) + (consistency_confidence * 0.3)
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Convert numeric confidence to descriptive level"""
        if confidence >= 0.8:
            return 'high'
        elif confidence >= 0.6:
            return 'medium'
        elif confidence >= 0.4:
            return 'low'
        else:
            return 'very_low'
    
    def _find_nearby_slot_prediction(self, pattern_data: Dict, weekday: int, 
                                   hour: int, minute_slot: int) -> Optional[Dict]:
        """
        Find prediction for nearby time slots if exact match not found
        
        Args:
            pattern_data: Historical patterns data
            weekday: Day of week (0-6)
            hour: Hour (0-23)
            minute_slot: Minute slot (0, 15, 30, 45)
            
        Returns:
            Prediction dict or None if no suitable nearby slot found
        """
        # Try adjacent time slots (±15, ±30 minutes)
        nearby_offsets = [-30, -15, 15, 30]  # minutes
        
        for offset in nearby_offsets:
            test_time = datetime.combine(
                datetime.today().replace(weekday=weekday),
                datetime.min.time().replace(hour=hour, minute=minute_slot)
            ) + timedelta(minutes=offset)
            
            test_weekday = test_time.weekday()
            test_hour = test_time.hour
            test_minute_slot = (test_time.minute // 15) * 15
            
            test_key = f"{test_weekday}_{test_hour:02d}_{test_minute_slot:02d}"
            
            if test_key in pattern_data:
                pattern = pattern_data[test_key]
                if pattern['sample_size'] >= self.min_sample_size:
                    # Return prediction with reduced confidence due to time offset
                    confidence = self._calculate_confidence(
                        pattern['sample_size'], 
                        pattern.get('std_dev', 0)
                    ) * 0.8  # Reduce confidence for nearby slot
                    
                    return {
                        'probability': max(0.0, 1.0 - (pattern['avg_occupancy'] / 100.0)),
                        'confidence': confidence,
                        'confidence_level': self._get_confidence_level(confidence),
                        'sample_size': pattern['sample_size'],
                        'avg_occupancy': pattern['avg_occupancy'],
                        'std_dev': pattern.get('std_dev', 0),
                        'reliable': confidence >= self.confidence_threshold,
                        'note': f'nearby_slot_offset_{offset}min'
                    }
        
        return None
    
    def _default_prediction(self, reason: str, target_time: Optional[datetime] = None) -> Dict:
        """
        Return default prediction when insufficient data
        
        Args:
            reason: Reason for default prediction
            target_time: Target forecast time
            
        Returns:
            Default prediction dict
        """
        return {
            'probability': 0.5,  # Neutral probability
            'confidence': 0.0,
            'confidence_level': 'none',
            'sample_size': 0,
            'avg_occupancy': 50.0,
            'std_dev': 0.0,
            'reliable': False,
            'reason': reason,
            'forecast_time': target_time.isoformat() if target_time else None
        }