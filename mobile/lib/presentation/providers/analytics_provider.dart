import 'package:flutter/foundation.dart';
import 'package:logger/logger.dart';
import '../../domain/entities/usage_analytics.dart';

class AnalyticsProvider extends ChangeNotifier {
  final Logger _logger = Logger();

  // State
  List<UsageAnalytics> _usageData = [];
  Map<String, List<UsageAnalytics>> _machineUsageData = {};
  bool _isLoading = false;
  String? _errorMessage;
  DateTime? _lastUpdated;

  // Analytics data
  Map<String, double> _peakHours = {};
  Map<String, int> _categoryUsage = {};
  Map<String, double> _occupancyRates = {};

  // Getters
  List<UsageAnalytics> get usageData => _usageData;
  Map<String, List<UsageAnalytics>> get machineUsageData => _machineUsageData;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  DateTime? get lastUpdated => _lastUpdated;
  Map<String, double> get peakHours => _peakHours;
  Map<String, int> get categoryUsage => _categoryUsage;
  Map<String, double> get occupancyRates => _occupancyRates;

  bool get hasData => _usageData.isNotEmpty;

  Future<void> loadUsageAnalytics(String branchId) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      // TODO: Implement actual API call to load analytics
      await _simulateApiCall();
      
      _usageData = _generateMockUsageData();
      _calculateAnalytics();
      _lastUpdated = DateTime.now();
      
      _logger.i('Loaded usage analytics for branch $branchId');
    } catch (e) {
      _errorMessage = e.toString();
      _logger.e('Error loading usage analytics: $e');
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> loadMachineUsageHistory(String machineId) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      // TODO: Implement actual API call to load machine history
      await _simulateApiCall();
      
      _machineUsageData[machineId] = _generateMockMachineUsageData(machineId);
      
      _logger.i('Loaded usage history for machine $machineId');
    } catch (e) {
      _errorMessage = e.toString();
      _logger.e('Error loading machine usage history: $e');
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> _simulateApiCall() async {
    await Future.delayed(const Duration(seconds: 1));
  }

  List<UsageAnalytics> _generateMockUsageData() {
    final now = DateTime.now();
    final data = <UsageAnalytics>[];

    // Generate 24 hours of data for the past week
    for (int day = 0; day < 7; day++) {
      for (int hour = 0; hour < 24; hour++) {
        final timestamp = now.subtract(Duration(days: day, hours: hour));
        
        // Simulate usage patterns
        double baseUsage = 0.3;
        if ((hour >= 6 && hour <= 9) || (hour >= 17 && hour <= 20)) {
          baseUsage = 0.8; // Peak hours
        } else if ((hour >= 10 && hour <= 16) || (hour >= 21 && hour <= 22)) {
          baseUsage = 0.5; // Moderate usage
        }

        // Add some randomness
        final usage = (baseUsage + (DateTime.now().millisecondsSinceEpoch % 100 - 50) / 100).clamp(0.0, 1.0);

        data.add(UsageAnalytics(
          machineId: 'mock_machine',
          hour: hour,
          dayOfWeek: timestamp.weekday % 7,
          averageUsage: usage,
          predictedFreeTime: usage > 0.7 ? '${(DateTime.now().millisecondsSinceEpoch % 30 + 5)} mins' : null,
          timestamp: timestamp,
          confidence: 0.85,
        ));
      }
    }

    return data;
  }

  List<UsageAnalytics> _generateMockMachineUsageData(String machineId) {
    final now = DateTime.now();
    final data = <UsageAnalytics>[];

    // Generate 24 hours of data for the past 3 days
    for (int day = 0; day < 3; day++) {
      for (int hour = 0; hour < 24; hour++) {
        final timestamp = now.subtract(Duration(days: day, hours: hour));
        
        // Simulate machine-specific usage patterns
        double baseUsage = 0.2;
        if (machineId.contains('cardio')) {
          baseUsage = 0.4; // Cardio machines are more popular
        } else if (machineId.contains('legs')) {
          baseUsage = 0.6; // Leg machines are very popular
        }

        if ((hour >= 6 && hour <= 9) || (hour >= 17 && hour <= 20)) {
          baseUsage *= 1.5; // Peak hours multiplier
        }

        final usage = baseUsage.clamp(0.0, 1.0);

        data.add(UsageAnalytics(
          machineId: machineId,
          hour: hour,
          dayOfWeek: timestamp.weekday % 7,
          averageUsage: usage,
          predictedFreeTime: usage > 0.7 ? '${(DateTime.now().millisecondsSinceEpoch % 30 + 5)} mins' : null,
          timestamp: timestamp,
          confidence: 0.9,
        ));
      }
    }

    return data;
  }

  void _calculateAnalytics() {
    _calculatePeakHours();
    _calculateCategoryUsage();
    _calculateOccupancyRates();
  }

  void _calculatePeakHours() {
    final hourUsage = <int, double>{};
    
    for (final data in _usageData) {
      hourUsage[data.hour] = (hourUsage[data.hour] ?? 0.0) + data.averageUsage;
    }

    _peakHours = hourUsage.map((hour, usage) => MapEntry(hour.toString(), usage));
  }

  void _calculateCategoryUsage() {
    // Mock category usage data
    _categoryUsage = {
      'legs': 45,
      'chest': 32,
      'back': 28,
      'cardio': 67,
      'arms': 23,
    };
  }

  void _calculateOccupancyRates() {
    // Mock occupancy rates
    _occupancyRates = {
      'legs': 0.75,
      'chest': 0.60,
      'back': 0.55,
      'cardio': 0.85,
      'arms': 0.40,
    };
  }

  List<UsageAnalytics> getUsageForHour(int hour) {
    return _usageData.where((data) => data.hour == hour).toList();
  }

  List<UsageAnalytics> getUsageForDay(int dayOfWeek) {
    return _usageData.where((data) => data.dayOfWeek == dayOfWeek).toList();
  }

  double getAverageUsageForHour(int hour) {
    final hourData = getUsageForHour(hour);
    if (hourData.isEmpty) return 0.0;
    
    return hourData.map((data) => data.averageUsage).reduce((a, b) => a + b) / hourData.length;
  }

  List<int> getTopPeakHours({int count = 3}) {
    final sortedHours = _peakHours.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    
    return sortedHours.take(count).map((entry) => int.parse(entry.key)).toList();
  }

  void clearData() {
    _usageData.clear();
    _machineUsageData.clear();
    _peakHours.clear();
    _categoryUsage.clear();
    _occupancyRates.clear();
    _lastUpdated = null;
    notifyListeners();
  }

  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _logger.d('AnalyticsProvider disposed');
    super.dispose();
  }
}
