"""
GymPulse CDK Stack - Python Implementation
Real-time gym equipment availability with IoT integration and AI chatbot
"""
from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_apigatewayv2 as apigatewayv2,
    aws_iot as iot,
    aws_iam as iam,
    aws_location as location,
)
from constructs import Construct


class GymPulseStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ========================================
        # DynamoDB Tables
        # ========================================
        
        # Current state table for real-time machine status
        current_state_table = dynamodb.Table(
            self, "CurrentStateTable",
            table_name="gym-pulse-current-state",
            partition_key=dynamodb.Attribute(
                name="machineId", 
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )

        # Time-series events table for historical tracking
        events_table = dynamodb.Table(
            self, "EventsTable",
            table_name="gym-pulse-events",
            partition_key=dynamodb.Attribute(
                name="machineId", 
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", 
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
        )

        # Aggregates table for analytics and heatmaps
        aggregates_table = dynamodb.Table(
            self, "AggregatesTable",
            table_name="gym-pulse-aggregates",
            partition_key=dynamodb.Attribute(
                name="gymId_category", 
                type=dynamodb.AttributeType.STRING
            ),  # format: "hk-central#legs"
            sort_key=dynamodb.Attribute(
                name="timestamp15min", 
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
        )

        # Alerts table for user notifications
        alerts_table = dynamodb.Table(
            self, "AlertsTable",
            table_name="gym-pulse-alerts",
            partition_key=dynamodb.Attribute(
                name="userId", 
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="machineId", 
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )
        
        # Add GSI to alerts table
        alerts_table.add_global_secondary_index(
            index_name="machineId-index",
            partition_key=dynamodb.Attribute(
                name="machineId",
                type=dynamodb.AttributeType.STRING
            ),
        )

        # ========================================
        # IoT Core Infrastructure
        # ========================================
        
        # IoT device policy for MQTT publishing
        iot_policy = iot.CfnPolicy(
            self, "GymDevicePolicy",
            policy_name="GymDevicePolicy",
            policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["iot:Connect"],
                        "Resource": f"arn:aws:iot:{self.region}:{self.account}:client/gym-*",
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["iot:Publish"],
                        "Resource": f"arn:aws:iot:{self.region}:{self.account}:topic/org/*/machines/*/status",
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["iot:UpdateThingShadow"],
                        "Resource": f"arn:aws:iot:{self.region}:{self.account}:thing/*",
                    },
                ],
            },
        )

        # ========================================
        # Lambda Functions
        # ========================================
        
        # IoT message ingest and processing
        ingest_lambda = _lambda.Function(
            self, "IngestLambda",
            function_name="gym-pulse-iot-ingest",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda/iot-ingest"),
            environment={
                "CURRENT_STATE_TABLE": current_state_table.table_name,
                "EVENTS_TABLE": events_table.table_name,
                "AGGREGATES_TABLE": aggregates_table.table_name,
                "ALERTS_TABLE": alerts_table.table_name,
            },
            timeout=Duration.seconds(30),
            memory_size=256,
        )

        # API handler for REST endpoints
        api_lambda = _lambda.Function(
            self, "ApiLambda",
            function_name="gym-pulse-api-handler",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda/api-handlers"),
            environment={
                "CURRENT_STATE_TABLE": current_state_table.table_name,
                "EVENTS_TABLE": events_table.table_name,
                "AGGREGATES_TABLE": aggregates_table.table_name,
                "ALERTS_TABLE": alerts_table.table_name,
            },
            timeout=Duration.seconds(30),
            memory_size=512,
        )

        # WebSocket connection handler
        websocket_connect_lambda = _lambda.Function(
            self, "WebSocketConnectLambda",
            function_name="gym-pulse-websocket-connect",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="connect.lambda_handler",
            code=_lambda.Code.from_asset("lambda/websocket-handlers"),
            timeout=Duration.seconds(30),
        )

        # WebSocket disconnect handler
        websocket_disconnect_lambda = _lambda.Function(
            self, "WebSocketDisconnectLambda",
            function_name="gym-pulse-websocket-disconnect",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="disconnect.lambda_handler",
            code=_lambda.Code.from_asset("lambda/websocket-handlers"),
            timeout=Duration.seconds(30),
        )

        # Bedrock tool: getAvailabilityByCategory
        availability_tool_lambda = _lambda.Function(
            self, "AvailabilityToolLambda",
            function_name="gym-pulse-availability-tool",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="availability.lambda_handler",
            code=_lambda.Code.from_asset("lambda/bedrock-tools"),
            environment={
                "CURRENT_STATE_TABLE": current_state_table.table_name,
                "AGGREGATES_TABLE": aggregates_table.table_name,
            },
            timeout=Duration.seconds(30),
        )

        # Bedrock tool: getRouteMatrix
        route_matrix_tool_lambda = _lambda.Function(
            self, "RouteMatrixToolLambda",
            function_name="gym-pulse-route-matrix-tool",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="route_matrix.lambda_handler",
            code=_lambda.Code.from_asset("lambda/bedrock-tools"),
            environment={
                "ROUTE_CALCULATOR_NAME": "gym-pulse-route-calculator",
            },
            timeout=Duration.seconds(30),
        )

        # ========================================
        # Amazon Location Service
        # ========================================
        
        # Route calculator for ETA computation
        route_calculator = location.CfnRouteCalculator(
            self, "RouteCalculator",
            calculator_name="gym-pulse-route-calculator",
            data_source="Here",  # Using HERE as data provider
        )

        # ========================================
        # API Gateway Setup
        # ========================================
        
        # REST API
        api = apigateway.RestApi(
            self, "GymPulseApi",
            rest_api_name="gym-pulse-api",
            description="GymPulse Real-time Gym Availability API",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"],
            ),
        )

        # WebSocket API for real-time updates  
        websocket_api = apigatewayv2.WebSocketApi(
            self, "GymPulseWebSocketApi",
            route_selection_expression="$request.body.action",
        )

        # ========================================
        # API Routes
        # ========================================
        
        # REST API routes
        branches_resource = api.root.add_resource("branches")
        branches_resource.add_method("GET", apigateway.LambdaIntegration(api_lambda))
        
        branch_resource = branches_resource.add_resource("{id}")
        categories_resource = branch_resource.add_resource("categories")
        category_resource = categories_resource.add_resource("{category}")
        machines_resource = category_resource.add_resource("machines")
        machines_resource.add_method("GET", apigateway.LambdaIntegration(api_lambda))
        
        machines_root = api.root.add_resource("machines")
        machine_resource = machines_root.add_resource("{id}")
        history_resource = machine_resource.add_resource("history")
        history_resource.add_method("GET", apigateway.LambdaIntegration(api_lambda))
        
        alerts_resource = api.root.add_resource("alerts")
        alerts_resource.add_method("POST", apigateway.LambdaIntegration(api_lambda))

        # WebSocket routes (simplified for initial deployment)
        # TODO: Add WebSocket integrations in Phase 4
        websocket_stage = apigatewayv2.WebSocketStage(
            self, "WebSocketStage",
            web_socket_api=websocket_api,
            stage_name="prod",
            auto_deploy=True
        )

        # ========================================
        # IoT Rule for Lambda Trigger
        # ========================================
        
        iot_rule = iot.CfnTopicRule(
            self, "MachineStatusRule",
            rule_name="GymPulseMachineStatusRule",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                sql="SELECT *, topic() as topic FROM 'org/+/machines/+/status'",
                actions=[
                    iot.CfnTopicRule.ActionProperty(
                        lambda_=iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=ingest_lambda.function_arn,
                        ),
                    ),
                ],
                error_action=iot.CfnTopicRule.ActionProperty(
                    republish=iot.CfnTopicRule.RepublishActionProperty(
                        role_arn="arn:aws:iam::123456789012:role/iot-error-role",
                        topic="error/gym-pulse"
                    )
                )
            ),
        )

        # ========================================
        # IAM Permissions
        # ========================================
        
        # DynamoDB permissions
        current_state_table.grant_read_write_data(ingest_lambda)
        events_table.grant_read_write_data(ingest_lambda)
        aggregates_table.grant_read_write_data(ingest_lambda)
        alerts_table.grant_read_write_data(ingest_lambda)
        
        current_state_table.grant_read_data(api_lambda)
        events_table.grant_read_data(api_lambda)
        aggregates_table.grant_read_data(api_lambda)
        alerts_table.grant_read_write_data(api_lambda)
        
        current_state_table.grant_read_data(availability_tool_lambda)
        aggregates_table.grant_read_data(availability_tool_lambda)

        # IoT Core permissions
        ingest_lambda.add_permission(
            "AllowIoTInvoke",
            principal=iam.ServicePrincipal("iot.amazonaws.com"),
            source_arn=iot_rule.attr_arn,
        )

        # Location Service permissions
        route_matrix_tool_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["geo:CalculateRouteMatrix"],
                resources=[route_calculator.attr_arn]
            )
        )

        # Bedrock agent role for tool invocation
        bedrock_agent_role = iam.Role(
            self, "BedrockAgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            inline_policies={
                "LambdaInvokePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction"],
                            resources=[
                                availability_tool_lambda.function_arn,
                                route_matrix_tool_lambda.function_arn
                            ]
                        )
                    ]
                )
            }
        )

        # Grant Bedrock permission to invoke tool Lambdas
        availability_tool_lambda.grant_invoke(iam.ServicePrincipal("bedrock.amazonaws.com"))
        route_matrix_tool_lambda.grant_invoke(iam.ServicePrincipal("bedrock.amazonaws.com"))

        # ========================================
        # CloudFormation Outputs
        # ========================================
        
        CfnOutput(
            self, "ApiGatewayUrl",
            value=api.url,
            description="REST API Gateway endpoint URL",
        )

        CfnOutput(
            self, "WebSocketApiUrl", 
            value=f"wss://{websocket_api.api_id}.execute-api.{self.region}.amazonaws.com/{websocket_stage.stage_name}",
            description="WebSocket API endpoint URL",
        )

        CfnOutput(
            self, "CurrentStateTableName",
            value=current_state_table.table_name,
            description="DynamoDB table for current machine states",
        )

        CfnOutput(
            self, "EventsTableName",
            value=events_table.table_name,
            description="DynamoDB table for time-series events",
        )

        CfnOutput(
            self, "AvailabilityToolArn",
            value=availability_tool_lambda.function_arn,
            description="Availability tool Lambda ARN for Bedrock agent",
        )

        CfnOutput(
            self, "RouteMatrixToolArn",
            value=route_matrix_tool_lambda.function_arn,
            description="Route matrix tool Lambda ARN for Bedrock agent",
        )

        CfnOutput(
            self, "RouteCalculatorName",
            value=route_calculator.calculator_name,
            description="Amazon Location Route Calculator name",
        )
