import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

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

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFF3F4F6)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.02),
            blurRadius: 1,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(8),
          hoverColor: const Color(0xFFF9FAFB),
          child: Padding(
            padding: const EdgeInsets.all(24),
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
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w600,
                            color: Color(0xFF111827),
                            height: 1.2,
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
                          color: branch.availabilityPercentage >= 70
                              ? const Color(0xFFECFDF5)
                              : branch.availabilityPercentage >= 40
                                  ? const Color(0xFFFFF7ED)
                                  : const Color(0xFFFEF2F2),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          branch.availabilityPercentage >= 70
                              ? 'High Availability'
                              : branch.availabilityPercentage >= 40
                                  ? 'Medium Availability'
                                  : 'Low Availability',
                          style: TextStyle(
                            color: branch.availabilityPercentage >= 70
                                ? const Color(0xFF059669)
                                : branch.availabilityPercentage >= 40
                                    ? const Color(0xFFD97706)
                                    : const Color(0xFFDC2626),
                            fontWeight: FontWeight.w600,
                            fontSize: 11,
                          ),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        distance != null
                            ? '${_formatDistance(distance)} • ${(distance * 12).round()} min'
                            : 'Distance unknown',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[600],
                          fontSize: 10,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: Row(
                      children: [
                        Icon(
                          Icons.people,
                          size: 16,
                          color: Colors.grey[400],
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${branch.availableMachines}/${branch.totalMachines} available',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                  SizedBox(
                    width: 80,
                    child: LinearProgressIndicator(
                      value: branch.availabilityPercentage / 100,
                      backgroundColor: Colors.grey[200],
                      valueColor: const AlwaysStoppedAnimation<Color>(
                        Color(0xFF3B82F6),
                      ),
                      minHeight: 6,
                    ),
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
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.only(top: 16),
                  decoration: BoxDecoration(
                    border: Border(
                      top: BorderSide(color: Colors.grey[100]!),
                    ),
                  ),
                  child: Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: [
                      ...branch.amenities.take(3).map((amenity) {
                        return Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.grey[100],
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            amenity,
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Colors.grey[600],
                              fontSize: 11,
                            ),
                          ),
                        );
                      }).toList(),
                      if (branch.amenities.length > 3)
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.grey[100],
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            '+${branch.amenities.length - 3} more',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Colors.grey[600],
                              fontSize: 11,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
        ),
      ),
    );
  }
}
