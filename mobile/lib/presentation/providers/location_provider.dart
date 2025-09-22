import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:logger/logger.dart';

class LocationProvider extends ChangeNotifier {
  final Logger _logger = Logger();

  // State
  Position? _currentPosition;
  String? _currentAddress;
  bool _isLoading = false;
  bool _hasPermission = false;
  String? _errorMessage;
  StreamSubscription<Position>? _positionStreamSubscription;

  // Getters
  Position? get currentPosition => _currentPosition;
  String? get currentAddress => _currentAddress;
  bool get isLoading => _isLoading;
  bool get hasPermission => _hasPermission;
  String? get errorMessage => _errorMessage;
  bool get hasLocation => _currentPosition != null;

  LocationProvider() {
    _checkPermissionStatus();
  }

  Future<void> _checkPermissionStatus() async {
    final status = await Permission.location.status;
    _hasPermission = status.isGranted;
    notifyListeners();
  }

  Future<bool> requestPermission() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final status = await Permission.location.request();
      _hasPermission = status.isGranted;
      
      if (_hasPermission) {
        _logger.i('Location permission granted');
        await getCurrentLocation();
      } else {
        _errorMessage = 'Location permission denied';
        _logger.w('Location permission denied');
      }
    } catch (e) {
      _errorMessage = e.toString();
      _logger.e('Error requesting location permission: $e');
    }

    _isLoading = false;
    notifyListeners();
    return _hasPermission;
  }

  Future<void> getCurrentLocation() async {
    if (!_hasPermission) {
      _errorMessage = 'Location permission not granted';
      notifyListeners();
      return;
    }

    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      // Check if location services are enabled
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        _errorMessage = 'Location services are disabled';
        _isLoading = false;
        notifyListeners();
        return;
      }

      // Get current position
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 10),
      );

      _currentPosition = position;
      await _getAddressFromPosition(position);
      
      _logger.i('Current location: ${position.latitude}, ${position.longitude}');
    } catch (e) {
      _errorMessage = e.toString();
      _logger.e('Error getting current location: $e');
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> _getAddressFromPosition(Position position) async {
    try {
      final placemarks = await placemarkFromCoordinates(
        position.latitude,
        position.longitude,
      );

      if (placemarks.isNotEmpty) {
        final placemark = placemarks.first;
        _currentAddress = _formatAddress(placemark);
        _logger.d('Address: $_currentAddress');
      }
    } catch (e) {
      _logger.e('Error getting address from position: $e');
    }
  }

  String _formatAddress(Placemark placemark) {
    final parts = <String>[];
    
    if (placemark.street != null && placemark.street!.isNotEmpty) {
      parts.add(placemark.street!);
    }
    if (placemark.locality != null && placemark.locality!.isNotEmpty) {
      parts.add(placemark.locality!);
    }
    if (placemark.administrativeArea != null && placemark.administrativeArea!.isNotEmpty) {
      parts.add(placemark.administrativeArea!);
    }
    if (placemark.country != null && placemark.country!.isNotEmpty) {
      parts.add(placemark.country!);
    }

    return parts.join(', ');
  }

  void startLocationUpdates() {
    if (!_hasPermission) return;

    _positionStreamSubscription?.cancel();
    _positionStreamSubscription = Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10, // Update every 10 meters
      ),
    ).listen(
      (position) {
        _currentPosition = position;
        _getAddressFromPosition(position);
        notifyListeners();
      },
      onError: (error) {
        _logger.e('Location stream error: $error');
        _errorMessage = error.toString();
        notifyListeners();
      },
    );
  }

  void stopLocationUpdates() {
    _positionStreamSubscription?.cancel();
    _positionStreamSubscription = null;
  }

  double calculateDistance(double lat, double lng) {
    if (_currentPosition == null) return 0.0;
    
    return Geolocator.distanceBetween(
      _currentPosition!.latitude,
      _currentPosition!.longitude,
      lat,
      lng,
    ) / 1000; // Convert to kilometers
  }

  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _positionStreamSubscription?.cancel();
    _logger.d('LocationProvider disposed');
    super.dispose();
  }
}
