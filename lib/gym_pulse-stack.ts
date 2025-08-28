import * as cdk from 'aws-cdk-lib';
import * as iot from 'aws-cdk-lib/aws-iot';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as apigatewayv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as location from 'aws-cdk-lib/aws-location';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

export class GymAvailabilityStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // DynamoDB Tables
    const machineStateTable = new dynamodb.Table(this, 'MachineStateTable', {
      tableName: 'gym-machine-states',
      partitionKey: { name: 'machineId', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'timestamp', type: dynamodb.AttributeType.NUMBER },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
    });

    const aggregatesTable = new dynamodb.Table(this, 'AggregatesTable', {
      tableName: 'gym-aggregates',
      partitionKey: { name: 'pk', type: dynamodb.AttributeType.STRING }, // branch#category#date
      sortKey: { name: 'sk', type: dynamodb.AttributeType.STRING }, // 15min-bin
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    const alertsTable = new dynamodb.Table(this, 'AlertsTable', {
      tableName: 'gym-alerts',
      partitionKey: { name: 'machineId', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'userId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    // IoT Core Setup
    const iotPolicy = new iot.CfnPolicy(this, 'GymDevicePolicy', {
      policyName: 'GymDevicePolicy',
      policyDocument: {
        Version: '2012-10-17',
        Statement: [
          {
            Effect: 'Allow',
            Action: ['iot:Connect'],
            Resource: `arn:aws:iot:${this.region}:${this.account}:client/gym-*`,
          },
          {
            Effect: 'Allow',
            Action: ['iot:Publish'],
            Resource: `arn:aws:iot:${this.region}:${this.account}:topic/org/*/machines/*/status`,
          },
          {
            Effect: 'Allow',
            Action: ['iot:Subscribe'],
            Resource: `arn:aws:iot:${this.region}:${this.account}:topicfilter/org/*/machines/*/status`,
          },
        ],
      },
    });

    // Lambda Functions
    const ingestLambda = new lambda.Function(this, 'IngestLambda', {
      functionName: 'gym-ingest-handler',
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'index.handler',
      code: lambda.Code.fromInline(`
import json
import boto3
import time
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
machine_table = dynamodb.Table('${machineStateTable.tableName}')
aggregates_table = dynamodb.Table('${aggregatesTable.tableName}')

def handler(event, context):
    try:
        # Parse IoT message
        topic = event['topic']
        payload = json.loads(event['payload'])
        
        machine_id = payload['machineId']
        status = payload['status']  # 'occupied' or 'free'
        timestamp = int(time.time())
        
        # Update current state
        machine_table.put_item(Item={
            'machineId': machine_id,
            'timestamp': timestamp,
            'status': status,
            'ttl': timestamp + 86400  # 24 hours TTL
        })
        
        # TODO: Update aggregates for heatmaps
        # TODO: Trigger alerts if status changed to 'free'
        
        return {'statusCode': 200}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500}
      `),
      environment: {
        MACHINE_STATE_TABLE: machineStateTable.tableName,
        AGGREGATES_TABLE: aggregatesTable.tableName,
      },
      timeout: cdk.Duration.seconds(30),
    });

    const apiLambda = new lambda.Function(this, 'ApiLambda', {
      functionName: 'gym-api-handler',
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'index.handler',
      code: lambda.Code.fromInline(`
import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
machine_table = dynamodb.Table('${machineStateTable.tableName}')

def handler(event, context):
    try:
        path = event['path']
        method = event['httpMethod']
        
        if path == '/branches' and method == 'GET':
            # Return branch list with availability counts
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps([
                    {
                        'id': 'branch-1',
                        'name': 'Central Branch',
                        'coordinates': [22.2783, 114.1747],
                        'categories': {
                            'legs': {'free': 3, 'total': 8},
                            'chest': {'free': 5, 'total': 10},
                            'back': {'free': 2, 'total': 6}
                        }
                    },
                    {
                        'id': 'branch-2', 
                        'name': 'Causeway Bay Branch',
                        'coordinates': [22.2783, 114.1830],
                        'categories': {
                            'legs': {'free': 1, 'total': 6},
                            'chest': {'free': 8, 'total': 12},
                            'back': {'free': 4, 'total': 8}
                        }
                    }
                ])
            }
        
        return {'statusCode': 404, 'body': 'Not found'}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
      `),
      environment: {
        MACHINE_STATE_TABLE: machineStateTable.tableName,
      },
      timeout: cdk.Duration.seconds(30),
    });

    // Tool functions for Bedrock Agent
    const availabilityToolLambda = new lambda.Function(this, 'AvailabilityToolLambda', {
      functionName: 'gym-availability-tool',
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'index.handler',
      code: lambda.Code.fromInline(`
import json
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def handler(event, context):
    try:
        # Parse tool input
        body = json.loads(event['body']) if 'body' in event else event
        lat = float(body['lat'])
        lon = float(body['lon']) 
        radius = float(body.get('radius', 5))  # 5km default
        category = body['category']
        
        # Mock branches data (replace with DynamoDB query)
        branches = [
            {
                'id': 'branch-1',
                'name': 'Central Branch',
                'coordinates': [22.2783, 114.1747],
                'categories': {
                    'legs': {'free': 3, 'total': 8},
                    'chest': {'free': 5, 'total': 10},
                    'back': {'free': 2, 'total': 6}
                }
            },
            {
                'id': 'branch-2',
                'name': 'Causeway Bay Branch', 
                'coordinates': [22.2783, 114.1830],
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
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'branches': sorted(results, key=lambda x: x['distance'])
            })
        }
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
      `),
      timeout: cdk.Duration.seconds(30),
    });

    const routeMatrixToolLambda = new lambda.Function(this, 'RouteMatrixToolLambda', {
      functionName: 'gym-route-matrix-tool',
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'index.handler',
      code: lambda.Code.fromInline(`
import json
import boto3

location_client = boto3.client('location')

def handler(event, context):
    try:
        body = json.loads(event['body']) if 'body' in event else event
        user_coord = body['userCoordinate']  # [lat, lon]
        branch_coords = body['branchCoordinates']  # [[lat, lon], ...]
        
        # Use Amazon Location Service to calculate route matrix
        response = location_client.calculate_route_matrix(
            CalculatorName='${this.stackName}-route-calculator',
            DeparturePositions=[user_coord],
            DestinationPositions=branch_coords,
            TravelMode='Car',
            DistanceUnit='Kilometers',
            DurationUnit='Seconds'
        )
        
        results = []
        for i, route in enumerate(response['RouteMatrix'][0]):
            if 'DurationSeconds' in route and 'DistanceKilometers' in route:
                results.append({
                    'branchIndex': i,
                    'etaMinutes': round(route['DurationSeconds'] / 60, 1),
                    'distanceKm': round(route['DistanceKilometers'], 2)
                })
        
        return {
            'statusCode': 200,
            'body': json.dumps({'routes': results})
        }
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
      `),
      timeout: cdk.Duration.seconds(30),
    });

    // Amazon Location Service
    const routeCalculator = new location.CfnRouteCalculator(this, 'RouteCalculator', {
      calculatorName: `${this.stackName}-route-calculator`,
      dataSource: 'Here',
    });

    // API Gateway
    const api = new apigateway.RestApi(this, 'GymAvailabilityApi', {
      restApiName: 'gym-availability-api',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key'],
      },
    });

    // API Routes
    const branchesResource = api.root.addResource('branches');
    branchesResource.addMethod('GET', new apigateway.LambdaIntegration(apiLambda));

    const toolsResource = api.root.addResource('tools');
    const availabilityResource = toolsResource.addResource('availability');
    availabilityResource.addMethod('POST', new apigateway.LambdaIntegration(availabilityToolLambda));
    
    const routeMatrixResource = toolsResource.addResource('route-matrix');
    routeMatrixResource.addMethod('POST', new apigateway.LambdaIntegration(routeMatrixToolLambda));

    // IoT Rule to trigger ingest Lambda
    const iotRule = new iot.CfnTopicRule(this, 'MachineStatusRule', {
      ruleName: 'GymMachineStatusRule',
      topicRulePayload: {
        sql: "SELECT * FROM 'org/+/machines/+/status'",
        actions: [
          {
            lambda: {
              functionArn: ingestLambda.functionArn,
            },
          },
        ],
      },
    });

    // Permissions
    machineStateTable.grantReadWriteData(ingestLambda);
    aggregatesTable.grantReadWriteData(ingestLambda);
    machineStateTable.grantReadData(apiLambda);
    machineStateTable.grantReadData(availabilityToolLambda);

    routeMatrixToolLambda.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['geo:CalculateRouteMatrix'],
      resources: [routeCalculator.attrArn],
    }));

    ingestLambda.addPermission('AllowIoTInvoke', {
      principal: new iam.ServicePrincipal('iot.amazonaws.com'),
      sourceArn: iotRule.attrArn,
    });

    // WebSocket API for real-time updates (placeholder)
    // TODO: Implement WebSocket API Gateway V2 for live machine status updates
    // - Connection management Lambda
    // - Broadcast Lambda for real-time notifications
    // - Connection store in DynamoDB

    // Bedrock Agent Configuration (placeholder)
    // TODO: Configure Bedrock Agent with Converse API
    // - Knowledge base for tool schemas
    // - Agent with tool-use capabilities
    // - Integration with availability and route-matrix tools
    const bedrockAgentRole = new iam.Role(this, 'BedrockAgentRole', {
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonBedrockFullAccess')
      ],
      inlinePolicies: {
        'LambdaInvokePolicy': new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: ['lambda:InvokeFunction'],
              resources: [
                availabilityToolLambda.functionArn,
                routeMatrixToolLambda.functionArn
              ]
            })
          ]
        })
      }
    });

    // Add Bedrock permissions to tool Lambdas
    availabilityToolLambda.grantInvoke(new iam.ServicePrincipal('bedrock.amazonaws.com'));
    routeMatrixToolLambda.grantInvoke(new iam.ServicePrincipal('bedrock.amazonaws.com'));

    // Outputs
    new cdk.CfnOutput(this, 'ApiGatewayUrl', {
      value: api.url,
      description: 'API Gateway endpoint URL',
    });

    new cdk.CfnOutput(this, 'MachineStateTableName', {
      value: machineStateTable.tableName,
      description: 'DynamoDB table for machine states',
    });

    new cdk.CfnOutput(this, 'RouteCalculatorName', {
      value: routeCalculator.calculatorName,
      description: 'Amazon Location Route Calculator name',
    });
  }
}