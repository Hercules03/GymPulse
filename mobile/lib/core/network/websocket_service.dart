import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:logger/logger.dart';
import '../constants/websocket_constants.dart';
import '../config/environment_config.dart';
import '../../data/models/websocket_message.dart';

class WebSocketService {
  static final Logger _logger = Logger();
  
  WebSocketChannel? _channel;
  StreamController<MachineUpdate> _machineUpdateController = StreamController.broadcast();
  StreamController<UserAlert> _userAlertController = StreamController.broadcast();
  StreamController<ConnectionStatus> _connectionStatusController = StreamController.broadcast();
  
  Timer? _pingTimer;
  Timer? _reconnectTimer;
  int _reconnectAttempts = 0;
  bool _isConnected = false;
  bool _isConnecting = false;

  // Stream getters
  Stream<MachineUpdate> get machineUpdateStream => _machineUpdateController.stream;
  Stream<UserAlert> get userAlertStream => _userAlertController.stream;
  Stream<ConnectionStatus> get connectionStatusStream => _connectionStatusController.stream;
  
  bool get isConnected => _isConnected;
  bool get isConnecting => _isConnecting;

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
    _connectionStatusController.add(ConnectionStatus(
      status: WebSocketConstants.connecting,
      timestamp: DateTime.now(),
    ));

    try {
      final queryParams = <String, String>{};
      if (branches?.isNotEmpty == true) {
        queryParams[WebSocketConstants.branchesParam] = branches!.join(',');
      }
      if (categories?.isNotEmpty == true) {
        queryParams[WebSocketConstants.categoriesParam] = categories!.join(',');
      }
      if (userId != null) {
        queryParams[WebSocketConstants.userIdParam] = userId;
      }
      if (deviceId != null) {
        queryParams[WebSocketConstants.deviceIdParam] = deviceId;
      }

      final uri = Uri.parse(EnvironmentConfig.websocketUrl).replace(
        queryParameters: queryParams,
      );

      _logger.i('Connecting to WebSocket: $uri');
      _channel = WebSocketChannel.connect(uri);

      _channel!.stream.listen(
        _handleMessage,
        onError: _handleError,
        onDone: _handleDisconnect,
      );

      _isConnected = true;
      _isConnecting = false;
      _reconnectAttempts = 0;
      
      _connectionStatusController.add(ConnectionStatus(
        status: WebSocketConstants.connected,
        timestamp: DateTime.now(),
      ));

      _startPingTimer();
      _logger.i('WebSocket connected successfully');
    } catch (e) {
      _isConnecting = false;
      _logger.e('Failed to connect to WebSocket: $e');
      _connectionStatusController.add(ConnectionStatus(
        status: WebSocketConstants.error,
        timestamp: DateTime.now(),
        message: e.toString(),
      ));
      _scheduleReconnect();
    }
  }

  void _handleMessage(dynamic data) {
    try {
      final json = jsonDecode(data as String);
      final message = WebSocketMessage.fromJson(json);

      _logger.d('Received WebSocket message: ${message.type}');

      switch (message.type) {
        case WebSocketConstants.machineUpdateType:
          final update = MachineUpdate.fromJson(message.data);
          _machineUpdateController.add(update);
          break;
        case WebSocketConstants.userAlertType:
          final alert = UserAlert.fromJson(message.data);
          _userAlertController.add(alert);
          break;
        case WebSocketConstants.pongType:
          _logger.d('Received pong');
          break;
        default:
          _logger.w('Unknown message type: ${message.type}');
      }
    } catch (e) {
      _logger.e('Error parsing WebSocket message: $e');
    }
  }

  void _handleError(dynamic error) {
    _logger.e('WebSocket error: $error');
    _connectionStatusController.add(ConnectionStatus(
      status: WebSocketConstants.error,
      timestamp: DateTime.now(),
      message: error.toString(),
    ));
    _scheduleReconnect();
  }

  void _handleDisconnect() {
    _logger.i('WebSocket disconnected');
    _isConnected = false;
    _isConnecting = false;
    _stopPingTimer();
    
    _connectionStatusController.add(ConnectionStatus(
      status: WebSocketConstants.disconnected,
      timestamp: DateTime.now(),
    ));
    
    _scheduleReconnect();
  }

  void _scheduleReconnect() {
    if (_reconnectAttempts >= WebSocketConstants.maxReconnectAttempts) {
      _logger.e('Max reconnection attempts reached');
      return;
    }

    _reconnectAttempts++;
    final delay = Duration(
      seconds: (WebSocketConstants.initialReconnectDelay.inSeconds * 
                _reconnectAttempts).clamp(
        WebSocketConstants.initialReconnectDelay.inSeconds,
        WebSocketConstants.maxReconnectDelay.inSeconds,
      ),
    );

    _logger.i('Scheduling reconnection attempt $_reconnectAttempts in ${delay.inSeconds}s');
    
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(delay, () {
      if (!_isConnected && !_isConnecting) {
        _logger.i('Attempting to reconnect...');
        connect(); // Reconnect with same parameters
      }
    });
  }

  void _startPingTimer() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(WebSocketConstants.pingInterval, (_) {
      if (_isConnected) {
        _sendPing();
      }
    });
  }

  void _stopPingTimer() {
    _pingTimer?.cancel();
  }

  void _sendPing() {
    if (_isConnected && _channel != null) {
      try {
        final pingMessage = {
          'type': WebSocketConstants.pingType,
          'timestamp': DateTime.now().toIso8601String(),
        };
        _channel!.sink.add(jsonEncode(pingMessage));
        _logger.d('Sent ping');
      } catch (e) {
        _logger.e('Error sending ping: $e');
      }
    }
  }

  void sendMessage(Map<String, dynamic> message) {
    if (_isConnected && _channel != null) {
      try {
        _channel!.sink.add(jsonEncode(message));
        _logger.d('Sent message: ${message['type']}');
      } catch (e) {
        _logger.e('Error sending message: $e');
      }
    } else {
      _logger.w('Cannot send message: WebSocket not connected');
    }
  }

  Future<void> disconnect() async {
    _logger.i('Disconnecting WebSocket...');
    
    _reconnectTimer?.cancel();
    _stopPingTimer();
    
    if (_channel != null) {
      await _channel!.sink.close();
      _channel = null;
    }
    
    _isConnected = false;
    _isConnecting = false;
    _reconnectAttempts = 0;
    
    _connectionStatusController.add(ConnectionStatus(
      status: WebSocketConstants.disconnected,
      timestamp: DateTime.now(),
    ));
    
    _logger.i('WebSocket disconnected');
  }

  void dispose() {
    disconnect();
    _machineUpdateController.close();
    _userAlertController.close();
    _connectionStatusController.close();
  }
}
