#!/usr/bin/env python3
"""
Command-line ML integration validation for GymPulse
Tests API connectivity, ML data presence, Gemini AI, and caching
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import time
import sys
from datetime import datetime

API_BASE = 'https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod'

def print_test_header(test_name):
    print(f"\n🧪 {test_name}")
    print("=" * 50)

def print_result(success, message, details=None):
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")
    if details:
        print(f"   {details}")

def test_api_connection():
    """Test basic API connectivity"""
    print_test_header("Test 1: API Connection")

    try:
        req = urllib.request.Request(f"{API_BASE}/branches")
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                branch_count = len(data.get('branches', []))
                print_result(True, "API Connection successful", f"Found {branch_count} branches")
                return True
            else:
                print_result(False, f"API returned status {response.status}")
                return False
    except urllib.error.HTTPError as e:
        print_result(False, f"HTTP error {e.code}: {e.reason}")
        return False
    except Exception as e:
        print_result(False, f"API connection failed: {str(e)}")
        return False

def test_ml_data():
    """Test ML data presence in machine history"""
    print_test_header("Test 2: ML Data Integration")

    try:
        req = urllib.request.Request(f"{API_BASE}/machines/leg-press-01/history")
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))

                # Check for ML indicators
                has_forecast = bool(data.get('forecast'))
                has_insights = bool(data.get('ml_insights'))
                has_anomalies = bool(data.get('anomalies'))

                ml_indicators = [has_forecast, has_insights, has_anomalies]
                has_ml_data = any(ml_indicators)

                if has_ml_data:
                    indicators = []
                    if has_forecast: indicators.append("forecast")
                    if has_insights: indicators.append("insights")
                    if has_anomalies: indicators.append("anomalies")
                    print_result(True, "ML data found", f"Indicators: {', '.join(indicators)}")
                else:
                    print_result(False, "No ML data found", "Missing forecast, insights, and anomalies")

                return has_ml_data
            else:
                print_result(False, f"Machine history API returned status {response.status}")
                return False
    except urllib.error.HTTPError as e:
        print_result(False, f"HTTP error {e.code}: {e.reason}")
        return False
    except Exception as e:
        print_result(False, f"ML data test failed: {str(e)}")
        return False

def test_gemini_integration():
    """Test Gemini AI chatbot integration"""
    print_test_header("Test 3: Gemini AI Integration")

    try:
        payload = {
            'message': 'Analyze usage patterns for gym equipment',
            'location': {'lat': 22.2819, 'lon': 114.1577}
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{API_BASE}/chat",
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                has_insights = bool(data.get('insights') or data.get('response'))

                if has_insights:
                    insight_preview = str(data.get('insights', data.get('response', '')))[:100]
                    print_result(True, "Gemini AI working", f"Preview: {insight_preview}...")

                    # Print full response for debugging
                    print("\n📝 Full Gemini Response:")
                    print(json.dumps(data, indent=2))
                    return True
                else:
                    print_result(False, "Gemini returned response but no insights")
                    print(f"Response: {json.dumps(data, indent=2)}")
                    return False
            else:
                print_result(False, f"Chat API returned status {response.status}")
                return False
    except urllib.error.HTTPError as e:
        error_response = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
        print_result(False, f"HTTP error {e.code}: {e.reason}")
        print(f"Response: {error_response}")
        return False
    except Exception as e:
        print_result(False, f"Gemini integration test failed: {str(e)}")
        return False

def test_caching_system():
    """Test API response caching"""
    print_test_header("Test 4: Caching System")

    try:
        test_endpoint = f"{API_BASE}/machines/test-cache-system/history"

        # First call
        start1 = time.time()
        req1 = urllib.request.Request(test_endpoint)
        with urllib.request.urlopen(req1, timeout=10) as response1:
            time1 = (time.time() - start1) * 1000  # Convert to milliseconds
            if response1.status != 200:
                print_result(False, f"Cache test endpoint returned {response1.status}")
                return False

        # Small delay to ensure different timestamp
        time.sleep(0.1)

        # Second call
        start2 = time.time()
        req2 = urllib.request.Request(test_endpoint)
        with urllib.request.urlopen(req2, timeout=10) as response2:
            time2 = (time.time() - start2) * 1000
            if response2.status != 200:
                print_result(False, f"Cache test second call returned {response2.status}")
                return False

        # Check if second call was faster (indicating caching)
        improvement = ((time1 - time2) / time1) * 100 if time1 > 0 else 0
        is_cached = time2 < (time1 * 0.7)  # Allow some variance

        print(f"   First call:  {time1:.1f}ms")
        print(f"   Second call: {time2:.1f}ms")
        print(f"   Improvement: {improvement:.1f}%")

        if is_cached and improvement > 10:
            print_result(True, "Caching system working", f"{improvement:.1f}% improvement")
            return True
        else:
            print_result(False, "Caching not detected", "Performance improvement insufficient")
            return False

    except urllib.error.HTTPError as e:
        print_result(False, f"HTTP error {e.code}: {e.reason}")
        return False
    except Exception as e:
        print_result(False, f"Caching test failed: {str(e)}")
        return False

def main():
    """Run all ML integration tests"""
    print("🎯 GymPulse ML Integration Validation")
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API Base: {API_BASE}")

    # Run all tests
    results = []

    results.append(("API Connection", test_api_connection()))
    results.append(("ML Data", test_ml_data()))
    results.append(("Gemini AI", test_gemini_integration()))
    results.append(("Caching", test_caching_system()))

    # Summary
    print_test_header("Test Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        icon = "✅" if result else "❌"
        print(f"{icon} {test_name}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All ML integrations working correctly!")
        return 0
    else:
        print("⚠️  Some integrations need attention.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
        sys.exit(1)