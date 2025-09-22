import 'package:flutter/foundation.dart';
import 'package:logger/logger.dart';
import 'package:geolocator/geolocator.dart';

import '../../core/network/api_client.dart';
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
      
      // Fallback to mock response if API fails
      final fallbackMessage = ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        message: _generateMockResponse(message),
        role: 'assistant',
        timestamp: DateTime.now(),
        recommendations: _generateMockRecommendations(),
      );
      
      _messages.add(fallbackMessage);
      _logger.w('Using fallback response due to API error');
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

  String _generateMockResponse(String userMessage) {
    final message = userMessage.toLowerCase();
    
    if (message.contains('available') || message.contains('free')) {
      return 'I can help you find available equipment! Based on current data, there are several machines available in the cardio and legs sections. Would you like me to show you specific recommendations?';
    } else if (message.contains('busy') || message.contains('crowded')) {
      return 'Peak hours are typically 6-9 AM and 5-8 PM. Right now, the gym is moderately busy. I recommend checking the real-time status of specific machines before heading over.';
    } else if (message.contains('recommend') || message.contains('suggest')) {
      return 'Here are some great options based on your preferences: The leg press machine is currently available, and the cardio section has several open treadmills. Would you like more details about any specific equipment?';
    } else {
      return 'I\'m here to help you with gym equipment availability, recommendations, and any questions about your workout! What would you like to know?';
    }
  }

  List<ChatRecommendation> _generateMockRecommendations() {
    return [
      const ChatRecommendation(
        type: 'machine',
        title: 'Leg Press Machine',
        description: 'Currently available - perfect for leg day!',
        machineId: 'leg_press_001',
        category: 'legs',
      ),
      const ChatRecommendation(
        type: 'category',
        title: 'Cardio Section',
        description: 'Multiple treadmills and bikes available',
        category: 'cardio',
      ),
      const ChatRecommendation(
        type: 'branch',
        title: 'Downtown Branch',
        description: 'Less crowded right now - 15 min walk away',
        branchId: 'downtown',
      ),
    ];
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

  @override
  void dispose() {
    _logger.d('ChatProvider disposed');
    super.dispose();
  }
}
