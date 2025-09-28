import 'package:flutter/material.dart';
import '../../../domain/entities/machine.dart';
import '../../../shared/enums/equipment_category.dart';
import '../../../shared/enums/machine_status.dart';

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
                          machine.displayType,
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
                      color: const Color(0xFFD97706),
                    ),
                    const SizedBox(width: 8),
                  ],
                  if (machine.lastUpdateTime != null) ...[
                    _InfoChip(
                      icon: Icons.update,
                      label: 'Updated ${_formatTimeAgo(machine.lastUpdateTime!)}',
                      color: const Color(0xFF2563EB),
                    ),
                    const SizedBox(width: 8),
                  ],
                  if (machine.alertEligible) ...[
                    _InfoChip(
                      icon: Icons.notifications,
                      label: 'Alerts enabled',
                      color: const Color(0xFF059669),
                    ),
                  ],
                ],
              ),
              if (machine.type != null) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    machine.type!,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey[700],
                      fontSize: 12,
                    ),
                  ),
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
        return const Color(0xFF2563EB);
      case EquipmentCategory.chest:
        return const Color(0xFFDC2626);
      case EquipmentCategory.back:
        return const Color(0xFF059669);
      case EquipmentCategory.cardio:
        return const Color(0xFF7C3AED);
      case EquipmentCategory.arms:
        return const Color(0xFFEA580C);
      default:
        return const Color(0xFF6B7280);
    }
  }

  String _formatTimeAgo(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inMinutes < 1) {
      return 'just now';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else {
      return '${difference.inDays}d ago';
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
        color = const Color(0xFF059669);
        label = 'Available';
        icon = Icons.check_circle;
        break;
      case MachineStatus.occupied:
        color = const Color(0xFFDC2626);
        label = 'Occupied';
        icon = Icons.person;
        break;
      case MachineStatus.offline:
        color = const Color(0xFF6B7280);
        label = 'Offline';
        icon = Icons.error;
        break;
      case MachineStatus.unknown:
        color = const Color(0xFFD97706);
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
