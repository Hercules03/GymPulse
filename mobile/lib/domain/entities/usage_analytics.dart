import 'package:equatable/equatable.dart';

class UsageAnalytics extends Equatable {
  final String machineId;
  final int hour;
  final int dayOfWeek;
  final double averageUsage;
  final String? predictedFreeTime;
  final DateTime timestamp;
  final double? confidence;

  const UsageAnalytics({
    required this.machineId,
    required this.hour,
    required this.dayOfWeek,
    required this.averageUsage,
    this.predictedFreeTime,
    required this.timestamp,
    this.confidence,
  });

  @override
  List<Object?> get props => [
        machineId,
        hour,
        dayOfWeek,
        averageUsage,
        predictedFreeTime,
        timestamp,
        confidence,
      ];

  bool get isPeakHour {
    // Peak hours: 6-9 AM and 5-8 PM
    return (hour >= 6 && hour <= 9) || (hour >= 17 && hour <= 20);
  }

  bool get isOffPeakHour {
    // Off-peak hours: 10 PM - 5 AM
    return hour >= 22 || hour <= 5;
  }

  String get dayOfWeekName {
    const days = [
      'Sunday',
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday',
      'Saturday'
    ];
    return days[dayOfWeek];
  }

  String get hourDisplay {
    if (hour == 0) return '12 AM';
    if (hour < 12) return '$hour AM';
    if (hour == 12) return '12 PM';
    return '${hour - 12} PM';
  }

  UsageAnalytics copyWith({
    String? machineId,
    int? hour,
    int? dayOfWeek,
    double? averageUsage,
    String? predictedFreeTime,
    DateTime? timestamp,
    double? confidence,
  }) {
    return UsageAnalytics(
      machineId: machineId ?? this.machineId,
      hour: hour ?? this.hour,
      dayOfWeek: dayOfWeek ?? this.dayOfWeek,
      averageUsage: averageUsage ?? this.averageUsage,
      predictedFreeTime: predictedFreeTime ?? this.predictedFreeTime,
      timestamp: timestamp ?? this.timestamp,
      confidence: confidence ?? this.confidence,
    );
  }

  @override
  String toString() {
    return 'UsageAnalytics(machineId: $machineId, hour: $hour, usage: $averageUsage)';
  }
}
