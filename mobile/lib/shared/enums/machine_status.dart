/// Enum representing the status of a gym machine
enum MachineStatus {
  /// Machine is available for use
  available('available'),

  /// Machine is currently being used
  occupied('occupied'),

  /// Machine is offline or out of service
  offline('offline'),

  /// Machine status is unknown
  unknown('unknown');

  const MachineStatus(this.value);

  /// String value used in API communications
  final String value;

  /// Create MachineStatus from string value
  static MachineStatus fromString(String value) {
    switch (value.toLowerCase()) {
      case 'available':
      case 'free':
        return MachineStatus.available;
      case 'occupied':
        return MachineStatus.occupied;
      case 'offline':
        return MachineStatus.offline;
      default:
        return MachineStatus.unknown;
    }
  }

  /// Get display text for UI
  String get displayText {
    switch (this) {
      case MachineStatus.available:
        return 'Available';
      case MachineStatus.occupied:
        return 'Occupied';
      case MachineStatus.offline:
        return 'Offline';
      case MachineStatus.unknown:
        return 'Unknown';
    }
  }

  /// Get display name for UI (alias for displayText)
  String get displayName => displayText;

  /// Check if machine is usable
  bool get isUsable => this == MachineStatus.available;

  /// Check if machine needs attention
  bool get needsAttention => this == MachineStatus.offline;
}