import 'package:flutter/material.dart';
import '../../../domain/entities/machine.dart';

class MachineCardWidget extends StatelessWidget {
  final Machine machine;
  final VoidCallback? onTap;

  const MachineCardWidget({
    super.key,
    required this.machine,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
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
                  _getMachineIcon(machine.category),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          machine.name,
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          machine.location,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                  _StatusBadge(status: machine.status),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  if (machine.estimatedFreeTime != null) ...[
                    _InfoChip(
                      icon: Icons.access_time,
                      label: 'Free in ${machine.estimatedFreeTime}',
                      color: Colors.orange,
                    ),
                    const SizedBox(width: 8),
                  ],
                  if (machine.usageCount != null) ...[
                    _InfoChip(
                      icon: Icons.trending_up,
                      label: '${machine.usageCount} uses',
                      color: Colors.blue,
                    ),
                    const SizedBox(width: 8),
                  ],
                  if (machine.averageUsageTime != null) ...[
                    _InfoChip(
                      icon: Icons.timer,
                      label: '${machine.averageUsageTime!.toInt()}min avg',
                      color: Colors.green,
                    ),
                  ],
                ],
              ),
              if (machine.features != null && machine.features!.isNotEmpty) ...[
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  children: machine.features!.map((feature) {
                    return Chip(
                      label: Text(
                        feature,
                        style: const TextStyle(fontSize: 12),
                      ),
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      backgroundColor: Colors.grey[100],
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

  Widget _getMachineIcon(EquipmentCategory category) {
    IconData iconData;
    Color color = _getCategoryColor(category);

    switch (category) {
      case EquipmentCategory.legs:
        iconData = Icons.directions_run;
        break;
      case EquipmentCategory.chest:
        iconData = Icons.fitness_center;
        break;
      case EquipmentCategory.back:
        iconData = Icons.accessibility_new;
        break;
      case EquipmentCategory.cardio:
        iconData = Icons.directions_bike;
        break;
      case EquipmentCategory.arms:
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

  Color _getCategoryColor(EquipmentCategory category) {
    switch (category) {
      case EquipmentCategory.legs:
        return Colors.blue;
      case EquipmentCategory.chest:
        return Colors.red;
      case EquipmentCategory.back:
        return Colors.green;
      case EquipmentCategory.cardio:
        return Colors.purple;
      case EquipmentCategory.arms:
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }
}

class _StatusBadge extends StatelessWidget {
  final MachineStatus status;

  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    Color color;
    String label;
    IconData icon;

    switch (status) {
      case MachineStatus.available:
        color = Colors.green;
        label = 'Available';
        icon = Icons.check_circle;
        break;
      case MachineStatus.occupied:
        color = Colors.red;
        label = 'Occupied';
        icon = Icons.person;
        break;
      case MachineStatus.offline:
        color = Colors.grey;
        label = 'Offline';
        icon = Icons.error;
        break;
      case MachineStatus.unknown:
        color = Colors.orange;
        label = 'Unknown';
        icon = Icons.help;
        break;
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
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 4),
          Text(
            label,
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

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;

  const _InfoChip({
    required this.icon,
    required this.label,
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
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            label,
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
