"""
Forecast API Handler

Dedicated endpoint for machine availability forecasting with caching and performance optimization.
"""
import json
import boto3
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

# Add forecast module to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from forecast.threshold_tuner import ThresholdTuner
    from forecast.seasonality_model import SeasonalityModel
    from forecast.data_processor import HistoricalDataProcessor
    from forecast_integration import forecast_integration
    FORECAST_AVAILABLE = True
except ImportError as e:
    print(f"Forecast modules not available: {e}")
    FORECAST_AVAILABLE = False

from utils.error_handler import (
    api_handler, log_structured, send_metric,
    ValidationError, ResourceNotFoundError, DatabaseError
)
from utils.cache_manager import cached, CacheInvalidationStrategy


class ForecastApiHandler:
    """Handles forecast-specific API endpoints"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.current_state_table = self.dynamodb.Table(os.environ.get('CURRENT_STATE_TABLE', 'gym-pulse-current-state'))
        
        if FORECAST_AVAILABLE:
            self.threshold_tuner = ThresholdTuner()
            self.seasonality_model = SeasonalityModel()
            self.data_processor = HistoricalDataProcessor()
        
        # Cache TTL settings
        self.CACHE_TTL_MINUTES = {
            'machine_forecast': 10,  # 10 minutes for individual machine forecasts
            'category_forecast': 5,  # 5 minutes for category forecasts
            'weekly_pattern': 60,    # 1 hour for weekly patterns
            'threshold_optimization': 240  # 4 hours for threshold optimization
        }
    
    @cached(ttl_minutes=10, invalidation_strategy=CacheInvalidationStrategy.TIME_BASED)
    def get_machine_forecast(self, machine_id: str, forecast_minutes: int = 30) -> Dict:
        """
        Get forecast for specific machine with caching
        
        Args:
            machine_id: Machine to forecast
            forecast_minutes: Minutes ahead to forecast (default 30)
            
        Returns:
            Dict with forecast results
        """
        start_time = time.time()
        
        try:
            if not FORECAST_AVAILABLE:
                return self._simple_forecast_fallback(machine_id, forecast_minutes)
            
            # Use integrated forecast system
            forecast_result = forecast_integration.get_enhanced_machine_forecast(machine_id)
            
            # Add additional metadata
            forecast_result['forecast_minutes'] = forecast_minutes
            forecast_result['generated_at'] = datetime.utcnow().isoformat()
            forecast_result['cache_key'] = f"machine_forecast_{machine_id}_{forecast_minutes}"
            
            # Log performance metrics
            duration_ms = (time.time() - start_time) * 1000
            send_metric('forecast.machine.duration_ms', duration_ms, 'Milliseconds')
            send_metric('forecast.machine.success', 1, 'Count')
            
            return {
                'machineId': machine_id,
                'forecast': forecast_result,
                'performance': {
                    'duration_ms': round(duration_ms, 2),
                    'cached': False  # Will be updated by cache decorator
                },
                'success': True
            }
            
        except Exception as e:
            log_structured('ERROR', 'machine_forecast_error', {
                'machine_id': machine_id,
                'error': str(e),
                'duration_ms': (time.time() - start_time) * 1000
            })
            
            send_metric('forecast.machine.error', 1, 'Count')
            return {
                'machineId': machine_id,
                'forecast': self._simple_forecast_fallback(machine_id, forecast_minutes),
                'error': str(e),
                'success': False
            }
    
    @cached(ttl_minutes=5, invalidation_strategy=CacheInvalidationStrategy.TIME_BASED)
    def get_category_forecast(self, gym_id: str, category: str, forecast_minutes: int = 30) -> Dict:
        """
        Get forecast for entire category with caching
        
        Args:
            gym_id: Gym branch ID
            category: Equipment category
            forecast_minutes: Minutes ahead to forecast
            
        Returns:
            Dict with category forecast results
        """
        start_time = time.time()
        
        try:
            if not FORECAST_AVAILABLE:
                return self._simple_category_forecast_fallback(gym_id, category, forecast_minutes)
            
            # Use integrated forecast system
            forecast_result = forecast_integration.get_category_forecast(gym_id, category)
            
            # Add additional context
            forecast_result['forecast_minutes'] = forecast_minutes
            forecast_result['generated_at'] = datetime.utcnow().isoformat()
            
            # Get current machine counts for context
            current_status = self._get_current_category_status(gym_id, category)
            forecast_result['current_status'] = current_status
            
            # Log performance
            duration_ms = (time.time() - start_time) * 1000
            send_metric('forecast.category.duration_ms', duration_ms, 'Milliseconds')
            send_metric('forecast.category.success', 1, 'Count')
            
            return {
                'gymId': gym_id,
                'category': category,
                'forecast': forecast_result,
                'performance': {
                    'duration_ms': round(duration_ms, 2),
                    'cached': False
                },
                'success': True
            }
            
        except Exception as e:
            log_structured('ERROR', 'category_forecast_error', {
                'gym_id': gym_id,
                'category': category,
                'error': str(e),
                'duration_ms': (time.time() - start_time) * 1000
            })
            
            send_metric('forecast.category.error', 1, 'Count')
            return {
                'gymId': gym_id,
                'category': category,
                'forecast': self._simple_category_forecast_fallback(gym_id, category, forecast_minutes),
                'error': str(e),
                'success': False
            }
    
    @cached(ttl_minutes=60, invalidation_strategy=CacheInvalidationStrategy.TIME_BASED)
    def get_weekly_pattern(self, machine_id: str) -> Dict:
        """
        Get weekly baseline pattern for machine
        
        Args:
            machine_id: Machine to analyze
            
        Returns:
            Dict with weekly pattern
        """
        start_time = time.time()
        
        try:
            if not FORECAST_AVAILABLE:
                return {
                    'machineId': machine_id,
                    'weeklyPattern': {},
                    'error': 'Enhanced forecasting not available',
                    'success': False
                }
            
            # Generate weekly baseline pattern
            pattern_result = self.seasonality_model.generate_baseline_weekly_pattern(machine_id, days_back=21)
            
            if not pattern_result.get('success', True):
                return pattern_result
            
            # Log performance
            duration_ms = (time.time() - start_time) * 1000
            send_metric('forecast.weekly_pattern.duration_ms', duration_ms, 'Milliseconds')
            send_metric('forecast.weekly_pattern.success', 1, 'Count')
            
            return {
                'machineId': machine_id,
                'weeklyPattern': pattern_result.get('weekly_baseline', {}),
                'statistics': pattern_result.get('statistics', {}),
                'dataQuality': pattern_result.get('data_quality', {}),
                'generatedAt': pattern_result.get('generated_at'),
                'performance': {
                    'duration_ms': round(duration_ms, 2)
                },
                'success': True
            }
            
        except Exception as e:
            log_structured('ERROR', 'weekly_pattern_error', {
                'machine_id': machine_id,
                'error': str(e),
                'duration_ms': (time.time() - start_time) * 1000
            })
            
            send_metric('forecast.weekly_pattern.error', 1, 'Count')
            return {
                'machineId': machine_id,
                'weeklyPattern': {},
                'error': str(e),
                'success': False
            }
    
    def get_multiple_machine_forecasts(self, machine_ids: List[str], forecast_minutes: int = 30) -> Dict:
        """
        Get forecasts for multiple machines in batch
        
        Args:
            machine_ids: List of machine IDs
            forecast_minutes: Minutes ahead to forecast
            
        Returns:
            Dict with batch forecast results
        """
        start_time = time.time()
        forecasts = {}
        errors = []
        
        try:
            for machine_id in machine_ids:
                try:
                    forecast = self.get_machine_forecast(machine_id, forecast_minutes)
                    forecasts[machine_id] = forecast['forecast']
                except Exception as e:
                    errors.append({
                        'machine_id': machine_id,
                        'error': str(e)
                    })
            
            duration_ms = (time.time() - start_time) * 1000
            send_metric('forecast.batch.duration_ms', duration_ms, 'Milliseconds')
            send_metric('forecast.batch.success', 1, 'Count')
            send_metric('forecast.batch.size', len(machine_ids), 'Count')
            
            return {
                'forecasts': forecasts,
                'errors': errors,
                'machineCount': len(machine_ids),
                'successfulForecasts': len(forecasts),
                'failedForecasts': len(errors),
                'performance': {
                    'duration_ms': round(duration_ms, 2),
                    'avg_per_machine_ms': round(duration_ms / len(machine_ids), 2) if machine_ids else 0
                },
                'success': len(forecasts) > 0
            }
            
        except Exception as e:
            log_structured('ERROR', 'batch_forecast_error', {
                'machine_ids': machine_ids,
                'error': str(e),
                'duration_ms': (time.time() - start_time) * 1000
            })
            
            send_metric('forecast.batch.error', 1, 'Count')
            return {
                'forecasts': forecasts,
                'errors': errors + [{'error': f'Batch processing failed: {str(e)}'}],
                'success': False
            }
    
    def _get_current_category_status(self, gym_id: str, category: str) -> Dict:
        """Get current status for machines in category"""
        try:
            response = self.current_state_table.scan(
                FilterExpression='gymId = :gym_id AND category = :category',
                ExpressionAttributeValues={
                    ':gym_id': gym_id,
                    ':category': category
                }
            )
            
            machines = response.get('Items', [])
            total_count = len(machines)
            free_count = sum(1 for machine in machines if machine.get('status') == 'free')
            occupied_count = total_count - free_count
            
            return {
                'totalMachines': total_count,
                'freeMachines': free_count,
                'occupiedMachines': occupied_count,
                'occupancyRate': (occupied_count / total_count * 100) if total_count > 0 else 0,
                'lastUpdated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            log_structured('WARNING', 'category_status_error', {
                'gym_id': gym_id,
                'category': category,
                'error': str(e)
            })
            
            return {
                'totalMachines': 0,
                'freeMachines': 0,
                'occupiedMachines': 0,
                'occupancyRate': 50.0,  # Default assumption
                'error': str(e)
            }
    
    def _simple_forecast_fallback(self, machine_id: str, forecast_minutes: int) -> Dict:
        """Simple forecast fallback when enhanced system unavailable"""
        return {
            'likelyFreeIn30m': False,
            'classification': 'unavailable',
            'display_text': 'Forecast unavailable',
            'color': 'gray',
            'confidence': 'none',
            'confidence_text': 'Enhanced forecasting system unavailable',
            'show_to_user': False,
            'reason': 'Forecast system not available',
            'forecast_minutes': forecast_minutes,
            'metadata': {
                'probability': 0.5,
                'sample_size': 0,
                'reliable': False,
                'fallback': True
            }
        }
    
    def _simple_category_forecast_fallback(self, gym_id: str, category: str, forecast_minutes: int) -> Dict:
        """Simple category forecast fallback"""
        return {
            'classification': 'unavailable',
            'display_text': 'Category forecast unavailable',
            'color': 'gray',
            'confidence': 'none',
            'show_to_user': False,
            'reason': 'Enhanced forecasting system not available',
            'forecast_minutes': forecast_minutes,
            'metadata': {
                'fallback': True,
                'gym_id': gym_id,
                'category': category
            }
        }


# Initialize handler instance
forecast_api = ForecastApiHandler()


@api_handler
def lambda_handler(event, context):
    """
    Handle forecast API requests
    """
    try:
        path = event.get('path', '')
        method = event.get('httpMethod', 'GET')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        # Route forecast endpoints
        if method == 'GET':
            if '/forecast/machine/' in path:
                machine_id = path_parameters.get('machineId')
                if not machine_id:
                    raise ValidationError("Missing machineId parameter")
                
                forecast_minutes = int(query_parameters.get('minutes', 30))
                return forecast_api.get_machine_forecast(machine_id, forecast_minutes)
            
            elif '/forecast/category/' in path:
                gym_id = path_parameters.get('gymId')
                category = path_parameters.get('category')
                
                if not gym_id or not category:
                    raise ValidationError("Missing gymId or category parameter")
                
                forecast_minutes = int(query_parameters.get('minutes', 30))
                return forecast_api.get_category_forecast(gym_id, category, forecast_minutes)
            
            elif '/forecast/weekly/' in path:
                machine_id = path_parameters.get('machineId')
                if not machine_id:
                    raise ValidationError("Missing machineId parameter")
                
                return forecast_api.get_weekly_pattern(machine_id)
            
            elif '/forecast/batch' in path:
                machine_ids = query_parameters.get('machineIds', '').split(',')
                machine_ids = [mid.strip() for mid in machine_ids if mid.strip()]
                
                if not machine_ids:
                    raise ValidationError("Missing machineIds parameter")
                
                forecast_minutes = int(query_parameters.get('minutes', 30))
                return forecast_api.get_multiple_machine_forecasts(machine_ids, forecast_minutes)
            
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({
                        'error': 'Forecast endpoint not found',
                        'availableEndpoints': [
                            'GET /forecast/machine/{machineId}',
                            'GET /forecast/category/{gymId}/{category}', 
                            'GET /forecast/weekly/{machineId}',
                            'GET /forecast/batch?machineIds=id1,id2,id3'
                        ]
                    })
                }
        
        else:
            return {
                'statusCode': 405,
                'body': json.dumps({'error': f'Method {method} not allowed'})
            }
    
    except ValidationError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        log_structured('ERROR', 'forecast_api_error', {
            'path': path,
            'method': method,
            'error': str(e)
        })
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e) if os.environ.get('DEBUG') else 'An error occurred'
            })
        }