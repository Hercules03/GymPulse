import '../entities/branch.dart';
import '../entities/machine.dart';

/// Abstract repository for gym-related data operations
abstract class GymRepository {
  /// Get all available branches
  Future<List<Branch>> getBranches();

  /// Get peak hours data for a specific branch
  Future<PeakHoursData> getBranchPeakHours(String branchId);

  /// Get machines for a specific branch and category
  Future<List<Machine>> getMachines(String branchId, String category);

  /// Get machine history data
  Future<MachineHistory> getMachineHistory(String machineId, {String range = '24h'});

  /// Get machine forecast
  Future<MachineForecast> getMachineForecast(String machineId, {int minutes = 30});

  /// Check service health
  Future<bool> healthCheck();
}

/// Data class for peak hours information
class PeakHoursData {
  const PeakHoursData({
    required this.branchId,
    required this.currentHour,
    required this.currentOccupancy,
    required this.peakHours,
    required this.confidence,
    required this.occupancyForecast,
    required this.nextPeakIn,
    required this.totalMachines,
    required this.generatedAt,
  });

  final String branchId;
  final int currentHour;
  final int currentOccupancy;
  final String peakHours;
  final String confidence;
  final Map<String, double> occupancyForecast;
  final int nextPeakIn;
  final int totalMachines;
  final String generatedAt;
}

/// Data class for machine usage history
class MachineHistory {
  const MachineHistory({
    required this.machineId,
    required this.history,
    required this.timeRange,
    required this.forecast,
    required this.totalBins,
  });

  final String machineId;
  final List<HistoryBin> history;
  final TimeRange timeRange;
  final BasicForecast forecast;
  final int totalBins;
}

/// Data class for history bin
class HistoryBin {
  const HistoryBin({
    required this.timestamp,
    required this.occupancyRatio,
    required this.freeCount,
    required this.totalCount,
    required this.status,
  });

  final int timestamp;
  final double occupancyRatio;
  final int freeCount;
  final int totalCount;
  final String status;

  /// Get usage percentage
  int get usagePercentage => (occupancyRatio * 100).round();

  /// Get hour of day
  int get hour => DateTime.fromMillisecondsSinceEpoch(timestamp * 1000).hour;
}

/// Data class for time range
class TimeRange {
  const TimeRange({
    required this.start,
    required this.end,
    required this.duration,
  });

  final int start;
  final int end;
  final String duration;
}

/// Data class for basic forecast
class BasicForecast {
  const BasicForecast({
    required this.likelyFreeIn30m,
    required this.confidence,
    required this.reason,
  });

  final bool likelyFreeIn30m;
  final String confidence;
  final String reason;
}

/// Data class for detailed machine forecast
class MachineForecast {
  const MachineForecast({
    required this.machineId,
    required this.forecast,
    required this.success,
  });

  final String machineId;
  final DetailedForecast forecast;
  final bool success;
}

/// Data class for detailed forecast
class DetailedForecast {
  const DetailedForecast({
    required this.likelyFreeIn30m,
    required this.classification,
    required this.displayText,
    required this.confidence,
    required this.probability,
    this.peakHours,
  });

  final bool likelyFreeIn30m;
  final String classification;
  final String displayText;
  final String confidence;
  final double probability;
  final String? peakHours;
}