"""
Data Minimizer for Privacy-by-Design Implementation

Ensures only necessary machine occupancy data is collected and stored,
with automatic anonymization and data retention policies.
"""
import json
import hashlib
import time
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal


class DataMinimizer:
    """Implements privacy-by-design data minimization principles"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        
        # Data retention policies (in seconds)
        self.RETENTION_POLICIES = {
            'current_state': None,  # No expiry for current state
            'events': 30 * 24 * 3600,  # 30 days for events
            'aggregates': 90 * 24 * 3600,  # 90 days for aggregates
            'alerts': 7 * 24 * 3600,  # 7 days for alerts
            'user_sessions': 24 * 3600,  # 24 hours for user sessions
        }
        
        # Anonymization salt (in production, store securely)
        self.ANONYMIZATION_SALT = os.environ.get('ANONYMIZATION_SALT', 'gym-pulse-2024')
    
    def anonymize_machine_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove any potentially identifying information from machine data
        
        Args:
            raw_data: Raw machine telemetry data
            
        Returns:
            Anonymized data containing only essential fields
        """
        # Only keep essential fields for gym availability service
        anonymized = {
            'machineId': raw_data['machineId'],  # Keep as-is (already anonymized machine IDs)
            'status': self._sanitize_status(raw_data.get('status', 'unknown')),
            'timestamp': self._round_timestamp(raw_data.get('timestamp', time.time())),
            'gymId': raw_data.get('gymId', 'unknown'),  # Branch identifier only
            'category': self._sanitize_category(raw_data.get('category', 'unknown'))
        }
        
        # Explicitly exclude any other fields that might contain PII
        # No user identifiers, no personal metadata, no location traces
        
        return self._clean_empty_values(anonymized)
    
    def anonymize_user_location(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Anonymize user location for routing purposes only
        
        Args:
            lat: User latitude
            lon: User longitude
            
        Returns:
            Anonymized location data for current session only
        """
        # Round coordinates to reduce precision (roughly 100m accuracy)
        rounded_lat = round(lat, 3)  # ~111m precision
        rounded_lon = round(lon, 3)  # ~85m precision in Hong Kong
        
        # Create session-only location token
        session_token = self._create_session_token(rounded_lat, rounded_lon)
        
        return {
            'lat': rounded_lat,
            'lon': rounded_lon,
            'session_token': session_token,
            'expires_at': int(time.time()) + self.RETENTION_POLICIES['user_sessions'],
            'anonymized': True,
            'precision_level': 'routing_only'  # Indicates limited precision
        }
    
    def minimize_aggregation_data(self, raw_aggregates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Minimize aggregation data to essential statistics only
        
        Args:
            raw_aggregates: Raw aggregation data
            
        Returns:
            Minimized aggregation data
        """
        minimized = {
            'gymId_category': raw_aggregates.get('gymId_category', 'unknown'),
            'timestamp15min': self._round_to_15min(raw_aggregates.get('timestamp15min', time.time())),
            'occupancyRatio': self._sanitize_ratio(raw_aggregates.get('occupancyRatio', 0)),
            'freeCount': max(0, int(raw_aggregates.get('freeCount', 0))),
            'totalCount': max(1, int(raw_aggregates.get('totalCount', 1))),  # Prevent division by zero
            'sampleSize': max(0, int(raw_aggregates.get('sampleSize', 0)))
        }
        
        # Add TTL for automatic cleanup
        if self.RETENTION_POLICIES['aggregates']:
            minimized['ttl'] = int(time.time()) + self.RETENTION_POLICIES['aggregates']
        
        return self._clean_empty_values(minimized)
    
    def apply_data_retention(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply appropriate data retention policy based on table type
        
        Args:
            table_name: DynamoDB table name
            data: Data to apply retention policy to
            
        Returns:
            Data with appropriate TTL settings
        """
        # Determine retention policy based on table name
        if 'events' in table_name.lower():
            retention_seconds = self.RETENTION_POLICIES['events']
        elif 'aggregates' in table_name.lower():
            retention_seconds = self.RETENTION_POLICIES['aggregates']
        elif 'alerts' in table_name.lower():
            retention_seconds = self.RETENTION_POLICIES['alerts']
        else:
            retention_seconds = None  # No automatic expiry for current state
        
        if retention_seconds:
            data_with_ttl = data.copy()
            data_with_ttl['ttl'] = int(time.time()) + retention_seconds
            return data_with_ttl
        
        return data
    
    def clean_expired_session_data(self):
        """
        Clean up expired session data (called by scheduled Lambda)
        """
        current_time = int(time.time())
        
        # In a real implementation, would scan for and remove expired session data
        # For demo, just log the cleanup activity
        print(f"Session cleanup: Removing data older than {current_time - self.RETENTION_POLICIES['user_sessions']}")
        
        # Return cleanup statistics
        return {
            'cleanup_time': current_time,
            'retention_policy_seconds': self.RETENTION_POLICIES['user_sessions'],
            'action': 'expired_session_cleanup'
        }
    
    def validate_data_compliance(self, data: Dict[str, Any], data_type: str) -> Dict[str, bool]:
        """
        Validate that data complies with privacy requirements
        
        Args:
            data: Data to validate
            data_type: Type of data (machine, user, aggregate)
            
        Returns:
            Compliance validation results
        """
        compliance = {
            'contains_pii': False,
            'has_retention_policy': False,
            'properly_anonymized': True,
            'compliant': True
        }
        
        # Check for potential PII
        pii_fields = ['email', 'phone', 'name', 'address', 'userId', 'personalId', 'device_serial']
        for field in pii_fields:
            if field in data or field.lower() in str(data).lower():
                compliance['contains_pii'] = True
                compliance['compliant'] = False
        
        # Check for retention policy
        if data_type in ['events', 'aggregates', 'alerts'] and 'ttl' in data:
            compliance['has_retention_policy'] = True
        
        # Check anonymization quality
        if data_type == 'machine':
            required_fields = ['machineId', 'status', 'timestamp', 'gymId', 'category']
            has_all_required = all(field in data for field in required_fields)
            has_extra_fields = len(data) > len(required_fields) + 1  # +1 for optional TTL
            
            if not has_all_required or has_extra_fields:
                compliance['properly_anonymized'] = False
                compliance['compliant'] = False
        
        return compliance
    
    def _sanitize_status(self, status: str) -> str:
        """Sanitize machine status to allowed values only"""
        allowed_statuses = ['occupied', 'free', 'offline', 'maintenance']
        sanitized = str(status).lower().strip()
        
        return sanitized if sanitized in allowed_statuses else 'unknown'
    
    def _sanitize_category(self, category: str) -> str:
        """Sanitize equipment category to allowed values only"""
        allowed_categories = ['legs', 'chest', 'back', 'cardio', 'functional']
        sanitized = str(category).lower().strip()
        
        return sanitized if sanitized in allowed_categories else 'unknown'
    
    def _sanitize_ratio(self, ratio: Any) -> float:
        """Sanitize occupancy ratio to valid 0-100 range"""
        try:
            value = float(ratio)
            return max(0.0, min(100.0, value))  # Clamp to 0-100 range
        except (ValueError, TypeError):
            return 0.0
    
    def _round_timestamp(self, timestamp: Any) -> int:
        """Round timestamp to nearest minute for privacy"""
        try:
            ts = float(timestamp)
            # Round to nearest minute (60-second intervals)
            return int(ts // 60) * 60
        except (ValueError, TypeError):
            return int(time.time() // 60) * 60
    
    def _round_to_15min(self, timestamp: Any) -> int:
        """Round timestamp to nearest 15-minute interval"""
        try:
            ts = float(timestamp)
            # Round to nearest 15-minute interval
            return int(ts // 900) * 900
        except (ValueError, TypeError):
            return int(time.time() // 900) * 900
    
    def _create_session_token(self, lat: float, lon: float) -> str:
        """Create anonymized session token for location"""
        session_data = f"{lat}:{lon}:{int(time.time() // 3600)}"  # Hourly token
        return hashlib.sha256((session_data + self.ANONYMIZATION_SALT).encode()).hexdigest()[:16]
    
    def _clean_empty_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove empty or None values from data"""
        return {k: v for k, v in data.items() if v is not None and v != ''}


# Lambda handler for data minimization processing
def lambda_handler(event, context):
    """
    Lambda handler for data minimization
    Used by other Lambda functions to ensure privacy compliance
    """
    minimizer = DataMinimizer()
    
    try:
        operation = event.get('operation', 'anonymize_machine_data')
        data = event.get('data', {})
        data_type = event.get('data_type', 'machine')
        
        if operation == 'anonymize_machine_data':
            result = minimizer.anonymize_machine_data(data)
        elif operation == 'anonymize_user_location':
            lat = data.get('lat', 0)
            lon = data.get('lon', 0)
            result = minimizer.anonymize_user_location(lat, lon)
        elif operation == 'minimize_aggregation_data':
            result = minimizer.minimize_aggregation_data(data)
        elif operation == 'validate_compliance':
            result = minimizer.validate_data_compliance(data, data_type)
        elif operation == 'apply_retention':
            table_name = event.get('table_name', '')
            result = minimizer.apply_data_retention(table_name, data)
        elif operation == 'cleanup_sessions':
            result = minimizer.clean_expired_session_data()
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result, default=str)
        }
        
    except Exception as e:
        print(f"Data minimization error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'operation': event.get('operation', 'unknown')
            })
        }