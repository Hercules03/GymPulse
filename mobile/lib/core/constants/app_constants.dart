class AppConstants {
  // App Information
  static const String appName = 'GymPulse';
  static const String appVersion = '1.0.0';
  
  // API Configuration
  static const String baseUrl = 'https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod';
  static const String websocketUrl = 'wss://f33iwzqgcd.execute-api.ap-east-1.amazonaws.com/prod';
  
  // Storage Keys
  static const String branchesCacheKey = 'cached_branches';
  static const String machinesCacheKey = 'cached_machines';
  static const String userPreferencesKey = 'user_preferences';
  static const String locationPermissionKey = 'location_permission_granted';
  
  // Timeouts
  static const Duration apiTimeout = Duration(seconds: 30);
  static const Duration websocketTimeout = Duration(seconds: 10);
  static const Duration locationTimeout = Duration(seconds: 15);
  
  // Pagination
  static const int defaultPageSize = 20;
  static const int maxCacheAge = 300; // 5 minutes in seconds
  
  // UI Constants
  static const double defaultPadding = 16.0;
  static const double smallPadding = 8.0;
  static const double largePadding = 24.0;
  static const double borderRadius = 12.0;
  static const double cardElevation = 2.0;
  
  // Animation Durations
  static const Duration shortAnimation = Duration(milliseconds: 200);
  static const Duration mediumAnimation = Duration(milliseconds: 300);
  static const Duration longAnimation = Duration(milliseconds: 500);
  
  // Machine Status Colors
  static const int availableColor = 0xFF4CAF50; // Green
  static const int occupiedColor = 0xFFF44336;  // Red
  static const int offlineColor = 0xFF9E9E9E;   // Grey
  static const int unknownColor = 0xFFFF9800;   // Orange
  
  // Equipment Categories
  static const List<String> equipmentCategories = [
    'legs',
    'chest',
    'back',
    'cardio',
    'arms',
  ];
  
  // Feature Flags
  static const bool enableAnalytics = true;
  static const bool enablePushNotifications = true;
  static const bool enableLocationServices = true;
  static const bool enableWebSocket = true;

  // WebSocket Configuration
  static const int maxReconnectAttempts = 5;
  static const Duration reconnectInterval = Duration(seconds: 5);
  static const Duration pingInterval = Duration(seconds: 30);
  static const bool enableOfflineMode = true;

  // Maps Configuration
  static const double defaultLatitude = 22.3193; // Hong Kong
  static const double defaultLongitude = 114.1694; // Hong Kong
  static const double defaultMapZoom = 15.0;

  // Error Messages
  static const String locationServiceDisabled = 'Location services are disabled. Please enable them in settings.';
  static const String locationPermissionDenied = 'Location permission is required to find nearby gyms.';
}
