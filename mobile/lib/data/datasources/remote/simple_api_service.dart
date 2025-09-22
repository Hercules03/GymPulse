import 'package:dio/dio.dart';
import 'package:logger/logger.dart';
import '../../../domain/entities/branch.dart';
import '../../../domain/entities/machine.dart';
import '../../../core/network/api_client.dart';

class SimpleApiService {
  final Logger _logger = Logger();
  final Dio _dio = ApiClient.dio;

  Future<List<Branch>> getBranches() async {
    try {
      _logger.i('Fetching branches from API');
      final response = await _dio.get('/branches');
      
      if (response.statusCode == 200) {
        _logger.i('API Response received: ${response.data}');
        
        // Handle the actual API response structure
        final Map<String, dynamic> responseData = response.data;
        final List<dynamic> branchesData = responseData['branches'] ?? [];
        
        _logger.i('Found ${branchesData.length} branches in API response');
        
        final List<Branch> branches = [];
        for (int i = 0; i < branchesData.length; i++) {
          try {
            final branch = Branch.fromJson(branchesData[i] as Map<String, dynamic>);
            branches.add(branch);
            _logger.i('Successfully parsed branch ${i + 1}: ${branch.name}');
          } catch (e) {
            _logger.e('Error parsing branch ${i + 1}: $e');
            _logger.e('Branch data: ${branchesData[i]}');
          }
        }
        
        return branches;
      } else {
        throw Exception('Failed to load branches: ${response.statusCode}');
      }
    } catch (e) {
      _logger.e('Error fetching branches from API: $e');
      rethrow;
    }
  }

  Future<Branch> getBranchDetails(String branchId) async {
    try {
      _logger.i('Fetching branch details for $branchId');
      final response = await _dio.get('/branches/$branchId');
      
      if (response.statusCode == 200) {
        return Branch.fromJson(response.data);
      } else {
        throw Exception('Failed to load branch details: ${response.statusCode}');
      }
    } catch (e) {
      _logger.e('Error fetching branch details: $e');
      rethrow;
    }
  }

  Future<List<Machine>> getMachines(String branchId, String category) async {
    try {
      _logger.i('Fetching machines for $category in $branchId');
      final response = await _dio.get('/branches/$branchId/categories/$category/machines');
      
      if (response.statusCode == 200) {
        final List<dynamic> machinesData = response.data['machines'] ?? response.data;
        return machinesData.map((json) => Machine.fromJson(json)).toList();
      } else {
        throw Exception('Failed to load machines: ${response.statusCode}');
      }
    } catch (e) {
      _logger.e('Error fetching machines: $e');
      rethrow;
    }
  }

  Future<Machine> getMachineDetails(String machineId) async {
    try {
      _logger.i('Fetching machine details for $machineId');
      final response = await _dio.get('/machines/$machineId');
      
      if (response.statusCode == 200) {
        return Machine.fromJson(response.data);
      } else {
        throw Exception('Failed to load machine details: ${response.statusCode}');
      }
    } catch (e) {
      _logger.e('Error fetching machine details: $e');
      rethrow;
    }
  }

  // Mock data methods for development
  Future<List<Branch>> getMockBranches() async {
    await Future.delayed(const Duration(seconds: 1)); // Simulate network delay
    
    return [
      const Branch(
        id: 'downtown',
        name: 'Downtown',
        address: '123 Main St, Downtown',
        phone: '(555) 123-4567',
        hours: '24/7',
        amenities: ['Pool', 'Sauna', 'Personal Training'],
        latitude: 40.7128,
        longitude: -74.0060,
        occupancyPercentage: 75,
      ),
      const Branch(
        id: 'westside',
        name: 'Westside',
        address: '456 West Ave, Westside',
        phone: '(555) 234-5678',
        hours: '5AM - 11PM',
        amenities: ['Pool', 'Group Classes'],
        latitude: 40.7589,
        longitude: -73.9851,
        occupancyPercentage: 60,
      ),
      const Branch(
        id: 'north-campus',
        name: 'North Campus',
        address: '789 University Blvd, North Campus',
        phone: '(555) 345-6789',
        hours: '6AM - 10PM',
        amenities: ['Student Discounts', 'Study Areas'],
        latitude: 40.7505,
        longitude: -73.9934,
        occupancyPercentage: 45,
      ),
      const Branch(
        id: 'eastside',
        name: 'Eastside',
        address: '321 East St, Eastside',
        phone: '(555) 456-7890',
        hours: '24/7',
        amenities: ['Sauna', 'Personal Training', 'Childcare'],
        latitude: 40.7282,
        longitude: -73.7949,
        occupancyPercentage: 85,
      ),
    ];
  }

  Future<List<Machine>> getMockMachines(String branchId, String category) async {
    await Future.delayed(const Duration(milliseconds: 500)); // Simulate network delay
    
    final machines = <Machine>[];
    
    switch (category.toLowerCase()) {
      case 'legs':
        machines.addAll([
          Machine(
            machineId: 'leg_press_001',
            name: 'Leg Press Machine',
            category: EquipmentCategory.legs,
            status: MachineStatus.available,
            location: branchId,
            branchId: branchId,
            lastUpdated: DateTime.now(),
          ),
          Machine(
            machineId: 'squat_rack_001',
            name: 'Squat Rack',
            category: EquipmentCategory.legs,
            status: MachineStatus.occupied,
            location: branchId,
            branchId: branchId,
            lastUpdated: DateTime.now(),
            estimatedFreeTime: '10 mins',
          ),
          Machine(
            machineId: 'leg_curl_001',
            name: 'Leg Curl Machine',
            category: EquipmentCategory.legs,
            status: MachineStatus.available,
            location: branchId,
            branchId: branchId,
            lastUpdated: DateTime.now(),
          ),
        ]);
        break;
      case 'chest':
        machines.addAll([
          Machine(
            machineId: 'bench_press_001',
            name: 'Bench Press',
            category: EquipmentCategory.chest,
            status: MachineStatus.occupied,
            location: branchId,
            branchId: branchId,
            lastUpdated: DateTime.now(),
            estimatedFreeTime: '15 mins',
          ),
          Machine(
            machineId: 'chest_fly_001',
            name: 'Chest Fly Machine',
            category: EquipmentCategory.chest,
            status: MachineStatus.available,
            location: branchId,
            branchId: branchId,
            lastUpdated: DateTime.now(),
          ),
        ]);
        break;
      case 'back':
        machines.addAll([
          Machine(
            machineId: 'lat_pulldown_001',
            name: 'Lat Pulldown',
            category: EquipmentCategory.back,
            status: MachineStatus.available,
            location: branchId,
            branchId: branchId,
            lastUpdated: DateTime.now(),
          ),
          Machine(
            machineId: 'back_extension_001',
            name: 'Back Extension',
            category: EquipmentCategory.back,
            status: MachineStatus.occupied,
            location: branchId,
            branchId: branchId,
            lastUpdated: DateTime.now(),
            estimatedFreeTime: '5 mins',
          ),
        ]);
        break;
      case 'cardio':
        machines.addAll([
          Machine(
            machineId: 'treadmill_001',
            name: 'Treadmill',
            category: EquipmentCategory.cardio,
            status: MachineStatus.available,
            location: branchId,
            branchId: branchId,
            lastUpdated: DateTime.now(),
          ),
          Machine(
            machineId: 'elliptical_001',
            name: 'Elliptical',
            category: EquipmentCategory.cardio,
            status: MachineStatus.available,
            location: branchId,
            branchId: branchId,
            lastUpdated: DateTime.now(),
          ),
          Machine(
            machineId: 'bike_001',
            name: 'Stationary Bike',
            category: EquipmentCategory.cardio,
            status: MachineStatus.occupied,
            location: branchId,
            branchId: branchId,
            lastUpdated: DateTime.now(),
            estimatedFreeTime: '20 mins',
          ),
        ]);
        break;
      case 'arms':
        machines.addAll([
          Machine(
            machineId: 'bicep_curl_001',
            name: 'Bicep Curl Machine',
            category: EquipmentCategory.arms,
            status: MachineStatus.available,
            location: branchId,
            branchId: branchId,
            lastUpdated: DateTime.now(),
          ),
          Machine(
            machineId: 'tricep_extension_001',
            name: 'Tricep Extension',
            category: EquipmentCategory.arms,
            status: MachineStatus.offline,
            location: branchId,
            branchId: branchId,
            lastUpdated: DateTime.now(),
          ),
        ]);
        break;
    }
    
    return machines;
  }
}
