import 'package:flutter/foundation.dart';
import 'dart:async';

import '../../domain/entities/branch.dart';
import '../../domain/entities/machine.dart';
import '../../domain/repositories/gym_repository.dart';
import '../../shared/enums/machine_status.dart';
import '../../shared/enums/equipment_category.dart';
import '../../core/services/websocket_service.dart';

/// Main state management provider for gym-related data
class GymProvider extends ChangeNotifier {
  GymProvider({
    required this.gymRepository,
  }) {
    _initializeWebSocket();
  }

  final GymRepository gymRepository;
  final WebSocketService _webSocketService = webSocketService;
  StreamSubscription? _machineUpdateSubscription;
  StreamSubscription? _branchUpdateSubscription;

  // State variables
  List<Branch> _branches = [];
  Branch? _selectedBranch;
  List<Machine> _machines = [];
  Machine? _selectedMachine;
  MachineHistory? _machineHistory;
  PeakHoursData? _peakHoursData;

  // Loading states
  bool _isLoadingBranches = false;
  bool _isLoadingMachines = false;
  bool _isLoadingMachineHistory = false;
  bool _isLoadingPeakHours = false;

  // Error states
  String? _errorMessage;

  // Getters
  List<Branch> get branches => _branches;
  Branch? get selectedBranch => _selectedBranch;
  List<Machine> get machines => _machines;
  Machine? get selectedMachine => _selectedMachine;
  MachineHistory? get machineHistory => _machineHistory;
  PeakHoursData? get peakHoursData => _peakHoursData;

  bool get isLoadingBranches => _isLoadingBranches;
  bool get isLoadingMachines => _isLoadingMachines;
  bool get isLoadingMachineHistory => _isLoadingMachineHistory;
  bool get isLoadingPeakHours => _isLoadingPeakHours;

  String? get errorMessage => _errorMessage;

  bool get hasError => _errorMessage != null;

  // WebSocket getters
  bool get isWebSocketConnected => _webSocketService.isConnected;
  WebSocketConnectionState get webSocketState => _webSocketService.connectionState;

  // Computed properties
  int get totalMachines {
    if (_selectedBranch != null) {
      return _selectedBranch!.totalMachines;
    }
    return _machines.length;
  }

  int get availableMachines {
    if (_selectedBranch != null) {
      return _selectedBranch!.availableMachines;
    }
    return _machines.where((m) => m.status.isUsable).length;
  }

  double get availabilityPercentage {
    if (_selectedBranch != null) {
      return _selectedBranch!.availabilityPercentage;
    }
    if (totalMachines == 0) return 0.0;
    return (availableMachines / totalMachines) * 100;
  }

  // Actions

  /// Load all branches
  Future<void> loadBranches() async {
    _isLoadingBranches = true;
    _errorMessage = null;
    notifyListeners();

    try {
      _branches = await gymRepository.getBranches();
      _errorMessage = null;
    } catch (e) {
      _errorMessage = e.toString();
      _branches = [];
    }

    _isLoadingBranches = false;
    notifyListeners();
  }

  /// Select a branch and load its peak hours data
  Future<void> selectBranch(String branchId) async {
    _selectedBranch = _branches.firstWhere(
      (branch) => branch.id == branchId,
      orElse: () => _branches.first,
    );

    // Clear machines when switching branches
    _machines = [];
    _selectedMachine = null;
    _machineHistory = null;

    notifyListeners();

    // Load peak hours data for the selected branch
    await loadPeakHours(branchId);

    // Subscribe to real-time updates for this branch
    subscribeToRealTimeUpdates(branchId);
  }

  /// Load peak hours data for a branch
  Future<void> loadPeakHours(String branchId) async {
    _isLoadingPeakHours = true;
    notifyListeners();

    try {
      _peakHoursData = await gymRepository.getBranchPeakHours(branchId);
    } catch (e) {
      debugPrint('Failed to load peak hours: $e');
      // Don't set error for peak hours failure, it's not critical
    }

    _isLoadingPeakHours = false;
    notifyListeners();
  }

  /// Load machines for a specific branch and category
  Future<void> loadMachines(String branchId, EquipmentCategory category) async {
    _isLoadingMachines = true;
    _errorMessage = null;
    notifyListeners();

    try {
      _machines = await gymRepository.getMachines(branchId, category.value);
      _errorMessage = null;
    } catch (e) {
      _errorMessage = e.toString();
      _machines = [];
    }

    _isLoadingMachines = false;
    notifyListeners();
  }

  /// Select a machine and load its history
  Future<void> selectMachine(String machineId) async {
    _selectedMachine = _machines.firstWhere(
      (machine) => machine.machineId == machineId,
      orElse: () => _machines.first,
    );

    notifyListeners();

    // Load machine history
    await loadMachineHistory(machineId);
  }

  /// Load machine history data
  Future<void> loadMachineHistory(String machineId) async {
    _isLoadingMachineHistory = true;
    notifyListeners();

    try {
      _machineHistory = await gymRepository.getMachineHistory(machineId);
    } catch (e) {
      debugPrint('Failed to load machine history: $e');
      _machineHistory = null;
    }

    _isLoadingMachineHistory = false;
    notifyListeners();
  }

  /// Update machine status (for real-time updates)
  void updateMachineStatus(String machineId, String newStatus, {int? timestamp}) {
    final machineIndex = _machines.indexWhere((m) => m.machineId == machineId);
    if (machineIndex != -1) {
      final updatedMachine = _machines[machineIndex].copyWithStatus(
        MachineStatus.fromString(newStatus),
        timestamp: timestamp,
      );
      _machines[machineIndex] = updatedMachine;

      // Update selected machine if it's the one being updated
      if (_selectedMachine?.machineId == machineId) {
        _selectedMachine = updatedMachine;
      }

      notifyListeners();
    }
  }

  /// Clear error message
  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  /// Refresh current data
  Future<void> refresh() async {
    if (_selectedBranch != null) {
      await Future.wait([
        loadBranches(),
        loadPeakHours(_selectedBranch!.id),
      ]);
    } else {
      await loadBranches();
    }
  }

  /// Get machines by category for the selected branch
  List<Machine> getMachinesByCategory(EquipmentCategory category) {
    return _machines.where((machine) => machine.category == category).toList();
  }

  /// Get category data for the selected branch
  CategoryData? getCategoryData(String categoryName) {
    return _selectedBranch?.getCategoryData(categoryName);
  }

  /// Check if service is healthy
  Future<bool> checkHealth() async {
    try {
      return await gymRepository.healthCheck();
    } catch (e) {
      return false;
    }
  }

  // WebSocket Methods

  /// Initialize WebSocket connection and listeners
  void _initializeWebSocket() {
    // Listen to machine status updates
    _machineUpdateSubscription = _webSocketService.machineUpdates.listen(
      _handleMachineUpdate,
      onError: (error) {
        debugPrint('Machine update stream error: $error');
      },
    );

    // Listen to branch stats updates
    _branchUpdateSubscription = _webSocketService.branchUpdates.listen(
      _handleBranchUpdate,
      onError: (error) {
        debugPrint('Branch update stream error: $error');
      },
    );

    // Listen to WebSocket connection state changes
    _webSocketService.addListener(_onWebSocketStateChange);
  }

  /// Connect to WebSocket for real-time updates
  Future<void> connectWebSocket({String? branchId}) async {
    try {
      await _webSocketService.connect(branchId: branchId);
      if (branchId != null) {
        _webSocketService.subscribeToBranch(branchId);
      }
    } catch (e) {
      debugPrint('Failed to connect WebSocket: $e');
    }
  }

  /// Disconnect from WebSocket
  void disconnectWebSocket() {
    _webSocketService.disconnect();
  }

  /// Subscribe to real-time updates for a specific branch
  void subscribeToRealTimeUpdates(String branchId) {
    if (_webSocketService.isConnected) {
      _webSocketService.subscribeToBranch(branchId);
    } else {
      connectWebSocket(branchId: branchId);
    }
  }

  /// Unsubscribe from real-time updates for a specific branch
  void unsubscribeFromRealTimeUpdates(String branchId) {
    _webSocketService.unsubscribeFromBranch(branchId);
  }

  /// Handle real-time machine status updates
  void _handleMachineUpdate(Map<String, dynamic> update) {
    try {
      final machineId = update['machineId'] as String?;
      final newStatus = update['status'] as String?;
      final timestamp = update['timestamp'] as int?;

      if (machineId != null && newStatus != null) {
        updateMachineStatus(machineId, newStatus, timestamp: timestamp);
        debugPrint('Real-time machine update: $machineId -> $newStatus');
      }
    } catch (e) {
      debugPrint('Error handling machine update: $e');
    }
  }

  /// Handle real-time branch statistics updates
  void _handleBranchUpdate(Map<String, dynamic> update) {
    try {
      final branchId = update['branchId'] as String?;
      final stats = update['stats'] as Map<String, dynamic>?;

      if (branchId != null && stats != null) {
        _updateBranchStats(branchId, stats);
        debugPrint('Real-time branch update: $branchId');
      }
    } catch (e) {
      debugPrint('Error handling branch update: $e');
    }
  }

  /// Update branch statistics from real-time data
  void _updateBranchStats(String branchId, Map<String, dynamic> stats) {
    final branchIndex = _branches.indexWhere((b) => b.id == branchId);
    if (branchIndex == -1) return;

    final branch = _branches[branchIndex];

    // Update categories data if provided
    final categoriesData = stats['categories'] as Map<String, dynamic>?;
    if (categoriesData != null) {
      final updatedCategories = <String, CategoryData>{};

      // Copy existing categories
      updatedCategories.addAll(branch.categories);

      // Update with new data
      categoriesData.forEach((key, value) {
        if (value is Map<String, dynamic>) {
          updatedCategories[key] = CategoryData(
            free: value['free'] ?? 0,
            total: value['total'] ?? 0,
          );
        }
      });

      // Create updated branch
      final updatedBranch = Branch(
        id: branch.id,
        name: branch.name,
        coordinates: branch.coordinates,
        categories: updatedCategories,
        address: branch.address,
        phone: branch.phone,
        hours: branch.hours,
        amenities: branch.amenities,
      );

      _branches[branchIndex] = updatedBranch;

      // Update selected branch if it's the one being updated
      if (_selectedBranch?.id == branchId) {
        _selectedBranch = updatedBranch;
      }

      notifyListeners();
    }
  }

  /// Handle WebSocket connection state changes
  void _onWebSocketStateChange() {
    notifyListeners();
  }

  @override
  void dispose() {
    _machineUpdateSubscription?.cancel();
    _branchUpdateSubscription?.cancel();
    _webSocketService.removeListener(_onWebSocketStateChange);
    _webSocketService.disconnect();
    super.dispose();
  }
}