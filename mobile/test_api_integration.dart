import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

/// This is a standalone test to verify API integration
/// Run this with: dart test_api_integration.dart
void main() async {
  print('🧪 Testing GymPulse API Integration...\n');

  // Test 1: Direct API call to verify backend is working
  await testDirectApiCall();

  // Test 2: Test the exact Flutter request format
  await testFlutterApiFormat();

  // Test 3: Test JSON parsing compatibility
  await testJsonParsing();
}

Future<void> testDirectApiCall() async {
  print('📡 Test 1: Direct API Call');
  print('---------------------------');

  try {
    final url = 'https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod/chat';
    final headers = {
      'Content-Type': 'application/json',
    };
    final body = json.encode({
      'message': 'Hello, this is a test message from direct API call',
      'sessionId': 'test_session_${DateTime.now().millisecondsSinceEpoch}',
    });

    print('🔗 Making request to: $url');
    print('📦 Request body: $body');

    final response = await http.post(
      Uri.parse(url),
      headers: headers,
      body: body,
    );

    print('📊 Status code: ${response.statusCode}');
    print('📋 Response headers: ${response.headers}');
    print('📄 Response body: ${response.body}');

    if (response.statusCode == 200) {
      print('✅ Direct API call successful!');
      final responseJson = json.decode(response.body);
      print('📝 Parsed response: $responseJson');
    } else {
      print('❌ Direct API call failed with status: ${response.statusCode}');
    }
  } catch (e) {
    print('💥 Direct API call error: $e');
  }
  print('');
}

Future<void> testFlutterApiFormat() async {
  print('📱 Test 2: Flutter API Format');
  print('---------------------------');

  try {
    final url = 'https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod/chat';
    final headers = {
      'Content-Type': 'application/json',
    };

    // This matches the exact format Flutter app sends
    final body = json.encode({
      'message': 'Test Flutter format request',
      'userLocation': {
        'lat': 22.3193,
        'lon': 114.1694,
      },
      'sessionId': 'mobile_app_${DateTime.now().millisecondsSinceEpoch}',
    });

    print('🔗 Making Flutter-format request to: $url');
    print('📦 Request body: $body');

    final response = await http.post(
      Uri.parse(url),
      headers: headers,
      body: body,
    );

    print('📊 Status code: ${response.statusCode}');
    print('📄 Response body: ${response.body}');

    if (response.statusCode == 200) {
      print('✅ Flutter format API call successful!');
      final responseJson = json.decode(response.body);
      print('📝 Parsed response keys: ${responseJson.keys.toList()}');

      // Check for Flutter model compatibility
      print('🔍 Checking Flutter model fields:');
      print('   - response: ${responseJson.containsKey('response') ? '✅' : '❌'}');
      print('   - recommendations: ${responseJson.containsKey('recommendations') ? '✅' : '❌'}');
      print('   - toolsUsed: ${responseJson.containsKey('toolsUsed') ? '✅' : '❌'}');
      print('   - sessionId: ${responseJson.containsKey('sessionId') ? '✅' : '❌'}');
      print('   - fallback: ${responseJson.containsKey('fallback') ? '✅' : '❌'}');
      print('   - gemini_powered: ${responseJson.containsKey('gemini_powered') ? '✅' : '❌'}');
      print('   - timestamp: ${responseJson.containsKey('timestamp') ? '✅' : '❌'}');

    } else {
      print('❌ Flutter format API call failed with status: ${response.statusCode}');
    }
  } catch (e) {
    print('💥 Flutter format API call error: $e');
  }
  print('');
}

Future<void> testJsonParsing() async {
  print('🔄 Test 3: JSON Parsing Compatibility');
  print('-----------------------------------');

  try {
    // Simulate a typical API response
    final mockResponse = {
      'response': 'This is a test AI response',
      'recommendations': [
        {
          'branchId': 'test_branch_1',
          'name': 'Test Gym Branch',
          'eta': '5 mins',
          'distance': '1.2 km',
          'availableCount': 15,
          'totalCount': 20,
          'category': 'cardio'
        }
      ],
      'toolsUsed': ['availability_tool'],
      'sessionId': 'test_session_123',
      'fallback': false,
      'gemini_powered': true,
      'timestamp': '2024-01-15T10:30:00Z'
    };

    print('📦 Mock response: ${json.encode(mockResponse)}');

    // Test JSON encoding/decoding
    final jsonString = json.encode(mockResponse);
    final parsedResponse = json.decode(jsonString);

    print('✅ JSON encoding/decoding successful!');
    print('📝 Parsed keys: ${parsedResponse.keys.toList()}');

    // Verify all Flutter model fields are present
    final requiredFields = ['response', 'sessionId'];
    final optionalFields = ['recommendations', 'toolsUsed', 'fallback', 'gemini_powered', 'timestamp'];

    bool allRequiredPresent = true;
    for (final field in requiredFields) {
      if (!parsedResponse.containsKey(field)) {
        print('❌ Missing required field: $field');
        allRequiredPresent = false;
      }
    }

    for (final field in optionalFields) {
      if (parsedResponse.containsKey(field)) {
        print('✅ Optional field present: $field');
      } else {
        print('⚠️  Optional field missing: $field');
      }
    }

    if (allRequiredPresent) {
      print('✅ All required fields present for Flutter model!');
    } else {
      print('❌ Some required fields missing!');
    }

  } catch (e) {
    print('💥 JSON parsing error: $e');
  }
  print('');
}