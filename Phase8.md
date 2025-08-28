# Phase 8: Security, Privacy, and Compliance - Step-by-Step Breakdown

## Overview
Implement security guardrails, privacy-by-design principles, and Hong Kong PDPO compliance for IoT system and user data protection.

## Prerequisites
- All core functionality implemented (Phases 1-7)
- Security review of existing components
- Understanding of Hong Kong privacy requirements

---

## Step 1: IoT Security Implementation
**Duration**: 40 minutes  
**Status**: ⏳ Pending

### 1.1 Mutual TLS Configuration
- [ ] **File**: `infra/iot-security-stack.ts`
- [ ] Configure mutual TLS for all IoT device connections
- [ ] Implement device certificate rotation policy
- [ ] Set up certificate authority (CA) management
- [ ] Add certificate validation in IoT Core

### 1.2 Device Identity and Authentication
- [ ] Unique certificate per simulated device
- [ ] Device registration and provisioning workflow
- [ ] Certificate lifecycle management
- [ ] Revocation and blacklisting capabilities

### 1.3 Least-Privilege IoT Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Publish"
      ],
      "Resource": [
        "arn:aws:iot:*:*:topic/org/${iot:Connection.Thing.ThingName}/machines/*/status"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:UpdateThingShadow"
      ],
      "Resource": [
        "arn:aws:iot:*:*:thing/${iot:Connection.Thing.ThingName}"
      ]
    }
  ]
}
```

### 1.4 MQTT Topic Security
- [ ] Scoped topic permissions per device
- [ ] Prevent cross-device message publishing
- [ ] Message encryption in transit
- [ ] Topic isolation by gym/machine hierarchy

---

## Step 2: Privacy-by-Design Implementation
**Duration**: 35 minutes  
**Status**: ⏳ Pending

### 2.1 Data Minimization
- [ ] **File**: `lambda/privacy/data-minimizer.py`
- [ ] Collect only machine occupancy events (no PII)
- [ ] Remove unnecessary metadata from telemetry
- [ ] Implement data retention policies
- [ ] Automatic data purging after TTL expiry

### 2.2 Anonymization and Aggregation
```python
def anonymize_machine_data(raw_data):
    """
    Remove any potentially identifying information
    """
    anonymized = {
        'machineId': hash_machine_id(raw_data['machineId']),  # One-way hash
        'status': raw_data['status'],  # occupied/free only
        'timestamp': round_timestamp(raw_data['timestamp']),  # Round to nearest minute
        'gymId': raw_data['gymId'],  # Branch identifier only
        'category': raw_data['category']  # Equipment category only
    }
    
    # Explicitly exclude any other fields
    return anonymized
```

### 2.3 User Location Privacy
- [ ] Geolocation used only for current session
- [ ] No persistent storage of user coordinates
- [ ] Clear data retention policy in privacy notice
- [ ] User consent required before location access

---

## Step 3: Hong Kong PDPO Compliance
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 3.1 Privacy Notice Implementation
- [ ] **File**: `frontend/src/components/privacy/PrivacyNotice.tsx`
- [ ] Clear explanation of data collection practices
- [ ] Purpose specification for geolocation use
- [ ] Data retention and deletion policies
- [ ] User rights under PDPO

### 3.2 Consent Management
- [ ] **File**: `frontend/src/components/privacy/ConsentManager.tsx`
- [ ] Granular consent for different data types
- [ ] Easy withdrawal of consent
- [ ] Consent logging and audit trail
- [ ] Age verification for users under 18

### 3.3 PDPO Compliance Documentation
```markdown
# Privacy Data Protection Ordinance (PDPO) Compliance

## Data Collection
- Machine occupancy status (non-personal)
- Session-based geolocation (with consent, not stored)
- No personal identifiers or behavioral tracking

## User Rights
- Access: Users can request data deletion
- Correction: No personal data stored to correct
- Erasure: Immediate deletion of location data on session end
- Portability: Occupancy data available via API

## Legal Basis
- Legitimate interest for gym availability service
- Explicit consent for location-based features
```

---

## Step 4: Security Headers and API Protection
**Duration**: 25 minutes  
**Status**: ⏳ Pending

### 4.1 Security Headers Configuration
- [ ] **File**: `infra/api-security-stack.ts`
- [ ] HTTPS Strict Transport Security (HSTS)
- [ ] Content Security Policy (CSP)
- [ ] X-Frame-Options and X-Content-Type-Options
- [ ] Cross-Origin Resource Sharing (CORS) configuration

### 4.2 API Security Measures
- [ ] Input validation and sanitization
- [ ] Rate limiting per IP and user
- [ ] SQL injection and XSS prevention
- [ ] Request size limitations
- [ ] API versioning and deprecation policies

### 4.3 WebSocket Security
- [ ] Origin validation for WebSocket connections
- [ ] Connection rate limiting
- [ ] Message size and frequency limits
- [ ] Secure disconnect handling

---

## Step 5: IAM and Access Control
**Duration**: 25 minutes  
**Status**: ⏳ Pending

### 5.1 Bedrock and Location Service IAM
- [ ] **File**: `infra/bedrock-security-stack.ts`
- [ ] Least-privilege IAM roles for Bedrock access
- [ ] Scoped permissions for Location Service APIs
- [ ] Cross-service access controls
- [ ] Regular IAM policy auditing

### 5.2 Lambda Execution Roles
- [ ] Separate IAM roles per Lambda function
- [ ] Minimum required permissions only
- [ ] No wildcard permissions in production
- [ ] VPC configuration for sensitive operations

### 5.3 DynamoDB Security
- [ ] Encryption at rest enabled
- [ ] Encryption in transit for all connections
- [ ] Access patterns auditing
- [ ] Point-in-time recovery configured

---

## Step 6: Security Monitoring and Alerting
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 6.1 CloudWatch Security Alarms
- [ ] **File**: `infra/security-monitoring-stack.ts`
- [ ] Failed authentication attempts monitoring
- [ ] Unusual API access patterns
- [ ] IoT device connection anomalies
- [ ] Data access pattern anomalies

### 6.2 Audit Logging
- [ ] Comprehensive audit logs for all data access
- [ ] User consent and withdrawal logging
- [ ] Security event logging and retention
- [ ] Log integrity and tamper protection

### 6.3 Incident Response
- [ ] Security incident response playbook
- [ ] Automated alert escalation procedures
- [ ] Data breach notification procedures
- [ ] Regular security review schedule

---

## Success Criteria
- [ ] All IoT communications use mutual TLS
- [ ] No personal data collected or stored beyond session requirements
- [ ] Privacy notice clearly explains data practices
- [ ] User consent properly captured and manageable
- [ ] Security headers properly configured
- [ ] IAM follows least-privilege principles
- [ ] Security monitoring and alerting operational
- [ ] Compliance documentation complete

## Estimated Total Time: 2.5 hours

## Next Phase
Phase 9: Testing, QA, and observability