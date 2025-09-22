import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_constants.dart';
import '../../../domain/entities/branch.dart';
import '../../../shared/enums/equipment_category.dart';
import '../../providers/gym_provider.dart';
import '../../widgets/common/error_widget.dart';
import '../../widgets/common/loading_widget.dart';
import '../../widgets/common/connection_status_widget.dart';
import '../../widgets/branch/branch_card.dart';
import '../../widgets/branch/branch_map.dart';
import '../machine/machine_list_page.dart';

class BranchListPage extends StatefulWidget {
  const BranchListPage({super.key});

  @override
  State<BranchListPage> createState() => _BranchListPageState();
}

class _BranchListPageState extends State<BranchListPage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Position? _currentPosition;
  bool _isLocationLoading = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadBranches();
    _getCurrentLocation();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadBranches() async {
    final gymProvider = context.read<GymProvider>();
    await gymProvider.loadBranches();
  }

  Future<void> _getCurrentLocation() async {
    setState(() {
      _isLocationLoading = true;
    });

    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text(AppConstants.locationServiceDisabled),
            ),
          );
        }
        return;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text(AppConstants.locationPermissionDenied),
              ),
            );
          }
          return;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text(AppConstants.locationPermissionDenied),
              action: SnackBarAction(
                label: 'Settings',
                onPressed: Geolocator.openAppSettings,
              ),
            ),
          );
        }
        return;
      }

      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: AppConstants.locationTimeout,
      );

      setState(() {
        _currentPosition = position;
      });
    } catch (e) {
      debugPrint('Error getting location: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to get location: ${e.toString()}'),
          ),
        );
      }
    } finally {
      setState(() {
        _isLocationLoading = false;
      });
    }
  }

  void _onBranchSelected(Branch branch) {
    final gymProvider = context.read<GymProvider>();
    gymProvider.selectBranch(branch.id);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _buildCategorySelectionSheet(branch),
    );
  }

  Widget _buildCategorySelectionSheet(Branch branch) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.6,
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        children: [
          Container(
            width: 40,
            height: 4,
            margin: const EdgeInsets.symmetric(vertical: 12),
            decoration: BoxDecoration(
              color: Colors.grey[300],
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(AppConstants.defaultPadding),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  branch.name,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Icon(
                      Icons.location_on,
                      color: Colors.grey[600],
                      size: 16,
                    ),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        branch.address ?? 'Address not available',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.grey[600],
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Text(
                  'Select Equipment Category',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(
                horizontal: AppConstants.defaultPadding,
              ),
              itemCount: EquipmentCategory.values.length,
              itemBuilder: (context, index) {
                final category = EquipmentCategory.values[index];
                final categoryData = branch.getCategoryData(category.value);

                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    leading: Icon(
                      _getCategoryIcon(category),
                      color: Theme.of(context).primaryColor,
                    ),
                    title: Text(
                      category.displayName,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    subtitle: categoryData != null
                        ? Text(
                            '${categoryData.free} available / ${categoryData.total} total',
                            style: TextStyle(
                              color: categoryData.free > 0
                                  ? Colors.green[600]
                                  : Colors.red[600],
                            ),
                          )
                        : const Text('No data available'),
                    trailing: categoryData != null
                        ? Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 4,
                            ),
                            decoration: BoxDecoration(
                              color: categoryData.free > 0
                                  ? Colors.green[100]
                                  : Colors.red[100],
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              '${((categoryData.free / categoryData.total) * 100).round()}%',
                              style: TextStyle(
                                color: categoryData.free > 0
                                    ? Colors.green[800]
                                    : Colors.red[800],
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                          )
                        : null,
                    onTap: categoryData != null
                        ? () {
                            Navigator.pop(context);
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) => MachineListPage(
                                  branch: branch,
                                  category: category,
                                ),
                              ),
                            );
                          }
                        : null,
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  IconData _getCategoryIcon(EquipmentCategory category) {
    switch (category) {
      case EquipmentCategory.cardio:
        return Icons.directions_run;
      case EquipmentCategory.strength:
        return Icons.fitness_center;
      case EquipmentCategory.functional:
        return Icons.sports_gymnastics;
      case EquipmentCategory.stretching:
        return Icons.self_improvement;
      default:
        return Icons.fitness_center;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Gym Branches'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(icon: Icon(Icons.list), text: 'List'),
            Tab(icon: Icon(Icons.map), text: 'Map'),
          ],
        ),
        actions: [
          const ConnectionStatusWidget(iconSize: 18),
          const SizedBox(width: 8),
          IconButton(
            icon: const Icon(Icons.chat),
            onPressed: () => context.go('/chat'),
            tooltip: 'AI Assistant',
          ),
          IconButton(
            icon: _isLocationLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.my_location),
            onPressed: _isLocationLoading ? null : _getCurrentLocation,
            tooltip: 'Get current location',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadBranches,
            tooltip: 'Refresh branches',
          ),
        ],
      ),
      body: Column(
        children: [
          const ConnectionStatusBanner(),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildListView(),
                _buildMapView(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildListView() {
    return Consumer<GymProvider>(
      builder: (context, gymProvider, child) {
        if (gymProvider.isLoadingBranches) {
          return const LoadingWidget(message: 'Loading branches...');
        }

        if (gymProvider.hasError) {
          return CustomErrorWidget(
            message: gymProvider.errorMessage ?? 'Failed to load branches',
            onRetry: _loadBranches,
          );
        }

        if (gymProvider.branches.isEmpty) {
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

        return RefreshIndicator(
          onRefresh: _loadBranches,
          child: ListView.builder(
            padding: const EdgeInsets.all(AppConstants.defaultPadding),
            itemCount: gymProvider.branches.length,
            itemBuilder: (context, index) {
              final branch = gymProvider.branches[index];
              return BranchCard(
                branch: branch,
                currentPosition: _currentPosition,
                onTap: () => _onBranchSelected(branch),
              );
            },
          ),
        );
      },
    );
  }

  Widget _buildMapView() {
    return Consumer<GymProvider>(
      builder: (context, gymProvider, child) {
        if (gymProvider.isLoadingBranches) {
          return const LoadingWidget(message: 'Loading map...');
        }

        if (gymProvider.hasError) {
          return CustomErrorWidget(
            message: gymProvider.errorMessage ?? 'Failed to load map',
            onRetry: _loadBranches,
          );
        }

        return Stack(
          children: [
            BranchMap(
              branches: gymProvider.branches,
              currentPosition: _currentPosition,
              onBranchSelected: _onBranchSelected,
            ),
            // Add a fallback button to switch to list view if map fails
            Positioned(
              top: 16,
              left: 16,
              child: FloatingActionButton(
                mini: true,
                backgroundColor: Colors.white,
                foregroundColor: Colors.black87,
                onPressed: () {
                  _tabController.animateTo(0); // Switch to list view
                },
                tooltip: 'Switch to list view',
                child: const Icon(Icons.list),
              ),
            ),
          ],
        );
      },
    );
  }
}