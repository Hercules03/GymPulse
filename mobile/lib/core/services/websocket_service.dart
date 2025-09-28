import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/io.dart';

import '../constants/app_constants.dart';

enum WebSocketConnectionState {
  disconnected,
  connecting,
  connected,
  reconnecting,
  error,
}

class WebSocketMessage {
  final String type;
  final Map<String, dynamic> data;
  final int timestamp;

  WebSocketMessage({
    required this.type,
    required this.data,
    required this.timestamp,
  });

  factory WebSocketMessage.fromJson(Map<String, dynamic> json) {
    return WebSocketMessage(
      type: json['type'] ?? 'unknown',
      data: json['data'] ?? {},
      timestamp: json['timestamp'] ?? DateTime.now().millisecondsSinceEpoch,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'data': data,
      'timestamp': timestamp,
    };
  }
}

class WebSocketService extends ChangeNotifier {
  WebSocketChannel? _channel;
  Timer? _reconnectTimer;
  Timer? _pingTimer;
  int _reconnectAttempts = 0;
  WebSocketConnectionState _connectionState = WebSocketConnectionState.disconnected;

  // Stream controllers for different message types
  final StreamController<WebSocketMessage> _messageController = StreamController.broadcast();
  final StreamController<Map<String, dynamic>> _machineUpdateController = StreamController.broadcast();
  final StreamController<Map<String, dynamic>> _branchUpdateController = StreamController.broadcast();
  final StreamController<Map<String, dynamic>> _alertController = StreamController.broadcast();

  // Getters
  WebSocketConnectionState get connectionState => _connectionState;
  bool get isConnected => _connectionState == WebSocketConnectionState.connected;
  Stream<WebSocketMessage> get messageStream => _messageController.stream;
  Stream<Map<String, dynamic>> get machineUpdates => _machineUpdateController.stream;
  Stream<Map<String, dynamic>> get branchUpdates => _branchUpdateController.stream;
  Stream<Map<String, dynamic>> get alerts => _alertController.stream;

  // Connect to WebSocket
  Future<void> connect({String? branchId}) async {
    if (_connectionState == WebSocketConnectionState.connected ||
        _connectionState == WebSocketConnectionState.connecting) {
      return;
    }

    _setConnectionState(WebSocketConnectionState.connecting);

    try {
      final uri = _buildWebSocketUri(branchId: branchId);
      debugPrint('Connecting to WebSocket: $uri');

      _channel = IOWebSocketChannel.connect(
        uri,
        headers: _buildHeaders(),
        connectTimeout: AppConstants.websocketTimeout,
      );

      // Listen to the stream
      _channel!.stream.listen(
        _handleMessage,
        onError: _handleError,
        onDone: _handleDisconnection,
        cancelOnError: false,
      );

      // Send initial connection message
      _sendMessage({
        'type': 'connect',
        'data': {
          'branchId': branchId,
          'clientType': 'flutter',
          'timestamp': DateTime.now().millisecondsSinceEpoch,
        },
      });

      _setConnectionState(WebSocketConnectionState.connected);
      _reconnectAttempts = 0;
      _startPingTimer();

      debugPrint('WebSocket connected successfully');
    } catch (e) {
      debugPrint('WebSocket connection error: $e');
      _setConnectionState(WebSocketConnectionState.error);
      _scheduleReconnect();
    }
  }

  // Disconnect from WebSocket
  void disconnect() {
    _reconnectTimer?.cancel();
    _pingTimer?.cancel();
    _channel?.sink.close();
    _channel = null;
    _setConnectionState(WebSocketConnectionState.disconnected);
    debugPrint('WebSocket disconnected');
  }

  // Subscribe to branch updates
  void subscribeToBranch(String branchId) {
    if (!isConnected) return;

    _sendMessage({
      'type': 'subscribe',
      'data': {
        'branchId': branchId,
        'events': ['machine_status', 'branch_stats', 'alerts'],
      },
    });
  }

  // Unsubscribe from branch updates
  void unsubscribeFromBranch(String branchId) {
    if (!isConnected) return;

    _sendMessage({
      'type': 'unsubscribe',
      'data': {
        'branchId': branchId,
      },
    });
  }

  // Subscribe to machine updates
  void subscribeToMachine(String machineId) {
    if (!isConnected) return;

    _sendMessage({
      'type': 'subscribe_machine',
      'data': {
        'machineId': machineId,
      },
    });
  }

  // Unsubscribe from machine updates
  void unsubscribeFromMachine(String machineId) {
    if (!isConnected) return;

    _sendMessage({
      'type': 'unsubscribe_machine',
      'data': {
        'machineId': machineId,
      },
    });
  }

  // Send ping to keep connection alive
  void sendPing() {
    if (!isConnected) return;

    _sendMessage({
      'type': 'ping',
      'data': {
        'timestamp': DateTime.now().millisecondsSinceEpoch,
      },
    });
  }

  // Private methods

  Uri _buildWebSocketUri({String? branchId}) {
    final baseUrl = AppConstants.websocketUrl;
    final uri = Uri.parse(baseUrl);

    final queryParams = <String, String>{};
    if (branchId != null) {
      queryParams['branchId'] = branchId;
    }

    return uri.replace(queryParameters: queryParams.isNotEmpty ? queryParams : null);
  }

  Map<String, String> _buildHeaders() {
    return {
      'User-Agent': 'GymPulse-Flutter/1.0.0',
      'Sec-WebSocket-Protocol': 'gym-pulse-protocol',
    };
  }

  void _sendMessage(Map<String, dynamic> message) {
    if (!isConnected || _channel == null) return;

    try {
      final jsonMessage = jsonEncode(message);
      _channel!.sink.add(jsonMessage);
      debugPrint('WebSocket message sent: ${message['type']}');
    } catch (e) {
      debugPrint('Error sending WebSocket message: $e');
    }
  }

  void _handleMessage(dynamic data) {
    try {
      final Map<String, dynamic> messageData = jsonDecode(data as String);
      final message = WebSocketMessage.fromJson(messageData);

      // Add to main message stream
      _messageController.add(message);

      // Route to specific streams based on message type
      switch (message.type) {
        case 'machine_status_update':
          _machineUpdateController.add(message.data);
          break;
        case 'branch_stats_update':
          _branchUpdateController.add(message.data);
          break;
        case 'alert':
        case 'notification':
          _alertController.add(message.data);
          break;
        case 'pong':
          // Handle pong response
          debugPrint('Received pong from server');
          break;
        case 'error':
          debugPrint('WebSocket error: ${message.data}');
          break;
        default:
          debugPrint('Unknown message type: ${message.type}');
      }
    } catch (e) {
      debugPrint('Error parsing WebSocket message: $e');
    }
  }

  void _handleError(error) {
    debugPrint('WebSocket error: $error');
    _setConnectionState(WebSocketConnectionState.error);
    _scheduleReconnect();
  }

  void _handleDisconnection() {
    debugPrint('WebSocket disconnected');
    _setConnectionState(WebSocketConnectionState.disconnected);
    _scheduleReconnect();
  }

  void _scheduleReconnect() {
    if (_reconnectAttempts >= AppConstants.maxReconnectAttempts) {
      debugPrint('Max reconnection attempts reached');
      _setConnectionState(WebSocketConnectionState.error);
      return;
    }

    _reconnectAttempts++;
    final delay = Duration(
      milliseconds: AppConstants.reconnectInterval.inMilliseconds * _reconnectAttempts,
    );

    debugPrint('Scheduling reconnect attempt $_reconnectAttempts in ${delay.inSeconds}s');

    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(delay, () {
      if (_connectionState != WebSocketConnectionState.connected) {
        _setConnectionState(WebSocketConnectionState.reconnecting);
        connect();
      }
    });
  }

  void _startPingTimer() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(
      AppConstants.pingInterval,
      (_) => sendPing(),
    );
  }

  void _setConnectionState(WebSocketConnectionState state) {
    if (_connectionState != state) {
      _connectionState = state;
      notifyListeners();
      debugPrint('WebSocket connection state: $state');
    }
  }

  @override
  void dispose() {
    disconnect();
    _messageController.close();
    _machineUpdateController.close();
    _branchUpdateController.close();
    _alertController.close();
    super.dispose();
  }
}

// Singleton instance
final webSocketService = WebSocketService();