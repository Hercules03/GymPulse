import 'package:json_annotation/json_annotation.dart';

part 'branch_response.g.dart';

/// API response model for branches endpoint
@JsonSerializable()
class BranchesResponse {
  const BranchesResponse({
    required this.branches,
    this.warnings,
  });

  final List<BranchModel> branches;
  final String? warnings;

  factory BranchesResponse.fromJson(Map<String, dynamic> json) =>
      _$BranchesResponseFromJson(json);

  Map<String, dynamic> toJson() => _$BranchesResponseToJson(this);
}

/// API model for individual branch data
@JsonSerializable()
class BranchModel {
  const BranchModel({
    required this.id,
    required this.name,
    required this.coordinates,
    required this.categories,
    this.address,
    this.phone,
    this.hours,
    this.amenities = const [],
  });

  final String id;
  final String name;
  final CoordinatesModel coordinates;
  final Map<String, CategoryDataModel> categories;
  final String? address;
  final String? phone;
  final String? hours;
  final List<String> amenities;

  factory BranchModel.fromJson(Map<String, dynamic> json) =>
      _$BranchModelFromJson(json);

  Map<String, dynamic> toJson() => _$BranchModelToJson(this);
}

/// API model for geographic coordinates
@JsonSerializable()
class CoordinatesModel {
  const CoordinatesModel({
    required this.lat,
    required this.lon,
  });

  final double lat;
  final double lon;

  factory CoordinatesModel.fromJson(Map<String, dynamic> json) =>
      _$CoordinatesModelFromJson(json);

  Map<String, dynamic> toJson() => _$CoordinatesModelToJson(this);
}

/// API model for category data with machine counts
@JsonSerializable()
class CategoryDataModel {
  const CategoryDataModel({
    required this.free,
    required this.total,
  });

  final int free;
  final int total;

  factory CategoryDataModel.fromJson(Map<String, dynamic> json) =>
      _$CategoryDataModelFromJson(json);

  Map<String, dynamic> toJson() => _$CategoryDataModelToJson(this);
}

/// API response for peak hours data
@JsonSerializable()
class PeakHoursResponse {
  const PeakHoursResponse({
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

  factory PeakHoursResponse.fromJson(Map<String, dynamic> json) =>
      _$PeakHoursResponseFromJson(json);

  Map<String, dynamic> toJson() => _$PeakHoursResponseToJson(this);
}