import 'package:json_annotation/json_annotation.dart';

part 'chat_response.g.dart';

/// API request model for chat messages
@JsonSerializable()
class ChatRequest {
  const ChatRequest({
    required this.message,
    this.userLocation,
    this.sessionId,
  });

  final String message;
  final UserLocationModel? userLocation;
  final String? sessionId;

  factory ChatRequest.fromJson(Map<String, dynamic> json) =>
      _$ChatRequestFromJson(json);

  Map<String, dynamic> toJson() => _$ChatRequestToJson(this);
}

/// API response model for chat messages
@JsonSerializable(ignoreUnannotated: false)
class ChatResponse {
  const ChatResponse({
    required this.response,
    this.recommendations,
    this.toolsUsed,
    required this.sessionId,
    this.fallback,
    this.geminiPowered,
    this.timestamp,
  });

  final String response;
  final List<BranchRecommendationModel>? recommendations;
  final List<String>? toolsUsed;
  final String sessionId;
  final bool? fallback;
  @JsonKey(name: 'gemini_powered')
  final bool? geminiPowered;
  final String? timestamp;

  factory ChatResponse.fromJson(Map<String, dynamic> json) =>
      _$ChatResponseFromJson(json);

  Map<String, dynamic> toJson() => _$ChatResponseToJson(this);
}

/// API model for user location
@JsonSerializable()
class UserLocationModel {
  const UserLocationModel({
    required this.lat,
    required this.lon,
  });

  final double lat;
  final double lon;

  factory UserLocationModel.fromJson(Map<String, dynamic> json) =>
      _$UserLocationModelFromJson(json);

  Map<String, dynamic> toJson() => _$UserLocationModelToJson(this);
}

/// API model for branch recommendations
@JsonSerializable()
class BranchRecommendationModel {
  const BranchRecommendationModel({
    required this.branchId,
    required this.name,
    required this.eta,
    required this.distance,
    required this.availableCount,
    required this.totalCount,
    required this.category,
  });

  final String branchId;
  final String name;
  final String eta;
  final String distance;
  final int availableCount;
  final int totalCount;
  final String category;

  factory BranchRecommendationModel.fromJson(Map<String, dynamic> json) =>
      _$BranchRecommendationModelFromJson(json);

  Map<String, dynamic> toJson() => _$BranchRecommendationModelToJson(this);
}

/// API request model for availability tool
@JsonSerializable()
class AvailabilityToolRequest {
  const AvailabilityToolRequest({
    required this.lat,
    required this.lon,
    required this.category,
    this.radius,
  });

  final double lat;
  final double lon;
  final String category;
  final double? radius;

  factory AvailabilityToolRequest.fromJson(Map<String, dynamic> json) =>
      _$AvailabilityToolRequestFromJson(json);

  Map<String, dynamic> toJson() => _$AvailabilityToolRequestToJson(this);
}

/// API response model for availability tool
@JsonSerializable()
class AvailabilityToolResponse {
  const AvailabilityToolResponse({
    required this.branches,
  });

  final List<BranchAvailabilityModel> branches;

  factory AvailabilityToolResponse.fromJson(Map<String, dynamic> json) =>
      _$AvailabilityToolResponseFromJson(json);

  Map<String, dynamic> toJson() => _$AvailabilityToolResponseToJson(this);
}

/// API model for branch availability in tools
@JsonSerializable()
class BranchAvailabilityModel {
  const BranchAvailabilityModel({
    required this.branchId,
    required this.name,
    required this.coordinates,
    required this.distance,
    required this.freeCount,
    required this.totalCount,
  });

  final String branchId;
  final String name;
  final List<double> coordinates;
  final double distance;
  final int freeCount;
  final int totalCount;

  factory BranchAvailabilityModel.fromJson(Map<String, dynamic> json) =>
      _$BranchAvailabilityModelFromJson(json);

  Map<String, dynamic> toJson() => _$BranchAvailabilityModelToJson(this);
}

/// API request model for route matrix tool
@JsonSerializable()
class RouteMatrixRequest {
  const RouteMatrixRequest({
    required this.userCoordinate,
    required this.branchCoordinates,
  });

  final UserCoordinateModel userCoordinate;
  final List<BranchCoordinateModel> branchCoordinates;

  factory RouteMatrixRequest.fromJson(Map<String, dynamic> json) =>
      _$RouteMatrixRequestFromJson(json);

  Map<String, dynamic> toJson() => _$RouteMatrixRequestToJson(this);
}

/// API response model for route matrix tool
@JsonSerializable()
class RouteMatrixResponse {
  const RouteMatrixResponse({
    required this.routes,
  });

  final List<RouteModel> routes;

  factory RouteMatrixResponse.fromJson(Map<String, dynamic> json) =>
      _$RouteMatrixResponseFromJson(json);

  Map<String, dynamic> toJson() => _$RouteMatrixResponseToJson(this);
}

/// API model for user coordinate
@JsonSerializable()
class UserCoordinateModel {
  const UserCoordinateModel({
    required this.lat,
    required this.lon,
  });

  final double lat;
  final double lon;

  factory UserCoordinateModel.fromJson(Map<String, dynamic> json) =>
      _$UserCoordinateModelFromJson(json);

  Map<String, dynamic> toJson() => _$UserCoordinateModelToJson(this);
}

/// API model for branch coordinate with ID
@JsonSerializable()
class BranchCoordinateModel {
  const BranchCoordinateModel({
    required this.branchId,
    required this.lat,
    required this.lon,
  });

  final String branchId;
  final double lat;
  final double lon;

  factory BranchCoordinateModel.fromJson(Map<String, dynamic> json) =>
      _$BranchCoordinateModelFromJson(json);

  Map<String, dynamic> toJson() => _$BranchCoordinateModelToJson(this);
}

/// API model for route information
@JsonSerializable()
class RouteModel {
  const RouteModel({
    required this.branchId,
    required this.durationSeconds,
    required this.distanceKm,
    required this.eta,
  });

  final String branchId;
  final int durationSeconds;
  final double distanceKm;
  final String eta;

  factory RouteModel.fromJson(Map<String, dynamic> json) =>
      _$RouteModelFromJson(json);

  Map<String, dynamic> toJson() => _$RouteModelToJson(this);
}

/// API response model for health check
@JsonSerializable()
class HealthResponse {
  const HealthResponse({
    required this.status,
    required this.service,
    required this.timestamp,
    required this.version,
  });

  final String status;
  final String service;
  final int timestamp;
  final String version;

  factory HealthResponse.fromJson(Map<String, dynamic> json) =>
      _$HealthResponseFromJson(json);

  Map<String, dynamic> toJson() => _$HealthResponseToJson(this);
}