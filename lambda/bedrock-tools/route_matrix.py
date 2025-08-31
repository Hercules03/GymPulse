"""
Bedrock Tool: getRouteMatrix
Calculate travel times and distances using Amazon Location Service
"""
import json
import math
import boto3
import os
from botocore.exceptions import ClientError


location_client = boto3.client('location')
route_calculator_name = os.environ['ROUTE_CALCULATOR_NAME']


def lambda_handler(event, context):
    """
    Calculate route matrix from user to multiple branch locations
    """
    try:
        # Parse tool input from Bedrock
        if isinstance(event, dict) and 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
            
        user_coord = body['userCoordinate']  # [lat, lon]
        branch_coords = body['branchCoordinates']  # [[lat, lon], ...]
        
        print(f"Route matrix request: {len(branch_coords)} destinations from {user_coord}")
        
        try:
            # Try to use Amazon Location Service
            origins = [[user_coord[1], user_coord[0]]]  # Location expects [lon, lat]
            destinations = [[coord[1], coord[0]] for coord in branch_coords]
            
            response = location_client.calculate_route_matrix(
                CalculatorName=route_calculator_name,
                DeparturePositions=origins,
                DestinationPositions=destinations,
                TravelMode='Car',
                DistanceUnit='Kilometers',
                DurationUnit='Seconds'
            )
            
            # Process Location Service results
            routes = []
            for i, route_result in enumerate(response['RouteMatrix'][0]):
                routes.append({
                    'branchIndex': i,
                    'durationSeconds': route_result.get('DurationSeconds'),
                    'distanceKm': route_result.get('Distance'),
                    'etaMinutes': round(route_result.get('DurationSeconds', 0) / 60, 1)
                })
                
        except (ClientError, KeyError) as e:
            print(f"Location Service error, falling back to distance calculation: {str(e)}")
            # Fallback to distance-based ETA estimation
            routes = []
            for i, coord in enumerate(branch_coords):
                distance = haversine_distance(user_coord[0], user_coord[1], coord[0], coord[1])
                # Estimate ETA: assume 30 km/h average speed in Hong Kong traffic
                eta_minutes = (distance / 30) * 60
                
                routes.append({
                    'branchIndex': i,
                    'etaMinutes': round(eta_minutes, 1),
                    'distanceKm': round(distance, 2),
                    'durationSeconds': round(eta_minutes * 60)
                })
        
        return {
            'statusCode': 200,
            'body': json.dumps({'routes': routes})
        }
        
    except Exception as e:
        print(f"Route matrix tool error: {str(e)}")
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