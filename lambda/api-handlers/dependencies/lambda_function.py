import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
import time
import warnings
import requests

# Import NumPy from the Lambda layer
import numpy as np

# Suppress warnings for cleaner logs
warnings.filterwarnings('ignore')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
lambda_client = boto3.client('lambda', region_name='ap-east-1')
current_state_table = dynamodb.Table('gym-pulse-current-state')
aggregates_table = dynamodb.Table('gym-pulse-aggregates')

# Google Gemini API configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

class MLForecastEngine:
    """
    AI-Powered Gym Equipment Forecasting Engine - Integrated into API Handler

    Features:
    1. Time Series Forecasting with Multiple Models
    2. Anomaly Detection for Unusual Patterns
    3. Google Gemini API Integration for AI Insights
    4. Real-time Model Updates
    5. Multi-feature Prediction (seasonality, trends, context)
    """

    def __init__(self):
        self.dynamodb = dynamodb
        self.events_table = None  # Not needed for this integration
        self.aggregates_table = aggregates_table
        self.current_state_table = current_state_table
        self.anomaly_threshold = 2.0  # Standard deviations for anomaly detection

    def generate_ai_forecast(self, machine_id, historical_data, current_context):
        """Main AI forecasting function combining multiple ML approaches"""
        print(f"🤖 Starting AI forecast generation for {machine_id}")

        try:
            # 1. Prepare time series data
            data_array = self.prepare_time_series_data(historical_data)

            if len(data_array) < 12:  # Need at least 12 data points
                return self.fallback_forecast(machine_id, current_context)

            # 2. Detect anomalies in historical data
            anomalies = self.detect_anomalies(data_array)

            # 3. Generate multiple forecasting models
            forecasts = {
                'seasonal_decomposition': self.seasonal_decomposition_forecast(data_array),
                'pattern_recognition': self.pattern_recognition_forecast(data_array),
                'trend_analysis': self.trend_analysis_forecast(data_array),
                'context_aware': self.context_aware_forecast(data_array, current_context)
            }

            # 4. Ensemble prediction combining all models
            ensemble_forecast = self.ensemble_prediction(forecasts)

            # 5. AI insights using Google Gemini API
            ai_insights = self.generate_gemini_insights(machine_id, data_array, ensemble_forecast, anomalies)

            # 6. Real-time confidence scoring
            confidence_score = self.calculate_confidence_score(data_array, forecasts, anomalies)

            result = {
                'machine_id': machine_id,
                'forecast_hours': ensemble_forecast,
                'confidence_score': confidence_score,
                'anomalies_detected': len(anomalies),
                'ai_insights': ai_insights,
                'model_performance': self.evaluate_model_performance(forecasts),
                'next_update': (datetime.now() + timedelta(hours=1)).isoformat(),
                'generated_at': datetime.now().isoformat()
            }

            print(f"✅ AI forecast generated with {confidence_score:.1f}% confidence")
            return result

        except Exception as e:
            print(f"❌ Error in AI forecast generation: {str(e)}")
            return self.fallback_forecast(machine_id, current_context)

    def prepare_time_series_data(self, historical_data):
        """Convert historical data to structured array for ML processing"""
        data_points = []
        for record in historical_data:
            dt = datetime.fromtimestamp(record['timestamp15min'])
            data_points.append({
                'timestamp': record['timestamp15min'],
                'occupancy_ratio': float(record['occupancyRatio']),
                'hour': dt.hour,
                'day_of_week': dt.weekday(),
                'is_weekend': dt.weekday() >= 5,
                'is_peak_hour': self.is_peak_hour(dt.hour)
            })

        # Sort by timestamp
        data_points.sort(key=lambda x: x['timestamp'])

        # Convert to structured numpy array
        dtype = [
            ('timestamp', 'i8'),
            ('occupancy_ratio', 'f8'),
            ('hour', 'i4'),
            ('day_of_week', 'i4'),
            ('is_weekend', 'bool'),
            ('is_peak_hour', 'bool')
        ]
        tuples = [(d['timestamp'], d['occupancy_ratio'], d['hour'],
                  d['day_of_week'], d['is_weekend'], d['is_peak_hour']) for d in data_points]
        data_array = np.array(tuples, dtype=dtype)
        return data_array

    def detect_anomalies(self, data_array):
        """Use statistical methods to detect unusual usage patterns"""
        anomalies = []

        # NumPy implementation for anomaly detection
        occupancy_mean = np.mean(data_array['occupancy_ratio'])
        occupancy_std = np.std(data_array['occupancy_ratio'])

        if occupancy_std > 0:  # Avoid division by zero
            z_scores = np.abs(data_array['occupancy_ratio'] - occupancy_mean) / occupancy_std
            anomaly_mask = z_scores > self.anomaly_threshold

            for i, is_anomaly in enumerate(anomaly_mask):
                if is_anomaly:
                    anomalies.append({
                        'timestamp': data_array[i]['timestamp'],
                        'occupancy_ratio': data_array[i]['occupancy_ratio'],
                        'hour': data_array[i]['hour'],
                        'anomaly_score': z_scores[i]
                    })

        print(f"🔍 Detected {len(anomalies)} anomalies in historical data")
        return anomalies

    def seasonal_decomposition_forecast(self, data_array):
        """Seasonal decomposition with trend analysis"""
        hourly_patterns = {}

        # Group by hour and calculate statistics
        for hour in range(24):
            # NumPy implementation for filtering by hour
            hour_mask = data_array['hour'] == hour
            hour_data = data_array[hour_mask]['occupancy_ratio']

            if len(hour_data) > 0:
                # Calculate seasonal patterns
                mean_usage = np.mean(hour_data)
                std_usage = np.std(hour_data)
                trend = self.calculate_trend(hour_data)

                # Apply trend to mean
                forecast = max(5.0, min(95.0, mean_usage + trend))

                hourly_patterns[hour] = {
                    'forecast': forecast,
                    'confidence': min(100, len(hour_data) * 10),  # More data = higher confidence
                    'trend': trend
                }
            else:
                hourly_patterns[hour] = {'forecast': 25.0, 'confidence': 20, 'trend': 0}

        return hourly_patterns

    def pattern_recognition_forecast(self, data_array):
        """Advanced pattern recognition using statistical analysis"""
        hourly_patterns = {}

        for hour in range(24):
            hour_data = [d for d in data_array if d['hour'] == hour]

            if len(hour_data) >= 2:
                # Pattern analysis using NumPy
                weekend_data = [d['occupancy_ratio'] for d in hour_data if d['is_weekend']]
                weekday_data = [d['occupancy_ratio'] for d in hour_data if not d['is_weekend']]

                weekend_avg = np.mean(weekend_data) if len(weekend_data) > 0 else np.nan
                weekday_avg = np.mean(weekday_data) if len(weekday_data) > 0 else np.nan

                # Current day context
                current_is_weekend = datetime.now().weekday() >= 5

                if not np.isnan(weekend_avg) and not np.isnan(weekday_avg):
                    if current_is_weekend:
                        forecast = weekend_avg
                    else:
                        forecast = weekday_avg
                else:
                    all_occupancy = [d['occupancy_ratio'] for d in hour_data]
                    forecast = np.mean(all_occupancy)

                # Apply smoothing
                forecast = max(5.0, min(95.0, forecast))

                hourly_patterns[hour] = {
                    'forecast': forecast,
                    'weekend_pattern': weekend_avg if not np.isnan(weekend_avg) else forecast,
                    'weekday_pattern': weekday_avg if not np.isnan(weekday_avg) else forecast
                }
            else:
                hourly_patterns[hour] = {'forecast': 25.0, 'weekend_pattern': 25.0, 'weekday_pattern': 25.0}

        return hourly_patterns

    def trend_analysis_forecast(self, data_array):
        """Trend analysis with momentum indicators"""
        hourly_patterns = {}

        # Recent trend analysis (last 3 days)
        cutoff_time = int(time.time()) - (3 * 24 * 60 * 60)
        recent_mask = data_array['timestamp'] >= cutoff_time
        recent_data = data_array[recent_mask]

        for hour in range(24):
            hour_mask = data_array['hour'] == hour
            hour_data = data_array[hour_mask]['occupancy_ratio']

            recent_hour_mask = (recent_data['hour'] == hour)
            recent_hour_data = recent_data[recent_hour_mask]['occupancy_ratio']

            if len(hour_data) >= 2:
                # Calculate momentum
                momentum = 0
                if len(recent_hour_data) >= 2:
                    recent_avg = np.mean(recent_hour_data)
                    historical_avg = np.mean(hour_data)
                    momentum = (recent_avg - historical_avg) / historical_avg if historical_avg > 0 else 0

                    # Apply momentum to forecast
                    forecast = historical_avg * (1 + momentum * 0.3)  # 30% momentum influence
                else:
                    forecast = np.mean(hour_data)

                forecast = max(5.0, min(95.0, forecast))

                hourly_patterns[hour] = {
                    'forecast': forecast,
                    'momentum': momentum,
                    'recent_avg': np.mean(recent_hour_data) if len(recent_hour_data) > 0 else forecast
                }
            else:
                hourly_patterns[hour] = {'forecast': 25.0, 'momentum': 0, 'recent_avg': 25.0}

        return hourly_patterns

    def context_aware_forecast(self, data_array, current_context):
        """Context-aware forecasting considering current machine state"""
        hourly_patterns = {}
        current_hour = datetime.now().hour
        current_status = current_context.get('status', 'unknown')

        for hour in range(24):
            hour_mask = data_array['hour'] == hour
            hour_data = data_array[hour_mask]['occupancy_ratio']

            if len(hour_data) > 0:
                base_forecast = np.mean(hour_data)

                # Context adjustments
                if hour == current_hour:
                    # Real-time adjustment
                    if current_status == 'occupied':
                        base_forecast *= 1.3  # If currently busy, expect continued busyness
                    elif current_status == 'free':
                        base_forecast *= 0.7  # If currently free, expect lower usage

                # Time-based adjustments
                time_until_hour = (hour - current_hour) % 24
                if time_until_hour <= 2:  # Next 2 hours are more predictable
                    confidence_multiplier = 1.0
                else:  # Further hours are less certain
                    confidence_multiplier = 0.9

                forecast = base_forecast * confidence_multiplier
                forecast = max(5.0, min(95.0, forecast))

                hourly_patterns[hour] = {
                    'forecast': forecast,
                    'context_adjustment': confidence_multiplier,
                    'time_until': time_until_hour
                }
            else:
                hourly_patterns[hour] = {'forecast': 25.0, 'context_adjustment': 1.0, 'time_until': (hour - current_hour) % 24}

        return hourly_patterns

    def ensemble_prediction(self, forecasts):
        """Combine multiple forecasting models using weighted ensemble"""
        # Model weights (can be dynamically adjusted based on historical performance)
        weights = {
            'seasonal_decomposition': 0.3,
            'pattern_recognition': 0.3,
            'trend_analysis': 0.2,
            'context_aware': 0.2
        }

        ensemble_forecast = {}

        for hour in range(24):
            weighted_sum = 0
            total_weight = 0

            for model_name, model_forecast in forecasts.items():
                if hour in model_forecast and 'forecast' in model_forecast[hour]:
                    weight = weights.get(model_name, 0.25)
                    forecast_value = model_forecast[hour]['forecast']

                    weighted_sum += forecast_value * weight
                    total_weight += weight

            if total_weight > 0:
                final_forecast = weighted_sum / total_weight
            else:
                final_forecast = 25.0  # Default fallback

            ensemble_forecast[hour] = {
                'forecast': round(final_forecast, 1),
                'models_used': len([m for m in forecasts.keys() if hour in forecasts[m]]),
                'ensemble_confidence': min(100, total_weight * 100)
            }

        return ensemble_forecast

    def generate_gemini_insights(self, machine_id, data_array, forecast, anomalies):
        """Generate AI insights using Google Gemini API"""
        try:
            # Prepare data summary for Gemini using NumPy operations only
            timestamps = data_array['timestamp']
            start_time = datetime.fromtimestamp(timestamps.min()).strftime('%Y-%m-%d')
            end_time = datetime.fromtimestamp(timestamps.max()).strftime('%Y-%m-%d')

            data_summary = {
                'machine_id': machine_id,
                'total_data_points': len(data_array),
                'date_range': f"{start_time} to {end_time}",
                'avg_occupancy': round(np.mean(data_array['occupancy_ratio']), 1),
                'peak_hours': self.get_peak_hours_numpy(data_array),
                'anomalies_count': len(anomalies),
                'forecast_summary': {hour: data['forecast'] for hour, data in forecast.items()}
            }

            prompt = f"""
            Analyze this gym equipment usage data and provide insights:

            Machine: {machine_id}
            Data Points: {data_summary['total_data_points']}
            Average Occupancy: {data_summary['avg_occupancy']}%
            Peak Hours: {data_summary['peak_hours']}
            Anomalies Detected: {data_summary['anomalies_count']}

            Today's Forecast: {data_summary['forecast_summary']}

            Provide:
            1. Key usage patterns identified
            2. Recommendations for gym members
            3. Operational insights for gym management
            4. Prediction confidence assessment

            Keep response concise and actionable. Format as plain text.
            """

            # Call Gemini API
            headers = {
                'x-goog-api-key': GEMINI_API_KEY,
                'Content-Type': 'application/json'
            }

            payload = {
                'contents': [{
                    'parts': [{'text': prompt}]
                }],
                'generationConfig': {
                    'maxOutputTokens': 500,
                    'temperature': 0.7
                }
            }

            response = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                ai_insights = result['candidates'][0]['content']['parts'][0]['text']
                print(f"🤖 Generated AI insights using Gemini API")
                return ai_insights
            else:
                print(f"❌ Gemini API error: {response.status_code} - {response.text}")
                return self.fallback_insights(machine_id, data_summary)

        except Exception as e:
            print(f"❌ Error calling Gemini API: {str(e)}")
            return self.fallback_insights(machine_id, data_summary)

    def fallback_insights(self, machine_id, data_summary):
        """Fallback insights when AI API fails"""
        avg_occupancy = data_summary['avg_occupancy']
        peak_hours = data_summary['peak_hours']

        if avg_occupancy > 60:
            usage_desc = "High usage"
            recommendation = "Consider visiting during off-peak hours"
        elif avg_occupancy > 30:
            usage_desc = "Moderate usage"
            recommendation = "Good availability most times"
        else:
            usage_desc = "Low usage"
            recommendation = "Generally available"

        return f"{usage_desc} machine. Peak times: {peak_hours}. {recommendation}."

    def calculate_confidence_score(self, data_array, forecasts, anomalies):
        """Calculate overall confidence score for the forecast"""
        # Base confidence from data quantity
        data_confidence = min(100, len(data_array) * 5)  # 5% per data point, max 100%

        # Model agreement confidence
        model_forecasts = []
        for hour in range(24):
            hour_forecasts = []
            for model_name, model_data in forecasts.items():
                if hour in model_data and 'forecast' in model_data[hour]:
                    hour_forecasts.append(model_data[hour]['forecast'])

            if len(hour_forecasts) >= 2:
                model_forecasts.append(np.std(hour_forecasts))

        if model_forecasts:
            agreement_confidence = max(0, 100 - np.mean(model_forecasts))
        else:
            agreement_confidence = 50

        # Anomaly penalty
        anomaly_penalty = min(20, len(anomalies) * 2)  # 2% penalty per anomaly, max 20%

        # Final confidence score
        confidence = (data_confidence * 0.4 + agreement_confidence * 0.5 - anomaly_penalty * 0.1)
        return max(0, min(100, confidence))

    def evaluate_model_performance(self, forecasts):
        """Evaluate individual model performance metrics"""
        performance = {}

        for model_name, model_data in forecasts.items():
            valid_forecasts = len([h for h in model_data.values() if 'forecast' in h])
            avg_forecast = np.mean([h['forecast'] for h in model_data.values() if 'forecast' in h])

            performance[model_name] = {
                'coverage': round(valid_forecasts / 24 * 100, 1),  # Percentage of hours covered
                'avg_prediction': round(avg_forecast, 1),
                'status': 'active' if valid_forecasts >= 12 else 'limited_data'
            }

        return performance

    # Helper methods
    def is_peak_hour(self, hour):
        """Determine if hour is typically a peak usage hour"""
        return hour in [7, 8, 12, 13, 18, 19, 20]

    def calculate_trend(self, values):
        """Calculate simple linear trend"""
        if len(values) < 2:
            return 0
        x = np.arange(len(values))
        return np.polyfit(x, values, 1)[0]  # Slope of linear fit

    def get_peak_hours_numpy(self, data_array):
        """Identify peak usage hours from data using NumPy only"""
        hourly_avg = {}

        # Calculate average occupancy per hour using NumPy
        for hour in range(24):
            hour_mask = data_array['hour'] == hour
            hour_data = data_array[hour_mask]['occupancy_ratio']
            if len(hour_data) > 0:
                hourly_avg[hour] = np.mean(hour_data)

        if hourly_avg:
            # Calculate 75th percentile threshold
            avg_values = list(hourly_avg.values())
            peak_threshold = np.percentile(avg_values, 75)

            # Find hours above threshold
            peak_hours = [hour for hour, avg in hourly_avg.items() if avg >= peak_threshold]
            return peak_hours
        else:
            return [7, 8, 18, 19, 20]  # Default peak hours

    def fallback_forecast(self, machine_id, current_context):
        """Simple fallback when ML models fail"""
        # Basic pattern based on typical gym usage
        basic_pattern = {
            6: 50, 7: 70, 8: 75, 9: 60, 10: 40, 11: 45,
            12: 60, 13: 55, 14: 35, 15: 30, 16: 35, 17: 50,
            18: 80, 19: 85, 20: 80, 21: 65, 22: 40, 23: 25,
            0: 15, 1: 10, 2: 5, 3: 5, 4: 5, 5: 15
        }

        forecast_hours = {}
        for hour, usage in basic_pattern.items():
            forecast_hours[hour] = {
                'forecast': usage,
                'models_used': 0,
                'ensemble_confidence': 30
            }

        return {
            'machine_id': machine_id,
            'forecast_hours': forecast_hours,
            'confidence_score': 30,
            'anomalies_detected': 0,
            'ai_insights': f"Basic forecast for {machine_id} - insufficient data for ML models",
            'model_performance': {},
            'generated_at': datetime.now().isoformat()
        }

# Initialize ML engine instance
ml_engine = MLForecastEngine()

def lambda_handler(event, context):
    """
    AWS Lambda handler for GymPulse API requests
    """
    try:
        
        # Extract HTTP method and path
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        print(f"API Request: {http_method} {path}")
        
        # Add CORS headers to all responses
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept',
            'Access-Control-Max-Age': '86400'
        }
        
        # Handle CORS preflight requests
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        # Route requests
        if path == '/branches' and http_method == 'GET':
            return handle_branches_request(event, context, cors_headers)
        elif path.startswith('/branches/') and path.endswith('/machines') and http_method == 'GET':
            return handle_machines_request(event, context, cors_headers)
        elif path.startswith('/machines/') and '/history' in path and http_method == 'GET':
            return handle_machine_history_request(event, context, cors_headers)
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    **cors_headers
                },
                'body': json.dumps({'error': 'Endpoint not found'})
            }
    
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        # Create default CORS headers in case of early exception
        cors_headers = {
            'Access-Control-Allow-Origin': 'http://localhost:3000',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps({'error': 'Internal server error'})
        }

def handle_branches_request(event, context, cors_headers):
    """
    Handle GET /branches - return all branches with machine counts
    """
    try:
        # Get current machine states (for live status)
        response = current_state_table.scan()
        live_machines = {machine['machineId']: machine for machine in response['Items']}
        
        # Complete machine configuration from simulator config
        machine_config = {
            'hk-central': {
                'machines': [
                    {'machineId': 'leg-press-01', 'name': 'Leg Press Machine 1', 'category': 'legs', 'type': 'leg-press'},
                    {'machineId': 'leg-press-02', 'name': 'Leg Press Machine 2', 'category': 'legs', 'type': 'leg-press'},
                    {'machineId': 'squat-rack-01', 'name': 'Squat Rack 1', 'category': 'legs', 'type': 'squat-rack'},
                    {'machineId': 'calf-raise-01', 'name': 'Calf Raise Machine 1', 'category': 'legs', 'type': 'calf-raise'},
                    {'machineId': 'bench-press-01', 'name': 'Bench Press 1', 'category': 'chest', 'type': 'bench-press'},
                    {'machineId': 'bench-press-02', 'name': 'Bench Press 2', 'category': 'chest', 'type': 'bench-press'},
                    {'machineId': 'chest-fly-01', 'name': 'Chest Fly Machine 1', 'category': 'chest', 'type': 'chest-fly'},
                    {'machineId': 'lat-pulldown-01', 'name': 'Lat Pulldown 1', 'category': 'back', 'type': 'lat-pulldown'},
                    {'machineId': 'rowing-01', 'name': 'Rowing Machine 1', 'category': 'back', 'type': 'rowing'},
                    {'machineId': 'pull-up-01', 'name': 'Pull-up Station 1', 'category': 'back', 'type': 'pull-up'}
                ]
            },
            'hk-causeway': {
                'machines': [
                    {'machineId': 'leg-press-03', 'name': 'Leg Press Machine 3', 'category': 'legs', 'type': 'leg-press'},
                    {'machineId': 'squat-rack-02', 'name': 'Squat Rack 2', 'category': 'legs', 'type': 'squat-rack'},
                    {'machineId': 'leg-curl-01', 'name': 'Leg Curl Machine 1', 'category': 'legs', 'type': 'leg-curl'},
                    {'machineId': 'bench-press-03', 'name': 'Bench Press 3', 'category': 'chest', 'type': 'bench-press'},
                    {'machineId': 'incline-press-01', 'name': 'Incline Press 1', 'category': 'chest', 'type': 'incline-press'},
                    {'machineId': 'dips-01', 'name': 'Dips Station 1', 'category': 'chest', 'type': 'dips'},
                    {'machineId': 'lat-pulldown-02', 'name': 'Lat Pulldown 2', 'category': 'back', 'type': 'lat-pulldown'},
                    {'machineId': 'rowing-02', 'name': 'Rowing Machine 2', 'category': 'back', 'type': 'rowing'},
                    {'machineId': 't-bar-row-01', 'name': 'T-Bar Row 1', 'category': 'back', 'type': 't-bar-row'}
                ]
            }
        }
        
        # Branch configuration
        branches = {
            'hk-central': {
                'id': 'hk-central',
                'name': 'Central Branch',
                'coordinates': {'lat': 22.2819, 'lon': 114.1577}
            },
            'hk-causeway': {
                'id': 'hk-causeway', 
                'name': 'Causeway Bay Branch',
                'coordinates': {'lat': 22.2783, 'lon': 114.1747}
            }
        }
        
        # Count machines by branch and category using complete configuration
        for branch_id in branches.keys():
            categories = {'legs': {'free': 0, 'total': 0}, 
                         'chest': {'free': 0, 'total': 0}, 
                         'back': {'free': 0, 'total': 0}}
            
            # Use configured machines instead of only live machines
            if branch_id in machine_config:
                for machine_def in machine_config[branch_id]['machines']:
                    machine_id = machine_def['machineId']
                    category = machine_def['category']
                    
                    if category in categories:
                        categories[category]['total'] += 1
                        
                        # Check if machine is live and get its status
                        live_machine = live_machines.get(machine_id)
                        if live_machine and live_machine.get('status') == 'free':
                            categories[category]['free'] += 1
                        elif live_machine and live_machine.get('status') == 'occupied':
                            # Occupied - don't count as free
                            pass  
                        else:
                            # Machine not connected yet - assume available
                            categories[category]['free'] += 1
            
            branches[branch_id]['categories'] = categories
        
        result = list(branches.values())
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps(result, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error in handle_branches_request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps({'error': f'Failed to retrieve branches: {str(e)}'})
        }

def handle_machines_request(event, context, cors_headers):
    """
    Handle GET /branches/{branchId}/categories/{category}/machines
    """
    try:
        # Extract path parameters
        path_params = event.get('pathParameters') or {}
        branch_id = path_params.get('branchId')
        category = path_params.get('category')
        
        # Get current machine states (for live status)
        response = current_state_table.scan()
        live_machines = {machine['machineId']: machine for machine in response['Items']}
        
        # Complete machine configuration (same as in branches API)
        machine_config = {
            'hk-central': {
                'machines': [
                    {'machineId': 'leg-press-01', 'name': 'Leg Press Machine 1', 'category': 'legs', 'type': 'leg-press'},
                    {'machineId': 'leg-press-02', 'name': 'Leg Press Machine 2', 'category': 'legs', 'type': 'leg-press'},
                    {'machineId': 'squat-rack-01', 'name': 'Squat Rack 1', 'category': 'legs', 'type': 'squat-rack'},
                    {'machineId': 'calf-raise-01', 'name': 'Calf Raise Machine 1', 'category': 'legs', 'type': 'calf-raise'},
                    {'machineId': 'bench-press-01', 'name': 'Bench Press 1', 'category': 'chest', 'type': 'bench-press'},
                    {'machineId': 'bench-press-02', 'name': 'Bench Press 2', 'category': 'chest', 'type': 'bench-press'},
                    {'machineId': 'chest-fly-01', 'name': 'Chest Fly Machine 1', 'category': 'chest', 'type': 'chest-fly'},
                    {'machineId': 'lat-pulldown-01', 'name': 'Lat Pulldown 1', 'category': 'back', 'type': 'lat-pulldown'},
                    {'machineId': 'rowing-01', 'name': 'Rowing Machine 1', 'category': 'back', 'type': 'rowing'},
                    {'machineId': 'pull-up-01', 'name': 'Pull-up Station 1', 'category': 'back', 'type': 'pull-up'}
                ]
            },
            'hk-causeway': {
                'machines': [
                    {'machineId': 'leg-press-03', 'name': 'Leg Press Machine 3', 'category': 'legs', 'type': 'leg-press'},
                    {'machineId': 'squat-rack-02', 'name': 'Squat Rack 2', 'category': 'legs', 'type': 'squat-rack'},
                    {'machineId': 'leg-curl-01', 'name': 'Leg Curl Machine 1', 'category': 'legs', 'type': 'leg-curl'},
                    {'machineId': 'bench-press-03', 'name': 'Bench Press 3', 'category': 'chest', 'type': 'bench-press'},
                    {'machineId': 'incline-press-01', 'name': 'Incline Press 1', 'category': 'chest', 'type': 'incline-press'},
                    {'machineId': 'dips-01', 'name': 'Dips Station 1', 'category': 'chest', 'type': 'dips'},
                    {'machineId': 'lat-pulldown-02', 'name': 'Lat Pulldown 2', 'category': 'back', 'type': 'lat-pulldown'},
                    {'machineId': 'rowing-02', 'name': 'Rowing Machine 2', 'category': 'back', 'type': 'rowing'},
                    {'machineId': 't-bar-row-01', 'name': 'T-Bar Row 1', 'category': 'back', 'type': 't-bar-row'}
                ]
            }
        }
        
        # Filter machines by branch and category from configuration
        machine_list = []
        if branch_id in machine_config:
            for machine_def in machine_config[branch_id]['machines']:
                if machine_def['category'] == category:
                    machine_id = machine_def['machineId']
                    live_machine = live_machines.get(machine_id)
                    
                    # Determine status
                    if live_machine:
                        status = live_machine.get('status', 'unknown')
                        last_update = live_machine.get('lastUpdate')
                    else:
                        # Machine not connected yet - show as available
                        status = 'free'
                        last_update = None
                    
                    machine_list.append({
                        'machineId': machine_id,
                        'name': machine_def['name'],
                        'status': status,
                        'lastUpdate': last_update,
                        'category': category,
                        'gymId': branch_id,
                        'type': machine_def['type'],
                        'alertEligible': status == 'occupied'
                    })
        
        result = {
            'machines': machine_list,
            'branchId': branch_id,
            'category': category,
            'totalCount': len(machine_list),
            'freeCount': len([m for m in machine_list if m['status'] == 'free']),
            'occupiedCount': len([m for m in machine_list if m['status'] == 'occupied'])
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps(result, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error in handle_machines_request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps({'error': f'Failed to retrieve machines: {str(e)}'})
        }

def handle_machine_history_request(event, context, cors_headers):
    """
    Handle GET /machines/{machineId}/history - return usage history for heatmap
    """
    import time
    from datetime import datetime, timedelta
    
    try:
        # Extract machine ID from path
        path = event.get('path', '')
        # Path format: /machines/{machineId}/history
        path_parts = path.split('/')
        if len(path_parts) >= 3:
            machine_id = path_parts[2]
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', **cors_headers},
                'body': json.dumps({'error': 'Missing machine ID'})
            }
        
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        range_param = query_params.get('range', '24h')
        
        print(f"Fetching history for machine: {machine_id}, range: {range_param}")
        
        # Get machine info from current state to find category and gymId
        machine_response = current_state_table.get_item(Key={'machineId': machine_id})
        if 'Item' not in machine_response:
            # If machine not found, return empty usage data
            print(f"Machine {machine_id} not found in current state")
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', **cors_headers},
                'body': json.dumps({'usageData': [], 'machineId': machine_id})
            }
        
        machine = machine_response['Item']
        gym_id = machine.get('gymId')
        category = machine.get('category')
        
        if not gym_id or not category:
            print(f"Missing gymId or category for machine {machine_id}")
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', **cors_headers},
                'body': json.dumps({'usageData': [], 'machineId': machine_id})
            }
        
        # Calculate time range - expand to include existing historical data
        current_time = int(time.time())
        start_time = current_time - (20 * 24 * 60 * 60)  # 20 days ago to include existing data
        
        # Query aggregates table for this gym/category combination
        gym_category_key = f"{gym_id}_{category}"
        
        response = aggregates_table.query(
            KeyConditionExpression='gymId_category = :gck AND timestamp15min BETWEEN :start AND :end',
            ExpressionAttributeValues={
                ':gck': gym_category_key,
                ':start': start_time,
                ':end': current_time
            },
            ScanIndexForward=True  # Sort by timestamp ascending
        )
        
        aggregates = response.get('Items', [])
        print(f"Found {len(aggregates)} aggregate records for {gym_category_key}")
        
        # Convert aggregates to hourly usage data for heatmap
        usage_data = []
        
        # Group aggregates by hour
        hourly_data = {}
        for aggregate in aggregates:
            timestamp = int(aggregate['timestamp15min'])
            hour = datetime.fromtimestamp(timestamp).hour
            occupancy_ratio = float(aggregate.get('occupancyRatio', 0))
            
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(occupancy_ratio)
        
        # Generate real forecast based on historical data only
        current_hour = datetime.now().hour

        # Only generate forecast if we have sufficient historical data
        if len(hourly_data) < 12:  # Need at least 12 hours of historical data for meaningful forecast
            usage_data = []
        else:
            # Real forecasting system: hourly updated predictions for today
            for hour in range(24):
                if hour < current_hour:
                    # Past hours: use actual historical data if available
                    if hour in hourly_data:
                        avg_usage_percentage = sum(hourly_data[hour]) / len(hourly_data[hour])
                    else:
                        continue  # Skip hours without historical data
                    data_type = 'historical'
                elif hour == current_hour:
                    # Current hour: blend historical pattern with real-time adjustment
                    if hour in hourly_data:
                        historical_avg = sum(hourly_data[hour]) / len(hourly_data[hour])
                        # Adjust based on current machine status (simple real-time correction)
                        current_status = machine.get('status', 'unknown')
                        if current_status == 'occupied':
                            avg_usage_percentage = min(95.0, historical_avg * 1.2)  # Increase if currently occupied
                        else:
                            avg_usage_percentage = max(5.0, historical_avg * 0.8)   # Decrease if currently free
                    else:
                        continue  # Skip if no historical data for current hour
                    data_type = 'current'
                else:
                    # Future hours: forecast based on historical patterns
                    if hour in hourly_data:
                        # Base forecast on historical average
                        historical_avg = sum(hourly_data[hour]) / len(hourly_data[hour])

                        # Apply trend adjustment based on recent hours' real vs predicted performance
                        # (This is where hourly updates would improve accuracy)
                        trend_adjustment = 1.0  # Placeholder for trend learning
                        avg_usage_percentage = historical_avg * trend_adjustment
                    else:
                        continue  # Skip future hours without historical baseline
                    data_type = 'forecast'

                usage_data.append({
                    'hour': hour,
                    'day_of_week': datetime.now().weekday(),
                    'usage_percentage': round(avg_usage_percentage, 1),
                    'timestamp': datetime.now().isoformat(),
                    'predicted_free_time': int((100 - avg_usage_percentage) * 60 / 100) if avg_usage_percentage < 100 else 0,
                    'data_type': data_type,  # 'historical', 'current', or 'forecast'
                    'confidence': 'high' if data_type == 'historical' else 'medium' if data_type == 'current' else 'low'
                })
        
        # Include current status information from the machine data we already fetched
        current_status = {
            'status': machine.get('status', 'unknown'),
            'lastUpdate': int(machine.get('lastUpdate', 0)),
            'gymId': gym_id,
            'category': category,
            'name': machine.get('name', machine_id),
            'alertEligible': machine.get('status') == 'occupied'
        }
        
        # 🤖 AI-POWERED FORECASTING using ML models
        forecast = {}

        if len(usage_data) > 0:
            try:
                # Call ML forecasting engine
                ml_forecast = invoke_ml_forecast_engine(machine_id, aggregates, machine)

                if ml_forecast and 'forecast_hours' in ml_forecast:
                    current_hour = datetime.now().hour
                    next_hour = (current_hour + 1) % 24

                    current_forecast = ml_forecast['forecast_hours'].get(str(current_hour), {}).get('forecast', 50)
                    next_forecast = ml_forecast['forecast_hours'].get(str(next_hour), {}).get('forecast', 50)

                    # 30-minute interpolation using AI forecasts
                    thirty_min_usage = (current_forecast + next_forecast) / 2

                    forecast = {
                        'likelyFreeIn30m': thirty_min_usage < 40,
                        'classification': 'likely_free' if thirty_min_usage < 40 else 'unlikely_free',
                        'display_text': 'AI: Likely free soon' if thirty_min_usage < 40 else 'AI: Busy period',
                        'color': 'green' if thirty_min_usage < 40 else 'red',
                        'confidence': ml_forecast.get('confidence_score', 75),
                        'show_to_user': True,
                        'forecast_usage': round(thirty_min_usage, 1),
                        'based_on_ai': True,
                        'ml_insights': ml_forecast.get('ai_insights', ''),
                        'models_used': ml_forecast['forecast_hours'].get(str(current_hour), {}).get('models_used', 4),
                        'anomalies_detected': ml_forecast.get('anomalies_detected', 0)
                    }

                    print(f"🤖 AI forecast for {machine_id}: {thirty_min_usage}% (confidence: {forecast['confidence']}%)")
                else:
                    raise Exception("ML engine returned invalid format")

            except Exception as e:
                print(f"⚠️  ML forecasting failed for {machine_id}: {str(e)}, falling back to statistical forecast")

                # Fallback to statistical forecasting
                current_hour = datetime.now().hour
                current_usage = next((item['usage_percentage'] for item in usage_data if item['hour'] == current_hour), None)
                next_hour_usage = next((item['usage_percentage'] for item in usage_data if item['hour'] == (current_hour + 1) % 24), None)

                if current_usage is not None and next_hour_usage is not None:
                    thirty_min_usage = (current_usage + next_hour_usage) / 2

                    forecast = {
                        'likelyFreeIn30m': thirty_min_usage < 40,
                        'classification': 'likely_free' if thirty_min_usage < 40 else 'unlikely_free',
                        'display_text': 'Likely free soon' if thirty_min_usage < 40 else 'Busy period',
                        'color': 'green' if thirty_min_usage < 40 else 'red',
                        'confidence': 60,  # Lower confidence for statistical model
                        'show_to_user': True,
                        'forecast_usage': round(thirty_min_usage, 1),
                        'based_on_ai': False
                    }
                else:
                    forecast = {
                        'likelyFreeIn30m': False,
                        'classification': 'insufficient_data',
                        'display_text': 'Forecast unavailable',
                        'color': 'gray',
                        'confidence': 0,
                        'show_to_user': False,
                        'based_on_ai': False
                    }
        else:
            # No data at all
            forecast = {
                'likelyFreeIn30m': False,
                'classification': 'no_data',
                'display_text': 'No historical data',
                'color': 'gray',
                'confidence': 0,
                'show_to_user': False,
                'based_on_ai': False
            }
        
        result = {
            'usageData': usage_data,
            'machineId': machine_id,
            'gymId': gym_id,
            'category': category,
            'currentStatus': current_status,
            'forecast': forecast,
            'dataPoints': len(aggregates),
            'timeRange': f"{range_param} ({len(aggregates)} 15-min intervals)"
        }
        
        print(f"Returning {len(usage_data)} hourly usage points")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps(result, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error in handle_machine_history_request: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps({'error': f'Failed to retrieve machine history: {str(e)}'})
        }

def decimal_default(obj):
    """
    JSON serializer for objects not serializable by default json code
    """
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def invoke_ml_forecast_engine(machine_id, historical_data, machine_context):
    """
    Use integrated AI-powered ML forecasting engine
    """
    try:
        print(f"🚀 Using integrated ML forecasting engine for {machine_id}")

        # Use the integrated ML engine instance
        ml_result = ml_engine.generate_ai_forecast(machine_id, historical_data, machine_context)

        if ml_result and 'forecast_hours' in ml_result:
            print(f"✅ ML forecast successful with {ml_result.get('confidence_score', 0):.1f}% confidence")
            return ml_result
        else:
            print(f"⚠️ ML engine returned invalid result, using fallback")
            return generate_lightweight_ml_forecast(machine_id, historical_data, machine_context)

    except Exception as e:
        print(f"❌ Integrated ML engine failed: {str(e)}, using fallback")
        return generate_lightweight_ml_forecast(machine_id, historical_data, machine_context)

def generate_lightweight_ml_forecast(machine_id, historical_data, machine_context):
    """
    Lightweight ML-inspired forecasting when full ML engine is unavailable
    """
    try:
        print(f"🤖 Generating lightweight AI forecast for {machine_id}")

        # Basic ML-style analysis
        hourly_patterns = {}
        current_hour = datetime.now().hour

        # Process historical data
        for record in historical_data:
            timestamp = int(record['timestamp15min'])
            hour = datetime.fromtimestamp(timestamp).hour
            occupancy_ratio = float(record.get('occupancyRatio', 0))

            if hour not in hourly_patterns:
                hourly_patterns[hour] = []
            hourly_patterns[hour].append(occupancy_ratio)

        # Generate forecast for each hour
        forecast_hours = {}
        confidence_scores = []

        for hour in range(24):
            if hour in hourly_patterns and len(hourly_patterns[hour]) >= 3:
                # Statistical analysis
                values = hourly_patterns[hour]
                mean_usage = sum(values) / len(values)

                # Simple trend detection
                recent_values = values[-5:] if len(values) >= 5 else values
                historical_values = values[:-5] if len(values) >= 10 else values[:len(values)//2]

                if len(recent_values) > 0 and len(historical_values) > 0:
                    recent_avg = sum(recent_values) / len(recent_values)
                    historical_avg = sum(historical_values) / len(historical_values)
                    trend = (recent_avg - historical_avg) / historical_avg if historical_avg > 0 else 0
                else:
                    trend = 0

                # Apply trend to forecast
                forecast = mean_usage * (1 + trend * 0.2)  # 20% trend influence

                # Context adjustment for current hour
                if hour == current_hour:
                    current_status = machine_context.get('status', 'unknown')
                    if current_status == 'occupied':
                        forecast *= 1.2
                    elif current_status == 'free':
                        forecast *= 0.8

                # Clamp to reasonable range
                forecast = max(5.0, min(95.0, forecast))

                # Calculate confidence based on data quantity and consistency
                data_confidence = min(100, len(values) * 5)
                consistency = 100 - (max(values) - min(values)) if len(values) > 1 else 50

                hour_confidence = (data_confidence + consistency) / 2
                confidence_scores.append(hour_confidence)

                forecast_hours[str(hour)] = {
                    'forecast': round(forecast, 1),
                    'models_used': 2,  # "trend" and "statistical"
                    'confidence': round(hour_confidence, 1),
                    'data_points': len(values),
                    'trend': round(trend, 3)
                }
            else:
                # Default pattern for hours without sufficient data
                default_patterns = {
                    6: 60, 7: 70, 8: 65, 9: 50, 10: 40, 11: 45,
                    12: 55, 13: 50, 14: 35, 15: 30, 16: 35, 17: 50,
                    18: 75, 19: 80, 20: 75, 21: 60, 22: 40, 23: 25,
                    0: 15, 1: 10, 2: 5, 3: 5, 4: 5, 5: 20
                }

                forecast_hours[str(hour)] = {
                    'forecast': default_patterns.get(hour, 25),
                    'models_used': 1,  # "default_pattern"
                    'confidence': 25,
                    'data_points': 0,
                    'trend': 0
                }

        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 30

        # Generate AI-style insights
        peak_hours = [h for h, data in forecast_hours.items() if data['forecast'] > 60]
        quiet_hours = [h for h, data in forecast_hours.items() if data['forecast'] < 30]

        ai_insights = f"Analysis for {machine_id}: Peak usage expected at hours {peak_hours}, quieter periods at {quiet_hours}. Confidence: {overall_confidence:.0f}%"

        result = {
            'machine_id': machine_id,
            'forecast_hours': forecast_hours,
            'confidence_score': round(overall_confidence, 1),
            'anomalies_detected': 0,  # Simplified for lightweight version
            'ai_insights': ai_insights,
            'model_performance': {
                'statistical_analysis': {'status': 'active', 'coverage': len(hourly_patterns)},
                'trend_detection': {'status': 'active', 'coverage': 100},
                'context_awareness': {'status': 'active', 'coverage': 100}
            },
            'generated_at': datetime.now().isoformat(),
            'ml_version': 'lightweight'
        }

        print(f"✅ Lightweight AI forecast generated with {overall_confidence:.1f}% confidence")
        return result

    except Exception as e:
        print(f"❌ Lightweight ML forecast failed: {str(e)}")
        return None
