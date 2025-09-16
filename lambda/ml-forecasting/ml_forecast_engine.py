import json
import boto3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time
from decimal import Decimal
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Google Gemini API for AI-powered insights
# Free tier with excellent performance for Hong Kong region
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if local) or Lambda environment
load_dotenv()

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

class MLForecastEngine:
    """
    AI-Powered Gym Equipment Forecasting Engine

    Features:
    1. Time Series Forecasting with Multiple Models
    2. Anomaly Detection for Unusual Patterns
    3. Amazon Bedrock Integration for AI Insights
    4. Real-time Model Updates
    5. Multi-feature Prediction (weather, events, seasonality)
    """

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.events_table = self.dynamodb.Table('gym-pulse-events')
        self.aggregates_table = self.dynamodb.Table('gym-pulse-aggregates')
        self.current_state_table = self.dynamodb.Table('gym-pulse-current-state')

        # ML Models
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()

    def generate_ai_forecast(self, machine_id, historical_data, current_context):
        """
        Main AI forecasting function combining multiple ML approaches
        """
        print(f"🤖 Starting AI forecast generation for {machine_id}")

        try:
            # 1. Prepare time series data
            df = self.prepare_time_series_data(historical_data)

            if len(df) < 48:  # Need at least 2 days of data
                return self.fallback_forecast(machine_id, current_context)

            # 2. Detect anomalies in historical data
            anomalies = self.detect_anomalies(df)

            # 3. Generate multiple forecasting models
            forecasts = {
                'seasonal_decomposition': self.seasonal_decomposition_forecast(df),
                'pattern_recognition': self.pattern_recognition_forecast(df),
                'trend_analysis': self.trend_analysis_forecast(df),
                'context_aware': self.context_aware_forecast(df, current_context)
            }

            # 4. Ensemble prediction combining all models
            ensemble_forecast = self.ensemble_prediction(forecasts)

            # 5. AI insights using Amazon Bedrock
            ai_insights = self.generate_gemini_insights(machine_id, df, ensemble_forecast, anomalies)

            # 6. Real-time confidence scoring
            confidence_score = self.calculate_confidence_score(df, forecasts, anomalies)

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
        """Convert historical data to pandas DataFrame for ML processing"""

        data_points = []
        for record in historical_data:
            data_points.append({
                'timestamp': datetime.fromtimestamp(record['timestamp15min']),
                'occupancy_ratio': float(record['occupancyRatio']),
                'hour': datetime.fromtimestamp(record['timestamp15min']).hour,
                'day_of_week': datetime.fromtimestamp(record['timestamp15min']).weekday(),
                'is_weekend': datetime.fromtimestamp(record['timestamp15min']).weekday() >= 5,
                'is_peak_hour': self.is_peak_hour(datetime.fromtimestamp(record['timestamp15min']).hour)
            })

        df = pd.DataFrame(data_points)
        df = df.sort_values('timestamp')
        df.set_index('timestamp', inplace=True)

        return df

    def detect_anomalies(self, df):
        """Use Isolation Forest to detect unusual usage patterns"""

        # Feature engineering for anomaly detection
        features = ['occupancy_ratio', 'hour', 'day_of_week', 'is_weekend', 'is_peak_hour']
        X = df[features].values

        # Normalize features
        X_scaled = self.scaler.fit_transform(X)

        # Detect anomalies
        anomaly_labels = self.anomaly_detector.fit_predict(X_scaled)

        # Extract anomalous points
        anomalies = df[anomaly_labels == -1].copy()
        anomalies['anomaly_score'] = self.anomaly_detector.decision_function(X_scaled)[anomaly_labels == -1]

        print(f"🔍 Detected {len(anomalies)} anomalies in historical data")

        return anomalies

    def seasonal_decomposition_forecast(self, df):
        """Seasonal decomposition with trend analysis"""

        hourly_patterns = {}

        # Group by hour and calculate statistics
        for hour in range(24):
            hour_data = df[df['hour'] == hour]['occupancy_ratio']

            if len(hour_data) > 0:
                # Calculate seasonal patterns
                mean_usage = hour_data.mean()
                std_usage = hour_data.std()
                trend = self.calculate_trend(hour_data.values)

                # Apply trend to mean
                forecast = max(5.0, min(95.0, mean_usage + trend))

                hourly_patterns[hour] = {
                    'forecast': forecast,
                    'confidence': min(100, len(hour_data) * 5),  # More data = higher confidence
                    'trend': trend
                }
            else:
                hourly_patterns[hour] = {'forecast': 25.0, 'confidence': 20, 'trend': 0}

        return hourly_patterns

    def pattern_recognition_forecast(self, df):
        """Advanced pattern recognition using statistical analysis"""

        hourly_patterns = {}

        for hour in range(24):
            hour_data = df[df['hour'] == hour]

            if len(hour_data) >= 3:
                # Pattern analysis
                weekend_avg = hour_data[hour_data['is_weekend'] == True]['occupancy_ratio'].mean()
                weekday_avg = hour_data[hour_data['is_weekend'] == False]['occupancy_ratio'].mean()

                # Current day context
                current_is_weekend = datetime.now().weekday() >= 5

                if pd.notna(weekend_avg) and pd.notna(weekday_avg):
                    if current_is_weekend:
                        forecast = weekend_avg
                    else:
                        forecast = weekday_avg
                else:
                    forecast = hour_data['occupancy_ratio'].mean()

                # Apply smoothing
                forecast = max(5.0, min(95.0, forecast))

                hourly_patterns[hour] = {
                    'forecast': forecast,
                    'weekend_pattern': weekend_avg if pd.notna(weekend_avg) else forecast,
                    'weekday_pattern': weekday_avg if pd.notna(weekday_avg) else forecast
                }
            else:
                hourly_patterns[hour] = {'forecast': 25.0, 'weekend_pattern': 25.0, 'weekday_pattern': 25.0}

        return hourly_patterns

    def trend_analysis_forecast(self, df):
        """Trend analysis with momentum indicators"""

        hourly_patterns = {}

        # Recent trend analysis (last 3 days)
        recent_data = df[df.index >= (datetime.now() - timedelta(days=3))]

        for hour in range(24):
            hour_data = df[df['hour'] == hour]['occupancy_ratio']
            recent_hour_data = recent_data[recent_data['hour'] == hour]['occupancy_ratio']

            if len(hour_data) >= 3:
                # Calculate momentum
                if len(recent_hour_data) >= 2:
                    recent_avg = recent_hour_data.mean()
                    historical_avg = hour_data.mean()
                    momentum = (recent_avg - historical_avg) / historical_avg if historical_avg > 0 else 0

                    # Apply momentum to forecast
                    forecast = historical_avg * (1 + momentum * 0.3)  # 30% momentum influence
                else:
                    forecast = hour_data.mean()

                forecast = max(5.0, min(95.0, forecast))

                hourly_patterns[hour] = {
                    'forecast': forecast,
                    'momentum': momentum if 'momentum' in locals() else 0,
                    'recent_avg': recent_hour_data.mean() if len(recent_hour_data) > 0 else forecast
                }
            else:
                hourly_patterns[hour] = {'forecast': 25.0, 'momentum': 0, 'recent_avg': 25.0}

        return hourly_patterns

    def context_aware_forecast(self, df, current_context):
        """Context-aware forecasting considering current machine state and external factors"""

        hourly_patterns = {}
        current_hour = datetime.now().hour
        current_status = current_context.get('status', 'unknown')

        for hour in range(24):
            hour_data = df[df['hour'] == hour]['occupancy_ratio']

            if len(hour_data) > 0:
                base_forecast = hour_data.mean()

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

    def generate_gemini_insights(self, machine_id, df, forecast, anomalies):
        """Generate AI insights using Google Gemini API"""

        try:
            # Prepare data summary for Gemini
            data_summary = {
                'machine_id': machine_id,
                'total_data_points': len(df),
                'date_range': f"{df.index.min()} to {df.index.max()}",
                'avg_occupancy': round(df['occupancy_ratio'].mean(), 1),
                'peak_hours': self.get_peak_hours(df),
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

    def calculate_confidence_score(self, df, forecasts, anomalies):
        """Calculate overall confidence score for the forecast"""

        # Base confidence from data quantity
        data_confidence = min(100, len(df) * 2)  # 2% per data point, max 100%

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

    def get_peak_hours(self, df):
        """Identify peak usage hours from data"""
        hourly_avg = df.groupby('hour')['occupancy_ratio'].mean()
        peak_threshold = hourly_avg.quantile(0.75)  # Top 25%
        peak_hours = hourly_avg[hourly_avg >= peak_threshold].index.tolist()
        return peak_hours

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


def lambda_handler(event, context):
    """Lambda handler for ML-powered forecasting"""

    try:
        machine_id = event.get('machine_id')
        if not machine_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'machine_id required'})
            }

        # Initialize ML engine
        ml_engine = MLForecastEngine()

        # Get historical data
        end_time = int(time.time())
        start_time = end_time - (20 * 24 * 60 * 60)  # 20 days

        response = ml_engine.aggregates_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('machineId').eq(machine_id) &
                                  boto3.dynamodb.conditions.Key('timestamp15min').between(start_time, end_time),
            ScanIndexForward=False
        )

        historical_data = response['Items']

        # Get current context
        current_response = ml_engine.current_state_table.get_item(Key={'machineId': machine_id})
        current_context = current_response.get('Item', {})

        # Generate AI-powered forecast
        forecast_result = ml_engine.generate_ai_forecast(machine_id, historical_data, current_context)

        return {
            'statusCode': 200,
            'body': json.dumps(forecast_result, default=str)
        }

    except Exception as e:
        print(f"Error in ML forecasting: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }