import 'package:flutter/material.dart';
import '../../../domain/entities/machine.dart';

class CategoryCardWidget extends StatelessWidget {
  final String category;
  final int totalMachines;
  final int availableCount;
  final int occupiedCount;
  final int offlineCount;
  final List<Machine> machines;
  final VoidCallback? onTap;

  const CategoryCardWidget({
    super.key,
    required this.category,
    required this.totalMachines,
    required this.availableCount,
    required this.occupiedCount,
    required this.offlineCount,
    required this.machines,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final availabilityPercentage = totalMachines > 0 
        ? (availableCount / totalMachines) * 100 
        : 0.0;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  _getCategoryIcon(category),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _getCategoryDisplayName(category),
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '$totalMachines machines',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                  _AvailabilityIndicator(
                    percentage: availabilityPercentage,
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  _StatusChip(
                    label: 'Available',
                    count: availableCount,
                    color: Colors.green,
                  ),
                  const SizedBox(width: 8),
                  _StatusChip(
                    label: 'Occupied',
                    count: occupiedCount,
                    color: Colors.red,
                  ),
                  const SizedBox(width: 8),
                  _StatusChip(
                    label: 'Offline',
                    count: offlineCount,
                    color: Colors.grey,
                  ),
                ],
              ),
              const SizedBox(height: 12),
              LinearProgressIndicator(
                value: availabilityPercentage / 100,
                backgroundColor: Colors.grey[300],
                valueColor: AlwaysStoppedAnimation<Color>(
                  _getCategoryColor(category),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _getCategoryIcon(String category) {
    IconData iconData;
    Color color = _getCategoryColor(category);

    switch (category.toLowerCase()) {
      case 'legs':
        iconData = Icons.directions_run;
        break;
      case 'chest':
        iconData = Icons.fitness_center;
        break;
      case 'back':
        iconData = Icons.accessibility_new;
        break;
      case 'cardio':
        iconData = Icons.directions_bike;
        break;
      case 'arms':
        iconData = Icons.sports_handball;
        break;
      default:
        iconData = Icons.fitness_center;
    }

    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(
        iconData,
        color: color,
        size: 20,
      ),
    );
  }

  String _getCategoryDisplayName(String category) {
    switch (category.toLowerCase()) {
      case 'legs':
        return 'Legs';
      case 'chest':
        return 'Chest';
      case 'back':
        return 'Back';
      case 'cardio':
        return 'Cardio';
      case 'arms':
        return 'Arms';
      default:
        return category.toUpperCase();
    }
  }

  Color _getCategoryColor(String category) {
    switch (category.toLowerCase()) {
      case 'legs':
        return Colors.blue;
      case 'chest':
        return Colors.red;
      case 'back':
        return Colors.green;
      case 'cardio':
        return Colors.purple;
      case 'arms':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }
}

class _AvailabilityIndicator extends StatelessWidget {
  final double percentage;

  const _AvailabilityIndicator({required this.percentage});

  @override
  Widget build(BuildContext context) {
    Color color;
    String status;

    if (percentage >= 70) {
      color = Colors.green;
      status = 'High';
    } else if (percentage >= 30) {
      color = Colors.orange;
      status = 'Moderate';
    } else {
      color = Colors.red;
      status = 'Low';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 4),
          Text(
            '$status (${percentage.toStringAsFixed(0)}%)',
            style: TextStyle(
              color: color,
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String label;
  final int count;
  final Color color;

  const _StatusChip({
    required this.label,
    required this.count,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        '$label: $count',
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}
