"""
IoT Security Stack - Mutual TLS, Device Certificates, and Topic Security
Implements comprehensive IoT security for GymPulse device connections
"""
import json
from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_iot as iot,
    aws_iam as iam,
    aws_certificatemanager as acm,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as _lambda,
    aws_ssm as ssm,
)
from constructs import Construct


class IoTSecurityStack(Construct):
    """IoT Security implementation with mutual TLS and device management"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)
        
        # Create IoT security logging
        self.iot_security_log_group = logs.LogGroup(
            self, "IoTSecurityLogs",
            log_group_name="/aws/iot/security/gym-pulse",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Create device certificate authority (simulate CA for demo)
        self.create_device_ca()
        
        # Create least-privilege IoT policies
        self.create_iot_policies()
        
        # Set up MQTT topic security
        self.setup_topic_security()
        
        # Create device certificate management
        self.setup_certificate_management()
        
        # Set up security monitoring
        self.setup_security_monitoring()
    
    def create_device_ca(self):
        """Create Certificate Authority for device certificates"""
        
        # Store CA configuration in Parameter Store
        self.ca_config = ssm.StringParameter(
            self, "DeviceCAConfig",
            parameter_name="/gym-pulse/security/device-ca-config",
            string_value=json.dumps({
                "ca_name": "GymPulseDeviceCA",
                "validity_days": 365,
                "certificate_rotation_days": 90,
                "revocation_check_enabled": True
            }),
            description="Device Certificate Authority configuration"
        )
        
        # Create CA certificate policy (for demo - in production would use AWS IoT Device Management)
        self.ca_certificate_policy = iot.CfnPolicy(
            self, "DeviceCACertificatePolicy",
            policy_name="GymPulse-DeviceCA-Policy",
            policy_document=json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "iot:CreateCertificateFromCsr",
                            "iot:CreateKeysAndCertificate",
                            "iot:UpdateCertificate"
                        ],
                        "Resource": "*",
                        "Condition": {
                            "StringEquals": {
                                "iot:CertificateMode": "SNI_ONLY"
                            }
                        }
                    }
                ]
            })
        )
    
    def create_iot_policies(self):
        """Create least-privilege IoT policies for different device types"""
        
        # Machine status publisher policy (most restrictive)
        self.machine_status_policy = iot.CfnPolicy(
            self, "MachineStatusPolicy",
            policy_name="GymPulse-MachineStatus-Policy",
            policy_document=json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "iot:Publish"
                        ],
                        "Resource": [
                            "arn:aws:iot:*:*:topic/org/${iot:Connection.Thing.ThingName}/machines/*/status"
                        ],
                        "Condition": {
                            "Bool": {
                                "iot:Connection.Thing.IsAttached": "true"
                            }
                        }
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "iot:UpdateThingShadow",
                            "iot:GetThingShadow"
                        ],
                        "Resource": [
                            "arn:aws:iot:*:*:thing/${iot:Connection.Thing.ThingName}"
                        ]
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "iot:Connect"
                        ],
                        "Resource": [
                            "arn:aws:iot:*:*:client/${iot:Connection.Thing.ThingName}"
                        ],
                        "Condition": {
                            "StringEquals": {
                                "iot:Connection.Thing.ThingTypeName": "GymMachine"
                            }
                        }
                    }
                ]
            })
        )
        
        # Device health monitoring policy (for maintenance systems)
        self.device_health_policy = iot.CfnPolicy(
            self, "DeviceHealthPolicy",
            policy_name="GymPulse-DeviceHealth-Policy", 
            policy_document=json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "iot:Publish"
                        ],
                        "Resource": [
                            "arn:aws:iot:*:*:topic/org/${iot:Connection.Thing.ThingName}/health/*"
                        ]
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "iot:Subscribe",
                            "iot:Receive"
                        ],
                        "Resource": [
                            "arn:aws:iot:*:*:topicfilter/org/${iot:Connection.Thing.ThingName}/commands/*"
                        ]
                    }
                ]
            })
        )
    
    def setup_topic_security(self):
        """Configure MQTT topic security and isolation"""
        
        # Create topic rule for security logging
        self.security_logging_rule = iot.CfnTopicRule(
            self, "SecurityLoggingRule",
            rule_name="GymPulse_SecurityLogging",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                sql="SELECT * FROM 'org/+/security/+'",
                description="Log all security-related messages",
                rule_disabled=False,
                actions=[
                    iot.CfnTopicRule.ActionProperty(
                        cloudwatch_logs=iot.CfnTopicRule.CloudwatchLogsActionProperty(
                            log_group_name=self.iot_security_log_group.log_group_name,
                            role_arn=self.create_logging_role().role_arn
                        )
                    )
                ]
            )
        )
        
        # Topic rule for unauthorized access attempts
        self.unauthorized_access_rule = iot.CfnTopicRule(
            self, "UnauthorizedAccessRule",
            rule_name="GymPulse_UnauthorizedAccess",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                sql="SELECT * FROM '$aws/events/presence/disconnected/+'",
                description="Monitor unauthorized disconnections",
                rule_disabled=False,
                actions=[
                    iot.CfnTopicRule.ActionProperty(
                        cloudwatch_logs=iot.CfnTopicRule.CloudwatchLogsActionProperty(
                            log_group_name=self.iot_security_log_group.log_group_name,
                            role_arn=self.create_logging_role().role_arn
                        )
                    )
                ]
            )
        )
    
    def setup_certificate_management(self):
        """Set up certificate lifecycle management"""
        
        # Lambda function for certificate rotation
        self.cert_rotation_function = _lambda.Function(
            self, "CertificateRotationFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="certificate_rotation.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import os
from datetime import datetime, timedelta

def lambda_handler(event, context):
    '''
    Handle certificate rotation for IoT devices
    '''
    iot_client = boto3.client('iot')
    
    try:
        # Get certificates expiring in next 30 days
        response = iot_client.list_certificates()
        expiring_certs = []
        
        for cert in response.get('certificates', []):
            cert_id = cert['certificateId']
            cert_details = iot_client.describe_certificate(certificateId=cert_id)
            
            expiry_date = cert_details['certificateDescription']['validity']['notAfter']
            
            # Check if certificate expires within 30 days
            if expiry_date < datetime.now() + timedelta(days=30):
                expiring_certs.append(cert_id)
                
                # Log expiring certificate
                print(f"Certificate {cert_id} expires on {expiry_date}")
        
        # In production, would create new certificates and update devices
        # For demo, just log the certificates that would be rotated
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Processed {len(expiring_certs)} expiring certificates',
                'expiring_certificates': expiring_certs
            })
        }
        
    except Exception as e:
        print(f"Certificate rotation error: {str(e)}")
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
        
        # Grant IoT permissions to certificate rotation function
        self.cert_rotation_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "iot:ListCertificates",
                    "iot:DescribeCertificate",
                    "iot:CreateKeysAndCertificate",
                    "iot:UpdateCertificate",
                    "iot:DeleteCertificate"
                ],
                resources=["*"]
            )
        )
        
        # Schedule certificate rotation check (weekly)
        certificate_rotation_rule = events.Rule(
            self, "CertificateRotationSchedule",
            schedule=events.Schedule.rate(Duration.days(7)),
            description="Weekly certificate expiration check"
        )
        certificate_rotation_rule.add_target(
            targets.LambdaFunction(self.cert_rotation_function)
        )
    
    def setup_security_monitoring(self):
        """Set up IoT security monitoring and alerting"""
        
        # Lambda function for security event processing
        self.security_monitor_function = _lambda.Function(
            self, "SecurityMonitorFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="security_monitor.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import os
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    '''
    Process IoT security events and generate metrics
    '''
    try:
        # Parse IoT security event
        records = event.get('Records', [])
        
        for record in records:
            # Extract security event details
            message = json.loads(record['body']) if 'body' in record else record
            
            event_type = message.get('eventType', 'unknown')
            timestamp = message.get('timestamp', datetime.utcnow().isoformat())
            client_id = message.get('clientId', 'unknown')
            
            # Generate security metrics
            cloudwatch.put_metric_data(
                Namespace='GymPulse/IoT/Security',
                MetricData=[
                    {
                        'MetricName': 'SecurityEvents',
                        'Dimensions': [
                            {
                                'Name': 'EventType',
                                'Value': event_type
                            },
                            {
                                'Name': 'ClientId', 
                                'Value': client_id
                            }
                        ],
                        'Value': 1,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
            
            # Log security event
            print(f"Security event: {event_type} from {client_id} at {timestamp}")
            
            # Check for suspicious patterns
            if event_type in ['AUTH_FAILURE', 'UNAUTHORIZED_PUBLISH', 'CERTIFICATE_INVALID']:
                # In production, would trigger alerts
                print(f"SECURITY ALERT: {event_type} detected for {client_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Security events processed successfully')
        }
        
    except Exception as e:
        print(f"Security monitoring error: {str(e)}")
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
        
        # Grant CloudWatch permissions
        self.security_monitor_function.add_to_role_policy(
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
    
    def create_logging_role(self):
        """Create IAM role for IoT Core logging"""
        
        logging_role = iam.Role(
            self, "IoTLoggingRole",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSIoTLoggingRole")
            ]
        )
        
        # Add specific CloudWatch logs permissions
        logging_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[
                    self.iot_security_log_group.log_group_arn
                ]
            )
        )
        
        return logging_role
    
    @property
    def outputs(self):
        """Return security configuration outputs"""
        return {
            'machine_status_policy_name': self.machine_status_policy.policy_name,
            'device_health_policy_name': self.device_health_policy.policy_name,
            'security_log_group': self.iot_security_log_group.log_group_name,
            'cert_rotation_function': self.cert_rotation_function.function_name,
            'security_monitor_function': self.security_monitor_function.function_name
        }