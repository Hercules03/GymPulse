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
                results.append({
                    'branchId': branch['id'],
                    'name': branch['name'],
                    'coordinates': branch['coordinates'],
                    'distance': round(distance, 2),
                    'freeCount': branch['categories'][category]['free'],
                    'totalCount': branch['categories'][category]['total']
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