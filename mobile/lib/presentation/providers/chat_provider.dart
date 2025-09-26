import 'package:flutter/foundation.dart';
import 'package:logger/logger.dart';
import 'package:geolocator/geolocator.dart';

import '../../core/network/api_client.dart';
import '../../core/constants/api_constants.dart';
import '../../data/models/api/chat_response.dart';
import '../../data/datasources/remote/gym_api_service.dart';

class ChatMessage {
  final String id;
  final String message;
  final String role; // 'user' or 'assistant'
  final DateTime timestamp;
  final List<ChatRecommendation>? recommendations;

  const ChatMessage({
    required this.id,
    required this.message,
    required this.role,
    required this.timestamp,
    this.recommendations,
  });
}

class ChatRecommendation {
  final String type;
  final String title;
  final String description;
  final String? branchId;
  final String? machineId;
  final String? category;

  const ChatRecommendation({
    required this.type,
    required this.title,
    required this.description,
    this.branchId,
    this.machineId,
    this.category,
  });
}

class ChatProvider extends ChangeNotifier {
  final Logger _logger = Logger();
  late final GymApiService _apiService;

  // State
  List<ChatMessage> _messages = [];
  bool _isLoading = false;
  String? _errorMessage;
  String _currentInput = '';
  Position? _userLocation;

  ChatProvider() {
    _apiService = GymApiService(ApiClient.createDio());
  }

  // Getters
  List<ChatMessage> get messages => _messages;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  String get currentInput => _currentInput;
  bool get hasMessages => _messages.isNotEmpty;

  void updateInput(String input) {
    _currentInput = input;
    notifyListeners();
  }

  void clearInput() {
    _currentInput = '';
    notifyListeners();
  }

  Future<void> sendMessage(String message) async {
    if (message.trim().isEmpty) return;

    // Add user message
    final userMessage = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      message: message.trim(),
      role: 'user',
      timestamp: DateTime.now(),
    );

    _messages.add(userMessage);
    _currentInput = '';
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      // Get user location if available
      await _getUserLocation();

      // Prepare chat request
      final chatRequest = ChatRequest(
        message: message.trim(),
        userLocation: _userLocation != null
            ? UserLocationModel(
                lat: _userLocation!.latitude,
                lon: _userLocation!.longitude,
              )
            : null,
        sessionId: 'mobile_app_${DateTime.now().millisecondsSinceEpoch}',
      );

      _logger.i('Sending chat request: ${chatRequest.toJson()}');

      // Send request to API
      final chatResponse = await _apiService.sendChatMessage(chatRequest);

      _logger.i('Chat response received: ${chatResponse.toJson()}');

      // Convert API recommendations to app format
      final recommendations = chatResponse.recommendations?.map((rec) =>
        ChatRecommendation(
          type: 'branch',
          title: rec.name,
          description: '${rec.availableCount}/${rec.totalCount} machines available • ${rec.distance} away',
          branchId: rec.branchId,
          category: rec.category,
        ),
      ).toList();

      // Add assistant response
      final assistantMessage = ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        message: chatResponse.response,
        role: 'assistant',
        timestamp: DateTime.now(),
        recommendations: recommendations,
      );

      _messages.add(assistantMessage);
      _logger.i('Chat message sent and response received');
    } catch (e) {
      _logger.e('Error sending chat message: $e');

      // Set error message instead of using mock response
      _errorMessage = 'Failed to send message: ${e.toString()}';

      // Add error message to chat
      final errorMessage = ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        message: 'Sorry, I\'m having trouble connecting to the server right now. Please check your internet connection and try again.',
        role: 'assistant',
        timestamp: DateTime.now(),
      );

      _messages.add(errorMessage);
      _logger.e('API call failed, showing error message to user');
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> _getUserLocation() async {
    if (_userLocation != null) return; // Already have location

    try {
      // Check if location services are enabled
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        _logger.w('Location services are disabled');
        return;
      }

      // Check permissions
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          _logger.w('Location permission denied');
          return;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        _logger.w('Location permission permanently denied');
        return;
      }

      // Get current position
      _userLocation = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.medium,
        timeLimit: const Duration(seconds: 10),
      );

      _logger.i('User location obtained: ${_userLocation!.latitude}, ${_userLocation!.longitude}');
    } catch (e) {
      _logger.w('Failed to get user location: $e');
    }
  }


  void clearMessages() {
    _messages.clear();
    notifyListeners();
  }

  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  void addMessage(String content, {required bool isUser}) {
    final message = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      message: content,
      role: isUser ? 'user' : 'assistant',
      timestamp: DateTime.now(),
    );
    
    _messages.add(message);
    notifyListeners();
  }

  /// Test function to check API connectivity
  Future<void> testApiConnection() async {
    try {
      _logger.i('=== TESTING API CONNECTION ===');
      _logger.i('Base URL: ${ApiConstants.baseUrl}');

      // Test health endpoint first
      final healthResponse = await _apiService.healthCheck();
      _logger.i('Health check successful: ${healthResponse.toJson()}');

      // Test simple chat message
      final testRequest = ChatRequest(
        message: 'Hello, this is a test message',
        sessionId: 'test_session_${DateTime.now().millisecondsSinceEpoch}',
      );

      _logger.i('Sending test chat request: ${testRequest.toJson()}');
      final testResponse = await _apiService.sendChatMessage(testRequest);
      _logger.i('Test chat response: ${testResponse.toJson()}');

    } catch (e, stackTrace) {
      _logger.e('API test failed: $e');
      _logger.e('Stack trace: $stackTrace');
    }
  }

  @override
  void dispose() {
    _logger.d('ChatProvider disposed');
    super.dispose();
  }
}
