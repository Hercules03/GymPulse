"""
Bedrock Tool: getAvailabilityByCategory
Returns gym machine availability by category near user location
"""
import json
import math
import boto3
import os


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
        
        # Mock branches data for now - replace with DynamoDB query
        branches = [
            {
                'id': 'hk-central',
                'name': 'Central Branch',
                'coordinates': [22.2819, 114.1577],
                'categories': {
                    'legs': {'free': 3, 'total': 8},
                    'chest': {'free': 5, 'total': 10},
                    'back': {'free': 2, 'total': 6}
                }
            },
            {
                'id': 'hk-causeway',
                'name': 'Causeway Bay Branch',
                'coordinates': [22.2783, 114.1747],
                'categories': {
                    'legs': {'free': 1, 'total': 6},
                    'chest': {'free': 8, 'total': 12},
                    'back': {'free': 4, 'total': 8}
                }
            }
        ]
        
        # Filter by distance and category availability
        results = []
        for branch in branches:
            branch_lat, branch_lon = branch['coordinates']
            distance = haversine_distance(lat, lon, branch_lat, branch_lon)
            
            if distance <= radius and category in branch['categories']:
                results.append({
                    'branchId': branch['id'],
                    'name': branch['name'],
                    'coordinates': branch['coordinates'],
                    'distance': round(distance, 2),
                    'freeCount': branch['categories'][category]['free'],
                    'totalCount': branch['categories'][category]['total']
                })
        
        # Sort by distance
        results.sort(key=lambda x: x['distance'])
        
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