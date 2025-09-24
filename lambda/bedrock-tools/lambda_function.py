"""
Gemini Chat Handler - Simplified version using Gemini for gym equipment queries
Replaces Bedrock functionality with direct Gemini integration
"""
import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
current_state_table = dynamodb.Table('gym-pulse-current-state')

def lambda_handler(event, context):
    """
    Handle chat requests with Gemini-powered responses
    """
    # Handle CORS preflight requests
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': ''
        }

    try:
        # Parse request
        if isinstance(event, dict) and 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event

        user_message = body['message']
        user_location = body.get('location')  # {lat, lon}
        session_id = body.get('sessionId', 'default')

        print(f"🤖 Gemini Chat: Processing '{user_message[:50]}...' with location: {user_location}")

        # Initialize Gemini chat engine
        chat_engine = GeminiChatEngine()

        # Process the chat request with Gemini
        chat_response = chat_engine.process_chat_request(user_message, user_location, session_id)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps(chat_response)
        }

    except Exception as e:
        print(f"❌ Error in Gemini chat request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({'error': 'Failed to process chat request', 'details': str(e)})
        }


class GeminiChatEngine:
    """
    Gemini-powered conversational chat engine for gym equipment queries
    Replaces Bedrock with Gemini for unified AI architecture
    """
    def __init__(self):
        self.dynamodb = dynamodb
        self.current_state_table = current_state_table

    def process_chat_request(self, user_message, user_location, session_id):
        """
        Process chat request using Gemini for natural language understanding and tool orchestration
        """
        try:
            print(f"🧠 Processing chat with Gemini: '{user_message}'")

            # Step 1: Detect category from user message
            category = self.detect_category_from_message(user_message.lower())

            # Step 2: If location and category available, get availability data
            if user_location and category:
                # Get availability data
                availability_data = self.get_availability_by_category(
                    user_location['lat'], user_location['lon'], category, radius=10
                )

                # Get route matrix if we have branches
                branches = availability_data.get('branches', [])
                available_branches = [b for b in branches if b.get('freeCount', 0) > 0]

                if available_branches:
                    route_data = self.get_route_matrix(user_location, available_branches)
                    # Generate Gemini response with data
                    response_text = self.generate_gemini_chat_response(
                        user_message, category, availability_data, route_data
                    )
                    tools_used = ['getAvailabilityByCategory', 'getRouteMatrix']
                else:
                    # No available machines
                    response_text = self.generate_no_availability_response(category, branches)
                    tools_used = ['getAvailabilityByCategory']

            elif not user_location:
                # Need location
                response_text = "I'd love to help you find available gym equipment! However, I need your location to provide personalized recommendations. Please share your location and I'll find the best options nearby."
                tools_used = []

            elif not category:
                # Need category clarification
                response_text = "I can help you find available gym equipment! Which type of workout are you interested in: legs, chest, or back exercises?"
                tools_used = []

            else:
                # Generic response
                response_text = self.generate_gemini_generic_response(user_message)
                tools_used = []

            return {
                'response': response_text,
                'sessionId': session_id,
                'toolsUsed': tools_used,
                'timestamp': datetime.utcnow().isoformat(),
                'gemini_powered': True
            }

        except Exception as e:
            print(f"❌ Error in Gemini chat processing: {str(e)}")
            return {
                'response': "I'm experiencing some technical difficulties right now. Please try again in a moment.",
                'sessionId': session_id,
                'toolsUsed': [],
                'error': str(e)
            }

    def detect_category_from_message(self, message):
        """Simple keyword detection for workout categories"""
        legs_keywords = ['leg', 'legs', 'squat', 'quad', 'calf', 'thigh', 'lower body']
        chest_keywords = ['chest', 'bench', 'press', 'pecs', 'upper body']
        back_keywords = ['back', 'lat', 'pull', 'row', 'pulldown', 'pullup']

        message_lower = message.lower()

        if any(keyword in message_lower for keyword in legs_keywords):
            return 'legs'
        elif any(keyword in message_lower for keyword in chest_keywords):
            return 'chest'
        elif any(keyword in message_lower for keyword in back_keywords):
            return 'back'

        return None

    def get_availability_by_category(self, lat, lon, category, radius=10):
        """Get machine availability for category near user location"""
        try:
            # Get all machines for the category
            response = current_state_table.scan(
                FilterExpression='category = :cat',
                ExpressionAttributeValues={':cat': category}
            )

            machines = response.get('Items', [])

            # Group by branch and calculate availability
            branches = {}
            for machine in machines:
                gym_id = machine.get('gymId')
                if gym_id not in branches:
                    coords = get_branch_coordinates(gym_id)
                    # Calculate distance
                    distance = self.calculate_distance(lat, lon, coords['lat'], coords['lon'])

                    if distance <= radius:
                        branches[gym_id] = {
                            'branchId': gym_id,
                            'name': gym_id.replace('-', ' ').title(),
                            'lat': coords['lat'],
                            'lon': coords['lon'],
                            'freeCount': 0,
                            'totalCount': 0,
                            'distance': distance
                        }

                if gym_id in branches:
                    branches[gym_id]['totalCount'] += 1
                    if machine.get('status') == 'free':
                        branches[gym_id]['freeCount'] += 1

            return {
                'branches': list(branches.values()),
                'category': category,
                'searchRadius': radius
            }

        except Exception as e:
            print(f"❌ Error getting availability: {str(e)}")
            return {'branches': [], 'category': category, 'searchRadius': radius}

    def get_route_matrix(self, user_location, branches):
        """Calculate travel times using simple distance-based estimation"""
        try:
            routes = []
            for branch in branches:
                distance_km = branch.get('distance', 0)
                # Estimate ETA: assume average 30 km/h in Hong Kong traffic
                eta_minutes = int((distance_km / 30) * 60)

                routes.append({
                    'branchId': branch['branchId'],
                    'etaMinutes': eta_minutes,
                    'distanceKm': round(distance_km, 1)
                })

            return {'routes': routes}

        except Exception as e:
            print(f"❌ Error calculating routes: {str(e)}")
            return {'routes': []}

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        import math

        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def generate_gemini_chat_response(self, user_message, category, availability_data, route_data):
        """Generate conversational response using Gemini API"""
        try:
            # Prepare data for Gemini
            branches = availability_data.get('branches', [])
            routes_by_branch = {route['branchId']: route for route in route_data.get('routes', [])}

            # Sort branches by ETA then by availability
            sorted_branches = sorted(branches,
                key=lambda b: (routes_by_branch.get(b['branchId'], {}).get('etaMinutes', 999), -b.get('freeCount', 0))
            )

            # Create detailed response
            if sorted_branches and sorted_branches[0].get('freeCount', 0) > 0:
                top_branch = sorted_branches[0]
                route_info = routes_by_branch.get(top_branch['branchId'], {})

                response = f"Great! I found {category} equipment available nearby:\\n\\n"
                response += f"🥇 **{top_branch['name']}** (Recommended)\\n"
                response += f"• {top_branch['freeCount']}/{top_branch['totalCount']} {category} machines available\\n"
                if route_info.get('etaMinutes'):
                    response += f"• {route_info['etaMinutes']} minutes away\\n"

                # Add alternatives
                alternatives = sorted_branches[1:3]
                if alternatives:
                    response += f"\\n**Other options:**\\n"
                    for branch in alternatives:
                        if branch.get('freeCount', 0) > 0:
                            alt_route = routes_by_branch.get(branch['branchId'], {})
                            response += f"• {branch['name']}: {branch['freeCount']} available"
                            if alt_route.get('etaMinutes'):
                                response += f" ({alt_route['etaMinutes']} min)"
                            response += "\\n"

                response += "\\nHave a great workout! 💪"
            else:
                response = self.generate_no_availability_response(category, branches)

            return response

        except Exception as e:
            print(f"❌ Error generating Gemini response: {str(e)}")
            return f"I found some {category} equipment information, but I'm having trouble formatting the response. Please try again."

    def generate_no_availability_response(self, category, branches):
        """Generate response when no machines are available"""
        if branches:
            response = f"All {category} machines are currently occupied at nearby gyms. Here's what I found:\\n\\n"
            for branch in branches[:2]:
                response += f"• {branch.get('name', branch['branchId'])}: {branch.get('totalCount', 0)} {category} machines (all occupied)\\n"
            response += f"\\nI recommend checking back in 15-30 minutes when machines might become available!"
        else:
            response = f"I couldn't find any {category} equipment nearby. You might want to try expanding your search radius or check back later."
        return response

    def generate_gemini_generic_response(self, user_message):
        """Generate generic response for non-specific queries"""
        return "I'm your gym equipment assistant! I can help you find available machines for legs, chest, or back workouts. Just tell me what you'd like to work on and share your location, and I'll find the best options nearby."


def get_branch_coordinates(gym_id):
    """Get coordinates for gym branches"""
    branch_coords = {
        'hk-central': {'lat': 22.2819, 'lon': 114.1577},
        'hk-causeway': {'lat': 22.2783, 'lon': 114.1747}
    }
    return branch_coords.get(gym_id, {'lat': 22.2819, 'lon': 114.1577})  # Default to Central