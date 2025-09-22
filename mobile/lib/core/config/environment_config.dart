import 'package:flutter_dotenv/flutter_dotenv.dart';

class EnvironmentConfig {
  static bool _initialized = false;

  // API Configuration
  static String get apiBaseUrl => 
      dotenv.env['API_BASE_URL'] ?? 'https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod';
  
  static String get websocketUrl => 
      dotenv.env['WEBSOCKET_URL'] ?? 'wss://f33iwzqgcd.execute-api.ap-east-1.amazonaws.com/prod';

  // Google Maps
  static String get googleMapsApiKey => 
      dotenv.env['GOOGLE_MAPS_API_KEY'] ?? '';

  // Firebase Configuration
  static String get firebaseProjectId => 
      dotenv.env['FIREBASE_PROJECT_ID'] ?? '';
  
  static String get firebaseMessagingSenderId => 
      dotenv.env['FIREBASE_MESSAGING_SENDER_ID'] ?? '';

  // App Configuration
  static String get appName => 
      dotenv.env['APP_NAME'] ?? 'GymPulse';
  
  static String get appVersion => 
      dotenv.env['APP_VERSION'] ?? '1.0.0';
  
  static bool get debugMode => 
      dotenv.env['DEBUG_MODE']?.toLowerCase() == 'true';

  // Feature Flags
  static bool get enableAnalytics => 
      dotenv.env['ENABLE_ANALYTICS']?.toLowerCase() == 'true';
  
  static bool get enablePushNotifications => 
      dotenv.env['ENABLE_PUSH_NOTIFICATIONS']?.toLowerCase() == 'true';
  
  static bool get enableLocationServices => 
      dotenv.env['ENABLE_LOCATION_SERVICES']?.toLowerCase() == 'true';
  
  static bool get enableWebSocket => 
      dotenv.env['ENABLE_WEBSOCKET']?.toLowerCase() == 'true';

  // Initialize environment configuration
  static Future<void> initialize() async {
    if (_initialized) return;
    
    try {
      await dotenv.load(fileName: '.env');
      _initialized = true;
    } catch (e) {
      // If .env file doesn't exist or can't be loaded, use defaults
      print('Warning: Could not load .env file, using default values: $e');
      _initialized = true;
    }
  }

  // Check if environment is properly configured
  static bool get isConfigured => _initialized;

  // Get all configuration as a map for debugging
  static Map<String, dynamic> getConfig() {
    return {
      'apiBaseUrl': apiBaseUrl,
      'websocketUrl': websocketUrl,
      'googleMapsApiKey': googleMapsApiKey.isNotEmpty ? '***hidden***' : 'not set',
      'firebaseProjectId': firebaseProjectId,
      'firebaseMessagingSenderId': firebaseMessagingSenderId,
      'appName': appName,
      'appVersion': appVersion,
      'debugMode': debugMode,
      'enableAnalytics': enableAnalytics,
      'enablePushNotifications': enablePushNotifications,
      'enableLocationServices': enableLocationServices,
      'enableWebSocket': enableWebSocket,
    };
  }
}
