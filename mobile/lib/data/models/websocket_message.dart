class WebSocketMessage {
  final String type;
  final Map<String, dynamic> data;
  final DateTime timestamp;

  const WebSocketMessage({
    required this.type,
    required this.data,
    required this.timestamp,
  });

  factory WebSocketMessage.fromJson(Map<String, dynamic> json) {
    return WebSocketMessage(
      type: json['type'] as String,
      data: json['data'] as Map<String, dynamic>,
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'data': data,
      'timestamp': timestamp.toIso8601String(),
    };
  }
}

class MachineUpdate {
  final String machineId;
  final String status;
  final String branchId;
  final DateTime timestamp;
  final String? estimatedFreeTime;
  final Map<String, dynamic>? metadata;

  const MachineUpdate({
    required this.machineId,
    required this.status,
    required this.branchId,
    required this.timestamp,
    this.estimatedFreeTime,
    this.metadata,
  });

  factory MachineUpdate.fromJson(Map<String, dynamic> json) {
    return MachineUpdate(
      machineId: json['machineId'] as String,
      status: json['status'] as String,
      branchId: json['branchId'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
      estimatedFreeTime: json['estimatedFreeTime'] as String?,
      metadata: json['metadata'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'machineId': machineId,
      'status': status,
      'branchId': branchId,
      'timestamp': timestamp.toIso8601String(),
      'estimatedFreeTime': estimatedFreeTime,
      'metadata': metadata,
    };
  }
}

class UserAlert {
  final String alertId;
  final String userId;
  final String machineId;
  final String branchId;
  final String status;
  final DateTime timestamp;
  final Map<String, dynamic>? metadata;

  const UserAlert({
    required this.alertId,
    required this.userId,
    required this.machineId,
    required this.branchId,
    required this.status,
    required this.timestamp,
    this.metadata,
  });

  factory UserAlert.fromJson(Map<String, dynamic> json) {
    return UserAlert(
      alertId: json['alertId'] as String,
      userId: json['userId'] as String,
      machineId: json['machineId'] as String,
      branchId: json['branchId'] as String,
      status: json['status'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
      metadata: json['metadata'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'alertId': alertId,
      'userId': userId,
      'machineId': machineId,
      'branchId': branchId,
      'status': status,
      'timestamp': timestamp.toIso8601String(),
      'metadata': metadata,
    };
  }
}

class ConnectionStatus {
  final String status;
  final DateTime timestamp;
  final String? message;

  const ConnectionStatus({
    required this.status,
    required this.timestamp,
    this.message,
  });

  factory ConnectionStatus.fromJson(Map<String, dynamic> json) {
    return ConnectionStatus(
      status: json['status'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
      message: json['message'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'status': status,
      'timestamp': timestamp.toIso8601String(),
      'message': message,
    };
  }
}
