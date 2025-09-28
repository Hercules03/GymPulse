import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../providers/gym_provider.dart';
import '../../providers/websocket_provider.dart';
import '../../widgets/dashboard/quick_stats_widget.dart';
import '../../widgets/dashboard/category_card_widget.dart';
import '../../widgets/common/loading_widget.dart';
import '../../widgets/common/error_widget.dart';
import '../../../domain/entities/branch.dart';

class DashboardPage extends StatefulWidget {
  final String branchId;

  const DashboardPage({
    super.key,
    required this.branchId,
  });

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  Branch? _currentBranch;
  Map<String, dynamic>? _peakHoursData;
  bool _isLoadingPeakHours = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadBranchData();
      _loadPeakHoursData();
    });
  }

  void _loadBranchData() {
    final gymProvider = context.read<GymProvider>();
    if (gymProvider.branches.isNotEmpty) {
      final branch = gymProvider.branches.firstWhere(
        (b) => b.id == widget.branchId,
        orElse: () => gymProvider.branches.first,
      );
      setState(() {
        _currentBranch = branch;
      });
    }
  }

  void _loadPeakHoursData() async {
    setState(() {
      _isLoadingPeakHours = true;
    });

    try {
      // Simulate API call for peak hours data
      await Future.delayed(const Duration(seconds: 1));
      
      // Mock peak hours data
      setState(() {
        _peakHoursData = {
          'peakHours': '6-9AM, 6-9PM',
          'confidence': 'high',
          'currentOccupancy': 65,
          'occupancyForecast': {
            '6': 20,
            '7': 45,
            '8': 70,
            '9': 60,
            '18': 80,
            '19': 85,
            '20': 75,
            '21': 50,
          },
        };
      });
    } catch (e) {
      // Handle error
    } finally {
      setState(() {
        _isLoadingPeakHours = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_currentBranch?.name ?? 'Dashboard'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/branches'),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              context.read<GymProvider>().loadBranches();
              _loadPeakHoursData();
            },
          ),
        ],
      ),
      body: Consumer2<GymProvider, WebSocketProvider>(
        builder: (context, gymProvider, websocketProvider, child) {
          if (gymProvider.isLoadingBranches) {
            return const LoadingWidget();
          }

          if (gymProvider.branchesError != null) {
            return CustomErrorWidget(
              message: gymProvider.branchesError!,
              onRetry: () => gymProvider.loadBranches(),
            );
          }

          if (_currentBranch == null) {
            return const Center(
              child: Text('Branch not found'),
            );
          }

          return _buildDashboardContent();
        },
      ),
    );
  }

  Widget _buildDashboardContent() {
    final branch = _currentBranch!;
    
    // Calculate stats from branch data
    final totalEquipment = branch.amenities?.length ?? 0;
    final totalAvailable = (totalEquipment * 0.7).round(); // Mock calculation
    final maintenanceNeeded = (totalEquipment * 0.05).round(); // Mock calculation

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Quick Stats
          Text(
            'Overview',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          QuickStatsWidget(
            totalEquipment: totalEquipment,
            totalAvailable: totalAvailable,
            peakHours: _peakHoursData?['peakHours'] ?? '6-9AM, 6-9PM',
            maintenanceNeeded: maintenanceNeeded,
            rawPeakHours: _peakHoursData?['peakHours'],
          ),
          const SizedBox(height: 32),

          // Equipment Categories
          Text(
            'Equipment Categories',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          _buildCategoryCards(),
          const SizedBox(height: 32),

          // Branch Information
          _buildBranchInfo(),
        ],
      ),
    );
  }

  Widget _buildCategoryCards() {
    // Mock category data - in real app, this would come from the branch data
    final categories = [
      {
        'name': 'legs',
        'total': 12,
        'available': 8,
        'occupied': 3,
        'offline': 1,
      },
      {
        'name': 'chest',
        'total': 10,
        'available': 6,
        'occupied': 3,
        'offline': 1,
      },
      {
        'name': 'cardio',
        'total': 15,
        'available': 12,
        'occupied': 2,
        'offline': 1,
      },
      {
        'name': 'arms',
        'total': 8,
        'available': 5,
        'occupied': 2,
        'offline': 1,
      },
    ];

    return Column(
      children: categories.map((category) {
        return Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: CategoryCardWidget(
            category: category['name'] as String,
            totalMachines: category['total'] as int,
            availableCount: category['available'] as int,
            occupiedCount: category['occupied'] as int,
            offlineCount: category['offline'] as int,
            machines: [], // Empty for now
            onTap: () {
              context.go('/machines?branch=${widget.branchId}&category=${category['name']}');
            },
          ),
        );
      }).toList(),
    );
  }

  Widget _buildBranchInfo() {
    final branch = _currentBranch!;
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Branch Information',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            _buildInfoRow(Icons.location_on, 'Address', branch.address),
            if (branch.phone != null)
              _buildInfoRow(Icons.phone, 'Phone', branch.phone!),
            if (branch.hours != null)
              _buildInfoRow(Icons.schedule, 'Hours', branch.hours!),
            if (branch.amenities != null && branch.amenities!.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                'Amenities',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 4,
                children: branch.amenities!.map((amenity) {
                  return Chip(
                    label: Text(amenity),
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  );
                }).toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: Colors.grey[600]),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              '$label: $value',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
        ],
      ),
    );
  }
}
