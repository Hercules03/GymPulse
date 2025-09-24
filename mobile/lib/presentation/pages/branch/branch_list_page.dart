import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_constants.dart';
import '../../../domain/entities/branch.dart';
import '../../../shared/enums/equipment_category.dart';
import '../../providers/gym_provider.dart';
import '../../providers/chat_provider.dart';
import '../../widgets/common/error_widget.dart';
import '../../widgets/common/loading_widget.dart';
import '../../widgets/common/connection_status_widget.dart';
import '../../widgets/branch/branch_card.dart';
import '../../widgets/branch/branch_map.dart';
import '../../widgets/common/shimmer_widget.dart';
import '../machine/machine_list_page.dart';

class ChatMessage {
  final String id;
  final String content;
  final bool isUser;
  final DateTime timestamp;

  ChatMessage({
    required this.id,
    required this.content,
    required this.isUser,
    required this.timestamp,
  });
}

class BranchListPage extends StatefulWidget {
  const BranchListPage({super.key});

  @override
  State<BranchListPage> createState() => _BranchListPageState();
}

class _BranchListPageState extends State<BranchListPage> with TickerProviderStateMixin {
  Position? _currentPosition;
  bool _isLocationLoading = false;
  bool _isBranchSheetOpen = false;
  bool _isChatExpanded = false;
  final TextEditingController _chatController = TextEditingController();
  final TextEditingController _searchController = TextEditingController();
  final List<ChatMessage> _chatMessages = [];
  bool _isChatLoading = false;
  String _searchTerm = '';
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 400),
      vsync: this,
    );
    _loadBranches();
    _getCurrentLocation();
  }

  @override
  void dispose() {
    _chatController.dispose();
    _searchController.dispose();
    _animationController.dispose();
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

  Widget _buildLegendItem(Color color, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white, width: 1.5),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 2,
                offset: const Offset(0, 1),
              ),
            ],
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: Colors.black54,
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(
        elevation: 0,
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.white,
        title: null,
        toolbarHeight: 0, // Hide the entire app bar
      ),
      body: Stack(
        children: [
          // Header with title and legend
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: Container(
              color: Colors.white,
              child: SafeArea(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(24, 16, 24, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Find a Gym',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 8),
                    // Map Legend
                    Row(
                      children: [
                        _buildLegendItem(const Color(0xFF81C784), 'Good'),
                        const SizedBox(width: 16),
                        _buildLegendItem(const Color(0xFFFFB74D), 'Moderate'),
                        const SizedBox(width: 16),
                        _buildLegendItem(const Color(0xFFE57373), 'Busy'),
                        const SizedBox(width: 16),
                        _buildLegendItem(const Color(0xFF7BB3F0), 'Your Location'),
                      ],
                    ),
                  ],
                ),
              ),
              ),
            ),
          ),

          // Map view - starts below header
          Positioned(
            top: 110, // Adjusted for SafeArea + header with legend
            left: 0,
            right: 0,
            bottom: 0,
            child: _buildMapView(),
          ),

          // Availability indicator - top left corner
          Positioned(
            top: 130, // Below the header with legend
            left: 16,
            child: Consumer<GymProvider>(
              builder: (context, gymProvider, child) {
                final branchCount = gymProvider.branches.length;
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1),
                        blurRadius: 4,
                        offset: const Offset(0, 1),
                      ),
                    ],
                  ),
                  child: Text(
                    '$branchCount gym${branchCount != 1 ? 's' : ''}',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                      color: Colors.black87,
                    ),
                  ),
                );
              },
            ),
          ),

          // Interactive Chat Bubble - floating above bottom sheet
          Positioned(
            bottom: 100, // Above bottom sheet
            left: 16,
            right: 16,
            child: _InteractiveChatBubble(),
          ),

          // Bottom sheet indicator
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Consumer<GymProvider>(
              builder: (context, gymProvider, child) {
                final branchCount = gymProvider.branches.length;
                return GestureDetector(
                  onTap: () {
                    setState(() {
                      _isBranchSheetOpen = true;
                    });
                  },
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                    decoration: const BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black12,
                          blurRadius: 8,
                          offset: Offset(0, -2),
                        ),
                      ],
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 48,
                          height: 6,
                          decoration: BoxDecoration(
                            color: Colors.grey[400],
                            borderRadius: BorderRadius.circular(3),
                          ),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Tap to search',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                            color: Colors.black54,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),

          // Bottom sheet overlay
          if (_isBranchSheetOpen)
            GestureDetector(
              onTap: () {
                setState(() {
                  _isBranchSheetOpen = false;
                });
              },
              child: Container(
                color: Colors.black.withOpacity(0.5),
                child: Align(
                  alignment: Alignment.bottomCenter,
                  child: GestureDetector(
                    onTap: () {}, // Prevent closing when tapping sheet content
                    child: Container(
                      height: MediaQuery.of(context).size.height * 0.75,
                      decoration: const BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
                      ),
                      child: Column(
                        children: [
                          // Drag handle
                          Container(
                            width: 40,
                            height: 4,
                            margin: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: Colors.grey[300],
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),

                          // Header
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 24),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Find a Gym',
                                      style: TextStyle(
                                        fontSize: 20,
                                        fontWeight: FontWeight.w600,
                                        color: Colors.black87,
                                      ),
                                    ),
                                    SizedBox(height: 4),
                                    Text(
                                      'Select a branch to see details',
                                      style: TextStyle(
                                        fontSize: 14,
                                        color: Colors.black54,
                                      ),
                                    ),
                                  ],
                                ),
                                IconButton(
                                  icon: const Icon(Icons.close),
                                  onPressed: () {
                                    setState(() {
                                      _isBranchSheetOpen = false;
                                    });
                                  },
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 16),

                          // Search
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 24),
                            child: Container(
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: const Color(0xFFE5E7EB)),
                              ),
                              child: TextField(
                                controller: _searchController,
                                onChanged: (value) {
                                  setState(() {
                                    _searchTerm = value;
                                  });
                                },
                                decoration: const InputDecoration(
                                  hintText: 'Search branches...',
                                  hintStyle: TextStyle(
                                    color: Color(0xFF9CA3AF),
                                    fontSize: 14,
                                  ),
                                  prefixIcon: Icon(
                                    Icons.search,
                                    color: Color(0xFF9CA3AF),
                                    size: 20,
                                  ),
                                  border: InputBorder.none,
                                  contentPadding: EdgeInsets.symmetric(
                                    horizontal: 16,
                                    vertical: 12,
                                  ),
                                ),
                                style: const TextStyle(fontSize: 14),
                              ),
                            ),
                          ),

                          const SizedBox(height: 16),

                          Container(
                            height: 1,
                            color: const Color(0xFFF3F4F6),
                          ),

                          // List content
                          Expanded(child: _buildFilteredListView()),
                        ],
                      ),
                    ),
                  ),
                ),
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

  Widget _buildFilteredListView() {
    return Consumer<GymProvider>(
      builder: (context, gymProvider, child) {
        if (gymProvider.isLoadingBranches) {
          return _buildShimmerLoading();
        }

        if (gymProvider.hasError) {
          return Padding(
            padding: const EdgeInsets.all(24),
            child: Center(
              child: Column(
                children: [
                  Text(
                    gymProvider.errorMessage ?? 'Failed to load branches',
                    style: const TextStyle(
                      color: Color(0xFFEF4444),
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  TextButton(
                    onPressed: _loadBranches,
                    child: const Text(
                      'Try Again',
                      style: TextStyle(
                        color: Color(0xFF3B82F6),
                        fontSize: 14,
                        decoration: TextDecoration.underline,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        // Filter branches based on search term
        final filteredBranches = gymProvider.branches.where((branch) {
          if (_searchTerm.isEmpty) return true;
          return branch.name.toLowerCase().contains(_searchTerm.toLowerCase()) ||
                 (branch.address?.toLowerCase().contains(_searchTerm.toLowerCase()) ?? false);
        }).toList();

        if (filteredBranches.isEmpty) {
          return const Padding(
            padding: EdgeInsets.all(24),
            child: Center(
              child: Text(
                'No branches found matching your search.',
                style: TextStyle(
                  color: Color(0xFF6B7280),
                  fontSize: 14,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          itemCount: filteredBranches.length,
          itemBuilder: (context, index) {
            final branch = filteredBranches[index];
            return AnimatedContainer(
              duration: Duration(milliseconds: 400 + (index * 100)),
              curve: Curves.easeOutBack,
              child: Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: BranchCard(
                  branch: branch,
                  currentPosition: _currentPosition,
                  onTap: () {
                    setState(() {
                      _isBranchSheetOpen = false;
                    });
                    _onBranchSelected(branch);
                  },
                ),
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildShimmerLoading() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: List.generate(3, (index) =>
          Container(
            margin: const EdgeInsets.only(bottom: 16),
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFFF3F4F6)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ShimmerContainer(
                  height: 16,
                  width: MediaQuery.of(context).size.width * 0.75,
                  borderRadius: BorderRadius.circular(4),
                ),
                const SizedBox(height: 12),
                ShimmerContainer(
                  height: 12,
                  width: MediaQuery.of(context).size.width * 0.5,
                  borderRadius: BorderRadius.circular(4),
                ),
                const SizedBox(height: 12),
                ShimmerContainer(
                  height: 8,
                  width: double.infinity,
                  borderRadius: BorderRadius.circular(4),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMapView() {
    return Consumer<GymProvider>(
      builder: (context, gymProvider, child) {
        if (gymProvider.isLoadingBranches) {
          return Container(
            color: const Color(0xFFF3F4F6),
            child: const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(
                    color: Color(0xFF3B82F6),
                  ),
                  SizedBox(height: 16),
                  Text(
                    'Loading Map',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w500,
                      color: Colors.black54,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Preparing to show branch locations and\navailability',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.black54,
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        if (gymProvider.hasError) {
          return Container(
            color: const Color(0xFFF3F4F6),
            child: CustomErrorWidget(
              message: gymProvider.errorMessage ?? 'Failed to load map',
              onRetry: _loadBranches,
            ),
          );
        }

        return BranchMap(
          branches: gymProvider.branches,
          currentPosition: _currentPosition,
          onBranchSelected: _onBranchSelected,
        );
      },
    );
  }

  Widget _InteractiveChatBubble() {
    final examplePrompts = [
      "Leg day nearby?",
      "Find chest equipment close to me",
      "Where can I do back exercises?",
      "What's available at Central branch?"
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Chat messages - show above input when expanded
        if (_isChatExpanded && (_chatMessages.isNotEmpty || _isChatLoading))
          Container(
            constraints: const BoxConstraints(maxHeight: 300),
            margin: const EdgeInsets.only(bottom: 12),
            child: ListView.builder(
              reverse: true,
              itemCount: _chatMessages.length + (_isChatLoading ? 1 : 0),
              itemBuilder: (context, index) {
                if (_isChatLoading && index == 0) {
                  return Container(
                    alignment: Alignment.centerLeft,
                    margin: const EdgeInsets.only(bottom: 8),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: BoxDecoration(
                        color: Colors.grey[100],
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.grey[400],
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            'Typing...',
                            style: TextStyle(
                              color: Colors.grey[600],
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                }

                final messageIndex = _isChatLoading ? index - 1 : index;
                final message = _chatMessages[messageIndex];

                return Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  child: Row(
                    mainAxisAlignment: message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      if (!message.isUser) ...[
                        CircleAvatar(
                          radius: 16,
                          backgroundColor: const Color(0xFFF3F4F6),
                          child: Icon(
                            Icons.smart_toy,
                            size: 16,
                            color: Colors.grey[600],
                          ),
                        ),
                        const SizedBox(width: 8),
                      ],
                      Container(
                        constraints: BoxConstraints(
                          maxWidth: MediaQuery.of(context).size.width * 0.7,
                        ),
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        decoration: BoxDecoration(
                          color: message.isUser
                              ? const Color(0xFF3B82F6).withOpacity(0.9)
                              : Colors.white.withOpacity(0.9),
                          borderRadius: BorderRadius.only(
                            topLeft: const Radius.circular(16),
                            topRight: const Radius.circular(16),
                            bottomLeft: Radius.circular(message.isUser ? 16 : 4),
                            bottomRight: Radius.circular(message.isUser ? 4 : 16),
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.1),
                              blurRadius: 4,
                              offset: const Offset(0, 1),
                            ),
                          ],
                          border: message.isUser ? null : Border.all(
                            color: Colors.grey[200]!.withOpacity(0.5),
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              message.content,
                              style: TextStyle(
                                color: message.isUser ? Colors.white : Colors.black87,
                                fontSize: 14,
                                height: 1.4,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              _formatTimestamp(message.timestamp),
                              style: TextStyle(
                                color: message.isUser
                                    ? Colors.blue[100]
                                    : Colors.grey[500],
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                      if (message.isUser) ...[
                        const SizedBox(width: 8),
                        CircleAvatar(
                          radius: 16,
                          backgroundColor: const Color(0xFF3B82F6),
                          child: const Icon(
                            Icons.person,
                            size: 16,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ],
                  ),
                );
              },
            ),
          ),

        // Example prompts - show above input when expanded and no messages
        if (_isChatExpanded && _chatMessages.isEmpty && !_isChatLoading)
          Container(
            margin: const EdgeInsets.only(bottom: 12),
            child: Column(
              children: examplePrompts.map((prompt) =>
                Container(
                  width: double.infinity,
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ElevatedButton(
                    onPressed: () => _sendMessage(prompt),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: Colors.black87,
                      elevation: 2,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20),
                        side: BorderSide(color: Colors.grey[300]!),
                      ),
                    ),
                    child: Text(
                      prompt,
                      style: const TextStyle(fontSize: 14),
                    ),
                  ),
                ),
              ).toList(),
            ),
          ),

        // Main chat input
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(24),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _chatController,
                  onTap: () {
                    setState(() {
                      _isChatExpanded = true;
                    });
                  },
                  onChanged: (value) {
                    setState(() {
                      // Update send button state
                    });
                    // Keep expanded if user is typing
                    if (value.isNotEmpty && !_isChatExpanded) {
                      setState(() {
                        _isChatExpanded = true;
                      });
                    }
                  },
                  onSubmitted: (value) {
                    if (value.trim().isNotEmpty) {
                      _sendMessage(value);
                    }
                  },
                  decoration: InputDecoration(
                    hintText: _chatMessages.isNotEmpty
                        ? "Continue the conversation..."
                        : "Ask me anything about gym equipment...",
                    hintStyle: const TextStyle(
                      color: Colors.black54,
                      fontSize: 14,
                    ),
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.zero,
                  ),
                  style: const TextStyle(fontSize: 14),
                ),
              ),
              AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                child: GestureDetector(
                  onTap: () {
                    if (_chatController.text.trim().isNotEmpty) {
                      _sendMessage(_chatController.text);
                    }
                  },
                  child: Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      color: _chatController.text.trim().isNotEmpty
                          ? const Color(0xFF3B82F6)
                          : const Color(0xFF9CA3AF),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.send,
                      color: Colors.white,
                      size: 16,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _sendMessage(String message) async {
    if (message.trim().isEmpty) return;

    // Add user message
    setState(() {
      _chatMessages.insert(0, ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        content: message,
        isUser: true,
        timestamp: DateTime.now(),
      ));
      _isChatLoading = true;
    });

    _chatController.clear();

    // Simulate AI response (replace with actual API call)
    await Future.delayed(const Duration(seconds: 2));

    setState(() {
      _chatMessages.insert(0, ChatMessage(
        id: (DateTime.now().millisecondsSinceEpoch + 1).toString(),
        content: "Thanks for your question! I'm here to help you find the best gym equipment. Let me check our availability for you.",
        isUser: false,
        timestamp: DateTime.now(),
      ));
      _isChatLoading = false;
    });
  }

  String _formatTimestamp(DateTime timestamp) {
    final now = DateTime.now();
    final diff = now.difference(timestamp);

    if (diff.inMinutes < 1) {
      return 'just now';
    } else if (diff.inMinutes < 60) {
      return '${diff.inMinutes}m ago';
    } else if (diff.inHours < 24) {
      return '${diff.inHours}h ago';
    } else {
      return '${timestamp.day}/${timestamp.month}';
    }
  }
}