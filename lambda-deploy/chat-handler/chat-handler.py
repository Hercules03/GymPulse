"""
Bedrock Chat Handler: Orchestrates tool-use conversations
Integrates with getAvailabilityByCategory and getRouteMatrix tools
"""
import json
import boto3
import os
from botocore.exceptions import ClientError


# Initialize Bedrock client - use us-east-1 since Bedrock not available in ap-east-1
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
lambda_client = boto3.client('lambda')

# Model configuration
MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')

# Tool function ARNs
AVAILABILITY_FUNCTION_ARN = os.environ['AVAILABILITY_FUNCTION_ARN']
ROUTE_MATRIX_FUNCTION_ARN = os.environ['ROUTE_MATRIX_FUNCTION_ARN']


def lambda_handler(event, context):
    """
    Handle chat requests with Bedrock Converse API and tool-use
    """
    try:
        # Parse request
        if isinstance(event, dict) and 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
            
        user_message = body['message']
        user_location = body.get('location')  # {lat, lon}
        session_id = body.get('sessionId', 'default')
        
        print(f"Chat request: '{user_message}' with location: {user_location}")
        
        # Build conversation with system prompt
        system_prompt = """You are a helpful gym assistant that helps users find available gym equipment. 
        You have access to real-time gym machine availability and can calculate travel times.
        When users ask about equipment availability, use your tools to provide specific recommendations.
        
        Always be enthusiastic and helpful. Include machine counts, travel times, and actionable next steps in your responses."""
        
        messages = []
        
        # Include location context if available
        if user_location:
            location_context = f"User is currently at coordinates: {user_location['lat']}, {user_location['lon']}"
            messages.append({
                "role": "user",
                "content": [{"text": f"{location_context}\\n{user_message}"}]
            })
        else:
            messages.append({
                "role": "user", 
                "content": [{"text": user_message}]
            })
        
        # Load tool specifications
        tool_specs = [
            load_availability_tool_spec(),
            load_route_matrix_tool_spec()
        ]
        
        # Make initial Bedrock call with tools
        response = bedrock_runtime.converse(
            modelId=MODEL_ID,
            messages=messages,
            system=[{"text": system_prompt}],
            toolConfig={
                "tools": tool_specs
            },
            inferenceConfig={
                "temperature": 0.1,
                "maxTokens": 1000
            }
        )
        
        # Process response and handle tool use
        output_message = response['output']['message']
        
        if output_message.get('content'):
            # Check if Bedrock wants to use tools
            tool_use_blocks = [
                block for block in output_message['content'] 
                if block.get('toolUse')
            ]
            
            if tool_use_blocks:
                # Execute tool requests
                tool_results = []
                for tool_block in tool_use_blocks:
                    tool_use = tool_block['toolUse']
                    tool_result = execute_tool(tool_use)
                    tool_results.append({
                        "toolResult": {
                            "toolUseId": tool_use['toolUseId'],
                            "content": [{"text": json.dumps(tool_result)}]
                        }
                    })
                
                # Continue conversation with tool results
                messages.append(output_message)
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
                
                # Get final response with tool results
                final_response = bedrock_runtime.converse(
                    modelId=MODEL_ID,
                    messages=messages,
                    system=[{"text": system_prompt}],
                    toolConfig={
                        "tools": tool_specs
                    },
                    inferenceConfig={
                        "temperature": 0.1,
                        "maxTokens": 1000
                    }
                )
                
                final_message = final_response['output']['message']
                response_text = extract_text_from_message(final_message)
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'response': response_text,
                        'toolsUsed': [tool['toolUse']['name'] for tool in tool_use_blocks],
                        'sessionId': session_id
                    })
                }
            else:
                # Direct response without tools
                response_text = extract_text_from_message(output_message)
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'response': response_text,
                        'toolsUsed': [],
                        'sessionId': session_id
                    })
                }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'No response from Bedrock'})
            }
            
    except Exception as e:
        print(f"Chat handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def execute_tool(tool_use):
    """
    Execute a tool function and return results
    """
    tool_name = tool_use['name']
    tool_input = tool_use['input']
    
    print(f"Executing tool: {tool_name} with input: {tool_input}")
    
    try:
        if tool_name == 'getAvailabilityByCategory':
            # Invoke availability function
            response = lambda_client.invoke(
                FunctionName=AVAILABILITY_FUNCTION_ARN,
                InvocationType='RequestResponse',
                Payload=json.dumps(tool_input)
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                return json.loads(result['body'])
            else:
                return {'error': 'Availability tool failed', 'details': result}
                
        elif tool_name == 'getRouteMatrix':
            # Invoke route matrix function
            response = lambda_client.invoke(
                FunctionName=ROUTE_MATRIX_FUNCTION_ARN,
                InvocationType='RequestResponse', 
                Payload=json.dumps(tool_input)
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                return json.loads(result['body'])
            else:
                return {'error': 'Route matrix tool failed', 'details': result}
        else:
            return {'error': f'Unknown tool: {tool_name}'}
            
    except Exception as e:
        print(f"Tool execution error for {tool_name}: {str(e)}")
        return {'error': f'Tool execution failed: {str(e)}'}


def extract_text_from_message(message):
    """
    Extract text content from Bedrock message
    """
    text_parts = []
    for content_block in message.get('content', []):
        if content_block.get('text'):
            text_parts.append(content_block['text'])
    return ' '.join(text_parts)


def load_availability_tool_spec():
    """
    Load availability tool specification
    """
    return {
        "toolSpec": {
            "name": "getAvailabilityByCategory",
            "description": "Get gym machine availability by category near user location",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "lat": {"type": "number", "description": "User latitude"},
                        "lon": {"type": "number", "description": "User longitude"},
                        "radius": {"type": "number", "description": "Search radius in kilometers", "default": 10},
                        "category": {"type": "string", "enum": ["legs", "chest", "back"], "description": "Equipment category"}
                    },
                    "required": ["lat", "lon", "category"]
                }
            }
        }
    }


def load_route_matrix_tool_spec():
    """
    Load route matrix tool specification
    """
    return {
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
                            },
                            "required": ["lat", "lon"]
                        },
                        "branchCoords": {
                            "type": "array",
                            "items": {
                                "type": "object", 
                                "properties": {
                                    "branchId": {"type": "string"},
                                    "lat": {"type": "number"},
                                    "lon": {"type": "number"}
                                },
                                "required": ["branchId", "lat", "lon"]
                            }
                        }
                    },
                    "required": ["userCoord", "branchCoords"]
                }
            }
        }
    }