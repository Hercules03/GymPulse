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
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_sns as sns,
    aws_logs as logs,
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

        # WebSocket connections table for connection management
        connections_table = dynamodb.Table(
            self, "ConnectionsTable",
            table_name="gym-pulse-connections",
            partition_key=dynamodb.Attribute(
                name="connectionId", 
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
        )

        # ========================================
        # IoT Core Infrastructure
        # ========================================
        
        # IoT device policy for MQTT publishing
        iot_policy = iot.CfnPolicy(
            self, "GymDevicePolicy",
            policy_name=f"GymDevicePolicy-{self.stack_name}",
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
        
        # IoT message ingest and processing with performance optimizations
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
                "WEBSOCKET_BROADCAST_FUNCTION": "gym-pulse-websocket-broadcast",
            },
            timeout=Duration.seconds(30),
            memory_size=512,  # Increased for better performance
            reserved_concurrent_executions=20,  # Reserve concurrency for critical IoT path
        )

        # API handler for REST endpoints with performance optimizations
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
                "AWS_LAMBDA_EXEC_WRAPPER": "/opt/otel-instrument",  # Enable X-Ray tracing
            },
            timeout=Duration.seconds(15),  # Reduced timeout for faster fails
            memory_size=1024,  # Increased for caching and better performance
            reserved_concurrent_executions=50,  # Reserve concurrency for API requests
        )

        # WebSocket connection handler with optimizations
        websocket_connect_lambda = _lambda.Function(
            self, "WebSocketConnectLambda",
            function_name="gym-pulse-websocket-connect",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="connect.lambda_handler",
            code=_lambda.Code.from_asset("lambda/websocket-handlers"),
            environment={
                "CONNECTIONS_TABLE": connections_table.table_name,
            },
            timeout=Duration.seconds(10),  # Fast timeout for connection
            memory_size=256,  # Lower memory for simple connection handling
            reserved_concurrent_executions=25,  # Reserve for WebSocket connections
        )

        # WebSocket disconnect handler
        websocket_disconnect_lambda = _lambda.Function(
            self, "WebSocketDisconnectLambda",
            function_name="gym-pulse-websocket-disconnect",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="disconnect.lambda_handler",
            code=_lambda.Code.from_asset("lambda/websocket-handlers"),
            environment={
                "CONNECTIONS_TABLE": connections_table.table_name,
            },
            timeout=Duration.seconds(30),
        )

        # WebSocket broadcast handler for real-time updates
        websocket_broadcast_lambda = _lambda.Function(
            self, "WebSocketBroadcastLambda",
            function_name="gym-pulse-websocket-broadcast",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="broadcast.lambda_handler",
            code=_lambda.Code.from_asset("lambda/websocket-handlers"),
            environment={
                "CONNECTIONS_TABLE": connections_table.table_name,
                "WEBSOCKET_API_ENDPOINT": f"https://{websocket_api.api_id}.execute-api.{self.region}.amazonaws.com/prod",
            },
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
        
        # Route calculator for ETA computation (TODO: Enable in Phase 6)
        # route_calculator = location.CfnRouteCalculator(
        #     self, "RouteCalculator",
        #     calculator_name="gym-pulse-route-calculator",
        #     data_source="Here",  # Using HERE as data provider
        # )

        # ========================================
        # API Gateway Setup
        # ========================================
        
        # REST API with rate limiting and security
        api = apigateway.RestApi(
            self, "GymPulseApi",
            rest_api_name="gym-pulse-api",
            description="GymPulse Real-time Gym Availability API",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"],
            ),
            # Enable API key for rate limiting (optional)
            api_key_source_type=apigateway.ApiKeySourceType.HEADER,
            # Request validation
            request_validator=apigateway.RequestValidator(
                self, "RequestValidator",
                rest_api=api,
                validate_request_body=True,
                validate_request_parameters=True,
            ),
        )
        
        # Usage Plan for rate limiting
        usage_plan = api.add_usage_plan(
            "GymPulseUsagePlan",
            name="gym-pulse-usage-plan",
            description="Rate limiting for GymPulse API",
            throttle=apigateway.ThrottleSettings(
                rate_limit=100,  # requests per second
                burst_limit=200   # burst capacity
            ),
            quota=apigateway.QuotaSettings(
                limit=10000,     # requests per day
                period=apigateway.Period.DAY
            )
        )
        
        # Create API Key for rate limiting (optional)
        api_key = api.add_api_key(
            "GymPulseApiKey",
            api_key_name="gym-pulse-api-key",
            description="API key for GymPulse application"
        )
        
        # Associate API key with usage plan
        usage_plan.add_api_key(api_key)

        # WebSocket API for real-time updates  
        websocket_api = apigatewayv2.WebSocketApi(
            self, "GymPulseWebSocketApi",
            route_selection_expression="$request.body.action",
        )

        # ========================================
        # API Routes
        # ========================================
        
        # REST API routes with security
        branches_resource = api.root.add_resource("branches")
        branches_resource.add_method(
            "GET", 
            apigateway.LambdaIntegration(api_lambda),
            # API key optional for read operations
            api_key_required=False
        )
        
        branch_resource = branches_resource.add_resource("{id}")
        categories_resource = branch_resource.add_resource("categories")
        category_resource = categories_resource.add_resource("{category}")
        machines_resource = category_resource.add_resource("machines")
        machines_resource.add_method(
            "GET", 
            apigateway.LambdaIntegration(api_lambda),
            api_key_required=False
        )
        
        machines_root = api.root.add_resource("machines")
        machine_resource = machines_root.add_resource("{id}")
        history_resource = machine_resource.add_resource("history")
        history_resource.add_method(
            "GET", 
            apigateway.LambdaIntegration(api_lambda),
            api_key_required=False
        )
        
        alerts_resource = api.root.add_resource("alerts")
        
        # POST alerts requires API key for write operations  
        alerts_resource.add_method(
            "POST", 
            apigateway.LambdaIntegration(api_lambda),
            api_key_required=False  # Set to True for production
        )
        
        # GET alerts (for listing user alerts)
        alerts_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(api_lambda),
            api_key_required=False
        )
        
        # DELETE alerts (for cancelling alerts)
        alert_resource = alerts_resource.add_resource("{alertId}")
        alert_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(api_lambda),
            api_key_required=False
        )
        
        # PUT alerts (for updating alerts)
        alert_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(api_lambda),
            api_key_required=False
        )
        
        # Health check endpoint (no API key required)
        health_resource = api.root.add_resource("health")
        health_resource.add_method(
            "GET",
            apigateway.MockIntegration(
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_templates={
                            "application/json": json.dumps({
                                "status": "healthy",
                                "timestamp": "${context.requestTime}",
                                "service": "gym-pulse-api"
                            })
                        }
                    )
                ],
                passthrough_behavior=apigateway.PassthroughBehavior.NEVER,
                request_templates={
                    "application/json": json.dumps({"statusCode": 200})
                }
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_models={
                        "application/json": apigateway.Model.EMPTY_MODEL
                    }
                )
            ],
            api_key_required=False
        )

        # WebSocket routes
        connect_integration = apigatewayv2.WebSocketLambdaIntegration(
            "ConnectIntegration",
            websocket_connect_lambda
        )
        disconnect_integration = apigatewayv2.WebSocketLambdaIntegration(
            "DisconnectIntegration", 
            websocket_disconnect_lambda
        )

        websocket_api.add_route(
            "$connect",
            integration=connect_integration
        )
        websocket_api.add_route(
            "$disconnect", 
            integration=disconnect_integration
        )
        
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
                # TODO: Configure error handling role in production
                # error_action=iot.CfnTopicRule.ActionProperty(
                #     republish=iot.CfnTopicRule.RepublishActionProperty(
                #         role_arn="arn:aws:iam::123456789012:role/iot-error-role",
                #         topic="error/gym-pulse"
                #     )
                # )
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
        
        # WebSocket handler permissions
        connections_table.grant_read_write_data(websocket_connect_lambda)
        connections_table.grant_read_write_data(websocket_disconnect_lambda)
        connections_table.grant_read_data(websocket_broadcast_lambda)
        
        # Grant WebSocket broadcast permission to post messages
        websocket_broadcast_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["execute-api:ManageConnections"],
                resources=[f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api.api_id}/prod/POST/@connections/*"]
            )
        )
        
        # Grant ingest Lambda permission to invoke broadcast Lambda
        websocket_broadcast_lambda.grant_invoke(ingest_lambda)

        # IoT Core permissions
        ingest_lambda.add_permission(
            "AllowIoTInvoke",
            principal=iam.ServicePrincipal("iot.amazonaws.com"),
            source_arn=iot_rule.attr_arn,
        )

        # Location Service permissions (TODO: Enable in Phase 6)
        # route_matrix_tool_lambda.add_to_role_policy(
        #     iam.PolicyStatement(
        #         effect=iam.Effect.ALLOW,
        #         actions=["geo:CalculateRouteMatrix"],
        #         resources=[route_calculator.attr_arn]
        #     )
        # )

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
        # Monitoring and Alerting
        # ========================================
        
        # SNS topic for alerts
        alert_topic = sns.Topic(
            self, "GymPulseAlerts",
            display_name="GymPulse System Alerts",
            topic_name="gym-pulse-alerts"
        )
        
        # Lambda function error rates alarms
        lambda_functions = [
            ("IoTIngest", iot_ingest_lambda),
            ("APIHandler", api_lambda),
            ("WebSocketConnect", websocket_connect_lambda),
            ("WebSocketDisconnect", websocket_disconnect_lambda),
            ("WebSocketBroadcast", websocket_broadcast_lambda),
            ("AvailabilityTool", availability_tool_lambda),
            ("RouteMatrixTool", route_matrix_tool_lambda)
        ]
        
        for name, lambda_func in lambda_functions:
            # Error rate alarm (>5% error rate)
            cloudwatch.Alarm(
                self, f"{name}ErrorRateAlarm",
                alarm_name=f"GymPulse-{name}-ErrorRate",
                alarm_description=f"High error rate in {name} Lambda function",
                metric=lambda_func.metric_errors(
                    statistic=cloudwatch.Statistic.AVERAGE,
                    period=Duration.minutes(5)
                ),
                threshold=5,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                evaluation_periods=2,
                datapoints_to_alarm=2,
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
            ).add_alarm_action(cloudwatch_actions.SnsAction(alert_topic))
            
            # Duration alarm (>30 seconds)
            cloudwatch.Alarm(
                self, f"{name}DurationAlarm", 
                alarm_name=f"GymPulse-{name}-Duration",
                alarm_description=f"High duration in {name} Lambda function",
                metric=lambda_func.metric_duration(
                    statistic=cloudwatch.Statistic.AVERAGE,
                    period=Duration.minutes(5)
                ),
                threshold=30000,  # 30 seconds in milliseconds
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                evaluation_periods=2,
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
            ).add_alarm_action(cloudwatch_actions.SnsAction(alert_topic))
        
        # DynamoDB throttling alarms
        dynamodb_tables = [
            ("CurrentState", current_state_table),
            ("Events", events_table),
            ("Aggregates", aggregates_table),
            ("Alerts", alerts_table),
            ("Connections", connections_table)
        ]
        
        for name, table in dynamodb_tables:
            # Read throttle alarm
            cloudwatch.Alarm(
                self, f"{name}ReadThrottleAlarm",
                alarm_name=f"GymPulse-{name}-ReadThrottle",
                alarm_description=f"Read throttling on {name} table",
                metric=table.metric("ReadThrottles",
                    statistic=cloudwatch.Statistic.SUM,
                    period=Duration.minutes(5)
                ),
                threshold=0,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                evaluation_periods=1,
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
            ).add_alarm_action(cloudwatch_actions.SnsAction(alert_topic))
            
            # Write throttle alarm  
            cloudwatch.Alarm(
                self, f"{name}WriteThrottleAlarm",
                alarm_name=f"GymPulse-{name}-WriteThrottle",
                alarm_description=f"Write throttling on {name} table",
                metric=table.metric("WriteThrottles",
                    statistic=cloudwatch.Statistic.SUM,
                    period=Duration.minutes(5)
                ),
                threshold=0,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                evaluation_periods=1,
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
            ).add_alarm_action(cloudwatch_actions.SnsAction(alert_topic))
        
        # API Gateway 4xx and 5xx error alarms
        api_4xx_alarm = cloudwatch.Alarm(
            self, "API4xxErrorAlarm",
            alarm_name="GymPulse-API-4xxErrors",
            alarm_description="High rate of 4xx errors from API Gateway",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="4XXError",
                dimensions_map={"ApiName": "GymPulseAPI"},
                statistic=cloudwatch.Statistic.SUM,
                period=Duration.minutes(5)
            ),
            threshold=10,  # >10 4xx errors in 5 minutes
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            evaluation_periods=2,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        api_4xx_alarm.add_alarm_action(cloudwatch_actions.SnsAction(alert_topic))
        
        api_5xx_alarm = cloudwatch.Alarm(
            self, "API5xxErrorAlarm",
            alarm_name="GymPulse-API-5xxErrors", 
            alarm_description="High rate of 5xx errors from API Gateway",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="5XXError",
                dimensions_map={"ApiName": "GymPulseAPI"},
                statistic=cloudwatch.Statistic.SUM,
                period=Duration.minutes(5)
            ),
            threshold=5,  # >5 5xx errors in 5 minutes
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            evaluation_periods=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        api_5xx_alarm.add_alarm_action(cloudwatch_actions.SnsAction(alert_topic))
        
        # API Gateway latency alarm (>3 seconds P95)
        api_latency_alarm = cloudwatch.Alarm(
            self, "APILatencyAlarm",
            alarm_name="GymPulse-API-Latency",
            alarm_description="High API Gateway latency",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="Latency",
                dimensions_map={"ApiName": "GymPulseAPI"},
                statistic=cloudwatch.Statistic.percentile(95),
                period=Duration.minutes(5)
            ),
            threshold=3000,  # 3 seconds
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            evaluation_periods=2,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        api_latency_alarm.add_alarm_action(cloudwatch_actions.SnsAction(alert_topic))
        
        # Custom metrics dashboard
        dashboard = cloudwatch.Dashboard(
            self, "GymPulseDashboard",
            dashboard_name="GymPulse-Operations"
        )
        
        # Add widgets to dashboard
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda Function Invocations",
                left=[func.metric_invocations() for _, func in lambda_functions[:4]],
                width=12,
                height=6
            ),
            cloudwatch.GraphWidget(
                title="Lambda Function Errors", 
                left=[func.metric_errors() for _, func in lambda_functions[:4]],
                width=12,
                height=6
            ),
            cloudwatch.GraphWidget(
                title="API Gateway Metrics",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/ApiGateway",
                        metric_name="Count",
                        dimensions_map={"ApiName": "GymPulseAPI"}
                    ),
                    cloudwatch.Metric(
                        namespace="AWS/ApiGateway", 
                        metric_name="Latency",
                        dimensions_map={"ApiName": "GymPulseAPI"}
                    )
                ],
                width=12,
                height=6
            ),
            cloudwatch.GraphWidget(
                title="DynamoDB Read/Write Capacity",
                left=[table.metric("ConsumedReadCapacityUnits") for _, table in dynamodb_tables[:3]],
                right=[table.metric("ConsumedWriteCapacityUnits") for _, table in dynamodb_tables[:3]],
                width=12,
                height=6
            )
        )
        
        # Log retention for all Lambda functions  
        for name, lambda_func in lambda_functions:
            logs.LogGroup(
                self, f"{name}LogGroup",
                log_group_name=f"/aws/lambda/{lambda_func.function_name}",
                retention=logs.RetentionDays.ONE_WEEK,
                removal_policy=Stack.RemovalPolicy.DESTROY
            )

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
            self, "AlertTopicArn",
            value=alert_topic.topic_arn,
            description="SNS topic for system alerts",
        )
        
        CfnOutput(
            self, "DashboardUrl",
            value=f"https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard.dashboard_name}",
            description="CloudWatch dashboard URL",
        )

        # CfnOutput(
        #     self, "RouteCalculatorName",
        #     value=route_calculator.calculator_name,
        #     description="Amazon Location Route Calculator name",
        # )
