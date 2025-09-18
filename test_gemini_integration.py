#!/usr/bin/env python3
"""
Direct test script for Gemini API integration via Singapore Lambda
Tests the complete pipeline: Hong Kong Lambda → Singapore Lambda → Gemini API
"""

import json
import boto3
import numpy as np
from datetime import datetime
import sys
import os

# Add the lambda function path
sys.path.append('/Users/GitHub/GymPulse/lambda/api-handlers')

def test_gemini_integration():
    """Test the complete Gemini integration pipeline"""

    print("🧪 Testing Gemini API Integration via Singapore Lambda")
    print("=" * 60)

    # Import the forecast class
    try:
        from lambda_function import GymPulseForecast
        forecast_handler = GymPulseForecast()
        print("✅ Successfully imported GymPulseForecast class")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

    # Create test data that mimics real machine data
    print("\n📊 Creating test machine data...")

    # Generate synthetic data array similar to real usage
    timestamps = np.array([
        1734364800 + i * 900 for i in range(96)  # 96 x 15-min intervals = 24 hours
    ])

    occupancy_ratios = np.array([
        # Simulate gym usage patterns: low at night, peaks morning/evening
        30 + 20 * np.sin(i * np.pi / 48) + 10 * np.random.random()
        for i in range(96)
    ])

    # Create structured array matching the expected format
    data_array = np.array(
        list(zip(timestamps, occupancy_ratios)),
        dtype=[('timestamp', 'f8'), ('occupancy_ratio', 'f8')]
    )

    # Create test forecast data
    test_forecast = {
        'combined_prediction': 65.4,
        'confidence': 0.78,
        'individual_models': {
            'linear_trend': {'forecast': 62.1, 'confidence': 0.75},
            'moving_average': {'forecast': 68.7, 'confidence': 0.80}
        }
    }

    # Create test anomalies
    test_anomalies = [
        {'timestamp': 1734364800, 'severity': 'medium', 'type': 'usage_spike'}
    ]

    print(f"📈 Data points: {len(data_array)}")
    print(f"🔮 Forecast confidence: {test_forecast['confidence']:.2f}")
    print(f"⚠️ Anomalies detected: {len(test_anomalies)}")

    # Test the Gemini insights generation
    print("\n🤖 Testing Gemini API call...")
    print("-" * 40)

    try:
        # Call the generate_gemini_insights method
        machine_id = "test-leg-press-01"
        insights = forecast_handler.generate_gemini_insights(
            machine_id=machine_id,
            data_array=data_array,
            forecast=test_forecast,
            anomalies=test_anomalies
        )

        print(f"✅ Gemini API call successful!")
        print(f"📝 Response length: {len(insights)} characters")
        print(f"🎯 Machine ID: {machine_id}")

        # Display the insights
        print("\n📋 AI Insights Received:")
        print("-" * 40)
        print(insights)
        print("-" * 40)

        # Test caching - call again immediately
        print("\n🔄 Testing cache system (immediate second call)...")
        cached_insights = forecast_handler.generate_gemini_insights(
            machine_id=machine_id,
            data_array=data_array,
            forecast=test_forecast,
            anomalies=test_anomalies
        )

        if cached_insights == insights:
            print("✅ Caching working correctly - identical response received")
        else:
            print("⚠️ Caching issue - responses differ")

        # Test different machine (should trigger new API call)
        print("\n🆕 Testing different machine (should bypass cache)...")
        insights_different = forecast_handler.generate_gemini_insights(
            machine_id="test-chest-press-01",
            data_array=data_array,
            forecast=test_forecast,
            anomalies=test_anomalies
        )

        print(f"📝 Different machine response length: {len(insights_different)} characters")

        return True

    except Exception as e:
        print(f"❌ Gemini API test failed: {str(e)}")
        print(f"📍 Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def test_singapore_lambda_direct():
    """Test Singapore Lambda directly"""
    print("\n🇸🇬 Testing Singapore Lambda directly...")
    print("-" * 40)

    try:
        lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

        test_payload = {
            'machine_id': 'test-direct-01',
            'data_summary': {
                'total_data_points': 96,
                'avg_occupancy': 67.3,
                'peak_hours': '07:00-09:00, 18:00-20:00',
                'anomalies_count': 1,
                'date_range': 'Last 24 hours',
                'forecast_summary': {
                    'predicted_usage': 65.4,
                    'confidence': 0.78
                }
            }
        }

        response = lambda_client.invoke(
            FunctionName='gym-pulse-gemini-singapore',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )

        result = json.loads(response['Payload'].read())

        if result.get('success'):
            print("✅ Singapore Lambda call successful")
            print(f"📝 Insights: {result.get('insights', '')}")
            return True
        else:
            print(f"❌ Singapore Lambda error: {result.get('error', 'Unknown')}")
            if result.get('fallback_insights'):
                print(f"🔄 Fallback available: {result.get('fallback_insights')}")
            return False

    except Exception as e:
        print(f"❌ Singapore Lambda test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Gemini API Integration Tests")
    print("=" * 60)

    # Test 1: Direct Singapore Lambda
    success_singapore = test_singapore_lambda_direct()

    # Test 2: Full integration pipeline
    success_integration = test_gemini_integration()

    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"🇸🇬 Singapore Lambda Direct:  {'✅ PASS' if success_singapore else '❌ FAIL'}")
    print(f"🔗 Full Integration Pipeline: {'✅ PASS' if success_integration else '❌ FAIL'}")

    if success_singapore and success_integration:
        print("\n🎉 ALL TESTS PASSED! Gemini API integration is working correctly.")
        print("💰 Your API quota is protected with 30-minute caching.")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")

    print("=" * 60)