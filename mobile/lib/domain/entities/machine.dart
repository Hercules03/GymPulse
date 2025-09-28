import 'package:equatable/equatable.dart';
import '../../shared/enums/machine_status.dart';
import '../../shared/enums/equipment_category.dart';

/// Business entity representing a gym machine
class Machine extends Equatable {
  const Machine({
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

  /// Unique identifier for the machine
  final String machineId;

  /// Display name of the machine
  final String name;

  /// Current status of the machine
  final MachineStatus status;

  /// Equipment category this machine belongs to
  final EquipmentCategory category;

  /// ID of the gym/branch this machine is located in
  final String gymId;

  /// Timestamp of last status update (Unix timestamp)
  final int? lastUpdate;

  /// Timestamp of last status change (Unix timestamp)
  final int? lastChange;

  /// Geographic coordinates of the machine (optional)
  final MachineCoordinates? coordinates;

  /// Whether this machine is eligible for notifications
  final bool alertEligible;

  /// Specific type/model of the machine (optional)
  final String? type;

  /// Estimated time until machine becomes free (optional)
  final String? estimatedFreeTime;

  /// Get formatted last update time
  DateTime? get lastUpdateTime {
    if (lastUpdate == null) return null;
    return DateTime.fromMillisecondsSinceEpoch(lastUpdate! * 1000);
  }

  /// Get formatted last change time
  DateTime? get lastChangeTime {
    if (lastChange == null) return null;
    return DateTime.fromMillisecondsSinceEpoch(lastChange! * 1000);
  }

  /// Check if machine data is recent (within last 5 minutes)
  bool get isDataRecent {
    if (lastUpdate == null) return false;
    final now = DateTime.now();
    final updateTime = lastUpdateTime!;
    return now.difference(updateTime).inMinutes < 5;
  }

  /// Check if machine can be reserved/alerted
  bool get canBeReserved {
    return alertEligible && status != MachineStatus.offline;
  }

  /// Get display text for machine type
  String get displayType {
    if (type != null) {
      return type!.replaceAll('-', ' ').split(' ').map((word) {
        return word[0].toUpperCase() + word.substring(1).toLowerCase();
      }).join(' ');
    }
    return category.displayName;
  }

  /// Create a copy with updated status
  Machine copyWithStatus(MachineStatus newStatus, {int? timestamp}) {
    return Machine(
      machineId: machineId,
      name: name,
      status: newStatus,
      category: category,
      gymId: gymId,
      lastUpdate: timestamp ?? DateTime.now().millisecondsSinceEpoch ~/ 1000,
      lastChange: status != newStatus
          ? (timestamp ?? DateTime.now().millisecondsSinceEpoch ~/ 1000)
          : lastChange,
      coordinates: coordinates,
      alertEligible: alertEligible,
      type: type,
      estimatedFreeTime: estimatedFreeTime,
    );
  }

  @override
  List<Object?> get props => [
        machineId,
        name,
        status,
        category,
        gymId,
        lastUpdate,
        lastChange,
        coordinates,
        alertEligible,
        type,
        estimatedFreeTime,
      ];
}

/// Geographic coordinates for machine location
class MachineCoordinates extends Equatable {
  const MachineCoordinates({
    required this.latitude,
    required this.longitude,
  });

  final double latitude;
  final double longitude;

  @override
  List<Object> get props => [latitude, longitude];
}