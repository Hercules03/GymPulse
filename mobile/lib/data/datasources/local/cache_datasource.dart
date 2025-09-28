import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:logger/logger.dart';
import '../../../domain/entities/branch.dart';
import '../../../domain/entities/machine.dart';
import '../../../core/constants/storage_keys.dart';

class CacheDataSource {
  final Logger _logger = Logger();
  late SharedPreferences _prefs;

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  Future<void> cacheBranches(List<Branch> branches) async {
    try {
      await init();
      final branchesJson = branches.map((branch) => branch.toJson()).toList();
      await _prefs.setString(StorageKeys.branchesCache, jsonEncode(branchesJson));
      _logger.d('Cached ${branches.length} branches');
    } catch (e) {
      _logger.e('Error caching branches: $e');
    }
  }

  Future<List<Branch>?> getCachedBranches() async {
    try {
      await init();
      final branchesJson = _prefs.getString(StorageKeys.branchesCache);
      if (branchesJson != null) {
        final List<dynamic> branchesList = jsonDecode(branchesJson);
        return branchesList.map((json) => Branch.fromJson(json)).toList();
      }
    } catch (e) {
      _logger.e('Error getting cached branches: $e');
    }
    return null;
  }

  Future<void> cacheMachines(List<Machine> machines, String branchId, String category) async {
    try {
      await init();
      final key = '${StorageKeys.machinesCache}_${branchId}_$category';
      final machinesJson = machines.map((machine) => machine.toJson()).toList();
      await _prefs.setString(key, jsonEncode(machinesJson));
      _logger.d('Cached ${machines.length} machines for $category in $branchId');
    } catch (e) {
      _logger.e('Error caching machines: $e');
    }
  }

  Future<List<Machine>?> getCachedMachines(String branchId, String category) async {
    try {
      await init();
      final key = '${StorageKeys.machinesCache}_${branchId}_$category';
      final machinesJson = _prefs.getString(key);
      if (machinesJson != null) {
        final List<dynamic> machinesList = jsonDecode(machinesJson);
        return machinesList.map((json) => Machine.fromJson(json)).toList();
      }
    } catch (e) {
      _logger.e('Error getting cached machines: $e');
    }
    return null;
  }

  Future<void> clearCache() async {
    try {
      await init();
      await _prefs.remove(StorageKeys.branchesCache);
      await _prefs.remove(StorageKeys.machinesCache);
      _logger.d('Cache cleared');
    } catch (e) {
      _logger.e('Error clearing cache: $e');
    }
  }
}
