# Phase 6: Agentic Chatbot with Tool-Use - Step-by-Step Breakdown

## Overview
Implement Bedrock Converse API chatbot with tool-use capabilities for availability queries and route-based recommendations using Amazon Location Service.

## Prerequisites
- Phase 1 Bedrock agent configured
- Phase 4 APIs operational
- Phase 5 frontend ready for chat integration
- Amazon Location Service deployed

---

## Step 1: Tool Schema Definitions
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 1.1 getAvailabilityByCategory Tool Schema
- [ ] **File**: `agent/schemas/availability-tool.json`
```json
{
  "toolSpec": {
    "name": "getAvailabilityByCategory",
    "description": "Get gym machine availability by category near user location",
    "inputSchema": {
      "json": {
        "type": "object",
        "properties": {
          "lat": {"type": "number", "description": "User latitude"},
          "lon": {"type": "number", "description": "User longitude"},
          "radius": {"type": "number", "description": "Search radius in kilometers"},
          "category": {"type": "string", "enum": ["legs", "chest", "back"], "description": "Equipment category"}
        },
        "required": ["lat", "lon", "category"]
      }
    }
  }
}
```

### 1.2 getRouteMatrix Tool Schema
- [ ] **File**: `agent/schemas/route-matrix-tool.json`
```json
{
  "toolSpec": {
    "name": "getRouteMatrix",
    "description": "Calculate travel times and distances to multiple gym branches",
    "inputSchema": {
      "json": {
        "type": "object", 
        "properties": {
          "userCoord": {
            "type": "object",
            "properties": {
              "lat": {"type": "number"},
              "lon": {"type": "number"}
            }
          },
          "branchCoords": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "branchId": {"type": "string"},
                "lat": {"type": "number"},
                "lon": {"type": "number"}
              }
            }
          }
        },
        "required": ["userCoord", "branchCoords"]
      }
    }
  }
}
```

---

## Step 2: getAvailabilityByCategory Implementation
**Duration**: 40 minutes  
**Status**: ⏳ Pending

### 2.1 Availability Tool Handler
- [ ] **File**: `lambda/bedrock-tools/availability-handler.py`
- [ ] Parse tool input parameters
- [ ] Query current_state table for machines
- [ ] Filter by category and location radius
- [ ] Aggregate free counts by branch

### 2.2 Data Processing Logic
```python
def get_availability_by_category(lat, lon, radius, category):
    """
    Get machine availability for category near user location
    """
    # Query all machines for the category
    machines = query_machines_by_category(category)
    
    # Filter by distance radius
    nearby_branches = []
    for branch in get_unique_branches(machines):
        distance = calculate_distance(lat, lon, branch['lat'], branch['lon'])
        if distance <= radius:
            free_count = count_free_machines(branch['id'], category)
            total_count = count_total_machines(branch['id'], category)
            nearby_branches.append({
                'branchId': branch['id'],
                'name': branch['name'],
                'lat': branch['lat'],
                'lon': branch['lon'],
                'freeCount': free_count,
                'totalCount': total_count,
                'distance': distance
            })
    
    return {
        'branches': nearby_branches,
        'category': category,
        'searchRadius': radius
    }
```

### 2.3 Integration with Current State API
- [ ] Reuse existing API logic from Phase 4
- [ ] Add geographic filtering capability
- [ ] Include forecast data if available
- [ ] Handle edge cases (no nearby branches, all occupied)

---

## Step 3: getRouteMatrix Implementation
**Duration**: 35 minutes  
**Status**: ⏳ Pending

### 3.1 Route Matrix Tool Handler
- [ ] **File**: `lambda/bedrock-tools/route-matrix-handler.py`
- [ ] Parse user and branch coordinates
- [ ] Call Amazon Location CalculateRouteMatrix API
- [ ] Process route results and format response

### 3.2 Amazon Location Integration
```python
import boto3
from botocore.exceptions import ClientError

def calculate_route_matrix(user_coord, branch_coords):
    """
    Calculate ETAs and distances using Amazon Location
    """
    location_client = boto3.client('location')
    
    # Prepare origins (user location) and destinations (branches)
    origins = [[user_coord['lon'], user_coord['lat']]]
    destinations = [[branch['lon'], branch['lat']] for branch in branch_coords]
    
    try:
        response = location_client.calculate_route_matrix(
            CalculatorName=ROUTE_CALCULATOR_NAME,
            DeparturePositions=origins,
            DestinationPositions=destinations,
            TravelMode='Car',
            DistanceUnit='Kilometers',
            DurationUnit='Seconds'
        )
        
        # Process results
        route_matrix = []
        for i, branch in enumerate(branch_coords):
            route_result = response['RouteMatrix'][0][i]  # First origin to i-th destination
            route_matrix.append({
                'branchId': branch['branchId'],
                'durationSeconds': route_result.get('DurationSeconds'),
                'distanceKm': route_result.get('Distance'),
                'eta': format_eta(route_result.get('DurationSeconds'))
            })
        
        return route_matrix
        
    except ClientError as e:
        print(f"Route calculation error: {e}")
        return fallback_route_estimates(user_coord, branch_coords)
```

### 3.3 Error Handling and Fallbacks
- [ ] Handle Amazon Location API errors
- [ ] Implement distance-based ETA fallback
- [ ] Add retry logic for transient failures
- [ ] Log route calculation metrics

---

## Step 4: Bedrock Converse API Integration
**Duration**: 45 minutes  
**Status**: ⏳ Pending

### 4.1 Bedrock Agent Endpoint
- [ ] **File**: `lambda/bedrock-tools/chat-handler.py`
- [ ] Set up Bedrock Converse API client
- [ ] Configure tool-use enabled model
- [ ] Handle chat session management

### 4.2 Tool-Use Orchestration Logic
```python
import boto3
import json

def handle_chat_request(user_message, user_location, session_id):
    """
    Process chat request with tool-use capabilities
    """
    bedrock_client = boto3.client('bedrock-runtime')
    
    # Prepare system prompt
    system_prompt = """You are a helpful gym assistant that helps users find available gym equipment. 
    You have access to real-time gym machine availability and can calculate travel times.
    When users ask about equipment availability, use the tools to provide specific recommendations."""
    
    # Prepare conversation with user message
    messages = [
        {
            "role": "user",
            "content": [{"text": user_message}]
        }
    ]
    
    # Include user location context if available
    if user_location:
        location_context = f"User location: {user_location['lat']}, {user_location['lon']}"
        messages[0]["content"].append({"text": location_context})
    
    # Invoke Bedrock with tool configuration
    response = bedrock_client.converse(
        modelId=MODEL_ID,
        messages=messages,
        system=[{"text": system_prompt}],
        toolConfig={
            "tools": [
                {"toolSpec": load_tool_spec("getAvailabilityByCategory")},
                {"toolSpec": load_tool_spec("getRouteMatrix")}
            ]
        }
    )
    
    return process_bedrock_response(response, user_location)
```

### 4.3 Tool Execution and Response Formatting
- [ ] Parse tool use requests from Bedrock
- [ ] Execute appropriate tool functions
- [ ] Format tool results for Bedrock
- [ ] Handle multi-turn conversations

---

## Step 5: Chat Response Processing
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 5.1 Response Ranking Logic
- [ ] **File**: `lambda/bedrock-tools/ranking.py`
- [ ] Combine availability and route data
- [ ] Rank branches by ETA then free count
- [ ] Apply business rules (minimum viable options)

### 5.2 Response Formatting
```python
def format_chat_response(availability_data, route_data):
    """
    Format structured response with recommendations
    """
    # Combine availability and route data
    combined_data = []
    for branch in availability_data['branches']:
        route_info = find_route_info(route_data, branch['branchId'])
        combined_data.append({
            **branch,
            'eta': route_info['eta'],
            'duration': route_info['durationSeconds'],
            'distance': route_info['distanceKm']
        })
    
    # Sort by ETA, then by free count
    combined_data.sort(key=lambda x: (x['duration'], -x['freeCount']))
    
    # Format response
    top_pick = combined_data[0] if combined_data else None
    alternatives = combined_data[1:3] if len(combined_data) > 1 else []
    
    return {
        'topRecommendation': top_pick,
        'alternatives': alternatives,
        'totalOptionsFound': len(combined_data)
    }
```

### 5.3 Conversational Response Generation
- [ ] Generate natural language responses
- [ ] Include specific machine counts and ETAs
- [ ] Provide actionable next steps
- [ ] Handle cases with no available machines

---

## Step 6: Chat UI Implementation
**Duration**: 35 minutes  
**Status**: ⏳ Pending

### 6.1 Chat Interface Component
- [ ] **File**: `src/components/chat/ChatInterface.tsx`
- [ ] Chat message display with typing indicators
- [ ] Message input with location sharing prompt
- [ ] Structured response rendering for recommendations
- [ ] Chat history and session management

### 6.2 Message Components
- [ ] **File**: `src/components/chat/MessageBubble.tsx`
- [ ] User and assistant message bubbles
- [ ] Rich content rendering (branch cards, maps)
- [ ] Action buttons for branch navigation
- [ ] Loading states for tool execution

### 6.3 Location Integration
- [ ] **File**: `src/components/chat/LocationPrompt.tsx`
- [ ] Request geolocation permission for chat
- [ ] Manual location entry fallback
- [ ] Privacy notice and consent
- [ ] Location sharing status indicator

---

## Step 7: Error Handling and Fallbacks
**Duration**: 25 minutes  
**Status**: ⏳ Pending

### 7.1 Tool Execution Error Handling
- [ ] Handle tool timeout errors
- [ ] Graceful degradation when tools fail
- [ ] User-friendly error messages
- [ ] Fallback recommendations without tools

### 7.2 Conversation Error Recovery
- [ ] Handle Bedrock API errors
- [ ] Session recovery and continuation
- [ ] Retry logic for transient failures
- [ ] Clear error communication to users

### 7.3 Fallback Responses
- [ ] Pre-defined responses for common failures
- [ ] Manual override for service outages
- [ ] Alternative recommendation strategies
- [ ] Graceful feature degradation

---

## Step 8: Testing and Optimization
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 8.1 Tool Function Testing
- [ ] Unit tests for availability and route tools
- [ ] Integration tests with real API data
- [ ] Performance testing under load
- [ ] Tool response time optimization

### 8.2 Conversation Flow Testing
- [ ] Test common user queries and intents
- [ ] Validate tool-use decision making
- [ ] Test multi-turn conversation handling
- [ ] Error scenario testing

### 8.3 End-to-End Testing
- [ ] Full chat workflow testing
- [ ] Location-based recommendation accuracy
- [ ] UI integration and user experience
- [ ] Cross-browser chat functionality

### 8.4 Evidence Capture and Commit
```bash
git add .
git commit -m "feat: Phase 6 agentic chatbot with tool-use

- Tool schemas for getAvailabilityByCategory and getRouteMatrix
- Lambda handlers for availability queries and route calculations
- Bedrock Converse API integration with tool-use orchestration
- Chat response ranking and formatting logic
- React chat interface with location integration
- Error handling and fallback strategies
- Comprehensive testing and optimization

🤖 Generated with Amazon Q Developer
Co-Authored-By: Amazon Q Developer <noreply@aws.amazon.com>"
```

---

## Success Criteria
- [ ] Chat interface accepts user queries and responds appropriately
- [ ] Tool-use correctly calls availability and route functions
- [ ] Recommendations ranked by ETA and machine availability
- [ ] Location integration works with user permissions
- [ ] Error handling provides graceful degradation
- [ ] Response times meet 3-second P95 target
- [ ] Multi-turn conversations function correctly
- [ ] Integration with frontend navigation works

## Estimated Total Time: 3.5 hours

## Next Phase
Phase 7: Forecasting chip baseline implementation