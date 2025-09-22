import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geolocator/geolocator.dart';

import '../../../core/constants/app_constants.dart';
import '../../../domain/entities/branch.dart';

class BranchMap extends StatefulWidget {
  final List<Branch> branches;
  final Position? currentPosition;
  final Function(Branch)? onBranchSelected;

  const BranchMap({
    super.key,
    required this.branches,
    this.currentPosition,
    this.onBranchSelected,
  });

  @override
  State<BranchMap> createState() => _BranchMapState();
}

class _BranchMapState extends State<BranchMap> {
  final Completer<GoogleMapController> _controller = Completer();
  Set<Marker> _markers = {};
  LatLng? _userLocation;
  Branch? _selectedBranch;

  @override
  void initState() {
    super.initState();
    _initializeMap();
  }

  @override
  void didUpdateWidget(BranchMap oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.branches != widget.branches ||
        oldWidget.currentPosition != widget.currentPosition) {
      _initializeMap();
    }
  }

  void _initializeMap() {
    _updateUserLocation();
    _createMarkers();
  }

  void _updateUserLocation() {
    if (widget.currentPosition != null) {
      _userLocation = LatLng(
        widget.currentPosition!.latitude,
        widget.currentPosition!.longitude,
      );
    }
  }

  void _createMarkers() {
    final Set<Marker> markers = {};

    // Add user location marker if available
    if (_userLocation != null) {
      markers.add(
        Marker(
          markerId: const MarkerId('user_location'),
          position: _userLocation!,
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
          infoWindow: const InfoWindow(
            title: 'Your Location',
          ),
        ),
      );
    }

    // Add branch markers
    for (final branch in widget.branches) {
      final position = LatLng(
        branch.coordinates.latitude,
        branch.coordinates.longitude,
      );

      // Determine marker color based on availability
      double hue = BitmapDescriptor.hueRed; // Default to red (busy)
      if (branch.availabilityPercentage > 50) {
        hue = BitmapDescriptor.hueGreen; // Green for good availability
      } else if (branch.availabilityPercentage > 25) {
        hue = BitmapDescriptor.hueOrange; // Orange for moderate availability
      }

      markers.add(
        Marker(
          markerId: MarkerId(branch.id),
          position: position,
          icon: BitmapDescriptor.defaultMarkerWithHue(hue),
          infoWindow: InfoWindow(
            title: branch.name,
            snippet: '${branch.availabilityPercentage.round()}% available',
            onTap: () => _onMarkerTapped(branch),
          ),
          onTap: () => _onMarkerTapped(branch),
        ),
      );
    }

    setState(() {
      _markers = markers;
    });
  }

  void _onMarkerTapped(Branch branch) {
    setState(() {
      _selectedBranch = branch;
    });

    if (widget.onBranchSelected != null) {
      widget.onBranchSelected!(branch);
    }
  }

  LatLng _getInitialCameraPosition() {
    if (_userLocation != null) {
      return _userLocation!;
    }

    if (widget.branches.isNotEmpty) {
      final firstBranch = widget.branches.first;
      return LatLng(
        firstBranch.coordinates.latitude,
        firstBranch.coordinates.longitude,
      );
    }

    // Default to Hong Kong
    return const LatLng(
      AppConstants.defaultLatitude,
      AppConstants.defaultLongitude,
    );
  }

  double _getInitialZoom() {
    if (widget.branches.length <= 1) {
      return 16.0; // Zoom in for single location
    }
    return AppConstants.defaultMapZoom; // Default zoom for multiple locations
  }

  Future<void> _fitAllMarkers() async {
    if (widget.branches.isEmpty) return;

    final GoogleMapController controller = await _controller.future;

    double minLat = widget.branches.first.coordinates.latitude;
    double maxLat = widget.branches.first.coordinates.latitude;
    double minLng = widget.branches.first.coordinates.longitude;
    double maxLng = widget.branches.first.coordinates.longitude;

    for (final branch in widget.branches) {
      minLat = minLat < branch.coordinates.latitude ? minLat : branch.coordinates.latitude;
      maxLat = maxLat > branch.coordinates.latitude ? maxLat : branch.coordinates.latitude;
      minLng = minLng < branch.coordinates.longitude ? minLng : branch.coordinates.longitude;
      maxLng = maxLng > branch.coordinates.longitude ? maxLng : branch.coordinates.longitude;
    }

    // Include user location in bounds if available
    if (_userLocation != null) {
      minLat = minLat < _userLocation!.latitude ? minLat : _userLocation!.latitude;
      maxLat = maxLat > _userLocation!.latitude ? maxLat : _userLocation!.latitude;
      minLng = minLng < _userLocation!.longitude ? minLng : _userLocation!.longitude;
      maxLng = maxLng > _userLocation!.longitude ? maxLng : _userLocation!.longitude;
    }

    await controller.animateCamera(
      CameraUpdate.newLatLngBounds(
        LatLngBounds(
          southwest: LatLng(minLat, minLng),
          northeast: LatLng(maxLat, maxLng),
        ),
        100.0, // padding
      ),
    );
  }

  Future<void> _goToUserLocation() async {
    if (_userLocation == null) return;

    final GoogleMapController controller = await _controller.future;
    await controller.animateCamera(
      CameraUpdate.newLatLngZoom(_userLocation!, 16.0),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Temporarily show error widget until Google Maps API key is configured
        _buildMapErrorWidget(context, 'Google Maps API key not configured'),

        // Custom controls
        Positioned(
          top: 16,
          right: 16,
          child: Column(
            children: [
              // Fit all markers button
              if (widget.branches.length > 1)
                FloatingActionButton(
                  mini: true,
                  backgroundColor: Colors.white,
                  foregroundColor: Colors.black87,
                  onPressed: _fitAllMarkers,
                  tooltip: 'Show all branches',
                  child: const Icon(Icons.zoom_out_map),
                ),

              if (widget.branches.length > 1)
                const SizedBox(height: 8),

              // Go to user location button
              if (_userLocation != null)
                FloatingActionButton(
                  mini: true,
                  backgroundColor: Colors.white,
                  foregroundColor: Colors.black87,
                  onPressed: _goToUserLocation,
                  tooltip: 'Go to my location',
                  child: const Icon(Icons.my_location),
                ),
            ],
          ),
        ),

        // Legend
        Positioned(
          bottom: 16,
          left: 16,
          child: Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(8),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 4,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Availability',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                _buildLegendItem(
                  color: Colors.green,
                  label: '50%+ available',
                ),
                const SizedBox(height: 4),
                _buildLegendItem(
                  color: Colors.orange,
                  label: '25-50% available',
                ),
                const SizedBox(height: 4),
                _buildLegendItem(
                  color: Colors.red,
                  label: '<25% available',
                ),
                if (_userLocation != null) ...[
                  const SizedBox(height: 4),
                  _buildLegendItem(
                    color: Colors.blue,
                    label: 'Your location',
                  ),
                ],
              ],
            ),
          ),
        ),

        // Selected branch info card
        if (_selectedBranch != null)
          Positioned(
            bottom: 120,
            left: 16,
            right: 16,
            child: Card(
              elevation: 4,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            _selectedBranch!.name,
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close),
                          onPressed: () {
                            setState(() {
                              _selectedBranch = null;
                            });
                          },
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: _selectedBranch!.availabilityPercentage > 50
                                ? Colors.green[100]
                                : _selectedBranch!.availabilityPercentage > 25
                                    ? Colors.orange[100]
                                    : Colors.red[100],
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            '${_selectedBranch!.availabilityPercentage.round()}% available',
                            style: TextStyle(
                              color: _selectedBranch!.availabilityPercentage > 50
                                  ? Colors.green[800]
                                  : _selectedBranch!.availabilityPercentage > 25
                                      ? Colors.orange[800]
                                      : Colors.red[800],
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                        ),
                        const Spacer(),
                        Text(
                          '${_selectedBranch!.availableMachines}/${_selectedBranch!.totalMachines} machines',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                    if (_selectedBranch!.address != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        _selectedBranch!.address!,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildLegendItem({
    required Color color,
    required String label,
  }) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 6),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }

  Widget _buildMapErrorWidget(BuildContext context, String error) {
    return Container(
      color: Colors.grey[200],
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.map_outlined,
                size: 64,
                color: Colors.grey[400],
              ),
              const SizedBox(height: 16),
              Text(
                'Map Unavailable',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: Colors.grey[600],
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Google Maps is not configured.\n\nTo enable maps:\n1. Get a Google Maps API key\n2. Add it to AppDelegate.swift\n3. Uncomment the API key line',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.grey[500],
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () {
                  // Show branch list instead
                  if (widget.branches.isNotEmpty) {
                    widget.onBranchSelected?.call(widget.branches.first);
                  }
                },
                icon: const Icon(Icons.list),
                label: const Text('View Branch List'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}