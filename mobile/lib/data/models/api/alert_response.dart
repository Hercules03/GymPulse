import 'package:json_annotation/json_annotation.dart';

part 'alert_response.g.dart';

/// API request model for creating alerts
@JsonSerializable()
class CreateAlertRequest {
  const CreateAlertRequest({
    required this.machineId,
    this.userId,
    this.quietHours,
  });

  final String machineId;
  final String? userId;
  final QuietHoursModel? quietHours;

  factory CreateAlertRequest.fromJson(Map<String, dynamic> json) =>
      _$CreateAlertRequestFromJson(json);

  Map<String, dynamic> toJson() => _$CreateAlertRequestToJson(this);
}

/// API request model for updating alerts
@JsonSerializable()
class UpdateAlertRequest {
  const UpdateAlertRequest({
    required this.quietHours,
  });

  final QuietHoursModel quietHours;

  factory UpdateAlertRequest.fromJson(Map<String, dynamic> json) =>
      _$UpdateAlertRequestFromJson(json);

  Map<String, dynamic> toJson() => _$UpdateAlertRequestToJson(this);
}

/// API response model for alert creation/update
@JsonSerializable()
class AlertResponse {
  const AlertResponse({
    required this.alertId,
    required this.message,
    required this.machineId,
    required this.userId,
    required this.quietHours,
    required this.expiresAt,
    required this.estimatedNotification,
  });

  final String alertId;
  final String message;
  final String machineId;
  final String userId;
  final QuietHoursModel quietHours;
  final int expiresAt;
  final String estimatedNotification;

  factory AlertResponse.fromJson(Map<String, dynamic> json) =>
      _$AlertResponseFromJson(json);

  Map<String, dynamic> toJson() => _$AlertResponseToJson(this);
}

/// API response model for listing alerts
@JsonSerializable()
class AlertsListResponse {
  const AlertsListResponse({
    required this.userId,
    required this.alerts,
    required this.count,
  });

  final String userId;
  final List<AlertModel> alerts;
  final int count;

  factory AlertsListResponse.fromJson(Map<String, dynamic> json) =>
      _$AlertsListResponseFromJson(json);

  Map<String, dynamic> toJson() => _$AlertsListResponseToJson(this);
}

/// API model for individual alert
@JsonSerializable()
class AlertModel {
  const AlertModel({
    required this.alertId,
    required this.machineId,
    required this.gymId,
    required this.category,
    required this.createdAt,
    required this.expiresAt,
    required this.quietHours,
    required this.machineName,
  });

  final String alertId;
  final String machineId;
  final String gymId;
  final String category;
  final int createdAt;
  final int expiresAt;
  final QuietHoursModel quietHours;
  final String machineName;

  factory AlertModel.fromJson(Map<String, dynamic> json) =>
      _$AlertModelFromJson(json);

  Map<String, dynamic> toJson() => _$AlertModelToJson(this);
}

/// API model for quiet hours configuration
@JsonSerializable()
class QuietHoursModel {
  const QuietHoursModel({
    required this.start,
    required this.end,
  });

  final int start;
  final int end;

  factory QuietHoursModel.fromJson(Map<String, dynamic> json) =>
      _$QuietHoursModelFromJson(json);

  Map<String, dynamic> toJson() => _$QuietHoursModelToJson(this);
}