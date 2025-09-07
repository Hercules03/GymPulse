"""
Threshold Tuning for Binary Classification of Machine Availability Forecasts

Optimizes probability thresholds for "likely free" predictions to balance precision and recall.
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from .seasonality_model import SeasonalityModel


class ThresholdTuner:
    def __init__(self):
        self.seasonality_model = SeasonalityModel()
        
        # Default threshold configuration
        self.default_thresholds = {
            'likely_free': 0.7,      # 70% probability threshold for "likely free"
            'possibly_free': 0.5,    # 50% probability threshold for "possibly free" 
            'unlikely_free': 0.3,    # 30% probability threshold for "unlikely free"
            'min_sample_size': 5,    # Minimum historical samples required
            'confidence_threshold': 0.6,  # Minimum confidence for display
            'high_confidence': 0.8,  # High confidence threshold
            'medium_confidence': 0.6  # Medium confidence threshold
        }
    
    def classify_availability_forecast(self, probability: float, confidence: float, 
                                     sample_size: int, 
                                     thresholds: Optional[Dict] = None) -> Dict:
        """
        Convert probability to user-friendly classification
        
        Args:
            probability: Free probability (0-1)
            confidence: Confidence score (0-1)
            sample_size: Number of historical samples
            thresholds: Custom thresholds (optional, uses defaults)
            
        Returns:
            Dict with classification, display info, and metadata
        """
        if thresholds is None:
            thresholds = self.default_thresholds
        
        # Check data quality first
        if sample_size < thresholds['min_sample_size']:
            return {
                'classification': 'insufficient_data',
                'display_text': 'Insufficient data',
                'color': 'gray',
                'confidence_level': 'none',
                'show_to_user': False,
                'reason': 'not_enough_samples',
                'metadata': {
                    'probability': probability,
                    'confidence': confidence,
                    'sample_size': sample_size,
                    'min_required': thresholds['min_sample_size']
                }
            }
        
        if confidence < thresholds['confidence_threshold']:
            return {
                'classification': 'low_confidence',
                'display_text': 'Uncertain',
                'color': 'gray',
                'confidence_level': 'low',
                'show_to_user': False,
                'reason': 'low_confidence',
                'metadata': {
                    'probability': probability,
                    'confidence': confidence,
                    'sample_size': sample_size,
                    'min_confidence': thresholds['confidence_threshold']
                }
            }
        
        # Classify based on probability thresholds
        if probability >= thresholds['likely_free']:
            classification = 'likely_free'
            display_text = 'Likely free in 30m'
            color = 'green'
        elif probability >= thresholds['possibly_free']:
            classification = 'possibly_free' 
            display_text = 'Possibly free in 30m'
            color = 'yellow'
        elif probability >= thresholds['unlikely_free']:
            classification = 'unlikely_free'
            display_text = 'Unlikely free in 30m'
            color = 'orange'
        else:
            classification = 'very_unlikely'
            display_text = 'Very unlikely free in 30m'
            color = 'red'
        
        # Determine confidence level display
        if confidence >= thresholds['high_confidence']:
            confidence_level = 'high'
            confidence_text = 'High confidence'
        elif confidence >= thresholds['medium_confidence']:
            confidence_level = 'medium'
            confidence_text = 'Medium confidence'
        else:
            confidence_level = 'low'
            confidence_text = 'Low confidence'
        
        return {
            'classification': classification,
            'display_text': display_text,
            'color': color,
            'confidence_level': confidence_level,
            'confidence_text': confidence_text,
            'show_to_user': True,
            'metadata': {
                'probability': probability,
                'confidence': confidence,
                'sample_size': sample_size,
                'probability_percentage': f"{probability * 100:.1f}%",
                'confidence_percentage': f"{confidence * 100:.1f}%"
            }
        }
    
    def tune_thresholds_for_category(self, gym_id: str, category: str, 
                                   target_precision: float = 0.7) -> Dict:
        """
        Tune thresholds for a specific category based on historical accuracy
        
        Args:
            gym_id: Gym branch ID
            category: Equipment category 
            target_precision: Target precision for "likely free" classification
            
        Returns:
            Dict with optimized thresholds and performance metrics
        """
        # Get historical patterns for validation
        patterns = self.seasonality_model.data_processor.analyze_category_patterns(
            gym_id, category, days_back=21
        )
        
        if 'error' in patterns or not patterns.get('patterns'):
            return {
                'gym_id': gym_id,
                'category': category,
                'optimized_thresholds': self.default_thresholds,
                'performance': None,
                'error': 'insufficient_historical_data'
            }
        
        # Test different threshold combinations
        threshold_candidates = [0.6, 0.65, 0.7, 0.75, 0.8]
        confidence_candidates = [0.5, 0.6, 0.7]
        
        best_thresholds = self.default_thresholds.copy()
        best_score = 0
        
        for prob_threshold in threshold_candidates:
            for conf_threshold in confidence_candidates:
                test_thresholds = self.default_thresholds.copy()
                test_thresholds['likely_free'] = prob_threshold
                test_thresholds['confidence_threshold'] = conf_threshold
                
                # Evaluate performance with these thresholds
                performance = self._evaluate_threshold_performance(
                    patterns, test_thresholds
                )
                
                # Calculate composite score (precision weighted more heavily)
                score = (performance['precision'] * 0.6 + 
                        performance['recall'] * 0.3 +
                        performance['coverage'] * 0.1)
                
                if score > best_score and performance['precision'] >= target_precision:
                    best_score = score
                    best_thresholds = test_thresholds
        
        # Validate final performance
        final_performance = self._evaluate_threshold_performance(patterns, best_thresholds)
        
        return {
            'gym_id': gym_id,
            'category': category,
            'optimized_thresholds': best_thresholds,
            'performance': final_performance,
            'optimization_score': best_score,
            'tuned_at': datetime.utcnow().isoformat()
        }
    
    def _evaluate_threshold_performance(self, patterns: Dict, thresholds: Dict) -> Dict:
        """
        Evaluate threshold performance against historical data
        
        Args:
            patterns: Historical patterns data
            thresholds: Threshold configuration to test
            
        Returns:
            Dict with performance metrics
        """
        pattern_data = patterns.get('patterns', {})
        
        if not pattern_data:
            return {
                'precision': 0.0,
                'recall': 0.0,
                'coverage': 0.0,
                'total_predictions': 0
            }
        
        # Simulate predictions for all time slots
        true_positives = 0  # Predicted free and actually was free
        false_positives = 0  # Predicted free but actually occupied
        true_negatives = 0  # Predicted occupied and actually was occupied
        false_negatives = 0  # Predicted occupied but actually was free
        predictions_made = 0  # Total predictions above confidence threshold
        
        for time_key, pattern in pattern_data.items():
            if pattern['sample_size'] < thresholds['min_sample_size']:
                continue
            
            # Calculate prediction
            free_probability = max(0.0, 1.0 - (pattern['avg_occupancy'] / 100.0))
            confidence = self.seasonality_model._calculate_confidence(
                pattern['sample_size'], 
                pattern.get('std_dev', 0)
            )
            
            if confidence < thresholds['confidence_threshold']:
                continue
            
            predictions_made += 1
            
            # Classify prediction
            predicted_free = free_probability >= thresholds['likely_free']
            
            # Ground truth: consider "actually free" if avg occupancy < 50%
            actually_free = pattern['avg_occupancy'] < 50.0
            
            # Update confusion matrix
            if predicted_free and actually_free:
                true_positives += 1
            elif predicted_free and not actually_free:
                false_positives += 1
            elif not predicted_free and not actually_free:
                true_negatives += 1
            else:  # not predicted_free and actually_free
                false_negatives += 1
        
        # Calculate metrics
        total_positive_predictions = true_positives + false_positives
        total_actual_positives = true_positives + false_negatives
        total_slots = len(pattern_data)
        
        precision = (true_positives / total_positive_predictions 
                    if total_positive_predictions > 0 else 0.0)
        recall = (true_positives / total_actual_positives 
                 if total_actual_positives > 0 else 0.0)
        coverage = predictions_made / total_slots if total_slots > 0 else 0.0
        
        return {
            'precision': precision,
            'recall': recall,
            'coverage': coverage,
            'total_predictions': predictions_made,
            'total_slots': total_slots,
            'confusion_matrix': {
                'true_positives': true_positives,
                'false_positives': false_positives,
                'true_negatives': true_negatives,
                'false_negatives': false_negatives
            }
        }
    
    def get_machine_forecast_display(self, machine_id: str, 
                                   current_time: Optional[datetime] = None) -> Dict:
        """
        Get display-ready forecast for a specific machine
        
        Args:
            machine_id: Machine to forecast
            current_time: Current time (defaults to now)
            
        Returns:
            Dict with display-ready forecast information
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        # Get historical patterns
        patterns = self.seasonality_model.data_processor.analyze_occupancy_patterns(
            machine_id, days_back=14
        )
        
        if 'error' in patterns:
            return {
                'machine_id': machine_id,
                'forecast': {
                    'classification': 'error',
                    'display_text': 'Forecast unavailable',
                    'show_to_user': False
                },
                'error': patterns['error']
            }
        
        # Calculate 30-minute forecast
        prediction = self.seasonality_model.calculate_free_probability(
            patterns, current_time, forecast_minutes=30
        )
        
        # Classify for display
        forecast_display = self.classify_availability_forecast(
            prediction['probability'],
            prediction['confidence'],
            prediction['sample_size']
        )
        
        return {
            'machine_id': machine_id,
            'forecast': forecast_display,
            'raw_prediction': prediction,
            'generated_at': datetime.utcnow().isoformat()
        }