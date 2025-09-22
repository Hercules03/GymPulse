// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'chat_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ChatRequest _$ChatRequestFromJson(Map<String, dynamic> json) => ChatRequest(
      message: json['message'] as String,
      userLocation: json['userLocation'] == null
          ? null
          : UserLocationModel.fromJson(
              json['userLocation'] as Map<String, dynamic>),
      sessionId: json['sessionId'] as String?,
    );

Map<String, dynamic> _$ChatRequestToJson(ChatRequest instance) =>
    <String, dynamic>{
      'message': instance.message,
      'userLocation': instance.userLocation,
      'sessionId': instance.sessionId,
    };

ChatResponse _$ChatResponseFromJson(Map<String, dynamic> json) => ChatResponse(
      response: json['response'] as String,
      recommendations: (json['recommendations'] as List<dynamic>?)
          ?.map((e) =>
              BranchRecommendationModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      toolsUsed: (json['toolsUsed'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
      sessionId: json['sessionId'] as String,
      fallback: json['fallback'] as bool?,
    );

Map<String, dynamic> _$ChatResponseToJson(ChatResponse instance) =>
    <String, dynamic>{
      'response': instance.response,
      'recommendations': instance.recommendations,
      'toolsUsed': instance.toolsUsed,
      'sessionId': instance.sessionId,
      'fallback': instance.fallback,
    };

UserLocationModel _$UserLocationModelFromJson(Map<String, dynamic> json) =>
    UserLocationModel(
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
    );

Map<String, dynamic> _$UserLocationModelToJson(UserLocationModel instance) =>
    <String, dynamic>{
      'lat': instance.lat,
      'lon': instance.lon,
    };

BranchRecommendationModel _$BranchRecommendationModelFromJson(
        Map<String, dynamic> json) =>
    BranchRecommendationModel(
      branchId: json['branchId'] as String,
      name: json['name'] as String,
      eta: json['eta'] as String,
      distance: json['distance'] as String,
      availableCount: (json['availableCount'] as num).toInt(),
      totalCount: (json['totalCount'] as num).toInt(),
      category: json['category'] as String,
    );

Map<String, dynamic> _$BranchRecommendationModelToJson(
        BranchRecommendationModel instance) =>
    <String, dynamic>{
      'branchId': instance.branchId,
      'name': instance.name,
      'eta': instance.eta,
      'distance': instance.distance,
      'availableCount': instance.availableCount,
      'totalCount': instance.totalCount,
      'category': instance.category,
    };

AvailabilityToolRequest _$AvailabilityToolRequestFromJson(
        Map<String, dynamic> json) =>
    AvailabilityToolRequest(
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
      category: json['category'] as String,
      radius: (json['radius'] as num?)?.toDouble(),
    );

Map<String, dynamic> _$AvailabilityToolRequestToJson(
        AvailabilityToolRequest instance) =>
    <String, dynamic>{
      'lat': instance.lat,
      'lon': instance.lon,
      'category': instance.category,
      'radius': instance.radius,
    };

AvailabilityToolResponse _$AvailabilityToolResponseFromJson(
        Map<String, dynamic> json) =>
    AvailabilityToolResponse(
      branches: (json['branches'] as List<dynamic>)
          .map((e) =>
              BranchAvailabilityModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$AvailabilityToolResponseToJson(
        AvailabilityToolResponse instance) =>
    <String, dynamic>{
      'branches': instance.branches,
    };

BranchAvailabilityModel _$BranchAvailabilityModelFromJson(
        Map<String, dynamic> json) =>
    BranchAvailabilityModel(
      branchId: json['branchId'] as String,
      name: json['name'] as String,
      coordinates: (json['coordinates'] as List<dynamic>)
          .map((e) => (e as num).toDouble())
          .toList(),
      distance: (json['distance'] as num).toDouble(),
      freeCount: (json['freeCount'] as num).toInt(),
      totalCount: (json['totalCount'] as num).toInt(),
    );

Map<String, dynamic> _$BranchAvailabilityModelToJson(
        BranchAvailabilityModel instance) =>
    <String, dynamic>{
      'branchId': instance.branchId,
      'name': instance.name,
      'coordinates': instance.coordinates,
      'distance': instance.distance,
      'freeCount': instance.freeCount,
      'totalCount': instance.totalCount,
    };

RouteMatrixRequest _$RouteMatrixRequestFromJson(Map<String, dynamic> json) =>
    RouteMatrixRequest(
      userCoordinate: UserCoordinateModel.fromJson(
          json['userCoordinate'] as Map<String, dynamic>),
      branchCoordinates: (json['branchCoordinates'] as List<dynamic>)
          .map((e) => BranchCoordinateModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$RouteMatrixRequestToJson(RouteMatrixRequest instance) =>
    <String, dynamic>{
      'userCoordinate': instance.userCoordinate,
      'branchCoordinates': instance.branchCoordinates,
    };

RouteMatrixResponse _$RouteMatrixResponseFromJson(Map<String, dynamic> json) =>
    RouteMatrixResponse(
      routes: (json['routes'] as List<dynamic>)
          .map((e) => RouteModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$RouteMatrixResponseToJson(
        RouteMatrixResponse instance) =>
    <String, dynamic>{
      'routes': instance.routes,
    };

UserCoordinateModel _$UserCoordinateModelFromJson(Map<String, dynamic> json) =>
    UserCoordinateModel(
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
    );

Map<String, dynamic> _$UserCoordinateModelToJson(
        UserCoordinateModel instance) =>
    <String, dynamic>{
      'lat': instance.lat,
      'lon': instance.lon,
    };

BranchCoordinateModel _$BranchCoordinateModelFromJson(
        Map<String, dynamic> json) =>
    BranchCoordinateModel(
      branchId: json['branchId'] as String,
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
    );

Map<String, dynamic> _$BranchCoordinateModelToJson(
        BranchCoordinateModel instance) =>
    <String, dynamic>{
      'branchId': instance.branchId,
      'lat': instance.lat,
      'lon': instance.lon,
    };

RouteModel _$RouteModelFromJson(Map<String, dynamic> json) => RouteModel(
      branchId: json['branchId'] as String,
      durationSeconds: (json['durationSeconds'] as num).toInt(),
      distanceKm: (json['distanceKm'] as num).toDouble(),
      eta: json['eta'] as String,
    );

Map<String, dynamic> _$RouteModelToJson(RouteModel instance) =>
    <String, dynamic>{
      'branchId': instance.branchId,
      'durationSeconds': instance.durationSeconds,
      'distanceKm': instance.distanceKm,
      'eta': instance.eta,
    };

HealthResponse _$HealthResponseFromJson(Map<String, dynamic> json) =>
    HealthResponse(
      status: json['status'] as String,
      service: json['service'] as String,
      timestamp: (json['timestamp'] as num).toInt(),
      version: json['version'] as String,
    );

Map<String, dynamic> _$HealthResponseToJson(HealthResponse instance) =>
    <String, dynamic>{
      'status': instance.status,
      'service': instance.service,
      'timestamp': instance.timestamp,
      'version': instance.version,
    };
