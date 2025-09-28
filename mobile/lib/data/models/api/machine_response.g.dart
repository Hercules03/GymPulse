// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'machine_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MachinesResponse _$MachinesResponseFromJson(Map<String, dynamic> json) =>
    MachinesResponse(
      machines: (json['machines'] as List<dynamic>)
          .map((e) => MachineModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      branchId: json['branchId'] as String,
      category: json['category'] as String,
      totalCount: (json['totalCount'] as num).toInt(),
      freeCount: (json['freeCount'] as num).toInt(),
      occupiedCount: (json['occupiedCount'] as num).toInt(),
    );

Map<String, dynamic> _$MachinesResponseToJson(MachinesResponse instance) =>
    <String, dynamic>{
      'machines': instance.machines,
      'branchId': instance.branchId,
      'category': instance.category,
      'totalCount': instance.totalCount,
      'freeCount': instance.freeCount,
      'occupiedCount': instance.occupiedCount,
    };

MachineModel _$MachineModelFromJson(Map<String, dynamic> json) => MachineModel(
      machineId: json['machineId'] as String,
      name: json['name'] as String,
      status: json['status'] as String,
      category: json['category'] as String,
      gymId: json['gymId'] as String,
      lastUpdate: (json['lastUpdate'] as num?)?.toInt(),
      lastChange: (json['lastChange'] as num?)?.toInt(),
      coordinates: json['coordinates'] == null
          ? null
          : MachineCoordinatesModel.fromJson(
              json['coordinates'] as Map<String, dynamic>),
      alertEligible: json['alertEligible'] as bool? ?? true,
      type: json['type'] as String?,
      estimatedFreeTime: json['estimatedFreeTime'] as String?,
    );

Map<String, dynamic> _$MachineModelToJson(MachineModel instance) =>
    <String, dynamic>{
      'machineId': instance.machineId,
      'name': instance.name,
      'status': instance.status,
      'category': instance.category,
      'gymId': instance.gymId,
      'lastUpdate': instance.lastUpdate,
      'lastChange': instance.lastChange,
      'coordinates': instance.coordinates,
      'alertEligible': instance.alertEligible,
      'type': instance.type,
      'estimatedFreeTime': instance.estimatedFreeTime,
    };

MachineCoordinatesModel _$MachineCoordinatesModelFromJson(
        Map<String, dynamic> json) =>
    MachineCoordinatesModel(
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
    );

Map<String, dynamic> _$MachineCoordinatesModelToJson(
        MachineCoordinatesModel instance) =>
    <String, dynamic>{
      'lat': instance.lat,
      'lon': instance.lon,
    };

MachineHistoryResponse _$MachineHistoryResponseFromJson(
        Map<String, dynamic> json) =>
    MachineHistoryResponse(
      machineId: json['machineId'] as String,
      history: (json['history'] as List<dynamic>)
          .map((e) => HistoryBinModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      timeRange:
          TimeRangeModel.fromJson(json['timeRange'] as Map<String, dynamic>),
      forecast:
          ForecastModel.fromJson(json['forecast'] as Map<String, dynamic>),
      totalBins: (json['totalBins'] as num).toInt(),
    );

Map<String, dynamic> _$MachineHistoryResponseToJson(
        MachineHistoryResponse instance) =>
    <String, dynamic>{
      'machineId': instance.machineId,
      'history': instance.history,
      'timeRange': instance.timeRange,
      'forecast': instance.forecast,
      'totalBins': instance.totalBins,
    };

HistoryBinModel _$HistoryBinModelFromJson(Map<String, dynamic> json) =>
    HistoryBinModel(
      timestamp: (json['timestamp'] as num).toInt(),
      occupancyRatio: (json['occupancyRatio'] as num).toDouble(),
      freeCount: (json['freeCount'] as num).toInt(),
      totalCount: (json['totalCount'] as num).toInt(),
      status: json['status'] as String,
    );

Map<String, dynamic> _$HistoryBinModelToJson(HistoryBinModel instance) =>
    <String, dynamic>{
      'timestamp': instance.timestamp,
      'occupancyRatio': instance.occupancyRatio,
      'freeCount': instance.freeCount,
      'totalCount': instance.totalCount,
      'status': instance.status,
    };

TimeRangeModel _$TimeRangeModelFromJson(Map<String, dynamic> json) =>
    TimeRangeModel(
      start: (json['start'] as num).toInt(),
      end: (json['end'] as num).toInt(),
      duration: json['duration'] as String,
    );

Map<String, dynamic> _$TimeRangeModelToJson(TimeRangeModel instance) =>
    <String, dynamic>{
      'start': instance.start,
      'end': instance.end,
      'duration': instance.duration,
    };

ForecastModel _$ForecastModelFromJson(Map<String, dynamic> json) =>
    ForecastModel(
      likelyFreeIn30m: json['likelyFreeIn30m'] as bool,
      confidence: json['confidence'] as String,
      reason: json['reason'] as String,
    );

Map<String, dynamic> _$ForecastModelToJson(ForecastModel instance) =>
    <String, dynamic>{
      'likelyFreeIn30m': instance.likelyFreeIn30m,
      'confidence': instance.confidence,
      'reason': instance.reason,
    };

MachineForecastResponse _$MachineForecastResponseFromJson(
        Map<String, dynamic> json) =>
    MachineForecastResponse(
      machineId: json['machineId'] as String,
      forecast: DetailedForecastModel.fromJson(
          json['forecast'] as Map<String, dynamic>),
      success: json['success'] as bool,
    );

Map<String, dynamic> _$MachineForecastResponseToJson(
        MachineForecastResponse instance) =>
    <String, dynamic>{
      'machineId': instance.machineId,
      'forecast': instance.forecast,
      'success': instance.success,
    };

DetailedForecastModel _$DetailedForecastModelFromJson(
        Map<String, dynamic> json) =>
    DetailedForecastModel(
      likelyFreeIn30m: json['likelyFreeIn30m'] as bool,
      classification: json['classification'] as String,
      displayText: json['display_text'] as String,
      confidence: json['confidence'] as String,
      probability: (json['probability'] as num).toDouble(),
      peakHours: json['peak_hours'] as String?,
    );

Map<String, dynamic> _$DetailedForecastModelToJson(
        DetailedForecastModel instance) =>
    <String, dynamic>{
      'likelyFreeIn30m': instance.likelyFreeIn30m,
      'classification': instance.classification,
      'display_text': instance.displayText,
      'confidence': instance.confidence,
      'probability': instance.probability,
      'peak_hours': instance.peakHours,
    };
