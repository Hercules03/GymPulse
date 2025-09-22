import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:logger/logger.dart';
import '../../core/network/websocket_service.dart';
import '../../data/models/websocket_message.dart';

class WebSocketProvider extends ChangeNotifier {
  final Logger _logger = Logger();
  final WebSocketService _webSocketService = WebSocketService();

  // State
  bool _isConnected = false;
  bool _isConnecting = false;
  String _connectionStatus = 'disconnected';
  List<MachineUpdate> _recentUpdates = [];
  List<UserAlert> _recentAlerts = [];
  String? _errorMessage;

  // Stream subscriptions
  StreamSubscription<MachineUpdate>? _machineUpdateSubscription;
  StreamSubscription<UserAlert>? _userAlertSubscription;
  StreamSubscription<ConnectionStatus>? _connectionStatusSubscription;

  // Getters
  bool get isConnected => _isConnected;
  bool get isConnecting => _isConnecting;
  String get connectionStatus => _connectionStatus;
  List<MachineUpdate> get recentUpdates => _recentUpdates;
  List<UserAlert> get recentAlerts => _recentAlerts;
  String? get errorMessage => _errorMessage;
  MachineUpdate? get lastMachineUpdate => _recentUpdates.isNotEmpty ? _recentUpdates.last : null;

  WebSocketProvider() {
    _setupSubscriptions();
  }

  void _setupSubscriptions() {
    _machineUpdateSubscription = _webSocketService.machineUpdateStream.listen(
      _handleMachineUpdate,
      onError: (error) {
        _logger.e('Machine update stream error: $error');
        _errorMessage = error.toString();
        notifyListeners();
      },
    );

    _userAlertSubscription = _webSocketService.userAlertStream.listen(
      _handleUserAlert,
      onError: (error) {
        _logger.e('User alert stream error: $error');
        _errorMessage = error.toString();
        notifyListeners();
      },
    );

    _connectionStatusSubscription = _webSocketService.connectionStatusStream.listen(
      _handleConnectionStatus,
      onError: (error) {
        _logger.e('Connection status stream error: $error');
        _errorMessage = error.toString();
        notifyListeners();
      },
    );
  }

  void _handleMachineUpdate(MachineUpdate update) {
    _recentUpdates.insert(0, update);
    
    // Keep only the last 100 updates
    if (_recentUpdates.length > 100) {
      _recentUpdates.removeLast();
    }
    
    _logger.d('Received machine update: ${update.machineId} - ${update.status}');
    notifyListeners();
  }

  void _handleUserAlert(UserAlert alert) {
    _recentAlerts.insert(0, alert);
    
    // Keep only the last 50 alerts
    if (_recentAlerts.length > 50) {
      _recentAlerts.removeLast();
    }
    
    _logger.d('Received user alert: ${alert.alertId} - ${alert.status}');
    notifyListeners();
  }

  void _handleConnectionStatus(ConnectionStatus status) {
    _connectionStatus = status.status;
    _isConnected = status.status == 'connected';
    _isConnecting = status.status == 'connecting';
    
    if (status.message != null) {
      _errorMessage = status.message;
    } else if (status.status == 'connected') {
      _errorMessage = null;
    }
    
    _logger.d('Connection status changed: ${status.status}');
    notifyListeners();
  }

  Future<void> connect({
    List<String>? branches,
    List<String>? categories,
    String? userId,
    String? deviceId,
  }) async {
    if (_isConnecting || _isConnected) {
      _logger.w('WebSocket already connecting or connected');
      return;
    }

    _isConnecting = true;
    _errorMessage = null;
    notifyListeners();

    try {
      await _webSocketService.connect(
        branches: branches,
        categories: categories,
        userId: userId,
        deviceId: deviceId,
      );
      _logger.i('WebSocket connection initiated');
    } catch (e) {
      _isConnecting = false;
      _errorMessage = e.toString();
      _logger.e('Failed to connect WebSocket: $e');
      notifyListeners();
    }
  }

  Future<void> disconnect() async {
    await _webSocketService.disconnect();
    _isConnected = false;
    _isConnecting = false;
    _connectionStatus = 'disconnected';
    _logger.i('WebSocket disconnected');
    notifyListeners();
  }

  void sendMessage(Map<String, dynamic> message) {
    _webSocketService.sendMessage(message);
  }

  void clearUpdates() {
    _recentUpdates.clear();
    notifyListeners();
  }

  void clearAlerts() {
    _recentAlerts.clear();
    notifyListeners();
  }

  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  List<MachineUpdate> getUpdatesForMachine(String machineId) {
    return _recentUpdates.where((update) => update.machineId == machineId).toList();
  }

  List<UserAlert> getAlertsForUser(String userId) {
    return _recentAlerts.where((alert) => alert.userId == userId).toList();
  }

  @override
  void dispose() {
    _machineUpdateSubscription?.cancel();
    _userAlertSubscription?.cancel();
    _connectionStatusSubscription?.cancel();
    _webSocketService.dispose();
    _logger.d('WebSocketProvider disposed');
    super.dispose();
  }
}
