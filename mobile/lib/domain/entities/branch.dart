import 'package:equatable/equatable.dart';

/// Business entity representing a gym branch
class Branch extends Equatable {
  const Branch({
    required this.id,
    required this.name,
    required this.coordinates,
    required this.categories,
    this.address,
    this.phone,
    this.hours,
    this.amenities = const [],
  });

  /// Unique identifier for the branch
  final String id;

  /// Display name of the branch
  final String name;

  /// Geographic coordinates
  final Coordinates coordinates;

  /// Available equipment categories with counts
  final Map<String, CategoryData> categories;

  /// Optional address
  final String? address;

  /// Optional phone number
  final String? phone;

  /// Optional operating hours
  final String? hours;

  /// List of amenities available at this branch
  final List<String> amenities;

  /// Calculate total machines across all categories
  int get totalMachines {
    return categories.values.fold(0, (sum, category) => sum + category.total);
  }

  /// Calculate total available machines
  int get availableMachines {
    return categories.values.fold(0, (sum, category) => sum + category.free);
  }

  /// Calculate availability percentage
  double get availabilityPercentage {
    if (totalMachines == 0) return 0.0;
    return (availableMachines / totalMachines) * 100;
  }

  /// Get category data by name
  CategoryData? getCategoryData(String categoryName) {
    return categories[categoryName];
  }

  @override
  List<Object?> get props => [
        id,
        name,
        coordinates,
        categories,
        address,
        phone,
        hours,
        amenities,
      ];
}

/// Geographic coordinates
class Coordinates extends Equatable {
  const Coordinates({
    required this.latitude,
    required this.longitude,
  });

  final double latitude;
  final double longitude;

  @override
  List<Object> get props => [latitude, longitude];
}

/// Equipment category data with availability counts
class CategoryData extends Equatable {
  const CategoryData({
    required this.free,
    required this.total,
  });

  /// Number of available machines in this category
  final int free;

  /// Total number of machines in this category
  final int total;

  /// Number of occupied machines
  int get occupied => total - free;

  /// Availability percentage for this category
  double get availabilityPercentage {
    if (total == 0) return 0.0;
    return (free / total) * 100;
  }

  @override
  List<Object> get props => [free, total];
}