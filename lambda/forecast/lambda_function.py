"""
Forecast Lambda Handler

Main entry point for machine availability forecasting requests.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any

from .threshold_tuner import ThresholdTuner
from .seasonality_model import SeasonalityModel
from .data_processor import HistoricalDataProcessor


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for forecast requests
    
    Expected event formats:
    - GET /forecast/machine/{machineId} - Get forecast for specific machine
    - GET /forecast/category/{gymId}/{category} - Get category forecast
    - POST /forecast/threshold-tune - Tune thresholds for category
    """
    
    try:
        # Parse request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        query_params = event.get('queryStringParameters') or {}
        
        # Initialize forecast components
        threshold_tuner = ThresholdTuner()
        seasonality_model = SeasonalityModel()
        data_processor = HistoricalDataProcessor()
        
        # Route requests
        if http_method == 'GET':
            if '/forecast/machine/' in path:
                return handle_machine_forecast(path, query_params, threshold_tuner)
            elif '/forecast/category/' in path:
                return handle_category_forecast(path, query_params, seasonality_model)
            elif path == '/forecast/health':
                return {
                    'statusCode': 200,
                    'headers': get_cors_headers(),
                    'body': json.dumps({
                        'status': 'healthy',
                        'service': 'forecast',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                }
        elif http_method == 'POST' and path == '/forecast/threshold-tune':
            body = json.loads(event.get('body', '{}'))
            return handle_threshold_tuning(body, threshold_tuner)
        
        # Invalid path/method
        return {
            'statusCode': 404,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Not found',
                'path': path,
                'method': http_method
            })
        }
        
    except Exception as e:
        print(f"Forecast Lambda error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def handle_machine_forecast(path: str, query_params: Dict, threshold_tuner: ThresholdTuner) -> Dict:
    """Handle machine-specific forecast requests"""
    
    # Extract machine ID from path
    path_parts = path.split('/')
    if len(path_parts) < 3 or not path_parts[-1]:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Machine ID required'})
        }
    
    machine_id = path_parts[-1]
    
    # Get current time or use provided timestamp
    current_time = datetime.utcnow()
    if 'timestamp' in query_params:
        try:
            current_time = datetime.fromisoformat(query_params['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            pass  # Use current time if invalid timestamp
    
    # Get forecast
    forecast_result = threshold_tuner.get_machine_forecast_display(machine_id, current_time)
    
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps(forecast_result, default=str)
    }


def handle_category_forecast(path: str, query_params: Dict, seasonality_model: SeasonalityModel) -> Dict:
    """Handle category-level forecast requests"""
    
    # Extract gym_id and category from path
    # Expected: /forecast/category/{gymId}/{category}
    path_parts = path.split('/')
    if len(path_parts) < 5:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Gym ID and category required'})
        }
    
    gym_id = path_parts[-2]
    category = path_parts[-1]
    
    # Validate category
    if category not in ['legs', 'chest', 'back']:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Invalid category',
                'valid_categories': ['legs', 'chest', 'back']
            })
        }
    
    # Get forecast minutes (default 30)
    forecast_minutes = int(query_params.get('minutes', 30))
    
    # Get current time
    current_time = datetime.utcnow()
    if 'timestamp' in query_params:
        try:
            current_time = datetime.fromisoformat(query_params['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            pass
    
    # Get category forecast
    forecast_result = seasonality_model.get_category_forecast(
        gym_id, category, current_time, forecast_minutes
    )
    
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps(forecast_result, default=str)
    }


def handle_threshold_tuning(body: Dict, threshold_tuner: ThresholdTuner) -> Dict:
    """Handle threshold tuning requests"""
    
    gym_id = body.get('gym_id')
    category = body.get('category')
    target_precision = body.get('target_precision', 0.7)
    
    if not gym_id or not category:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'gym_id and category required',
                'received': {'gym_id': gym_id, 'category': category}
            })
        }
    
    # Tune thresholds
    tuning_result = threshold_tuner.tune_thresholds_for_category(
        gym_id, category, target_precision
    )
    
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps(tuning_result, default=str)
    }


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers for API responses"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
    }