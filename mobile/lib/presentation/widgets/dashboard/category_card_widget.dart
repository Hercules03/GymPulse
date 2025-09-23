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
      elevation: 1,
      shadowColor: Colors.black.withOpacity(0.08),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey.withOpacity(0.1)),
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
                  const Spacer(),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        '$availableCount',
                        style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: Colors.grey[900],
                        ),
                      ),
                      Text(
                        'of $totalMachines',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[500],
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 24),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _getCategoryDisplayName(category),
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w600,
                      color: Colors.grey[900],
                    ),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    width: double.infinity,
                    height: 6,
                    decoration: BoxDecoration(
                      color: Colors.grey[200],
                      borderRadius: BorderRadius.circular(3),
                    ),
                    child: FractionallySizedBox(
                      alignment: Alignment.centerLeft,
                      widthFactor: availabilityPercentage / 100,
                      child: Container(
                        decoration: BoxDecoration(
                          color: const Color(0xFF10B981),
                          borderRadius: BorderRadius.circular(3),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '$availableCount available',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[500],
                          fontSize: 11,
                        ),
                      ),
                      Text(
                        '$occupiedCount in use',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[500],
                          fontSize: 11,
                        ),
                      ),
                      if (offlineCount > 0)
                        Text(
                          '$offlineCount offline',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.grey[500],
                            fontSize: 11,
                          ),
                        ),
                    ],
                  ),
                ],
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
    Color backgroundColor = _getCategoryBackgroundColor(category);

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
      width: 48,
      height: 48,
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Icon(
        iconData,
        color: color,
        size: 24,
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
        return const Color(0xFF2563EB);
      case 'chest':
        return const Color(0xFFDC2626);
      case 'back':
        return const Color(0xFF059669);
      case 'cardio':
        return const Color(0xFF7C3AED);
      case 'arms':
        return const Color(0xFFEA580C);
      default:
        return const Color(0xFF6B7280);
    }
  }

  Color _getCategoryBackgroundColor(String category) {
    switch (category.toLowerCase()) {
      case 'legs':
        return const Color(0xFFDBEAFE);
      case 'chest':
        return const Color(0xFFFEF2F2);
      case 'back':
        return const Color(0xFFECFDF5);
      case 'cardio':
        return const Color(0xFFF3E8FF);
      case 'arms':
        return const Color(0xFFFFF7ED);
      default:
        return const Color(0xFFF9FAFB);
    }
  }
}

