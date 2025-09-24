"""
Response ranking and formatting utilities
Combines availability and route data for optimal recommendations
"""
import json


def format_chat_response(availability_data, route_data=None):
    """
    Format structured response with recommendations
    Combines availability and route data for ranking
    """
    if not availability_data or not availability_data.get('branches'):
        return {
            'topRecommendation': None,
            'alternatives': [],
            'totalOptionsFound': 0,
            'message': 'No available equipment found nearby'
        }
    
    branches = availability_data['branches']
    category = availability_data.get('category', 'equipment')
    
    # If we have route data, merge it with availability data
    if route_data and route_data.get('routes'):
        branches_with_routes = merge_availability_and_routes(branches, route_data['routes'])
    else:
        # Use distance-based ranking if no route data
        branches_with_routes = [
            {
                **branch,
                'etaMinutes': estimate_eta_from_distance(branch.get('distance', 5)),
                'durationSeconds': estimate_eta_from_distance(branch.get('distance', 5)) * 60
            }
            for branch in branches
        ]
    
    # Sort by ETA first, then by availability (more free machines preferred)
    sorted_branches = sorted(
        branches_with_routes, 
        key=lambda x: (
            x.get('etaMinutes', 999),  # Shorter ETA first
            -x.get('freeCount', 0),    # More free machines first
            x.get('distance', 999)     # Shorter distance as tiebreaker
        )
    )
    
    # Format response
    top_pick = sorted_branches[0] if sorted_branches else None
    alternatives = sorted_branches[1:3] if len(sorted_branches) > 1 else []
    
    return {
        'topRecommendation': format_branch_recommendation(top_pick, category) if top_pick else None,
        'alternatives': [format_branch_recommendation(branch, category) for branch in alternatives],
        'totalOptionsFound': len(sorted_branches),
        'category': category
    }


def merge_availability_and_routes(branches, routes):
    """
    Merge availability data with route information
    """
    # Create a mapping of branchId to route info
    route_map = {route['branchId']: route for route in routes}
    
    merged_branches = []
    for branch in branches:
        branch_id = branch['branchId']
        route_info = route_map.get(branch_id, {})
        
        merged_branch = {
            **branch,
            'etaMinutes': route_info.get('etaMinutes', estimate_eta_from_distance(branch.get('distance', 5))),
            'durationSeconds': route_info.get('durationSeconds', estimate_eta_from_distance(branch.get('distance', 5)) * 60),
            'distanceKm': route_info.get('distanceKm', branch.get('distance', 5))
        }
        merged_branches.append(merged_branch)
    
    return merged_branches


def format_branch_recommendation(branch, category):
    """
    Format a single branch recommendation for display
    """
    if not branch:
        return None
        
    eta_text = f"{branch.get('etaMinutes', 0):.0f} mins"
    distance_text = f"{branch.get('distance', branch.get('distanceKm', 0)):.1f} km"
    
    free_count = branch.get('freeCount', 0)
    total_count = branch.get('totalCount', 0)
    
    availability_text = f"{free_count}/{total_count} available"
    if free_count == 0:
        availability_text = "Currently full"
    elif free_count == total_count:
        availability_text = "All equipment available"
    
    return {
        'branchId': branch['branchId'],
        'name': branch['name'],
        'eta': eta_text,
        'distance': distance_text,
        'availableCount': free_count,
        'totalCount': total_count,
        'category': category,
        'availabilityText': availability_text,
        'coordinates': branch.get('coordinates', [0, 0])
    }


def estimate_eta_from_distance(distance_km):
    """
    Estimate ETA in minutes based on distance
    Assumes 25 km/h average speed in Hong Kong urban traffic
    """
    if not distance_km:
        return 5  # Default 5 minutes for unknown distance
        
    # Convert km to minutes at 25 km/h average speed
    eta_minutes = (distance_km / 25) * 60
    
    # Add base travel time for urban navigation
    base_time = 3  # 3 minutes base time
    
    return max(base_time, eta_minutes)


def generate_recommendation_text(formatted_response, user_query=""):
    """
    Generate natural language recommendation text
    """
    category = formatted_response.get('category', 'equipment')
    top_rec = formatted_response.get('topRecommendation')
    alternatives = formatted_response.get('alternatives', [])
    total_found = formatted_response.get('totalOptionsFound', 0)
    
    if not top_rec:
        return f"Sorry, I couldn't find any available {category} equipment nearby right now. Try checking back later!"
    
    # Build recommendation text
    text_parts = []
    
    # Greeting based on category
    if 'legs' in category.lower():
        text_parts.append("Great choice for leg day! 💪")
    elif 'chest' in category.lower():
        text_parts.append("Time to work that chest! 💪") 
    elif 'back' in category.lower():
        text_parts.append("Perfect for back training! 💪")
    else:
        text_parts.append("Let's find you some equipment! 💪")
    
    # Top recommendation
    text_parts.append(
        f"Your best option is **{top_rec['name']}** - just {top_rec['eta']} away "
        f"with {top_rec['availableCount']}/{top_rec['totalCount']} {category} machines available."
    )
    
    # Alternatives if available
    if alternatives:
        if len(alternatives) == 1:
            alt = alternatives[0]
            text_parts.append(
                f"Alternative: **{alt['name']}** ({alt['eta']}, {alt['availableCount']}/{alt['totalCount']} available)"
            )
        else:
            alt_text = []
            for alt in alternatives:
                alt_text.append(f"**{alt['name']}** ({alt['eta']}, {alt['availableCount']}/{alt['totalCount']} available)")
            text_parts.append(f"Alternatives: {', '.join(alt_text)}")
    
    # Call to action
    text_parts.append("Tap a gym to see more details and get directions! 🗺️")
    
    return " ".join(text_parts)