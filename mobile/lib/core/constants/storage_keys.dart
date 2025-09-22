class StorageKeys {
  // Cache Keys
  static const String branchesCache = 'cached_branches';
  static const String machinesCache = 'cached_machines';
  static const String alertsCache = 'cached_alerts';
  static const String chatHistoryCache = 'cached_chat_history';
  static const String analyticsCache = 'cached_analytics';
  
  // User Preferences
  static const String userPreferences = 'user_preferences';
  static const String selectedBranch = 'selected_branch';
  static const String selectedCategory = 'selected_category';
  static const String lastLocation = 'last_location';
  static const String notificationSettings = 'notification_settings';
  static const String themeMode = 'theme_mode';
  static const String language = 'language';
  
  // Permission States
  static const String locationPermissionGranted = 'location_permission_granted';
  static const String notificationPermissionGranted = 'notification_permission_granted';
  static const String cameraPermissionGranted = 'camera_permission_granted';
  
  // Session Data
  static const String sessionToken = 'session_token';
  static const String refreshToken = 'refresh_token';
  static const String userId = 'user_id';
  static const String deviceId = 'device_id';
  
  // App State
  static const String firstLaunch = 'first_launch';
  static const String onboardingCompleted = 'onboarding_completed';
  static const String lastAppVersion = 'last_app_version';
  static const String lastSyncTime = 'last_sync_time';
  
  // Feature Flags
  static const String analyticsEnabled = 'analytics_enabled';
  static const String pushNotificationsEnabled = 'push_notifications_enabled';
  static const String locationServicesEnabled = 'location_services_enabled';
  static const String websocketEnabled = 'websocket_enabled';
  static const String offlineModeEnabled = 'offline_mode_enabled';
  
  // Debug Settings
  static const String debugMode = 'debug_mode';
  static const String logLevel = 'log_level';
  static const String apiBaseUrl = 'api_base_url';
  static const String websocketUrl = 'websocket_url';
}
