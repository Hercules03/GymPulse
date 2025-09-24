"""
Bedrock Tool: getAvailabilityByCategory
Returns gym machine availability by category near user location
"""
import json
import math
import boto3
import os
from botocore.exceptions import ClientError


dynamodb = boto3.resource('dynamodb')
current_state_table = dynamodb.Table(os.environ['CURRENT_STATE_TABLE'])


def lambda_handler(event, context):
    """
    Get availability by category and location
    """
    try:
        # Parse tool input from Bedrock
        if isinstance(event, dict) and 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
            
        lat = float(body['lat'])
        lon = float(body['lon'])
        radius = float(body.get('radius', 5))  # 5km default
        category = body['category']
        
        print(f"Availability request: {category} within {radius}km of ({lat}, {lon})")
        
        # Branch configurations - should match API handler
        branch_configs = [
            {
                'id': 'hk-central',
                'name': 'Central Branch',
                'coordinates': [22.2819, 114.1577]
            },
            {
                'id': 'hk-causeway',
                'name': 'Causeway Bay Branch', 
                'coordinates': [22.2783, 114.1747]
            }
        ]
        
        # Query real DynamoDB data
        branches = []
        for branch_config in branch_configs:
            branch_id = branch_config['id']
            branch_lat, branch_lon = branch_config['coordinates']
            
            # Calculate distance first to filter nearby branches
            distance = haversine_distance(lat, lon, branch_lat, branch_lon)
            
            if distance <= radius:
                try:
                    # Query current state for this branch and category
                    response = current_state_table.scan(
                        FilterExpression='gymId = :gym_id AND category = :category',
                        ExpressionAttributeValues={
                            ':gym_id': branch_id,
                            ':category': category
                        }
                    )
                    
                    machines = response.get('Items', [])
                    total_count = len(machines)
                    free_count = sum(1 for m in machines if m.get('status') == 'free')
                    
                    if total_count > 0:  # Only include branches with equipment
                        branches.append({
                            'id': branch_id,
                            'name': branch_config['name'],
                            'coordinates': branch_config['coordinates'],
                            'categories': {
                                category: {'free': free_count, 'total': total_count}
                            }
                        })
                        
                    print(f"Branch {branch_id}: {free_count}/{total_count} {category} equipment free")
                    
                except ClientError as e:
                    print(f"DynamoDB error for {branch_id}: {str(e)}")
                    # Continue with other branches on error
        
        # Process results - already filtered by distance and category
        results = []
        for branch in branches:
            branch_lat, branch_lon = branch['coordinates'] 
            distance = haversine_distance(lat, lon, branch_lat, branch_lon)
            
            if category in branch['categories']:
                # Get category forecast for this branch
                category_forecast = get_category_forecast(branch['id'], category)
                
                results.append({
                    'branchId': branch['id'],
                    'name': branch['name'],
                    'coordinates': branch['coordinates'],
                    'distance': round(distance, 2),
                    'freeCount': branch['categories'][category]['free'],
                    'totalCount': branch['categories'][category]['total'],
                    'forecast': category_forecast
                })
        
        # Sort by distance, then by availability (more free machines first)
        results.sort(key=lambda x: (x['distance'], -x['freeCount']))
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'branches': results,
                'category': category,
                'searchRadius': radius
            })
        }
        
    except Exception as e:
        print(f"Availability tool error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def get_category_forecast(gym_id, category):
    """
    Get forecast for category at gym branch
    Falls back to simple forecast if enhanced forecasting unavailable
    """
    try:
        # Try to import and use enhanced forecasting
        import sys
        import os
        
        # Add forecast module to path
        forecast_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'forecast')
        if forecast_path not in sys.path:
            sys.path.append(forecast_path)
        
        from threshold_tuner import ThresholdTuner
        from seasonality_model import SeasonalityModel
        from datetime import datetime
        
        # Get enhanced forecast
        seasonality_model = SeasonalityModel()
        forecast_result = seasonality_model.get_category_forecast(
            gym_id, category, datetime.utcnow(), forecast_minutes=30
        )
        
        if 'error' not in forecast_result:
            forecast_data = forecast_result['forecast']
            
            # Classify using threshold tuner
            threshold_tuner = ThresholdTuner()
            if forecast_data.get('reliable'):
                classification = threshold_tuner.classify_availability_forecast(
                    forecast_data['probability'],
                    forecast_data['confidence'],
                    forecast_data['sample_size']
                )
                
                return {
                    'classification': classification['classification'],
                    'display_text': classification['display_text'],
                    'confidence': classification['confidence_level'],
                    'probability': f"{forecast_data['probability'] * 100:.0f}%",
                    'reliable': True
                }
            else:
                return {
                    'classification': 'insufficient_data',
                    'display_text': 'Limited forecast data',
                    'confidence': 'low',
                    'reliable': False
                }
        
    except ImportError:
        print("Enhanced forecasting not available, using fallback")
    except Exception as e:
        print(f"Forecast error for {gym_id}/{category}: {str(e)}")
    
    # Fallback forecast
    return {
        'classification': 'unavailable',
        'display_text': 'Forecast unavailable',
        'confidence': 'none',
        'reliable': False
    }


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points using Haversine formula
    """
    R = 6371  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c