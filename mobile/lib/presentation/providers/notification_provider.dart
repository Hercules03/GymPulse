import 'package:flutter/foundation.dart';
import 'package:logger/logger.dart';

class UserAlert {
  final String alertId;
  final String userId;
  final String machineId;
  final String branchId;
  final String status;
  final DateTime createdAt;
  final DateTime? expiresAt;
  final Map<String, dynamic>? metadata;

  const UserAlert({
    required this.alertId,
    required this.userId,
    required this.machineId,
    required this.branchId,
    required this.status,
    required this.createdAt,
    this.expiresAt,
    this.metadata,
  });
}

class NotificationProvider extends ChangeNotifier {
  final Logger _logger = Logger();

  // State
  List<UserAlert> _alerts = [];
  bool _isLoading = false;
  String? _errorMessage;
  bool _notificationsEnabled = true;
  bool _quietHoursEnabled = false;
  int _quietStartHour = 22; // 10 PM
  int _quietEndHour = 6; // 6 AM

  // Getters
  List<UserAlert> get alerts => _alerts;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get notificationsEnabled => _notificationsEnabled;
  bool get quietHoursEnabled => _quietHoursEnabled;
  int get quietStartHour => _quietStartHour;
  int get quietEndHour => _quietEndHour;
  bool get hasAlerts => _alerts.isNotEmpty;

  List<UserAlert> get activeAlerts => _alerts.where((alert) => 
    alert.status == 'active' && 
    (alert.expiresAt == null || alert.expiresAt!.isAfter(DateTime.now()))
  ).toList();

  List<UserAlert> get expiredAlerts => _alerts.where((alert) => 
    alert.status == 'expired' || 
    (alert.expiresAt != null && alert.expiresAt!.isBefore(DateTime.now()))
  ).toList();

  Future<void> loadAlerts(String userId) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      // TODO: Implement actual API call to load alerts
      await _simulateApiCall();
      
      // Mock data for now
      _alerts = _generateMockAlerts(userId);
      _logger.i('Loaded ${_alerts.length} alerts for user $userId');
    } catch (e) {
      _errorMessage = e.toString();
      _logger.e('Error loading alerts: $e');
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> _simulateApiCall() async {
    await Future.delayed(const Duration(seconds: 1));
  }

  List<UserAlert> _generateMockAlerts(String userId) {
    final now = DateTime.now();
    return [
      UserAlert(
        alertId: 'alert_001',
        userId: userId,
        machineId: 'bench_press_001',
        branchId: 'downtown',
        status: 'active',
        createdAt: now.subtract(const Duration(minutes: 30)),
        expiresAt: now.add(const Duration(hours: 2)),
      ),
      UserAlert(
        alertId: 'alert_002',
        userId: userId,
        machineId: 'squat_rack_001',
        branchId: 'downtown',
        status: 'expired',
        createdAt: now.subtract(const Duration(hours: 1)),
        expiresAt: now.subtract(const Duration(minutes: 30)),
      ),
    ];
  }

  Future<void> createAlert({
    required String userId,
    required String machineId,
    required String branchId,
    Map<String, dynamic>? metadata,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      // TODO: Implement actual API call to create alert
      await _simulateApiCall();
      
      final newAlert = UserAlert(
        alertId: 'alert_${DateTime.now().millisecondsSinceEpoch}',
        userId: userId,
        machineId: machineId,
        branchId: branchId,
        status: 'active',
        createdAt: DateTime.now(),
        expiresAt: DateTime.now().add(const Duration(hours: 2)),
        metadata: metadata,
      );
      
      _alerts.add(newAlert);
      _logger.i('Created alert for machine $machineId');
    } catch (e) {
      _errorMessage = e.toString();
      _logger.e('Error creating alert: $e');
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> cancelAlert(String alertId) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      // TODO: Implement actual API call to cancel alert
      await _simulateApiCall();
      
      final index = _alerts.indexWhere((alert) => alert.alertId == alertId);
      if (index != -1) {
        _alerts[index] = UserAlert(
          alertId: _alerts[index].alertId,
          userId: _alerts[index].userId,
          machineId: _alerts[index].machineId,
          branchId: _alerts[index].branchId,
          status: 'cancelled',
          createdAt: _alerts[index].createdAt,
          expiresAt: _alerts[index].expiresAt,
          metadata: _alerts[index].metadata,
        );
        _logger.i('Cancelled alert $alertId');
      }
    } catch (e) {
      _errorMessage = e.toString();
      _logger.e('Error cancelling alert: $e');
    }

    _isLoading = false;
    notifyListeners();
  }

  void updateNotificationSettings({
    bool? notificationsEnabled,
    bool? quietHoursEnabled,
    int? quietStartHour,
    int? quietEndHour,
  }) {
    if (notificationsEnabled != null) {
      _notificationsEnabled = notificationsEnabled;
    }
    if (quietHoursEnabled != null) {
      _quietHoursEnabled = quietHoursEnabled;
    }
    if (quietStartHour != null) {
      _quietStartHour = quietStartHour;
    }
    if (quietEndHour != null) {
      _quietEndHour = quietEndHour;
    }
    
    _logger.i('Updated notification settings');
    notifyListeners();
  }

  bool shouldSendNotification() {
    if (!_notificationsEnabled) return false;
    
    if (_quietHoursEnabled) {
      final now = DateTime.now();
      final currentHour = now.hour;
      
      if (_quietStartHour > _quietEndHour) {
        // Quiet hours span midnight (e.g., 10 PM to 6 AM)
        return currentHour < _quietEndHour || currentHour >= _quietStartHour;
      } else {
        // Quiet hours within same day (e.g., 10 PM to 11 PM)
        return currentHour < _quietStartHour || currentHour >= _quietEndHour;
      }
    }
    
    return true;
  }

  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _logger.d('NotificationProvider disposed');
    super.dispose();
  }
}
