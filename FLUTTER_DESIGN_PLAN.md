# GymPulse Flutter Mobile App - Design & Implementation Plan

## Project Overview

This document outlines the comprehensive design and implementation plan for creating a Flutter mobile version of the GymPulse web application, maintaining feature parity while leveraging Flutter's native mobile capabilities.

## Current Web App Feature Analysis

### 🏗️ Core Features Identified

#### 1. **Branch Management System**
- **Branch Listing**: Interactive map with branch locations and real-time availability
- **Branch Details**: Individual branch information with equipment categories
- **Location Services**: User geolocation for distance calculations and ETA
- **Search & Filter**: Branch search by name/address with filtering capabilities
- **Bottom Sheet UI**: Mobile-optimized branch selection interface

#### 2. **Equipment & Machine Management**
- **Category-Based Organization**: Equipment grouped by body parts (legs, chest, back, cardio, arms)
- **Real-time Status Tracking**: Live machine status (available, occupied, offline)
- **Machine Details**: Individual machine information with usage history
- **Status Updates**: WebSocket-based real-time status changes
- **Machine Cards**: Rich UI cards with status badges and action buttons

#### 3. **Smart Analytics & Forecasting**
- **24-Hour Usage History**: Heatmap visualization of machine usage patterns
- **Peak Hours Analysis**: AI-powered peak time predictions with confidence levels
- **Usage Forecasting**: ML-based predictions for machine availability
- **Occupancy Analytics**: Real-time occupancy percentages and trends
- **Development/Demo Modes**: Configurable data sources (real API vs mock data)

#### 4. **Notification & Alert System**
- **Machine Alerts**: "Notify when free" functionality for occupied equipment
- **User Preferences**: Quiet hours configuration for notifications
- **Alert Management**: List, update, and cancel active alerts
- **Alert API**: Full CRUD operations for user notifications

#### 5. **AI-Powered Chat Assistant**
- **Natural Language Processing**: Bedrock-powered chatbot for gym queries
- **Location-Aware Recommendations**: Context-aware branch and equipment suggestions
- **Tool Integration**: Backend tools for availability lookup and route calculation
- **Chat Interface**: Modern chat UI with message bubbles and typing indicators

#### 6. **Real-time Data Integration**
- **WebSocket Connectivity**: Live updates for machine status changes
- **Connection Management**: Auto-reconnection and fallback strategies
- **Subscription Management**: Dynamic filtering by branches and categories
- **Mock Data Support**: Development mode with simulated real-time updates

#### 7. **User Experience Features**
- **Responsive Design**: Mobile-first with desktop optimization
- **Bottom Sheet Navigation**: Mobile-optimized UI patterns
- **Loading States**: Skeleton screens and progress indicators
- **Error Handling**: Graceful error recovery and user feedback
- **Animations**: Smooth transitions and micro-interactions

## 🎯 Flutter Architecture Design

### 1. **Project Structure** (Clean Architecture)

```
/mobile/
├── lib/
│   ├── main.dart                       # App entry point
│   ├── app/
│   │   ├── app.dart                    # Main app configuration
│   │   ├── routes.dart                 # Navigation routes
│   │   ├── themes.dart                 # Material Design 3 themes
│   │   └── config.dart                 # App configuration
│   ├── core/
│   │   ├── constants/
│   │   │   ├── api_constants.dart      # API endpoints and URLs
│   │   │   ├── app_constants.dart      # App-wide constants
│   │   │   ├── storage_keys.dart       # SharedPreferences keys
│   │   │   └── websocket_constants.dart # WebSocket configurations
│   │   ├── network/
│   │   │   ├── api_client.dart         # Dio + Retrofit client setup
│   │   │   ├── websocket_service.dart  # Real-time connectivity
│   │   │   ├── network_interceptors.dart # Request/response interceptors
│   │   │   └── connection_checker.dart # Network connectivity monitoring
│   │   ├── services/
│   │   │   ├── location_service.dart   # GPS and permissions
│   │   │   ├── notification_service.dart # Local notifications
│   │   │   ├── storage_service.dart    # Local data persistence
│   │   │   └── permission_service.dart # Permission management
│   │   ├── utils/
│   │   │   ├── date_utils.dart         # Date/time utilities
│   │   │   ├── validation_utils.dart   # Input validation
│   │   │   ├── format_utils.dart       # Data formatting
│   │   │   └── debug_utils.dart        # Development helpers
│   │   └── errors/
│   │       ├── exceptions.dart         # Custom exceptions
│   │       ├── failures.dart           # Error handling
│   │       └── error_handler.dart      # Global error management
│   ├── data/
│   │   ├── models/
│   │   │   ├── api/
│   │   │   │   ├── branch_response.dart    # API response models
│   │   │   │   ├── machines_response.dart
│   │   │   │   ├── alert_response.dart
│   │   │   │   ├── chat_response.dart
│   │   │   │   └── websocket_message.dart
│   │   │   ├── entities/
│   │   │   │   ├── branch_model.dart       # Data transfer objects
│   │   │   │   ├── machine_model.dart
│   │   │   │   ├── alert_model.dart
│   │   │   │   ├── chat_message_model.dart
│   │   │   │   └── usage_history_model.dart
│   │   │   └── local/
│   │   │       ├── cached_branch.dart      # Local storage models
│   │   │       ├── cached_machine.dart
│   │   │       └── user_preferences.dart
│   │   ├── repositories/
│   │   │   ├── gym_repository_impl.dart    # Repository implementations
│   │   │   ├── chat_repository_impl.dart
│   │   │   ├── notification_repository_impl.dart
│   │   │   └── analytics_repository_impl.dart
│   │   └── datasources/
│   │       ├── remote/
│   │       │   ├── gym_api_service.dart     # Retrofit API definitions
│   │       │   ├── chat_api_service.dart
│   │       │   ├── websocket_datasource.dart
│   │       │   └── notification_api_service.dart
│   │       └── local/
│   │           ├── cache_datasource.dart    # Hive local storage
│   │           ├── preferences_datasource.dart # SharedPreferences
│   │           └── secure_storage_datasource.dart # Secure storage
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── branch.dart                 # Pure business objects
│   │   │   ├── machine.dart
│   │   │   ├── equipment_category.dart
│   │   │   ├── alert.dart
│   │   │   ├── chat_message.dart
│   │   │   ├── usage_analytics.dart
│   │   │   └── user_location.dart
│   │   ├── repositories/
│   │   │   ├── gym_repository.dart         # Abstract repositories
│   │   │   ├── chat_repository.dart
│   │   │   ├── notification_repository.dart
│   │   │   └── analytics_repository.dart
│   │   └── usecases/
│   │       ├── branch/
│   │       │   ├── get_branches.dart       # Business use cases
│   │       │   ├── get_branch_details.dart
│   │       │   └── search_branches.dart
│   │       ├── machine/
│   │       │   ├── get_machines.dart
│   │       │   ├── get_machine_details.dart
│   │       │   ├── get_machine_history.dart
│   │       │   └── get_machine_forecast.dart
│   │       ├── notification/
│   │       │   ├── create_alert.dart
│   │       │   ├── manage_alerts.dart
│   │       │   └── update_alert_settings.dart
│   │       ├── chat/
│   │       │   ├── send_message.dart
│   │       │   └── get_recommendations.dart
│   │       └── analytics/
│   │           ├── get_usage_analytics.dart
│   │           └── get_peak_hours.dart
│   ├── presentation/
│   │   ├── pages/
│   │   │   ├── splash/
│   │   │   │   └── splash_page.dart        # App initialization
│   │   │   ├── branch/
│   │   │   │   ├── branches_page.dart      # Main branch listing
│   │   │   │   └── branch_detail_page.dart # Individual branch
│   │   │   ├── dashboard/
│   │   │   │   └── dashboard_page.dart     # Category overview
│   │   │   ├── machines/
│   │   │   │   ├── machines_page.dart      # Machine listing
│   │   │   │   └── machine_detail_page.dart # Individual machine
│   │   │   ├── notifications/
│   │   │   │   ├── alerts_page.dart        # User alerts management
│   │   │   │   └── alert_settings_page.dart # Alert configuration
│   │   │   ├── chat/
│   │   │   │   └── chat_page.dart          # AI assistant interface
│   │   │   └── settings/
│   │   │       ├── settings_page.dart      # App settings
│   │   │       └── permissions_page.dart   # Permission management
│   │   ├── widgets/
│   │   │   ├── common/
│   │   │   │   ├── status_badge.dart       # Reusable status indicators
│   │   │   │   ├── loading_widget.dart     # Loading states
│   │   │   │   ├── error_widget.dart       # Error handling UI
│   │   │   │   ├── empty_state_widget.dart # Empty state displays
│   │   │   │   ├── refresh_indicator.dart  # Pull-to-refresh
│   │   │   │   └── bottom_sheet_wrapper.dart # Bottom sheet container
│   │   │   ├── branch/
│   │   │   │   ├── branch_card.dart        # Branch list item
│   │   │   │   ├── branch_map.dart         # Google Maps integration
│   │   │   │   ├── branch_search_bar.dart  # Search functionality
│   │   │   │   └── branch_filter_chip.dart # Filter options
│   │   │   ├── machine/
│   │   │   │   ├── machine_card.dart       # Machine list item
│   │   │   │   ├── machine_grid.dart       # Grid layout
│   │   │   │   ├── status_indicator.dart   # Live status display
│   │   │   │   ├── usage_heatmap.dart      # Analytics visualization
│   │   │   │   ├── prediction_chip.dart    # AI predictions
│   │   │   │   └── notification_button.dart # Alert setup
│   │   │   ├── dashboard/
│   │   │   │   ├── category_card.dart      # Equipment categories
│   │   │   │   ├── quick_stats.dart        # Summary statistics
│   │   │   │   └── peak_hours_display.dart # Peak time info
│   │   │   ├── chat/
│   │   │   │   ├── chat_bubble.dart        # Message display
│   │   │   │   ├── typing_indicator.dart   # Loading animation
│   │   │   │   ├── recommendation_card.dart # Branch suggestions
│   │   │   │   └── chat_input.dart         # Message input
│   │   │   └── analytics/
│   │   │       ├── usage_chart.dart        # Chart components
│   │   │       ├── occupancy_gauge.dart    # Circular progress
│   │   │       └── trends_graph.dart       # Line charts
│   │   ├── providers/
│   │   │   ├── gym_provider.dart           # Main app state
│   │   │   ├── websocket_provider.dart     # Real-time updates
│   │   │   ├── location_provider.dart      # GPS and location state
│   │   │   ├── chat_provider.dart          # AI assistant state
│   │   │   ├── notification_provider.dart  # Alert management
│   │   │   └── analytics_provider.dart     # Usage analytics
│   │   └── utils/
│   │       ├── route_generator.dart        # Navigation logic
│   │       ├── theme_helper.dart           # Theme utilities
│   │       └── responsive_helper.dart      # Screen size helpers
│   └── shared/
       ├── extensions/
       │   ├── context_extensions.dart     # BuildContext helpers
       │   ├── string_extensions.dart      # String utilities
       │   ├── datetime_extensions.dart    # Date/time helpers
       │   └── color_extensions.dart       # Color utilities
       ├── constants/
       │   ├── app_colors.dart             # Design system colors
       │   ├── app_text_styles.dart        # Typography scale
       │   ├── app_dimensions.dart         # Spacing and sizing
       │   └── app_icons.dart              # Icon constants
       └── enums/
           ├── machine_status.dart         # Status enumeration
           ├── equipment_category.dart     # Category types
           └── connection_state.dart       # Network states
```

### 2. **Technology Stack & Dependencies**

```yaml
dependencies:
  # Core Flutter
  flutter:
    sdk: flutter

  # State Management
  provider: ^6.1.1              # Recommended for this complexity level

  # Network & API
  dio: ^5.4.0                   # HTTP client with interceptors
  retrofit: ^4.0.3              # Type-safe API client generation
  json_annotation: ^4.8.1       # JSON serialization annotations
  web_socket_channel: ^2.4.0    # WebSocket connectivity
  connectivity_plus: ^5.0.0     # Network state monitoring

  # Local Storage & Caching
  shared_preferences: ^2.2.2    # Simple key-value storage
  hive: ^2.2.3                  # NoSQL object database
  hive_flutter: ^1.1.0          # Flutter integration for Hive
  flutter_secure_storage: ^9.0.0 # Secure storage for sensitive data

  # Location Services
  geolocator: ^10.1.0           # GPS functionality and permissions
  geocoding: ^2.1.1             # Address to coordinates conversion
  permission_handler: ^11.2.0   # Comprehensive permission management

  # Maps & Visualization
  google_maps_flutter: ^2.5.0   # Interactive maps integration
  fl_chart: ^0.66.0             # Beautiful charts for analytics

  # UI & Navigation
  go_router: ^12.1.0            # Declarative navigation solution
  animations: ^2.0.8            # Custom animations and transitions
  flutter_slidable: ^3.0.1      # Swipe actions for list items
  modal_bottom_sheet: ^3.0.0    # Enhanced bottom sheets

  # Notifications
  flutter_local_notifications: ^16.3.0  # Local notification system
  firebase_messaging: ^14.7.6   # Push notifications (optional)

  # Utilities
  intl: ^0.19.0                 # Internationalization support
  flutter_dotenv: ^5.1.0        # Environment configuration
  equatable: ^2.0.5             # Value equality comparisons
  freezed_annotation: ^2.4.1    # Immutable classes (optional)

  # Development & Debugging
  logger: ^2.0.2                # Structured logging

dev_dependencies:
  # Code Generation
  build_runner: ^2.4.7          # Code generation runner
  retrofit_generator: ^8.0.4    # Retrofit code generation
  json_serializable: ^6.7.1     # JSON serialization generation
  hive_generator: ^2.0.1        # Hive type adapters
  freezed: ^2.4.6               # Immutable classes (optional)

  # Testing
  flutter_test:
    sdk: flutter
  mockito: ^5.4.4               # Mocking framework
  build_verify: ^3.1.0          # Verify generated code
  integration_test:
    sdk: flutter

  # Analysis & Linting
  flutter_lints: ^3.0.1         # Recommended linting rules
  very_good_analysis: ^5.1.0    # Enhanced linting (optional)
```

### 3. **State Management Strategy**

#### Provider Pattern Implementation
```dart
// Main app state management
class GymProvider extends ChangeNotifier {
  // Branches
  List<Branch> _branches = [];
  Branch? _selectedBranch;

  // Machines
  List<Machine> _machines = [];
  Machine? _selectedMachine;

  // Loading states
  bool _isLoadingBranches = false;
  bool _isLoadingMachines = false;

  // Error handling
  String? _errorMessage;

  // Getters
  List<Branch> get branches => _branches;
  Branch? get selectedBranch => _selectedBranch;
  // ... other getters

  // Actions
  Future<void> loadBranches() async {
    _isLoadingBranches = true;
    notifyListeners();

    try {
      _branches = await _gymRepository.getBranches();
      _errorMessage = null;
    } catch (e) {
      _errorMessage = e.toString();
    }

    _isLoadingBranches = false;
    notifyListeners();
  }
}

// WebSocket real-time updates
class WebSocketProvider extends ChangeNotifier {
  final WebSocketService _webSocketService;
  StreamSubscription? _subscription;

  bool _isConnected = false;
  List<MachineUpdate> _recentUpdates = [];

  bool get isConnected => _isConnected;
  List<MachineUpdate> get recentUpdates => _recentUpdates;

  Future<void> connect(List<String> branches, List<String> categories) async {
    await _webSocketService.connect(branches: branches, categories: categories);
    _subscription = _webSocketService.updateStream.listen(_handleUpdate);
  }

  void _handleUpdate(MachineUpdate update) {
    _recentUpdates.insert(0, update);
    if (_recentUpdates.length > 100) {
      _recentUpdates.removeLast();
    }
    notifyListeners();
  }
}
```

### 4. **API Integration Strategy**

#### Retrofit API Service
```dart
@RestApi(baseUrl: "https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod")
abstract class GymApiService {
  factory GymApiService(Dio dio) = _GymApiService;

  // Branch endpoints
  @GET("/branches")
  Future<BranchesResponse> getBranches();

  @GET("/branches/{branchId}/peak-hours")
  Future<PeakHoursResponse> getBranchPeakHours(@Path() String branchId);

  // Machine endpoints
  @GET("/branches/{branchId}/categories/{category}/machines")
  Future<MachinesResponse> getMachines(
    @Path() String branchId,
    @Path() String category,
  );

  @GET("/machines/{machineId}/history")
  Future<MachineHistoryResponse> getMachineHistory(
    @Path() String machineId,
    @Query("range") String range,
  );

  @GET("/forecast/machine/{machineId}")
  Future<MachineForecastResponse> getMachineForecast(
    @Path() String machineId,
    @Query("minutes") int minutes,
  );

  // Alert endpoints
  @POST("/alerts")
  Future<AlertResponse> createAlert(@Body() CreateAlertRequest request);

  @GET("/alerts")
  Future<AlertsListResponse> listAlerts(@Query("userId") String userId);

  @PUT("/alerts/{alertId}")
  Future<AlertResponse> updateAlert(
    @Path() String alertId,
    @Body() UpdateAlertRequest request,
  );

  @DELETE("/alerts/{alertId}")
  Future<void> cancelAlert(@Path() String alertId);

  // Chat endpoints
  @POST("/chat")
  Future<ChatResponse> sendChatMessage(@Body() ChatRequest request);

  // Tool endpoints for chatbot
  @POST("/tools/availability")
  Future<AvailabilityToolResponse> getAvailabilityByCategory(
    @Body() AvailabilityToolRequest request,
  );

  @POST("/tools/route-matrix")
  Future<RouteMatrixResponse> getRouteMatrix(
    @Body() RouteMatrixRequest request,
  );
}

// Dio client setup with interceptors
class ApiClient {
  static Dio createDio() {
    final dio = Dio(BaseOptions(
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    // Add logging interceptor
    dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
      logPrint: (obj) => logger.d(obj),
    ));

    // Add error handling interceptor
    dio.interceptors.add(ErrorInterceptor());

    return dio;
  }
}
```

### 5. **Real-time Features Implementation**

#### WebSocket Service
```dart
class WebSocketService {
  static const String _baseWsUrl = 'wss://your-websocket-url.com/ws';

  WebSocketChannel? _channel;
  StreamController<MachineUpdate> _updateController = StreamController.broadcast();
  StreamController<UserAlert> _alertController = StreamController.broadcast();

  Stream<MachineUpdate> get machineUpdateStream => _updateController.stream;
  Stream<UserAlert> get userAlertStream => _alertController.stream;

  bool _isConnected = false;
  bool get isConnected => _isConnected;

  Future<void> connect({
    List<String>? branches,
    List<String>? categories,
    String? userId,
  }) async {
    try {
      final queryParams = <String, String>{};
      if (branches?.isNotEmpty == true) {
        queryParams['branches'] = branches!.join(',');
      }
      if (categories?.isNotEmpty == true) {
        queryParams['categories'] = categories!.join(',');
      }
      if (userId != null) {
        queryParams['userId'] = userId;
      }

      final uri = Uri.parse(_baseWsUrl).replace(queryParameters: queryParams);
      _channel = WebSocketChannel.connect(uri);

      _channel!.stream.listen(
        _handleMessage,
        onError: _handleError,
        onDone: _handleDisconnect,
      );

      _isConnected = true;
      logger.i('WebSocket connected successfully');
    } catch (e) {
      logger.e('Failed to connect to WebSocket: $e');
      _isConnected = false;
      rethrow;
    }
  }

  void _handleMessage(dynamic data) {
    try {
      final json = jsonDecode(data as String);
      final message = WebSocketMessage.fromJson(json);

      switch (message.type) {
        case 'machine_update':
          _updateController.add(MachineUpdate.fromJson(json));
          break;
        case 'user_alert':
          _alertController.add(UserAlert.fromJson(json));
          break;
        default:
          logger.w('Unknown message type: ${message.type}');
      }
    } catch (e) {
      logger.e('Error parsing WebSocket message: $e');
    }
  }

  Future<void> disconnect() async {
    await _channel?.sink.close();
    _isConnected = false;
    logger.i('WebSocket disconnected');
  }
}
```

### 6. **UI Component System**

#### Material Design 3 Theme
```dart
class AppTheme {
  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.blue,
      brightness: Brightness.light,
    ),
    appBarTheme: const AppBarTheme(
      centerTitle: true,
      elevation: 0,
      scrolledUnderElevation: 1,
    ),
    cardTheme: CardTheme(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
    ),
    bottomSheetTheme: const BottomSheetThemeData(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
    ),
  );

  static ThemeData darkTheme = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.blue,
      brightness: Brightness.dark,
    ),
    // ... dark theme configuration
  );
}
```

#### Custom Widgets
```dart
// Status Badge Component
class StatusBadge extends StatelessWidget {
  final MachineStatus status;
  final bool showPulse;

  const StatusBadge({
    super.key,
    required this.status,
    this.showPulse = false,
  });

  @override
  Widget build(BuildContext context) {
    final (color, text, icon) = _getStatusProperties(status);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (showPulse && status == MachineStatus.available)
            _PulsingDot(color: color)
          else
            Icon(icon, size: 12, color: color),
          const SizedBox(width: 4),
          Text(
            text,
            style: TextStyle(
              color: color,
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  (Color, String, IconData) _getStatusProperties(MachineStatus status) {
    switch (status) {
      case MachineStatus.available:
        return (Colors.green, 'Available', Icons.check_circle);
      case MachineStatus.occupied:
        return (Colors.red, 'Occupied', Icons.person);
      case MachineStatus.offline:
        return (Colors.grey, 'Offline', Icons.error);
      case MachineStatus.unknown:
        return (Colors.orange, 'Unknown', Icons.help);
    }
  }
}

// Machine Card Component
class MachineCard extends StatelessWidget {
  final Machine machine;
  final VoidCallback? onTap;
  final VoidCallback? onNotifyPressed;

  const MachineCard({
    super.key,
    required this.machine,
    this.onTap,
    this.onNotifyPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(
                    _getCategoryIcon(machine.category),
                    size: 32,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          machine.name,
                          style: Theme.of(context).textTheme.titleMedium,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Text(
                          machine.machineId,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                  StatusBadge(
                    status: machine.status,
                    showPulse: true,
                  ),
                ],
              ),
              const SizedBox(height: 16),
              if (machine.lastUpdate != null)
                Row(
                  children: [
                    Icon(
                      Icons.schedule,
                      size: 16,
                      color: Theme.of(context).colorScheme.outline,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      'Updated ${_formatLastUpdate(machine.lastUpdate!)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: FilledButton.tonal(
                      onPressed: onTap,
                      child: const Text('Details'),
                    ),
                  ),
                  if (machine.status == MachineStatus.occupied) ...[
                    const SizedBox(width: 8),
                    IconButton.outlined(
                      onPressed: onNotifyPressed,
                      icon: const Icon(Icons.notifications),
                      tooltip: 'Notify when free',
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

### 7. **Navigation Architecture**

#### Go Router Configuration
```dart
final appRouter = GoRouter(
  initialLocation: '/branches',
  routes: [
    GoRoute(
      path: '/splash',
      builder: (context, state) => const SplashPage(),
    ),
    GoRoute(
      path: '/branches',
      builder: (context, state) => const BranchesPage(),
      routes: [
        GoRoute(
          path: '/branch/:branchId',
          builder: (context, state) => BranchDetailPage(
            branchId: state.pathParameters['branchId']!,
          ),
        ),
      ],
    ),
    GoRoute(
      path: '/dashboard/:branchId',
      builder: (context, state) => DashboardPage(
        branchId: state.pathParameters['branchId']!,
      ),
    ),
    GoRoute(
      path: '/machines',
      builder: (context, state) => MachinesPage(
        branchId: state.uri.queryParameters['branch'] ?? '',
        category: state.uri.queryParameters['category'] ?? 'legs',
      ),
      routes: [
        GoRoute(
          path: '/machine/:machineId',
          builder: (context, state) => MachineDetailPage(
            machineId: state.pathParameters['machineId']!,
            branchId: state.uri.queryParameters['branch'] ?? '',
            category: state.uri.queryParameters['category'] ?? 'legs',
          ),
        ),
      ],
    ),
    GoRoute(
      path: '/chat',
      builder: (context, state) => const ChatPage(),
    ),
    GoRoute(
      path: '/alerts',
      builder: (context, state) => const AlertsPage(),
    ),
    GoRoute(
      path: '/settings',
      builder: (context, state) => const SettingsPage(),
    ),
  ],
);
```

### 8. **Key Flutter Features Leveraging**

#### Platform Integration
- **Native GPS**: Geolocator for accurate positioning
- **Push Notifications**: Firebase Cloud Messaging integration
- **Background Processing**: For real-time updates when app is backgrounded
- **Deep Linking**: Navigate directly to specific machines/branches
- **Biometric Authentication**: Secure alert management (optional)

#### Performance Optimizations
- **Lazy Loading**: Load machines on-demand as user scrolls
- **Image Caching**: Efficient branch photo loading
- **State Persistence**: Maintain app state across sessions
- **Memory Management**: Proper disposal of streams and controllers
- **Build Optimization**: Tree shaking and code splitting

#### Offline Support
```dart
class CacheService {
  static const String _branchesKey = 'cached_branches';
  static const String _machinesKey = 'cached_machines';

  Future<void> cacheBranches(List<Branch> branches) async {
    final box = await Hive.openBox('gym_cache');
    await box.put(_branchesKey, branches.map((b) => b.toJson()).toList());
  }

  Future<List<Branch>?> getCachedBranches() async {
    final box = await Hive.openBox('gym_cache');
    final cached = box.get(_branchesKey) as List<dynamic>?;
    if (cached != null) {
      return cached.map((json) => Branch.fromJson(json)).toList();
    }
    return null;
  }

  Future<bool> hasInternetConnection() async {
    final connectivityResult = await Connectivity().checkConnectivity();
    return connectivityResult != ConnectivityResult.none;
  }
}
```

### 9. **Development Phases & Timeline**

#### Phase 1: Foundation (Week 1-2)
- Project setup and folder structure
- Dependencies configuration
- Basic routing and navigation
- API client setup with Retrofit
- Data models and entities

#### Phase 2: Core Features (Week 3-4)
- Branch listing with basic UI
- Google Maps integration
- Location services implementation
- Basic state management with Provider
- Error handling and loading states

#### Phase 3: Machine Management (Week 5-6)
- Machine listing and filtering
- Machine detail pages
- WebSocket integration for real-time updates
- Status badges and indicators
- Category-based organization

#### Phase 4: Dashboard & Analytics (Week 7-8)
- Dashboard with category overview
- Usage analytics with charts
- Peak hours display
- Quick statistics
- Performance optimizations

#### Phase 5: Advanced Features (Week 9-10)
- AI chat assistant integration
- Notification system implementation
- Alert management (create, update, cancel)
- Chat UI with recommendations
- Push notification setup

#### Phase 6: Polish & Testing (Week 11-12)
- UI/UX refinements
- Performance optimizations
- Comprehensive testing (unit, widget, integration)
- Bug fixes and edge case handling
- Documentation and deployment preparation

### 10. **Testing Strategy**

#### Unit Tests
```dart
// Example unit test for use case
void main() {
  group('GetBranches UseCase', () {
    late MockGymRepository mockRepository;
    late GetBranches useCase;

    setUp(() {
      mockRepository = MockGymRepository();
      useCase = GetBranches(mockRepository);
    });

    test('should return branches when repository call is successful', () async {
      // Arrange
      final expectedBranches = [
        Branch(id: '1', name: 'Central', coordinates: Coordinates(0, 0)),
      ];
      when(mockRepository.getBranches()).thenAnswer((_) async => expectedBranches);

      // Act
      final result = await useCase();

      // Assert
      expect(result, equals(expectedBranches));
      verify(mockRepository.getBranches()).called(1);
    });
  });
}
```

#### Widget Tests
```dart
// Example widget test
void main() {
  group('StatusBadge Widget', () {
    testWidgets('should display correct status for available machine', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StatusBadge(status: MachineStatus.available),
          ),
        ),
      );

      expect(find.text('Available'), findsOneWidget);
      expect(find.byIcon(Icons.check_circle), findsOneWidget);
    });
  });
}
```

#### Integration Tests
```dart
// Example integration test
void main() {
  group('App Integration Tests', () {
    testWidgets('should navigate from branches to machine detail', (tester) async {
      await tester.pumpWidget(MyApp());

      // Start at branches page
      expect(find.byType(BranchesPage), findsOneWidget);

      // Tap on first branch
      await tester.tap(find.byType(BranchCard).first);
      await tester.pumpAndSettle();

      // Should navigate to dashboard
      expect(find.byType(DashboardPage), findsOneWidget);
    });
  });
}
```

### 11. **Feature Parity Matrix**

| Web Feature | Flutter Implementation | Priority | Status |
|------------|------------------------|----------|---------|
| **Branch Listing + Interactive Map** | google_maps_flutter + custom bottom sheet | High | 📋 Planned |
| **Real-time Machine Status** | WebSocket + Provider + StreamBuilder | High | 📋 Planned |
| **Equipment Categories** | TabBar + GridView with custom cards | High | 📋 Planned |
| **Machine Detail with History** | Custom page + fl_chart heatmap | High | 📋 Planned |
| **Usage Analytics & Forecasting** | fl_chart + custom widgets | Medium | 📋 Planned |
| **AI Chat Assistant** | Chat UI + API integration | Medium | 📋 Planned |
| **Push Notifications & Alerts** | flutter_local_notifications + FCM | Medium | 📋 Planned |
| **Location Services** | geolocator + permission_handler | High | 📋 Planned |
| **Offline Caching** | Hive database + connectivity monitoring | Medium | ✨ Enhanced |
| **Biometric Authentication** | local_auth (optional) | Low | ➕ New |
| **Dark Mode Support** | Material Design 3 theming | Low | ➕ New |
| **Deep Linking** | go_router configuration | Low | ➕ New |

### 12. **Performance Considerations**

#### Memory Management
- Proper disposal of StreamSubscriptions
- WebSocket connection lifecycle management
- Image caching with automatic cleanup
- List virtualization for large datasets

#### Network Optimization
- Request caching and deduplication
- Retry mechanisms with exponential backoff
- Connection pooling for HTTP requests
- Efficient WebSocket reconnection strategy

#### UI Performance
- Lazy loading of list items
- Image placeholder and progressive loading
- Smooth animations with proper curves
- Efficient rebuild strategies with Provider

This comprehensive plan ensures the Flutter mobile app will provide feature parity with the React web application while leveraging Flutter's native capabilities for enhanced mobile user experience.

## Next Steps

1. **Environment Setup**: Configure development environment with Flutter SDK
2. **Project Initialization**: Create Flutter project with proper folder structure
3. **Dependencies**: Add all required packages to pubspec.yaml
4. **API Integration**: Set up Retrofit and Dio for backend communication
5. **State Management**: Implement Provider-based state management
6. **UI Implementation**: Build core screens starting with branch listing
7. **Testing**: Implement comprehensive test coverage
8. **Performance**: Optimize for mobile performance and battery life
9. **Deployment**: Prepare for app store deployment

The implementation will follow clean architecture principles, ensuring maintainable, testable, and scalable code that can evolve with the GymPulse platform.