// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'branch_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

BranchesResponse _$BranchesResponseFromJson(Map<String, dynamic> json) =>
    BranchesResponse(
      branches: (json['branches'] as List<dynamic>)
          .map((e) => BranchModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      warnings: json['warnings'] as String?,
    );

Map<String, dynamic> _$BranchesResponseToJson(BranchesResponse instance) =>
    <String, dynamic>{
      'branches': instance.branches,
      'warnings': instance.warnings,
    };

BranchModel _$BranchModelFromJson(Map<String, dynamic> json) => BranchModel(
      id: json['id'] as String,
      name: json['name'] as String,
      coordinates: CoordinatesModel.fromJson(
          json['coordinates'] as Map<String, dynamic>),
      categories: (json['categories'] as Map<String, dynamic>).map(
        (k, e) =>
            MapEntry(k, CategoryDataModel.fromJson(e as Map<String, dynamic>)),
      ),
      address: json['address'] as String?,
      phone: json['phone'] as String?,
      hours: json['hours'] as String?,
      amenities: (json['amenities'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
    );

Map<String, dynamic> _$BranchModelToJson(BranchModel instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'coordinates': instance.coordinates,
      'categories': instance.categories,
      'address': instance.address,
      'phone': instance.phone,
      'hours': instance.hours,
      'amenities': instance.amenities,
    };

CoordinatesModel _$CoordinatesModelFromJson(Map<String, dynamic> json) =>
    CoordinatesModel(
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
    );

Map<String, dynamic> _$CoordinatesModelToJson(CoordinatesModel instance) =>
    <String, dynamic>{
      'lat': instance.lat,
      'lon': instance.lon,
    };

CategoryDataModel _$CategoryDataModelFromJson(Map<String, dynamic> json) =>
    CategoryDataModel(
      free: (json['free'] as num).toInt(),
      total: (json['total'] as num).toInt(),
    );

Map<String, dynamic> _$CategoryDataModelToJson(CategoryDataModel instance) =>
    <String, dynamic>{
      'free': instance.free,
      'total': instance.total,
    };

PeakHoursResponse _$PeakHoursResponseFromJson(Map<String, dynamic> json) =>
    PeakHoursResponse(
      branchId: json['branchId'] as String,
      currentHour: (json['currentHour'] as num).toInt(),
      currentOccupancy: (json['currentOccupancy'] as num).toInt(),
      peakHours: json['peakHours'] as String,
      confidence: json['confidence'] as String,
      occupancyForecast:
          (json['occupancyForecast'] as Map<String, dynamic>).map(
        (k, e) => MapEntry(k, (e as num).toDouble()),
      ),
      nextPeakIn: (json['nextPeakIn'] as num).toInt(),
      totalMachines: (json['totalMachines'] as num).toInt(),
      generatedAt: json['generatedAt'] as String,
    );

Map<String, dynamic> _$PeakHoursResponseToJson(PeakHoursResponse instance) =>
    <String, dynamic>{
      'branchId': instance.branchId,
      'currentHour': instance.currentHour,
      'currentOccupancy': instance.currentOccupancy,
      'peakHours': instance.peakHours,
      'confidence': instance.confidence,
      'occupancyForecast': instance.occupancyForecast,
      'nextPeakIn': instance.nextPeakIn,
      'totalMachines': instance.totalMachines,
      'generatedAt': instance.generatedAt,
    };
