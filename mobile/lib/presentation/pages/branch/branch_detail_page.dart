import 'package:flutter/material.dart';

class BranchDetailPage extends StatelessWidget {
  final String branchId;

  const BranchDetailPage({
    super.key,
    required this.branchId,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Branch $branchId'),
      ),
      body: const Center(
        child: Text('Branch Detail Page - Coming Soon'),
      ),
    );
  }
}
