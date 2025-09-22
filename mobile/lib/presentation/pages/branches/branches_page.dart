import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../providers/gym_provider.dart';
import '../../providers/location_provider.dart';
import '../../widgets/branch/branch_card.dart';
import '../../widgets/common/loading_widget.dart';
import '../../widgets/common/error_widget.dart';

class BranchesPage extends StatefulWidget {
  const BranchesPage({super.key});

  @override
  State<BranchesPage> createState() => _BranchesPageState();
}

class _BranchesPageState extends State<BranchesPage> {
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<GymProvider>().loadBranches();
      context.read<LocationProvider>().getCurrentLocation();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('GymPulse'),
        actions: [
          IconButton(
            icon: const Icon(Icons.chat),
            onPressed: () => context.go('/chat'),
          ),
          IconButton(
            icon: const Icon(Icons.notifications),
            onPressed: () => context.go('/alerts'),
          ),
        ],
      ),
      body: Column(
        children: [
          // Search bar
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              controller: _searchController,
              decoration: const InputDecoration(
                hintText: 'Search branches...',
                prefixIcon: Icon(Icons.search),
                border: OutlineInputBorder(),
              ),
              onChanged: (value) {
                setState(() {
                  _searchQuery = value;
                });
              },
            ),
          ),
          // Branches list
          Expanded(
            child: Consumer<GymProvider>(
              builder: (context, gymProvider, child) {
                if (gymProvider.isLoadingBranches) {
                  return const LoadingWidget();
                }

                if (gymProvider.branchesError != null) {
                  return CustomErrorWidget(
                    message: gymProvider.branchesError!,
                    onRetry: () => gymProvider.loadBranches(),
                  );
                }

                final branches = gymProvider.searchBranches(_searchQuery);

                if (branches.isEmpty) {
                  return const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.location_off,
                          size: 64,
                          color: Colors.grey,
                        ),
                        SizedBox(height: 16),
                        Text(
                          'No branches found',
                          style: TextStyle(
                            fontSize: 18,
                            color: Colors.grey,
                          ),
                        ),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: branches.length,
                  itemBuilder: (context, index) {
                    final branch = branches[index];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: BranchCard(
                        branch: branch,
                        onTap: () {
                          gymProvider.selectBranch(branch);
                          context.go('/dashboard/${branch.id}');
                        },
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
