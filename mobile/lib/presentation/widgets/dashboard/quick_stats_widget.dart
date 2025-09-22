import 'package:flutter/material.dart';

class QuickStatsWidget extends StatelessWidget {
  final int totalEquipment;
  final int totalAvailable;
  final String peakHours;
  final int maintenanceNeeded;
  final String? rawPeakHours;

  const QuickStatsWidget({
    super.key,
    required this.totalEquipment,
    required this.totalAvailable,
    required this.peakHours,
    required this.maintenanceNeeded,
    this.rawPeakHours,
  });

  @override
  Widget build(BuildContext context) {
    final stats = [
      _StatItem(
        label: 'Total Equipment',
        value: totalEquipment.toString(),
        icon: Icons.trending_up,
        color: Colors.blue,
        bgColor: Colors.blue.shade50,
      ),
      _StatItem(
        label: 'Available Now',
        value: totalAvailable.toString(),
        icon: Icons.people,
        color: Colors.green,
        bgColor: Colors.green.shade50,
      ),
      _StatItem(
        label: 'Peak Hours',
        value: peakHours,
        icon: Icons.access_time,
        color: Colors.orange,
        bgColor: Colors.orange.shade50,
        tooltip: rawPeakHours,
      ),
      _StatItem(
        label: 'Maintenance',
        value: maintenanceNeeded.toString(),
        icon: Icons.warning,
        color: Colors.red,
        bgColor: Colors.red.shade50,
      ),
    ];

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 1.5,
        crossAxisSpacing: 16,
        mainAxisSpacing: 16,
      ),
      itemCount: stats.length,
      itemBuilder: (context, index) {
        final stat = stats[index];
        return _StatCard(stat: stat);
      },
    );
  }
}

class _StatItem {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final Color bgColor;
  final String? tooltip;

  _StatItem({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
    required this.bgColor,
    this.tooltip,
  });
}

class _StatCard extends StatelessWidget {
  final _StatItem stat;

  const _StatCard({required this.stat});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        stat.label,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[600],
                        ),
                      ),
                      const SizedBox(height: 4),
                      Tooltip(
                        message: stat.tooltip ?? stat.value,
                        child: Text(
                          stat.value,
                          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: Colors.grey[900],
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: stat.bgColor,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(
                    stat.icon,
                    color: stat.color,
                    size: 20,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
