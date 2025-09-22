import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../providers/gym_provider.dart';
import '../../providers/websocket_provider.dart';
import '../../widgets/machine/machine_card_widget.dart';
import '../../widgets/common/loading_widget.dart';
import '../../widgets/common/error_widget.dart';
import '../../../domain/entities/machine.dart';

class MachinesPage extends StatefulWidget {
  final String branchId;
  final String category;

  const MachinesPage({
    super.key,
    required this.branchId,
    required this.category,
  });

  @override
  State<MachinesPage> createState() => _MachinesPageState();
}

class _MachinesPageState extends State<MachinesPage> {
  List<Machine> _machines = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadMachines();
  }

  void _loadMachines() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // Simulate API call for machines
      await Future.delayed(const Duration(seconds: 1));
      
      // Mock machines data
      final machines = _generateMockMachines();
      setState(() {
        _machines = machines;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load machines: $e';
        _isLoading = false;
      });
    }
  }

  List<Machine> _generateMockMachines() {
    final category = widget.category;
    final branchId = widget.branchId;
    
    // Generate different machines based on category
    final machineNames = _getMachineNamesForCategory(category);
    
    return machineNames.map((name) {
      return Machine(
        machineId: '${category}-${name.toLowerCase().replaceAll(' ', '-')}',
        name: name,
        category: _parseCategory(category),
        status: _getRandomStatus(),
        location: 'Floor 1',
        branchId: branchId,
        lastUpdated: DateTime.now(),
        estimatedFreeTime: _getRandomEstimatedTime(),
        usageCount: (DateTime.now().millisecondsSinceEpoch % 100),
        averageUsageTime: 30.0 + (DateTime.now().millisecondsSinceEpoch % 30),
        features: _getRandomFeatures(),
        description: 'High-quality $category equipment',
        imageUrl: null,
      );
    }).toList();
  }

  List<String> _getMachineNamesForCategory(String category) {
    switch (category.toLowerCase()) {
      case 'legs':
        return [
          'Leg Press',
          'Squat Rack',
          'Leg Extension',
          'Leg Curl',
          'Calf Raise',
          'Hack Squat',
        ];
      case 'chest':
        return [
          'Bench Press',
          'Chest Press',
          'Cable Crossover',
          'Incline Press',
          'Dumbbell Press',
          'Pec Deck',
        ];
      case 'cardio':
        return [
          'Treadmill',
          'Stationary Bike',
          'Elliptical',
          'Rowing Machine',
          'Stair Climber',
          'Cross Trainer',
        ];
      case 'arms':
        return [
          'Bicep Curl',
          'Tricep Extension',
          'Preacher Curl',
          'Cable Pulley',
          'Dumbbell Rack',
          'Arm Blaster',
        ];
      case 'back':
        return [
          'Lat Pulldown',
          'Seated Row',
          'Cable Row',
          'Pull-up Bar',
          'T-Bar Row',
          'Back Extension',
        ];
      default:
        return ['Machine 1', 'Machine 2', 'Machine 3'];
    }
  }

  MachineStatus _getRandomStatus() {
    final statuses = [MachineStatus.available, MachineStatus.occupied, MachineStatus.offline];
    return statuses[DateTime.now().millisecondsSinceEpoch % statuses.length];
  }

  String? _getRandomEstimatedTime() {
    final times = ['5 min', '10 min', '15 min', '20 min', '30 min', null];
    return times[DateTime.now().millisecondsSinceEpoch % times.length];
  }

  List<String> _getRandomFeatures() {
    final allFeatures = ['Digital Display', 'Weight Plates', 'Adjustable', 'Premium'];
    final count = 1 + (DateTime.now().millisecondsSinceEpoch % 3);
    return allFeatures.take(count).toList();
  }

  EquipmentCategory _parseCategory(String category) {
    switch (category.toLowerCase()) {
      case 'legs':
        return EquipmentCategory.legs;
      case 'chest':
        return EquipmentCategory.chest;
      case 'back':
        return EquipmentCategory.back;
      case 'cardio':
        return EquipmentCategory.cardio;
      case 'arms':
        return EquipmentCategory.arms;
      default:
        return EquipmentCategory.other;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${_capitalizeFirst(widget.category)} Machines'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/branches'),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadMachines,
          ),
        ],
      ),
      body: Consumer<WebSocketProvider>(
        builder: (context, websocketProvider, child) {
          // Listen for real-time updates
          if (websocketProvider.lastMachineUpdate != null) {
            _updateMachineFromWebSocket(websocketProvider.lastMachineUpdate!);
          }

          if (_isLoading) {
            return const LoadingWidget();
          }

          if (_error != null) {
            return CustomErrorWidget(
              message: _error!,
              onRetry: _loadMachines,
            );
          }

          if (_machines.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.fitness_center,
                    size: 64,
                    color: Colors.grey,
                  ),
                  SizedBox(height: 16),
                  Text(
                    'No machines found',
                    style: TextStyle(
                      fontSize: 18,
                      color: Colors.grey,
                    ),
                  ),
                ],
              ),
            );
          }

          return _buildMachinesList();
        },
      ),
    );
  }

  void _updateMachineFromWebSocket(dynamic update) {
    // Update machine status based on WebSocket update
    // This would be implemented based on the actual WebSocket message format
  }

  Widget _buildMachinesList() {
    return Column(
      children: [
        // Stats header
        _buildStatsHeader(),
        const SizedBox(height: 16),
        // Machines list
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: _machines.length,
            itemBuilder: (context, index) {
              final machine = _machines[index];
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: MachineCardWidget(
                  machine: machine,
                  onTap: () {
                    context.go('/machines/machine/${machine.machineId}?branch=${widget.branchId}&category=${widget.category}');
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildStatsHeader() {
    final totalMachines = _machines.length;
    final availableMachines = _machines.where((m) => m.status == MachineStatus.available).length;
    final occupiedMachines = _machines.where((m) => m.status == MachineStatus.occupied).length;
    final offlineMachines = _machines.where((m) => m.status == MachineStatus.offline).length;

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primaryContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatItem('Total', totalMachines.toString(), Colors.blue),
          _buildStatItem('Available', availableMachines.toString(), Colors.green),
          _buildStatItem('Occupied', occupiedMachines.toString(), Colors.red),
          _buildStatItem('Offline', offlineMachines.toString(), Colors.grey),
        ],
      ),
    );
  }

  Widget _buildStatItem(String label, String value, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }

  String _capitalizeFirst(String text) {
    if (text.isEmpty) return text;
    return text[0].toUpperCase() + text.substring(1);
  }
}
