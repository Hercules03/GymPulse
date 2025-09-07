"""
IAM Security Stack - Least-Privilege Access Control
Implements comprehensive IAM security for Bedrock, Location Service, and DynamoDB
"""
import json
from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_kms as kms,
    aws_lambda as _lambda,
)
from constructs import Construct


class IAMSecurityStack(Construct):
    """IAM Security implementation with least-privilege principles"""
    
    def __init__(self, scope: Construct, construct_id: str, 
                 current_state_table, events_table, aggregates_table, alerts_table, **kwargs) -> None:
        super().__init__(scope, construct_id)
        
        self.current_state_table = current_state_table
        self.events_table = events_table
        self.aggregates_table = aggregates_table
        self.alerts_table = alerts_table
        
        # Create encryption keys
        self.setup_encryption_keys()
        
        # Create service-specific roles
        self.create_bedrock_roles()
        self.create_location_service_roles()
        self.create_lambda_execution_roles()
        self.create_iot_service_roles()
        
        # Configure DynamoDB security
        self.configure_dynamodb_security()
        
        # Set up access monitoring
        self.setup_access_monitoring()
    
    def setup_encryption_keys(self):
        """Create KMS keys for encryption at rest"""
        
        # Create key for DynamoDB encryption
        self.dynamodb_key = kms.Key(
            self, "DynamoDBEncryptionKey",
            description="KMS key for DynamoDB table encryption",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY  # For demo only
        )
        
        # Create key for Lambda environment variables
        self.lambda_key = kms.Key(
            self, "LambdaEncryptionKey",
            description="KMS key for Lambda environment variables",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY  # For demo only
        )
        
        # Add key aliases for easier management
        kms.Alias(
            self, "DynamoDBKeyAlias",
            alias_name="alias/gym-pulse-dynamodb",
            target_key=self.dynamodb_key
        )
        
        kms.Alias(
            self, "LambdaKeyAlias",
            alias_name="alias/gym-pulse-lambda",
            target_key=self.lambda_key
        )
    
    def create_bedrock_roles(self):
        """Create least-privilege roles for Bedrock access"""
        
        # Role for Bedrock inference (chat handler)
        self.bedrock_inference_role = iam.Role(
            self, "BedrockInferenceRole",
            role_name="GymPulse-Bedrock-Inference-Role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Least-privilege role for Bedrock model inference",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Add specific Bedrock permissions
        self.bedrock_inference_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                resources=[
                    # Only allow specific models (Claude, etc.)
                    "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
                    "arn:aws:bedrock:*::foundation-model/amazon.titan-*"
                ],
                conditions={
                    "StringEquals": {
                        "bedrock:ModelId": [
                            "anthropic.claude-3-sonnet-20240229-v1:0",
                            "anthropic.claude-3-haiku-20240307-v1:0"
                        ]
                    }
                }
            )
        )
        
        # Add CloudWatch Logs permissions
        self.bedrock_inference_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[
                    "arn:aws:logs:*:*:log-group:/aws/lambda/gym-pulse-*"
                ]
            )
        )
    
    def create_location_service_roles(self):
        """Create roles for Amazon Location Service"""
        
        # Role for location calculations (route matrix)
        self.location_service_role = iam.Role(
            self, "LocationServiceRole",
            role_name="GymPulse-Location-Service-Role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Role for Amazon Location Service operations",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Add Location Service permissions
        self.location_service_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "geo:CalculateRoute",
                    "geo:CalculateRouteMatrix"
                ],
                resources=[
                    "arn:aws:geo:*:*:route-calculator/gym-pulse-route-calculator"
                ],
                conditions={
                    "StringEquals": {
                        "geo:RouteCalculatorName": "gym-pulse-route-calculator"
                    }
                }
            )
        )
    
    def create_lambda_execution_roles(self):
        """Create separate execution roles for different Lambda functions"""
        
        # Role for IoT data processing
        self.iot_processor_role = iam.Role(
            self, "IoTProcessorRole",
            role_name="GymPulse-IoT-Processor-Role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Add DynamoDB permissions for IoT processor
        self.iot_processor_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:GetItem",
                    "dynamodb:Query"
                ],
                resources=[
                    self.current_state_table.table_arn,
                    self.events_table.table_arn,
                    self.aggregates_table.table_arn
                ]
            )
        )
        
        # Role for API handlers (read-only access)
        self.api_handler_role = iam.Role(
            self, "ApiHandlerRole",
            role_name="GymPulse-API-Handler-Role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Add read permissions for API handlers
        self.api_handler_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[
                    self.current_state_table.table_arn,
                    self.events_table.table_arn,
                    self.aggregates_table.table_arn,
                    f"{self.current_state_table.table_arn}/index/*",
                    f"{self.events_table.table_arn}/index/*",
                    f"{self.aggregates_table.table_arn}/index/*"
                ]
            )
        )
        
        # Role for alert management
        self.alert_manager_role = iam.Role(
            self, "AlertManagerRole",
            role_name="GymPulse-Alert-Manager-Role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Add alerts table permissions
        self.alert_manager_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[
                    self.alerts_table.table_arn,
                    f"{self.alerts_table.table_arn}/index/*"
                ]
            )
        )
        
        # Add WebSocket permissions for real-time notifications
        self.alert_manager_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "execute-api:ManageConnections"
                ],
                resources=[
                    "arn:aws:execute-api:*:*:*/*/POST/@connections/*"
                ]
            )
        )
    
    def create_iot_service_roles(self):
        """Create roles for IoT Core operations"""
        
        # Role for IoT Rules to invoke Lambda
        self.iot_rules_role = iam.Role(
            self, "IoTRulesRole",
            role_name="GymPulse-IoT-Rules-Role",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
            description="Role for IoT Rules to invoke Lambda functions"
        )
        
        # Add Lambda invoke permissions
        self.iot_rules_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:InvokeFunction"
                ],
                resources=[
                    "arn:aws:lambda:*:*:function:gym-pulse-*"
                ]
            )
        )
        
        # Add CloudWatch Logs permissions for IoT
        self.iot_rules_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[
                    "arn:aws:logs:*:*:log-group:/aws/iot/*"
                ]
            )
        )
    
    def configure_dynamodb_security(self):
        """Configure DynamoDB encryption and access patterns"""
        
        # Note: Encryption configuration would be done during table creation
        # This method documents the security requirements
        
        # Create resource-based policy for DynamoDB (if needed)
        self.dynamodb_resource_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowAccessFromVPC",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "*"
                    },
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                        "dynamodb:UpdateItem"
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "aws:SourceVpce": "vpce-*"  # Restrict to VPC endpoint
                        }
                    }
                }
            ]
        }
        
        # Create backup role for point-in-time recovery
        self.dynamodb_backup_role = iam.Role(
            self, "DynamoDBBackupRole",
            role_name="GymPulse-DynamoDB-Backup-Role",
            assumed_by=iam.ServicePrincipal("dynamodb.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSBackupServiceRolePolicyForBackup")
            ]
        )
    
    def setup_access_monitoring(self):
        """Set up IAM access monitoring and alerting"""
        
        # Lambda function for access pattern monitoring
        self.access_monitor_function = _lambda.Function(
            self, "AccessMonitorFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="access_monitor.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
from datetime import datetime, timedelta

cloudwatch = boto3.client('cloudwatch')
iam = boto3.client('iam')

def lambda_handler(event, context):
    '''
    Monitor IAM access patterns and generate security metrics
    '''
    try:
        # Parse CloudTrail event
        records = event.get('Records', [])
        
        for record in records:
            # Extract access information
            detail = record.get('detail', {})
            event_name = detail.get('eventName', '')
            source_ip = detail.get('sourceIPAddress', '')
            user_agent = detail.get('userAgent', '')
            user_identity = detail.get('userIdentity', {})
            
            # Check for suspicious access patterns
            suspicious_events = [
                'AssumeRole', 
                'GetSessionToken',
                'CreateAccessKey',
                'DeleteUser',
                'AttachUserPolicy',
                'PutUserPolicy'
            ]
            
            if event_name in suspicious_events:
                # Generate security alert metric
                cloudwatch.put_metric_data(
                    Namespace='GymPulse/IAM/Security',
                    MetricData=[
                        {
                            'MetricName': 'SuspiciousIAMActivity',
                            'Dimensions': [
                                {
                                    'Name': 'EventName',
                                    'Value': event_name
                                },
                                {
                                    'Name': 'SourceIP',
                                    'Value': source_ip
                                }
                            ],
                            'Value': 1,
                            'Unit': 'Count',
                            'Timestamp': datetime.utcnow()
                        }
                    ]
                )
                
                print(f"SECURITY ALERT: Suspicious IAM activity - {event_name} from {source_ip}")
        
        # Check for unused roles (simplified)
        # In production, would analyze CloudTrail logs over time
        
        return {
            'statusCode': 200,
            'body': json.dumps('Access monitoring completed')
        }
        
    except Exception as e:
        print(f"Access monitoring error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
"""),
            timeout=Duration.minutes(5),
            environment={
                'LOG_LEVEL': 'INFO'
            }
        )
        
        # Grant monitoring permissions
        self.access_monitor_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData",
                    "iam:ListRoles",
                    "iam:GetRole",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=["*"]
            )
        )
    
    def create_security_boundary_policy(self):
        """Create permissions boundary policy for additional security"""
        
        self.security_boundary = iam.ManagedPolicy(
            self, "SecurityBoundaryPolicy",
            managed_policy_name="GymPulse-Security-Boundary",
            description="Permissions boundary for GymPulse resources",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "dynamodb:*",
                        "lambda:*",
                        "iot:*",
                        "bedrock:InvokeModel",
                        "geo:CalculateRoute*",
                        "logs:*",
                        "cloudwatch:*"
                    ],
                    resources=["*"],
                    conditions={
                        "StringLike": {
                            "aws:RequestedRegion": ["us-east-1", "ap-east-1", "ap-southeast-1"]
                        }
                    }
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.DENY,
                    actions=[
                        "iam:CreateUser",
                        "iam:CreateRole", 
                        "iam:AttachUserPolicy",
                        "iam:AttachRolePolicy",
                        "iam:DeleteUser",
                        "iam:DeleteRole"
                    ],
                    resources=["*"]
                )
            ]
        )
        
        return self.security_boundary
    
    @property
    def outputs(self):
        """Return IAM security configuration outputs"""
        return {
            'bedrock_inference_role_arn': self.bedrock_inference_role.role_arn,
            'location_service_role_arn': self.location_service_role.role_arn,
            'iot_processor_role_arn': self.iot_processor_role.role_arn,
            'api_handler_role_arn': self.api_handler_role.role_arn,
            'alert_manager_role_arn': self.alert_manager_role.role_arn,
            'iot_rules_role_arn': self.iot_rules_role.role_arn,
            'dynamodb_key_id': self.dynamodb_key.key_id,
            'lambda_key_id': self.lambda_key.key_id,
            'access_monitor_function': self.access_monitor_function.function_name
        }