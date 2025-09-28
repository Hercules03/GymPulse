import 'package:equatable/equatable.dart';

class EquipmentCategory extends Equatable {
  final String id;
  final String name;
  final String displayName;
  final String iconPath;
  final String color;
  final int machineCount;
  final int availableCount;
  final int occupiedCount;
  final int offlineCount;

  const EquipmentCategory({
    required this.id,
    required this.name,
    required this.displayName,
    required this.iconPath,
    required this.color,
    required this.machineCount,
    required this.availableCount,
    required this.occupiedCount,
    required this.offlineCount,
  });

  @override
  List<Object> get props => [
        id,
        name,
        displayName,
        iconPath,
        color,
        machineCount,
        availableCount,
        occupiedCount,
        offlineCount,
      ];

  double get availabilityPercentage {
    if (machineCount == 0) return 0.0;
    return (availableCount / machineCount) * 100;
  }

  double get occupancyPercentage {
    if (machineCount == 0) return 0.0;
    return (occupiedCount / machineCount) * 100;
  }

  EquipmentCategory copyWith({
    String? id,
    String? name,
    String? displayName,
    String? iconPath,
    String? color,
    int? machineCount,
    int? availableCount,
    int? occupiedCount,
    int? offlineCount,
  }) {
    return EquipmentCategory(
      id: id ?? this.id,
      name: name ?? this.name,
      displayName: displayName ?? this.displayName,
      iconPath: iconPath ?? this.iconPath,
      color: color ?? this.color,
      machineCount: machineCount ?? this.machineCount,
      availableCount: availableCount ?? this.availableCount,
      occupiedCount: occupiedCount ?? this.occupiedCount,
      offlineCount: offlineCount ?? this.offlineCount,
    );
  }

  @override
  String toString() {
    return 'EquipmentCategory(id: $id, name: $name, machineCount: $machineCount)';
  }
}
