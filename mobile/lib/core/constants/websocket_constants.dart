class WebSocketConstants {
  // Connection URLs
  static const String baseWsUrl = 'wss://f33iwzqgcd.execute-api.ap-east-1.amazonaws.com/prod';
  static const String devWsUrl = 'wss://f33iwzqgcd.execute-api.ap-east-1.amazonaws.com/prod';
  
  // Message Types
  static const String machineUpdateType = 'machine_update';
  static const String userAlertType = 'user_alert';
  static const String connectionStatusType = 'connection_status';
  static const String errorType = 'error';
  static const String pingType = 'ping';
  static const String pongType = 'pong';
  
  // Connection States
  static const String connecting = 'connecting';
  static const String connected = 'connected';
  static const String disconnected = 'disconnected';
  static const String reconnecting = 'reconnecting';
  static const String error = 'error';
  
  // Reconnection Settings
  static const int maxReconnectAttempts = 5;
  static const Duration initialReconnectDelay = Duration(seconds: 1);
  static const Duration maxReconnectDelay = Duration(seconds: 30);
  static const Duration pingInterval = Duration(seconds: 30);
  static const Duration pongTimeout = Duration(seconds: 10);
  
  // Subscription Types
  static const String subscribeBranches = 'subscribe_branches';
  static const String subscribeCategories = 'subscribe_categories';
  static const String subscribeUserAlerts = 'subscribe_user_alerts';
  static const String unsubscribeBranches = 'unsubscribe_branches';
  static const String unsubscribeCategories = 'unsubscribe_categories';
  static const String unsubscribeUserAlerts = 'unsubscribe_user_alerts';
  
  // Query Parameters
  static const String branchesParam = 'branches';
  static const String categoriesParam = 'categories';
  static const String userIdParam = 'userId';
  static const String deviceIdParam = 'deviceId';
  
  // Error Codes
  static const String connectionFailed = 'connection_failed';
  static const String authenticationFailed = 'authentication_failed';
  static const String subscriptionFailed = 'subscription_failed';
  static const String messageParseError = 'message_parse_error';
  static const String unknownError = 'unknown_error';
}
