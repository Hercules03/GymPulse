import 'dart:async';
import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geolocator/geolocator.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/constants/map_styles.dart';
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
  String _mapStyle = MapStyles.minimal;

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

  Future<void> _initializeMap() async {
    _updateUserLocation();
    await _createMarkers();
  }

  void _updateUserLocation() {
    if (widget.currentPosition != null) {
      _userLocation = LatLng(
        widget.currentPosition!.latitude,
        widget.currentPosition!.longitude,
      );
    }
  }

  Future<void> _createMarkers() async {
    final Set<Marker> markers = {};

    // Add user location marker if available
    if (_userLocation != null) {
      final userIcon = await _createSimpleMarkerIcon(
        const Color(0xFF7BB3F0), // Muted blue with less saturation
        12.0,
      );
      markers.add(
        Marker(
          markerId: const MarkerId('user_location'),
          position: _userLocation!,
          icon: userIcon,
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

      // Determine marker color based on availability with less saturation
      Color markerColor = const Color(0xFFE57373); // Muted red (busy)
      if (branch.availabilityPercentage > 50) {
        markerColor = const Color(0xFF81C784); // Muted green (good availability)
      } else if (branch.availabilityPercentage > 25) {
        markerColor = const Color(0xFFFFB74D); // Muted orange (moderate availability)
      }

      final branchIcon = await _createSimpleMarkerIcon(markerColor, 16.0);
      markers.add(
        Marker(
          markerId: MarkerId(branch.id),
          position: position,
          icon: branchIcon,
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

  Future<void> _changeMapStyle() async {
    final GoogleMapController controller = await _controller.future;

    // Cycle through different styles
    String newStyle;
    switch (_mapStyle) {
      case MapStyles.minimal:
        newStyle = MapStyles.silver;
        break;
      case MapStyles.silver:
        newStyle = MapStyles.retro;
        break;
      case MapStyles.retro:
      default:
        newStyle = MapStyles.minimal;
        break;
    }

    setState(() {
      _mapStyle = newStyle;
    });

    await controller.setMapStyle(_mapStyle);
  }

  Future<BitmapDescriptor> _createSimpleMarkerIcon(Color color, double size) async {
    final ui.PictureRecorder pictureRecorder = ui.PictureRecorder();
    final Canvas canvas = Canvas(pictureRecorder);
    final Paint paint = Paint()..color = color;
    final Paint strokePaint = Paint()
      ..color = Colors.white
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;

    // Draw simple circle marker
    final double radius = size;
    canvas.drawCircle(Offset(radius, radius), radius - 1, paint);
    canvas.drawCircle(Offset(radius, radius), radius - 1, strokePaint);

    // Convert to image
    final ui.Picture picture = pictureRecorder.endRecording();
    final ui.Image image = await picture.toImage((radius * 2).toInt(), (radius * 2).toInt());
    final ByteData? byteData = await image.toByteData(format: ui.ImageByteFormat.png);
    final Uint8List bytes = byteData!.buffer.asUint8List();

    return BitmapDescriptor.fromBytes(bytes);
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Google Maps with error handling
        Builder(
          builder: (context) {
            try {
              return GoogleMap(
                mapType: MapType.normal,
                initialCameraPosition: CameraPosition(
                  target: _getInitialCameraPosition(),
                  zoom: _getInitialZoom(),
                ),
                onMapCreated: (GoogleMapController controller) async {
                  _controller.complete(controller);
                  // Apply minimal map style
                  await controller.setMapStyle(_mapStyle);
                  // Fit all markers after a short delay to ensure map is ready
                  Future.delayed(const Duration(milliseconds: 500), _fitAllMarkers);
                },
                markers: _markers,
                myLocationEnabled: widget.currentPosition != null,
                myLocationButtonEnabled: false,
                zoomControlsEnabled: false,
                compassEnabled: false,
                buildingsEnabled: false,
                trafficEnabled: false,
                rotateGesturesEnabled: false,
                tiltGesturesEnabled: false,
                onTap: (LatLng position) {
                  setState(() {
                    _selectedBranch = null;
                  });
                },
              );
            } catch (e) {
              // Fallback UI when Google Maps fails to load
              return _buildMapErrorWidget(context, 'Google Maps failed to load: ${e.toString()}');
            }
          },
        ),

        // Custom controls
        Positioned(
          top: 16,
          right: 16,
          child: Column(
            children: [
              // Map style button
              FloatingActionButton(
                mini: true,
                backgroundColor: Colors.white,
                foregroundColor: Colors.black87,
                onPressed: _changeMapStyle,
                tooltip: 'Change map style',
                child: const Icon(Icons.palette_outlined),
              ),

              const SizedBox(height: 8),

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