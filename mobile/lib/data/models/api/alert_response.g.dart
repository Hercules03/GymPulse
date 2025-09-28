// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'alert_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CreateAlertRequest _$CreateAlertRequestFromJson(Map<String, dynamic> json) =>
    CreateAlertRequest(
      machineId: json['machineId'] as String,
      userId: json['userId'] as String?,
      quietHours: json['quietHours'] == null
          ? null
          : QuietHoursModel.fromJson(
              json['quietHours'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$CreateAlertRequestToJson(CreateAlertRequest instance) =>
    <String, dynamic>{
      'machineId': instance.machineId,
      'userId': instance.userId,
      'quietHours': instance.quietHours,
    };

UpdateAlertRequest _$UpdateAlertRequestFromJson(Map<String, dynamic> json) =>
    UpdateAlertRequest(
      quietHours:
          QuietHoursModel.fromJson(json['quietHours'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$UpdateAlertRequestToJson(UpdateAlertRequest instance) =>
    <String, dynamic>{
      'quietHours': instance.quietHours,
    };

AlertResponse _$AlertResponseFromJson(Map<String, dynamic> json) =>
    AlertResponse(
      alertId: json['alertId'] as String,
      message: json['message'] as String,
      machineId: json['machineId'] as String,
      userId: json['userId'] as String,
      quietHours:
          QuietHoursModel.fromJson(json['quietHours'] as Map<String, dynamic>),
      expiresAt: (json['expiresAt'] as num).toInt(),
      estimatedNotification: json['estimatedNotification'] as String,
    );

Map<String, dynamic> _$AlertResponseToJson(AlertResponse instance) =>
    <String, dynamic>{
      'alertId': instance.alertId,
      'message': instance.message,
      'machineId': instance.machineId,
      'userId': instance.userId,
      'quietHours': instance.quietHours,
      'expiresAt': instance.expiresAt,
      'estimatedNotification': instance.estimatedNotification,
    };

AlertsListResponse _$AlertsListResponseFromJson(Map<String, dynamic> json) =>
    AlertsListResponse(
      userId: json['userId'] as String,
      alerts: (json['alerts'] as List<dynamic>)
          .map((e) => AlertModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      count: (json['count'] as num).toInt(),
    );

Map<String, dynamic> _$AlertsListResponseToJson(AlertsListResponse instance) =>
    <String, dynamic>{
      'userId': instance.userId,
      'alerts': instance.alerts,
      'count': instance.count,
    };

AlertModel _$AlertModelFromJson(Map<String, dynamic> json) => AlertModel(
      alertId: json['alertId'] as String,
      machineId: json['machineId'] as String,
      gymId: json['gymId'] as String,
      category: json['category'] as String,
      createdAt: (json['createdAt'] as num).toInt(),
      expiresAt: (json['expiresAt'] as num).toInt(),
      quietHours:
          QuietHoursModel.fromJson(json['quietHours'] as Map<String, dynamic>),
      machineName: json['machineName'] as String,
    );

Map<String, dynamic> _$AlertModelToJson(AlertModel instance) =>
    <String, dynamic>{
      'alertId': instance.alertId,
      'machineId': instance.machineId,
      'gymId': instance.gymId,
      'category': instance.category,
      'createdAt': instance.createdAt,
      'expiresAt': instance.expiresAt,
      'quietHours': instance.quietHours,
      'machineName': instance.machineName,
    };

QuietHoursModel _$QuietHoursModelFromJson(Map<String, dynamic> json) =>
    QuietHoursModel(
      start: (json['start'] as num).toInt(),
      end: (json['end'] as num).toInt(),
    );

Map<String, dynamic> _$QuietHoursModelToJson(QuietHoursModel instance) =>
    <String, dynamic>{
      'start': instance.start,
      'end': instance.end,
    };
