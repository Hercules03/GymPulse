import 'package:json_annotation/json_annotation.dart';

part 'machine_response.g.dart';

/// API response model for machines endpoint
@JsonSerializable()
class MachinesResponse {
  const MachinesResponse({
    required this.machines,
    required this.branchId,
    required this.category,
    required this.totalCount,
    required this.freeCount,
    required this.occupiedCount,
  });

  final List<MachineModel> machines;
  final String branchId;
  final String category;
  final int totalCount;
  final int freeCount;
  final int occupiedCount;

  factory MachinesResponse.fromJson(Map<String, dynamic> json) =>
      _$MachinesResponseFromJson(json);

  Map<String, dynamic> toJson() => _$MachinesResponseToJson(this);
}

/// API model for individual machine data
@JsonSerializable()
class MachineModel {
  const MachineModel({
    required this.machineId,
    required this.name,
    required this.status,
    required this.category,
    required this.gymId,
    this.lastUpdate,
    this.lastChange,
    this.coordinates,
    this.alertEligible = true,
    this.type,
    this.estimatedFreeTime,
  });

  final String machineId;
  final String name;
  final String status;
  final String category;
  final String gymId;
  final int? lastUpdate;
  final int? lastChange;
  final MachineCoordinatesModel? coordinates;
  final bool alertEligible;
  final String? type;
  final String? estimatedFreeTime;

  factory MachineModel.fromJson(Map<String, dynamic> json) =>
      _$MachineModelFromJson(json);

  Map<String, dynamic> toJson() => _$MachineModelToJson(this);
}

/// API model for machine coordinates
@JsonSerializable()
class MachineCoordinatesModel {
  const MachineCoordinatesModel({
    required this.lat,
    required this.lon,
  });

  final double lat;
  final double lon;

  factory MachineCoordinatesModel.fromJson(Map<String, dynamic> json) =>
      _$MachineCoordinatesModelFromJson(json);

  Map<String, dynamic> toJson() => _$MachineCoordinatesModelToJson(this);
}

/// API response for machine history
@JsonSerializable()
class MachineHistoryResponse {
  const MachineHistoryResponse({
    required this.machineId,
    required this.history,
    required this.timeRange,
    required this.forecast,
    required this.totalBins,
  });

  final String machineId;
  final List<HistoryBinModel> history;
  final TimeRangeModel timeRange;
  final ForecastModel forecast;
  final int totalBins;

  factory MachineHistoryResponse.fromJson(Map<String, dynamic> json) =>
      _$MachineHistoryResponseFromJson(json);

  Map<String, dynamic> toJson() => _$MachineHistoryResponseToJson(this);
}

/// API model for usage history bin
@JsonSerializable()
class HistoryBinModel {
  const HistoryBinModel({
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

  factory HistoryBinModel.fromJson(Map<String, dynamic> json) =>
      _$HistoryBinModelFromJson(json);

  Map<String, dynamic> toJson() => _$HistoryBinModelToJson(this);
}

/// API model for time range
@JsonSerializable()
class TimeRangeModel {
  const TimeRangeModel({
    required this.start,
    required this.end,
    required this.duration,
  });

  final int start;
  final int end;
  final String duration;

  factory TimeRangeModel.fromJson(Map<String, dynamic> json) =>
      _$TimeRangeModelFromJson(json);

  Map<String, dynamic> toJson() => _$TimeRangeModelToJson(this);
}

/// API model for machine forecast
@JsonSerializable()
class ForecastModel {
  const ForecastModel({
    required this.likelyFreeIn30m,
    required this.confidence,
    required this.reason,
  });

  final bool likelyFreeIn30m;
  final String confidence;
  final String reason;

  factory ForecastModel.fromJson(Map<String, dynamic> json) =>
      _$ForecastModelFromJson(json);

  Map<String, dynamic> toJson() => _$ForecastModelToJson(this);
}

/// API response for machine forecast endpoint
@JsonSerializable()
class MachineForecastResponse {
  const MachineForecastResponse({
    required this.machineId,
    required this.forecast,
    required this.success,
  });

  final String machineId;
  final DetailedForecastModel forecast;
  final bool success;

  factory MachineForecastResponse.fromJson(Map<String, dynamic> json) =>
      _$MachineForecastResponseFromJson(json);

  Map<String, dynamic> toJson() => _$MachineForecastResponseToJson(this);
}

/// API model for detailed forecast data
@JsonSerializable()
class DetailedForecastModel {
  const DetailedForecastModel({
    required this.likelyFreeIn30m,
    required this.classification,
    required this.displayText,
    required this.confidence,
    required this.probability,
    this.peakHours,
  });

  final bool likelyFreeIn30m;
  final String classification;
  @JsonKey(name: 'display_text')
  final String displayText;
  final String confidence;
  final double probability;
  @JsonKey(name: 'peak_hours')
  final String? peakHours;

  factory DetailedForecastModel.fromJson(Map<String, dynamic> json) =>
      _$DetailedForecastModelFromJson(json);

  Map<String, dynamic> toJson() => _$DetailedForecastModelToJson(this);
}