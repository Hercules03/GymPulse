import json
import urllib.request
import urllib.parse
import urllib.error
import os
from datetime import datetime

# Gemini API configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent'

def lambda_handler(event, context):
    """
    Singapore-based Lambda function for Gemini API calls
    Receives data from Hong Kong Lambda and returns AI insights
    """
    try:
        print(f"🇸🇬 Singapore Lambda: Processing Gemini request")

        # Extract payload from Hong Kong Lambda
        data_summary = event.get('data_summary', {})
        machine_id = event.get('machine_id', 'unknown')

        # Validate required data
        if not data_summary:
            return {
                'statusCode': 400,
                'success': False,
                'error': 'Missing data_summary in request'
            }

        # Generate Gemini insights
        insights = generate_gemini_insights(machine_id, data_summary)

        return {
            'statusCode': 200,
            'success': True,
            'insights': insights,
            'region': 'ap-southeast-1',
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"❌ Singapore Lambda error: {str(e)}")
        return {
            'statusCode': 500,
            'success': False,
            'error': str(e),
            'fallback_insights': generate_fallback_insights(
                event.get('machine_id', 'unknown'),
                event.get('data_summary', {})
            )
        }

def generate_gemini_insights(machine_id, data_summary):
    """Generate AI insights using Google Gemini API from Singapore"""
    try:
        print(f"🤖 Calling Gemini API from Singapore for {machine_id}")

        # Prepare enhanced prompt with data summary
        prompt = f"""
        Analyze this gym equipment usage data and provide actionable insights:

        Machine: {machine_id}
        Data Points: {data_summary.get('total_data_points', 0)}
        Average Occupancy: {data_summary.get('avg_occupancy', 0)}%
        Peak Hours: {data_summary.get('peak_hours', 'unknown')}
        Anomalies Detected: {data_summary.get('anomalies_count', 0)}
        Date Range: {data_summary.get('date_range', 'unknown')}

        Current Forecast: {data_summary.get('forecast_summary', {})}

        Provide a concise analysis covering:
        1. Key usage patterns identified
        2. Recommendations for gym members (best times to visit)
        3. Operational insights for gym management
        4. Prediction confidence assessment

        Keep response under 200 words, actionable and user-friendly.
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
                'temperature': 0.7,
                'topK': 40,
                'topP': 0.95
            }
        }

        print(f"🌐 Making Gemini API request from Singapore...")

        try:
            # Prepare request data
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(GEMINI_URL, data=data, headers=headers)

            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    ai_insights = result['candidates'][0]['content']['parts'][0]['text']
                    print(f"✅ Gemini API success from Singapore: {len(ai_insights)} characters")
                    return ai_insights
                else:
                    print(f"❌ Gemini API error: {response.status}")
                    return generate_fallback_insights(machine_id, data_summary)

        except urllib.error.HTTPError as e:
            error_response = e.read().decode('utf-8')
            print(f"❌ Gemini API HTTP error: {e.code} - {error_response}")
            return generate_fallback_insights(machine_id, data_summary)
        except Exception as e:
            print(f"❌ Gemini API request error: {str(e)}")
            return generate_fallback_insights(machine_id, data_summary)

    except Exception as e:
        print(f"❌ Error calling Gemini API: {str(e)}")
        return generate_fallback_insights(machine_id, data_summary)

def generate_fallback_insights(machine_id, data_summary):
    """Generate fallback insights when Gemini API is unavailable"""
    try:
        total_points = data_summary.get('total_data_points', 0)
        avg_occupancy = data_summary.get('avg_occupancy', 50)
        peak_hours = data_summary.get('peak_hours', 'various')
        anomalies = data_summary.get('anomalies_count', 0)

        # Determine usage level
        if avg_occupancy < 30:
            usage_level = "low usage patterns"
            recommendation = "Excellent availability throughout the day"
        elif avg_occupancy < 60:
            usage_level = "moderate usage patterns"
            recommendation = "Generally good availability with some busy periods"
        else:
            usage_level = "high usage patterns"
            recommendation = "Popular machine with frequent busy periods"

        # Generate contextual insights
        insights = f"Analysis for {machine_id}: {usage_level} detected over {total_points} data points. {recommendation}. Peak activity during {peak_hours} hours."

        if anomalies > 0:
            insights += f" {anomalies} usage anomalies detected, suggesting irregular patterns or maintenance events."

        print(f"🔄 Generated fallback insights for {machine_id}")
        return insights

    except Exception as e:
        print(f"❌ Error generating fallback insights: {str(e)}")
        return f"Analysis pending for {machine_id}. System collecting usage patterns for improved recommendations."