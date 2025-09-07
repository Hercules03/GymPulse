"""
Historical Occupancy Data Processor for Forecasting

Processes historical aggregates data to prepare for weekly seasonality analysis.
"""
import boto3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal


class HistoricalDataProcessor:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.aggregates_table = self.dynamodb.Table('gym-pulse-aggregates')
    
    def analyze_occupancy_patterns(self, machine_id: str, days_back: int = 14) -> Dict:
        """
        Analyze historical occupancy patterns for a specific machine
        
        Args:
            machine_id: Machine to analyze
            days_back: Number of days of historical data to analyze
            
        Returns:
            Dict with patterns organized by weekday_hour_minute keys
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        # Convert to 15-minute timestamp bins
        start_timestamp = int(start_time.timestamp() // 900) * 900  # Round to 15min
        end_timestamp = int(end_time.timestamp() // 900) * 900
        
        patterns = {}
        
        try:
            # Query aggregates table for historical data
            response = self.aggregates_table.query(
                KeyConditionExpression='machineId = :machine_id AND #ts BETWEEN :start_ts AND :end_ts',
                ExpressionAttributeNames={'#ts': 'timestamp15min'},
                ExpressionAttributeValues={
                    ':machine_id': machine_id,
                    ':start_ts': start_timestamp,
                    ':end_ts': end_timestamp
                }
            )
            
            # Process each aggregated record
            for record in response.get('Items', []):
                timestamp = int(record['timestamp15min'])
                occupancy_ratio = float(record.get('occupancyRatio', 0))
                
                # Convert timestamp to datetime for pattern analysis
                dt = datetime.fromtimestamp(timestamp)
                weekday = dt.weekday()  # 0=Monday, 6=Sunday
                hour = dt.hour
                minute_slot = (dt.minute // 15) * 15  # 0, 15, 30, 45
                
                # Create pattern key
                time_key = f"{weekday}_{hour:02d}_{minute_slot:02d}"
                
                if time_key not in patterns:
                    patterns[time_key] = []
                
                patterns[time_key].append(occupancy_ratio)
            
            # Calculate statistics for each pattern
            processed_patterns = {}
            for time_key, values in patterns.items():
                if len(values) > 0:
                    processed_patterns[time_key] = {
                        'values': values,
                        'avg_occupancy': sum(values) / len(values),
                        'min_occupancy': min(values),
                        'max_occupancy': max(values),
                        'sample_size': len(values),
                        'std_dev': self._calculate_std_dev(values)
                    }
            
            return {
                'machineId': machine_id,
                'patterns': processed_patterns,
                'analysis_period': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'days': days_back
                },
                'total_data_points': len(response.get('Items', []))
            }
            
        except Exception as e:
            print(f"Error analyzing patterns for {machine_id}: {str(e)}")
            return {
                'machineId': machine_id,
                'patterns': {},
                'error': str(e)
            }
    
    def analyze_category_patterns(self, gym_id: str, category: str, days_back: int = 14) -> Dict:
        """
        Analyze occupancy patterns for all machines in a category at a gym
        
        Args:
            gym_id: Gym branch to analyze
            category: Equipment category (legs, chest, back)
            days_back: Number of days of historical data
            
        Returns:
            Dict with aggregated category patterns
        """
        # For now, create a composite key pattern
        category_key = f"{gym_id}_{category}"
        
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days_back)
            start_timestamp = int(start_time.timestamp() // 900) * 900
            end_timestamp = int(end_time.timestamp() // 900) * 900
            
            response = self.aggregates_table.query(
                KeyConditionExpression='gymId_category = :category_key AND #ts BETWEEN :start_ts AND :end_ts',
                ExpressionAttributeNames={'#ts': 'timestamp15min'},
                ExpressionAttributeValues={
                    ':category_key': category_key,
                    ':start_ts': start_timestamp,
                    ':end_ts': end_timestamp
                }
            )
            
            patterns = {}
            for record in response.get('Items', []):
                timestamp = int(record['timestamp15min'])
                occupancy_ratio = float(record.get('occupancyRatio', 0))
                
                dt = datetime.fromtimestamp(timestamp)
                weekday = dt.weekday()
                hour = dt.hour
                minute_slot = (dt.minute // 15) * 15
                
                time_key = f"{weekday}_{hour:02d}_{minute_slot:02d}"
                
                if time_key not in patterns:
                    patterns[time_key] = []
                patterns[time_key].append(occupancy_ratio)
            
            # Process patterns
            processed_patterns = {}
            for time_key, values in patterns.items():
                if len(values) > 0:
                    processed_patterns[time_key] = {
                        'values': values,
                        'avg_occupancy': sum(values) / len(values),
                        'sample_size': len(values),
                        'std_dev': self._calculate_std_dev(values)
                    }
            
            return {
                'gymId': gym_id,
                'category': category,
                'patterns': processed_patterns,
                'analysis_period': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'days': days_back
                },
                'total_data_points': len(response.get('Items', []))
            }
            
        except Exception as e:
            print(f"Error analyzing category patterns for {gym_id}/{category}: {str(e)}")
            return {
                'gymId': gym_id,
                'category': category,
                'patterns': {},
                'error': str(e)
            }
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation of values"""
        if len(values) <= 1:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def assess_data_quality(self, patterns: Dict) -> Dict:
        """
        Assess the quality of historical data for forecasting
        
        Args:
            patterns: Patterns dict from analyze_occupancy_patterns
            
        Returns:
            Dict with data quality metrics
        """
        if 'patterns' not in patterns:
            return {'quality': 'insufficient', 'reason': 'no_patterns'}
        
        pattern_data = patterns['patterns']
        
        # Calculate coverage metrics
        total_slots_in_week = 7 * 24 * 4  # 7 days * 24 hours * 4 (15-min slots)
        covered_slots = len(pattern_data)
        coverage_percentage = (covered_slots / total_slots_in_week) * 100
        
        # Calculate sample size distribution
        sample_sizes = [p['sample_size'] for p in pattern_data.values()]
        min_sample_size = min(sample_sizes) if sample_sizes else 0
        avg_sample_size = sum(sample_sizes) / len(sample_sizes) if sample_sizes else 0
        
        # Assess quality
        if coverage_percentage < 20:
            quality = 'insufficient'
            reason = 'low_coverage'
        elif min_sample_size < 3:
            quality = 'poor'
            reason = 'small_samples'
        elif avg_sample_size < 5:
            quality = 'fair'
            reason = 'moderate_samples'
        elif coverage_percentage > 60 and avg_sample_size > 7:
            quality = 'good'
            reason = 'sufficient_data'
        else:
            quality = 'fair'
            reason = 'adequate_data'
        
        return {
            'quality': quality,
            'reason': reason,
            'metrics': {
                'coverage_percentage': coverage_percentage,
                'covered_slots': covered_slots,
                'total_possible_slots': total_slots_in_week,
                'min_sample_size': min_sample_size,
                'avg_sample_size': avg_sample_size,
                'max_sample_size': max(sample_sizes) if sample_sizes else 0
            }
        }