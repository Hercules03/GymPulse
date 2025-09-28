import '../../domain/entities/branch.dart';
import '../../domain/entities/machine.dart';
import '../../domain/repositories/gym_repository.dart';
import '../../shared/enums/machine_status.dart';
import '../../shared/enums/equipment_category.dart';
import '../datasources/remote/gym_api_service.dart';
import '../models/api/branch_response.dart';
import '../models/api/machine_response.dart';

/// Implementation of GymRepository using remote API
class GymRepositoryImpl implements GymRepository {
  const GymRepositoryImpl({
    required this.apiService,
  });

  final GymApiService apiService;

  @override
  Future<List<Branch>> getBranches() async {
    try {
      final response = await apiService.getBranches();
      return response.branches.map(_mapBranchModelToDomain).toList();
    } catch (e) {
      throw GymRepositoryException('Failed to fetch branches: $e');
    }
  }

  @override
  Future<PeakHoursData> getBranchPeakHours(String branchId) async {
    try {
      final response = await apiService.getBranchPeakHours(branchId);
      return PeakHoursData(
        branchId: response.branchId,
        currentHour: response.currentHour,
        currentOccupancy: response.currentOccupancy,
        peakHours: response.peakHours,
        confidence: response.confidence,
        occupancyForecast: response.occupancyForecast,
        nextPeakIn: response.nextPeakIn,
        totalMachines: response.totalMachines,
        generatedAt: response.generatedAt,
      );
    } catch (e) {
      throw GymRepositoryException('Failed to fetch peak hours: $e');
    }
  }

  @override
  Future<List<Machine>> getMachines(String branchId, String category) async {
    try {
      final response = await apiService.getMachines(branchId, category);
      return response.machines.map(_mapMachineModelToDomain).toList();
    } catch (e) {
      throw GymRepositoryException('Failed to fetch machines: $e');
    }
  }

  @override
  Future<MachineHistory> getMachineHistory(String machineId, {String range = '24h'}) async {
    try {
      final response = await apiService.getMachineHistory(machineId, range);
      return MachineHistory(
        machineId: response.machineId,
        history: response.history.map((bin) => HistoryBin(
          timestamp: bin.timestamp,
          occupancyRatio: bin.occupancyRatio,
          freeCount: bin.freeCount,
          totalCount: bin.totalCount,
          status: bin.status,
        )).toList(),
        timeRange: TimeRange(
          start: response.timeRange.start,
          end: response.timeRange.end,
          duration: response.timeRange.duration,
        ),
        forecast: BasicForecast(
          likelyFreeIn30m: response.forecast.likelyFreeIn30m,
          confidence: response.forecast.confidence,
          reason: response.forecast.reason,
        ),
        totalBins: response.totalBins,
      );
    } catch (e) {
      throw GymRepositoryException('Failed to fetch machine history: $e');
    }
  }

  @override
  Future<MachineForecast> getMachineForecast(String machineId, {int minutes = 30}) async {
    try {
      final response = await apiService.getMachineForecast(machineId, minutes);
      return MachineForecast(
        machineId: response.machineId,
        forecast: DetailedForecast(
          likelyFreeIn30m: response.forecast.likelyFreeIn30m,
          classification: response.forecast.classification,
          displayText: response.forecast.displayText,
          confidence: response.forecast.confidence,
          probability: response.forecast.probability,
          peakHours: response.forecast.peakHours,
        ),
        success: response.success,
      );
    } catch (e) {
      throw GymRepositoryException('Failed to fetch machine forecast: $e');
    }
  }

  @override
  Future<bool> healthCheck() async {
    try {
      final response = await apiService.healthCheck();
      return response.status.toLowerCase() == 'ok' || response.status.toLowerCase() == 'healthy';
    } catch (e) {
      return false;
    }
  }

  // Private mapping methods
  Branch _mapBranchModelToDomain(BranchModel branchModel) {
    return Branch(
      id: branchModel.id,
      name: branchModel.name,
      coordinates: Coordinates(
        latitude: branchModel.coordinates.lat,
        longitude: branchModel.coordinates.lon,
      ),
      categories: branchModel.categories.map(
        (key, value) => MapEntry(
          key,
          CategoryData(
            free: value.free,
            total: value.total,
          ),
        ),
      ),
      address: branchModel.address,
      phone: branchModel.phone,
      hours: branchModel.hours,
      amenities: branchModel.amenities,
    );
  }

  Machine _mapMachineModelToDomain(MachineModel machineModel) {
    return Machine(
      machineId: machineModel.machineId,
      name: machineModel.name,
      status: MachineStatus.fromString(machineModel.status),
      category: EquipmentCategory.fromString(machineModel.category),
      gymId: machineModel.gymId,
      lastUpdate: machineModel.lastUpdate,
      lastChange: machineModel.lastChange,
      coordinates: machineModel.coordinates != null
          ? MachineCoordinates(
              latitude: machineModel.coordinates!.lat,
              longitude: machineModel.coordinates!.lon,
            )
          : null,
      alertEligible: machineModel.alertEligible,
      type: machineModel.type,
      estimatedFreeTime: machineModel.estimatedFreeTime,
    );
  }
}

/// Custom exception for repository errors
class GymRepositoryException implements Exception {
  const GymRepositoryException(this.message);

  final String message;

  @override
  String toString() => 'GymRepositoryException: $message';
}