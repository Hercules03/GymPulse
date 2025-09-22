import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

import '../../../core/constants/app_constants.dart';
import '../../../domain/entities/branch.dart';

class BranchCard extends StatelessWidget {
  final Branch branch;
  final Position? currentPosition;
  final VoidCallback? onTap;

  const BranchCard({
    super.key,
    required this.branch,
    this.currentPosition,
    this.onTap,
  });

  double? _calculateDistance() {
    if (currentPosition == null) return null;

    return Geolocator.distanceBetween(
      currentPosition!.latitude,
      currentPosition!.longitude,
      branch.coordinates.latitude,
      branch.coordinates.longitude,
    ) / 1000; // Convert to kilometers
  }

  String _formatDistance(double distance) {
    if (distance < 1) {
      return '${(distance * 1000).round()}m';
    } else {
      return '${distance.toStringAsFixed(1)}km';
    }
  }

  @override
  Widget build(BuildContext context) {
    final distance = _calculateDistance();

    return Card(
      margin: const EdgeInsets.only(bottom: AppConstants.defaultPadding),
      elevation: AppConstants.cardElevation,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppConstants.borderRadius),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppConstants.borderRadius),
        child: Padding(
          padding: const EdgeInsets.all(AppConstants.defaultPadding),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          branch.name,
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        if (branch.address != null) ...[
                          const SizedBox(height: 4),
                          Row(
                            children: [
                              Icon(
                                Icons.location_on,
                                size: 16,
                                color: Colors.grey[600],
                              ),
                              const SizedBox(width: 4),
                              Expanded(
                                child: Text(
                                  branch.address!,
                                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: Colors.grey[600],
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                        if (distance != null) ...[
                          const SizedBox(height: 4),
                          Row(
                            children: [
                              Icon(
                                Icons.directions_walk,
                                size: 16,
                                color: Colors.grey[600],
                              ),
                              const SizedBox(width: 4),
                              Text(
                                _formatDistance(distance),
                                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: Colors.grey[600],
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: branch.availabilityPercentage > 30
                              ? Colors.green[100]
                              : branch.availabilityPercentage > 10
                                  ? Colors.orange[100]
                                  : Colors.red[100],
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          '${branch.availabilityPercentage.round()}%',
                          style: TextStyle(
                            color: branch.availabilityPercentage > 30
                                ? Colors.green[800]
                                : branch.availabilityPercentage > 10
                                    ? Colors.orange[800]
                                    : Colors.red[800],
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Available',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: AppConstants.defaultPadding),
              Row(
                children: [
                  _buildStatChip(
                    context,
                    icon: Icons.fitness_center,
                    label: 'Total',
                    value: '${branch.totalMachines}',
                    color: Colors.blue,
                  ),
                  const SizedBox(width: 8),
                  _buildStatChip(
                    context,
                    icon: Icons.check_circle,
                    label: 'Available',
                    value: '${branch.availableMachines}',
                    color: Colors.green,
                  ),
                  const SizedBox(width: 8),
                  _buildStatChip(
                    context,
                    icon: Icons.access_time,
                    label: 'Busy',
                    value: '${branch.totalMachines - branch.availableMachines}',
                    color: Colors.orange,
                  ),
                ],
              ),
              if (branch.hours != null) ...[
                const SizedBox(height: 12),
                Row(
                  children: [
                    Icon(
                      Icons.schedule,
                      size: 16,
                      color: Colors.grey[600],
                    ),
                    const SizedBox(width: 4),
                    Text(
                      branch.hours!,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ],
              if (branch.amenities.isNotEmpty) ...[
                const SizedBox(height: 8),
                Wrap(
                  spacing: 4,
                  runSpacing: 4,
                  children: branch.amenities.take(3).map((amenity) {
                    return Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.grey[200],
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        amenity,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[700],
                          fontSize: 10,
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatChip(
    BuildContext context, {
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: 8,
          vertical: 6,
        ),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: color.withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 16,
              color: color,
            ),
            const SizedBox(height: 2),
            Text(
              value,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            Text(
              label,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                fontSize: 10,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
