import 'package:flutter/material.dart';

class MachineDetailPage extends StatelessWidget {
  final String machineId;
  final String branchId;
  final String category;

  const MachineDetailPage({
    super.key,
    required this.machineId,
    required this.branchId,
    required this.category,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Machine $machineId'),
      ),
      body: Center(
        child: Text('Machine Detail Page - $machineId - Coming Soon'),
      ),
    );
  }
}
