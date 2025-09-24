"""
Security Monitoring Stack - CloudWatch Alarms, Audit Logging, Incident Response
Implements comprehensive security monitoring and alerting for GymPulse
"""
import json
from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_sns as sns,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_logs as logs,
    aws_iam as iam,
    aws_s3 as s3,
)
from constructs import Construct


class SecurityMonitoringStack(Construct):
    """Security Monitoring implementation with alarms, audit logging, and incident response"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)
        
        # Create SNS topic for security alerts
        self.create_alert_topic()
        
        # Set up CloudWatch security alarms
        self.setup_security_alarms()
        
        # Configure audit logging
        self.setup_audit_logging()
        
        # Create incident response automation
        self.setup_incident_response()
        
        # Set up security dashboard
        self.create_security_dashboard()
    
    def create_alert_topic(self):
        """Create SNS topic for security alerts"""
        
        self.security_alert_topic = sns.Topic(
            self, "SecurityAlertTopic",
            topic_name="GymPulse-Security-Alerts",
            display_name="GymPulse Security Alerts"
        )
        
        # Add email subscription for critical alerts (replace with actual email)
        self.security_alert_topic.add_subscription(
            sns.Subscription(
                self, "SecurityAlertEmail",
                topic=self.security_alert_topic,
                protocol=sns.SubscriptionProtocol.EMAIL,
                endpoint="security@gym-pulse.app"  # Replace with actual security team email
            )
        )
    
    def setup_security_alarms(self):
        """Set up CloudWatch alarms for security monitoring"""
        
        # Failed authentication attempts
        self.failed_auth_alarm = cloudwatch.Alarm(
            self, "FailedAuthenticationAlarm",
            alarm_name="GymPulse-Failed-Authentication-Attempts",
            alarm_description="Alert when failed authentication attempts exceed threshold",
            metric=cloudwatch.Metric(
                namespace="GymPulse/Security",
                metric_name="FailedAuthentication",
                statistic="Sum"
            ),
            threshold=10,  # 10 failed attempts in 5 minutes
            evaluation_periods=1,
            period=Duration.minutes(5),
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        self.failed_auth_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.security_alert_topic)
        )
        
        # Unusual API access patterns
        self.unusual_api_access_alarm = cloudwatch.Alarm(
            self, "UnusualAPIAccessAlarm",
            alarm_name="GymPulse-Unusual-API-Access",
            alarm_description="Alert on unusual API access patterns",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="4XXError",
                dimensions_map={
                    "ApiName": "GymPulse-API"
                },
                statistic="Sum"
            ),
            threshold=50,  # 50 4XX errors in 5 minutes
            evaluation_periods=1,
            period=Duration.minutes(5),
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        self.unusual_api_access_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.security_alert_topic)
        )
        
        # IoT device connection anomalies
        self.iot_connection_alarm = cloudwatch.Alarm(
            self, "IoTConnectionAnomaliesAlarm",
            alarm_name="GymPulse-IoT-Connection-Anomalies",
            alarm_description="Alert on IoT device connection anomalies",
            metric=cloudwatch.Metric(
                namespace="AWS/IoT",
                metric_name="Connect.ClientError",
                statistic="Sum"
            ),
            threshold=20,  # 20 connection errors in 10 minutes
            evaluation_periods=1,
            period=Duration.minutes(10),
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        self.iot_connection_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.security_alert_topic)
        )
        
        # DynamoDB throttling (potential DoS attack)
        self.dynamodb_throttling_alarm = cloudwatch.Alarm(
            self, "DynamoDBThrottlingAlarm",
            alarm_name="GymPulse-DynamoDB-Throttling",
            alarm_description="Alert on DynamoDB throttling events",
            metric=cloudwatch.Metric(
                namespace="AWS/DynamoDB",
                metric_name="ThrottledRequests",
                statistic="Sum"
            ),
            threshold=10,  # 10 throttled requests in 5 minutes
            evaluation_periods=1,
            period=Duration.minutes(5),
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        self.dynamodb_throttling_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.security_alert_topic)
        )
        
        # Bedrock API errors (potential abuse)
        self.bedrock_errors_alarm = cloudwatch.Alarm(
            self, "BedrockErrorsAlarm",
            alarm_name="GymPulse-Bedrock-Errors",
            alarm_description="Alert on Bedrock API errors",
            metric=cloudwatch.Metric(
                namespace="AWS/Bedrock",
                metric_name="InvocationClientErrors",
                statistic="Sum"
            ),
            threshold=15,  # 15 errors in 5 minutes
            evaluation_periods=1,
            period=Duration.minutes(5),
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        self.bedrock_errors_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.security_alert_topic)
        )
    
    def setup_audit_logging(self):
        """Set up comprehensive audit logging"""
        
        # Create S3 bucket for audit logs
        self.audit_logs_bucket = s3.Bucket(
            self, "AuditLogsBucket",
            bucket_name="gym-pulse-audit-logs-${AWS::AccountId}",
            versioning=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            lifecycle_rules=[
                s3.LifecycleRule(
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ],
                    expiration=Duration.days(2555)  # 7 years retention
                )
            ],
            public_read_access=False,
            public_write_access=False
        )
        
        # Create CloudWatch log group for security events
        self.security_log_group = logs.LogGroup(
            self, "SecurityEventLogs",
            log_group_name="/aws/security/gym-pulse",
            retention=logs.RetentionDays.ONE_YEAR
        )
        
        # Lambda function for audit log processing
        self.audit_processor_function = _lambda.Function(
            self, "AuditProcessorFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="audit_processor.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import hashlib
import time
from datetime import datetime

s3 = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    '''
    Process security events and create audit logs
    '''
    try:
        # Extract event information
        event_source = event.get('source', 'unknown')
        event_type = event.get('detail-type', 'unknown')
        event_detail = event.get('detail', {})
        timestamp = event.get('time', datetime.utcnow().isoformat())
        
        # Create audit log entry
        audit_entry = {
            'timestamp': timestamp,
            'event_id': generate_event_id(event),
            'event_source': event_source,
            'event_type': event_type,
            'event_detail': event_detail,
            'user_identity': event_detail.get('userIdentity', {}),
            'source_ip': event_detail.get('sourceIPAddress', 'unknown'),
            'user_agent': event_detail.get('userAgent', 'unknown'),
            'request_id': event_detail.get('requestId', 'unknown'),
            'api_version': event_detail.get('apiVersion', 'unknown'),
            'integrity_hash': None  # Will be calculated
        }
        
        # Calculate integrity hash
        audit_entry['integrity_hash'] = calculate_integrity_hash(audit_entry)
        
        # Store audit log in S3
        bucket_name = os.environ['AUDIT_LOGS_BUCKET']
        key = f"audit-logs/{datetime.utcnow().strftime('%Y/%m/%d')}/{audit_entry['event_id']}.json"
        
        s3.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json.dumps(audit_entry, indent=2),
            ServerSideEncryption='AES256',
            Metadata={
                'event-source': event_source,
                'event-type': event_type,
                'timestamp': timestamp
            }
        )
        
        # Generate CloudWatch metrics
        cloudwatch.put_metric_data(
            Namespace='GymPulse/Security/Audit',
            MetricData=[
                {
                    'MetricName': 'AuditEventsProcessed',
                    'Dimensions': [
                        {
                            'Name': 'EventSource',
                            'Value': event_source
                        },
                        {
                            'Name': 'EventType',
                            'Value': event_type
                        }
                    ],
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
        
        # Check for security patterns
        security_score = assess_security_risk(audit_entry)
        if security_score > 7:  # High risk threshold
            generate_security_alert(audit_entry, security_score)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Audit log processed successfully',
                'event_id': audit_entry['event_id'],
                'security_score': security_score
            })
        }
        
    except Exception as e:
        print(f"Audit processing error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def generate_event_id(event):
    '''Generate unique event ID'''
    event_str = json.dumps(event, sort_keys=True)
    return hashlib.sha256(event_str.encode()).hexdigest()[:16]

def calculate_integrity_hash(audit_entry):
    '''Calculate integrity hash for tamper detection'''
    # Remove hash field for calculation
    entry_copy = {k: v for k, v in audit_entry.items() if k != 'integrity_hash'}
    entry_str = json.dumps(entry_copy, sort_keys=True)
    return hashlib.sha256(entry_str.encode()).hexdigest()

def assess_security_risk(audit_entry):
    '''Assess security risk score (0-10)'''
    score = 0
    
    # Check for suspicious patterns
    if 'error' in audit_entry.get('event_type', '').lower():
        score += 2
    
    if audit_entry.get('source_ip', '').startswith('10.'):
        score += 0  # Internal IP
    else:
        score += 1  # External IP
    
    if 'failed' in audit_entry.get('event_type', '').lower():
        score += 3
    
    if 'admin' in str(audit_entry.get('user_identity', {})).lower():
        score += 2
    
    return min(score, 10)

def generate_security_alert(audit_entry, security_score):
    '''Generate security alert for high-risk events'''
    print(f"SECURITY ALERT: High risk event detected (score: {security_score})")
    print(f"Event ID: {audit_entry['event_id']}")
    print(f"Event Type: {audit_entry['event_type']}")
    print(f"Source IP: {audit_entry['source_ip']}")
    
    # In production, would send to SNS or trigger incident response
"""),
            timeout=Duration.minutes(5),
            environment={
                'AUDIT_LOGS_BUCKET': self.audit_logs_bucket.bucket_name,
                'LOG_LEVEL': 'INFO'
            }
        )
        
        # Grant permissions to audit processor
        self.audit_logs_bucket.grant_write(self.audit_processor_function)
        
        self.audit_processor_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=["*"]
            )
        )
    
    def setup_incident_response(self):
        """Set up automated incident response"""
        
        # Lambda function for incident response automation
        self.incident_response_function = _lambda.Function(
            self, "IncidentResponseFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="incident_response.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    '''
    Automated incident response for security events
    '''
    try:
        # Parse SNS alarm message
        message = json.loads(event['Records'][0]['Sns']['Message'])
        alarm_name = message.get('AlarmName', 'Unknown')
        alarm_description = message.get('AlarmDescription', '')
        new_state = message.get('NewStateValue', 'UNKNOWN')
        
        print(f"Processing security incident: {alarm_name}")
        
        # Determine incident severity
        severity = determine_incident_severity(alarm_name, message)
        
        # Execute response based on severity
        if severity == 'CRITICAL':
            response = handle_critical_incident(alarm_name, message)
        elif severity == 'HIGH':
            response = handle_high_incident(alarm_name, message)
        elif severity == 'MEDIUM':
            response = handle_medium_incident(alarm_name, message)
        else:
            response = handle_low_incident(alarm_name, message)
        
        # Log incident response
        incident_log = {
            'timestamp': datetime.utcnow().isoformat(),
            'alarm_name': alarm_name,
            'severity': severity,
            'response_actions': response['actions'],
            'status': response['status']
        }
        
        print(f"Incident response completed: {json.dumps(incident_log)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Incident response executed',
                'severity': severity,
                'actions_taken': len(response['actions'])
            })
        }
        
    except Exception as e:
        print(f"Incident response error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def determine_incident_severity(alarm_name, message):
    '''Determine incident severity based on alarm'''
    if 'Failed-Authentication' in alarm_name:
        return 'HIGH'
    elif 'Unusual-API-Access' in alarm_name:
        return 'MEDIUM'
    elif 'IoT-Connection-Anomalies' in alarm_name:
        return 'MEDIUM'
    elif 'DynamoDB-Throttling' in alarm_name:
        return 'HIGH'
    elif 'Bedrock-Errors' in alarm_name:
        return 'LOW'
    else:
        return 'MEDIUM'

def handle_critical_incident(alarm_name, message):
    '''Handle critical security incidents'''
    actions = []
    
    # Log critical alert
    actions.append(f"CRITICAL ALERT: {alarm_name}")
    
    # In production, would:
    # - Block suspicious IPs
    # - Disable compromised accounts
    # - Scale down services if needed
    # - Notify security team immediately
    
    return {
        'status': 'CRITICAL_RESPONSE_ACTIVATED',
        'actions': actions
    }

def handle_high_incident(alarm_name, message):
    '''Handle high priority incidents'''
    actions = []
    
    actions.append(f"HIGH PRIORITY: {alarm_name}")
    
    # In production, would:
    # - Increase monitoring
    # - Rate limit suspicious sources
    # - Generate detailed forensic logs
    
    return {
        'status': 'HIGH_PRIORITY_RESPONSE',
        'actions': actions
    }

def handle_medium_incident(alarm_name, message):
    '''Handle medium priority incidents'''
    actions = []
    
    actions.append(f"MEDIUM ALERT: {alarm_name}")
    
    # In production, would:
    # - Log for investigation
    # - Increase alerting sensitivity
    # - Schedule security review
    
    return {
        'status': 'MEDIUM_RESPONSE',
        'actions': actions
    }

def handle_low_incident(alarm_name, message):
    '''Handle low priority incidents'''
    actions = []
    
    actions.append(f"LOW PRIORITY: {alarm_name}")
    
    # Log for trend analysis
    return {
        'status': 'LOGGED_FOR_ANALYSIS',
        'actions': actions
    }
"""),
            timeout=Duration.minutes(10),
            environment={
                'LOG_LEVEL': 'INFO'
            }
        )
        
        # Subscribe incident response to security alerts
        self.security_alert_topic.add_subscription(
            sns.Subscription(
                self, "IncidentResponseSubscription",
                topic=self.security_alert_topic,
                protocol=sns.SubscriptionProtocol.LAMBDA,
                endpoint=self.incident_response_function.function_arn
            )
        )
        
        # Grant SNS invoke permission
        self.incident_response_function.add_permission(
            "AllowSNSInvoke",
            principal=iam.ServicePrincipal("sns.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=self.security_alert_topic.topic_arn
        )
    
    def create_security_dashboard(self):
        """Create CloudWatch dashboard for security monitoring"""
        
        self.security_dashboard = cloudwatch.Dashboard(
            self, "SecurityMonitoringDashboard",
            dashboard_name="GymPulse-Security-Monitoring"
        )
        
        # Add widgets to dashboard
        self.security_dashboard.add_widgets(
            # API Security Metrics
            cloudwatch.GraphWidget(
                title="API Security Metrics",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/ApiGateway",
                        metric_name="4XXError",
                        dimensions_map={"ApiName": "GymPulse-API"}
                    ),
                    cloudwatch.Metric(
                        namespace="AWS/ApiGateway", 
                        metric_name="5XXError",
                        dimensions_map={"ApiName": "GymPulse-API"}
                    )
                ],
                period=Duration.minutes(5)
            ),
            
            # IoT Security Metrics
            cloudwatch.GraphWidget(
                title="IoT Security Metrics",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/IoT",
                        metric_name="Connect.ClientError"
                    ),
                    cloudwatch.Metric(
                        namespace="GymPulse/IoT/Security",
                        metric_name="SecurityEvents"
                    )
                ],
                period=Duration.minutes(5)
            ),
            
            # Authentication Metrics
            cloudwatch.GraphWidget(
                title="Authentication Security",
                left=[
                    cloudwatch.Metric(
                        namespace="GymPulse/Security",
                        metric_name="FailedAuthentication"
                    )
                ],
                period=Duration.minutes(5)
            ),
            
            # System Health
            cloudwatch.SingleValueWidget(
                title="Security Alarms Active",
                metrics=[
                    cloudwatch.Metric(
                        namespace="AWS/CloudWatch",
                        metric_name="MetricCount",
                        dimensions_map={"MetricName": "AlarmState"}
                    )
                ]
            )
        )
    
    @property
    def outputs(self):
        """Return security monitoring configuration outputs"""
        return {
            'security_alert_topic_arn': self.security_alert_topic.topic_arn,
            'audit_logs_bucket_name': self.audit_logs_bucket.bucket_name,
            'security_log_group_name': self.security_log_group.log_group_name,
            'audit_processor_function': self.audit_processor_function.function_name,
            'incident_response_function': self.incident_response_function.function_name,
            'security_dashboard_name': self.security_dashboard.dashboard_name,
            'failed_auth_alarm_name': self.failed_auth_alarm.alarm_name,
            'api_access_alarm_name': self.unusual_api_access_alarm.alarm_name
        }