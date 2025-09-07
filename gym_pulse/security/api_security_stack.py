"""
API Security Stack - Security Headers, Rate Limiting, Input Validation
Implements comprehensive API security measures for GymPulse
"""
import json
from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    aws_apigateway as apigateway,
    aws_apigatewayv2 as apigatewayv2,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_wafv2 as wafv2,
    aws_logs as logs,
)
from constructs import Construct


class ApiSecurityStack(Construct):
    """API Security implementation with headers, rate limiting, and input validation"""
    
    def __init__(self, scope: Construct, construct_id: str, api_gateway, websocket_api, **kwargs) -> None:
        super().__init__(scope, construct_id)
        
        self.api_gateway = api_gateway
        self.websocket_api = websocket_api
        
        # Create security monitoring logs
        self.api_security_log_group = logs.LogGroup(
            self, "ApiSecurityLogs",
            log_group_name="/aws/apigateway/security/gym-pulse",
            retention=logs.RetentionDays.ONE_MONTH
        )
        
        # Set up Web Application Firewall
        self.setup_waf()
        
        # Configure security headers
        self.setup_security_headers()
        
        # Implement rate limiting
        self.setup_rate_limiting()
        
        # Add input validation
        self.setup_input_validation()
        
        # Configure CORS properly
        self.setup_cors()
        
        # Set up WebSocket security
        self.setup_websocket_security()
    
    def setup_waf(self):
        """Set up Web Application Firewall for API protection"""
        
        # Create IP rate limiting rule
        ip_rate_limit_rule = wafv2.CfnWebACL.RuleProperty(
            name="IPRateLimitRule",
            priority=10,
            action=wafv2.CfnWebACL.RuleActionProperty(
                block={}
            ),
            statement=wafv2.CfnWebACL.StatementProperty(
                rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                    limit=2000,  # 2000 requests per 5-minute period
                    aggregate_key_type="IP"
                )
            ),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name="IPRateLimitRule"
            )
        )
        
        # Create SQL injection protection rule
        sql_injection_rule = wafv2.CfnWebACL.RuleProperty(
            name="SQLInjectionRule",
            priority=20,
            action=wafv2.CfnWebACL.RuleActionProperty(
                block={}
            ),
            statement=wafv2.CfnWebACL.StatementProperty(
                managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                    vendor_name="AWS",
                    name="AWSManagedRulesSQLiRuleSet"
                )
            ),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name="SQLInjectionRule"
            ),
            override_action=wafv2.CfnWebACL.OverrideActionProperty(
                none={}
            )
        )
        
        # Create XSS protection rule
        xss_protection_rule = wafv2.CfnWebACL.RuleProperty(
            name="XSSProtectionRule",
            priority=30,
            action=wafv2.CfnWebACL.RuleActionProperty(
                block={}
            ),
            statement=wafv2.CfnWebACL.StatementProperty(
                managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                    vendor_name="AWS",
                    name="AWSManagedRulesCommonRuleSet"
                )
            ),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name="XSSProtectionRule"
            ),
            override_action=wafv2.CfnWebACL.OverrideActionProperty(
                none={}
            )
        )
        
        # Create WAF ACL
        self.web_acl = wafv2.CfnWebACL(
            self, "ApiWebACL",
            scope="REGIONAL",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(
                allow={}
            ),
            rules=[
                ip_rate_limit_rule,
                sql_injection_rule,
                xss_protection_rule
            ],
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name="GymPulseAPIWebACL"
            ),
            name="GymPulse-API-WebACL"
        )
    
    def setup_security_headers(self):
        """Configure security headers for API responses"""
        
        # Lambda function to add security headers
        self.security_headers_function = _lambda.Function(
            self, "SecurityHeadersFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="security_headers.lambda_handler",
            code=_lambda.Code.from_inline("""
import json

def lambda_handler(event, context):
    '''
    Add security headers to API responses
    '''
    response = event.get('response', {})
    
    # Add security headers
    headers = response.get('headers', {})
    
    # HTTPS Strict Transport Security
    headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
    # Content Security Policy
    headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://maps.googleapis.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' wss: https:; "
        "frame-src 'none'; "
        "object-src 'none'; "
        "base-uri 'self'"
    )
    
    # X-Frame-Options
    headers['X-Frame-Options'] = 'DENY'
    
    # X-Content-Type-Options
    headers['X-Content-Type-Options'] = 'nosniff'
    
    # X-XSS-Protection
    headers['X-XSS-Protection'] = '1; mode=block'
    
    # Referrer Policy
    headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions Policy
    headers['Permissions-Policy'] = (
        'geolocation=(), '
        'microphone=(), '
        'camera=(), '
        'payment=(), '
        'usb=(), '
        'magnetometer=(), '
        'gyroscope=(), '
        'speaker=(), '
        'ambient-light-sensor=(), '
        'accelerometer=(), '
        'vr=(), '
        'midi=()'
    )
    
    # Cache control for sensitive endpoints
    if '/alerts' in event.get('path', '') or '/forecast' in event.get('path', ''):
        headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        headers['Pragma'] = 'no-cache'
    
    response['headers'] = headers
    
    return {
        'statusCode': response.get('statusCode', 200),
        'headers': headers,
        'body': response.get('body', '')
    }
"""),
            timeout=Duration.seconds(30)
        )
    
    def setup_rate_limiting(self):
        """Implement API rate limiting"""
        
        # Create usage plan for API rate limiting
        self.usage_plan = apigateway.UsagePlan(
            self, "ApiUsagePlan",
            name="GymPulse-API-UsagePlan",
            description="Rate limiting for GymPulse API",
            throttle=apigateway.ThrottleSettings(
                rate_limit=1000,  # requests per second
                burst_limit=2000  # burst capacity
            ),
            quota=apigateway.QuotaSettings(
                limit=50000,  # requests per day
                period=apigateway.Period.DAY
            )
        )
        
        # Associate usage plan with API stage
        self.usage_plan.add_api_stage(
            stage=self.api_gateway.deployment_stage,
            throttle=[
                apigateway.ThrottlingPerMethod(
                    method=self.api_gateway.root.add_method("GET"),
                    throttle=apigateway.ThrottleSettings(
                        rate_limit=100,   # 100 RPS for GET requests
                        burst_limit=200
                    )
                ),
                apigateway.ThrottlingPerMethod(
                    method=self.api_gateway.root.add_method("POST"),
                    throttle=apigateway.ThrottleSettings(
                        rate_limit=50,    # 50 RPS for POST requests
                        burst_limit=100
                    )
                )
            ]
        )
        
        # Create API key for monitoring (optional)
        self.api_key = apigateway.ApiKey(
            self, "ApiKey",
            api_key_name="GymPulse-API-Key",
            description="API key for GymPulse monitoring"
        )
        
        self.usage_plan.add_api_key(self.api_key)
    
    def setup_input_validation(self):
        """Set up input validation for API endpoints"""
        
        # Create request validator
        self.request_validator = apigateway.RequestValidator(
            self, "ApiRequestValidator",
            rest_api=self.api_gateway,
            request_validator_name="GymPulse-Request-Validator",
            validate_request_body=True,
            validate_request_parameters=True
        )
        
        # Define request schemas
        self.request_schemas = {
            'alert_request': apigateway.JsonSchema(
                schema=apigateway.JsonSchemaVersion.DRAFT4,
                type=apigateway.JsonSchemaType.OBJECT,
                properties={
                    'machineId': apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING,
                        min_length=1,
                        max_length=50,
                        pattern='^[a-zA-Z0-9-_]+$'
                    ),
                    'userId': apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING,
                        min_length=1,
                        max_length=50,
                        pattern='^[a-zA-Z0-9-_]+$'
                    ),
                    'quietHours': apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.OBJECT,
                        properties={
                            'start': apigateway.JsonSchema(
                                type=apigateway.JsonSchemaType.INTEGER,
                                minimum=0,
                                maximum=23
                            ),
                            'end': apigateway.JsonSchema(
                                type=apigateway.JsonSchemaType.INTEGER,
                                minimum=0,
                                maximum=23
                            )
                        }
                    )
                },
                required=['machineId', 'userId']
            ),
            'chat_request': apigateway.JsonSchema(
                schema=apigateway.JsonSchemaVersion.DRAFT4,
                type=apigateway.JsonSchemaType.OBJECT,
                properties={
                    'message': apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING,
                        min_length=1,
                        max_length=500
                    ),
                    'userLocation': apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.OBJECT,
                        properties={
                            'lat': apigateway.JsonSchema(
                                type=apigateway.JsonSchemaType.NUMBER,
                                minimum=-90,
                                maximum=90
                            ),
                            'lon': apigateway.JsonSchema(
                                type=apigateway.JsonSchemaType.NUMBER,
                                minimum=-180,
                                maximum=180
                            )
                        }
                    ),
                    'sessionId': apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING,
                        max_length=50
                    )
                },
                required=['message']
            )
        }
    
    def setup_cors(self):
        """Configure CORS properly for security"""
        
        # Define CORS configuration
        self.cors_config = {
            'allow_origins': [
                'https://gym-pulse.app',  # Production domain
                'https://localhost:3000',  # Local development
                'https://127.0.0.1:3000'   # Local development
            ],
            'allow_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_headers': [
                'Content-Type',
                'Authorization',
                'X-Amz-Date',
                'X-Api-Key',
                'X-Amz-Security-Token',
                'X-Requested-With'
            ],
            'expose_headers': [
                'Content-Length',
                'Date',
                'X-Amzn-RequestId'
            ],
            'allow_credentials': False,  # Disable credentials for security
            'max_age': 86400  # 24 hours
        }
    
    def setup_websocket_security(self):
        """Configure WebSocket security measures"""
        
        # Lambda function for WebSocket connection authorization
        self.websocket_authorizer = _lambda.Function(
            self, "WebSocketAuthorizer",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="websocket_auth.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import time

def lambda_handler(event, context):
    '''
    Authorize WebSocket connections with security checks
    '''
    try:
        # Get connection info
        connection_id = event.get('requestContext', {}).get('connectionId')
        source_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp')
        user_agent = event.get('headers', {}).get('User-Agent', '')
        
        # Basic security checks
        
        # 1. Check for valid User-Agent (prevent automated attacks)
        if not user_agent or len(user_agent) < 10:
            print(f"Rejected connection {connection_id}: Invalid User-Agent")
            return generate_policy('Deny', 'Invalid request')
        
        # 2. Rate limit by IP (simplified check)
        # In production, would use DynamoDB or ElastiCache for rate limiting
        
        # 3. Check origin (if provided)
        origin = event.get('headers', {}).get('Origin', '')
        allowed_origins = [
            'https://gym-pulse.app',
            'https://localhost:3000',
            'https://127.0.0.1:3000'
        ]
        
        if origin and origin not in allowed_origins:
            print(f"Rejected connection {connection_id}: Invalid origin {origin}")
            return generate_policy('Deny', 'Invalid origin')
        
        # Generate connection context
        context = {
            'connectionId': connection_id,
            'sourceIp': source_ip,
            'userAgent': user_agent,
            'connectedAt': int(time.time()),
            'rateLimitBucket': f"ws_rate_limit_{source_ip}"
        }
        
        print(f"Authorized WebSocket connection: {connection_id} from {source_ip}")
        
        return generate_policy('Allow', 'Connection authorized', context)
        
    except Exception as e:
        print(f"WebSocket authorization error: {str(e)}")
        return generate_policy('Deny', 'Authorization failed')

def generate_policy(effect, reason, context=None):
    '''Generate IAM policy for WebSocket connection'''
    
    policy = {
        'principalId': 'gym-pulse-websocket-user',
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': effect,
                    'Action': 'execute-api:Invoke',
                    'Resource': '*'
                }
            ]
        }
    }
    
    if context:
        policy['context'] = context
        
    policy['context'] = policy.get('context', {})
    policy['context']['authReason'] = reason
    
    return policy
"""),
            timeout=Duration.seconds(30)
        )
        
        # Grant CloudWatch Logs permissions
        self.websocket_authorizer.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=["*"]
            )
        )
    
    @property
    def outputs(self):
        """Return API security configuration outputs"""
        return {
            'web_acl_id': self.web_acl.attr_id,
            'usage_plan_id': self.usage_plan.usage_plan_id,
            'api_key_id': self.api_key.key_id,
            'security_headers_function': self.security_headers_function.function_name,
            'websocket_authorizer_function': self.websocket_authorizer.function_name,
            'security_log_group': self.api_security_log_group.log_group_name
        }