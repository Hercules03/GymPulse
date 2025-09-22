/// API endpoint constants for GymPulse backend services
class ApiConstants {
  ApiConstants._();

  // Base URLs
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod',
  );

  static const String websocketUrl = String.fromEnvironment(
    'WEBSOCKET_URL',
    defaultValue: 'wss://f33iwzqgcd.execute-api.ap-east-1.amazonaws.com/prod',
  );

  // API Endpoints
  static const String branches = '/branches';
  static const String machines = '/branches/{branchId}/categories/{category}/machines';
  static const String machineHistory = '/machines/{machineId}/history';
  static const String machineForecast = '/forecast/machine/{machineId}';
  static const String branchPeakHours = '/branches/{branchId}/peak-hours';

  // Alert endpoints
  static const String alerts = '/alerts';
  static const String alertById = '/alerts/{alertId}';

  // Chat endpoints
  static const String chat = '/chat';
  static const String chatTools = '/tools';
  static const String availabilityTool = '/tools/availability';
  static const String routeMatrixTool = '/tools/route-matrix';

  // Health check
  static const String health = '/health';

  // Request timeouts (in milliseconds)
  static const int connectTimeout = 10000;
  static const int receiveTimeout = 30000;
  static const int sendTimeout = 30000;

  // Headers
  static const Map<String, String> defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
}