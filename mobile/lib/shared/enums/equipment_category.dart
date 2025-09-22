/// Enum representing equipment categories in the gym
enum EquipmentCategory {
  legs('legs', 'Legs'),
  chest('chest', 'Chest'),
  back('back', 'Back'),
  arms('arms', 'Arms'),
  cardio('cardio', 'Cardio'),
  strength('strength', 'Strength'),
  functional('functional', 'Functional'),
  stretching('stretching', 'Stretching');

  const EquipmentCategory(this.value, this.displayName);

  /// String value used in API communications
  final String value;

  /// Display name for UI
  final String displayName;

  /// Create EquipmentCategory from string value
  static EquipmentCategory fromString(String value) {
    for (final category in EquipmentCategory.values) {
      if (category.value.toLowerCase() == value.toLowerCase()) {
        return category;
      }
    }
    return EquipmentCategory.legs; // Default fallback
  }

  /// Get all category values as strings
  static List<String> get allValues => EquipmentCategory.values.map((e) => e.value).toList();

  /// Get all display names
  static List<String> get allDisplayNames => EquipmentCategory.values.map((e) => e.displayName).toList();
}