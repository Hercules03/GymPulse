import 'dart:io';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geolocator/geolocator.dart';
import 'package:url_launcher/url_launcher.dart';

/// Service for handling routing and navigation functionality
/// Uses Google Maps APIs for routing while the map display uses native implementations
class RoutingService {
  static const String _googleMapsPackage = 'com.google.android.apps.maps';
  static const String _appleMapsScheme = 'maps://';

  /// Launch navigation to a destination using the device's default maps app
  static Future<void> navigateToDestination({
    required double destinationLat,
    required double destinationLng,
    Position? currentPosition,
    String? destinationName,
  }) async {
    try {
      // Try to use device's native maps app first
      final bool launched = await _launchNativeMapsApp(
        destinationLat: destinationLat,
        destinationLng: destinationLng,
        currentPosition: currentPosition,
        destinationName: destinationName,
      );

      if (!launched) {
        // Fallback to Google Maps web
        await _launchGoogleMapsWeb(
          destinationLat: destinationLat,
          destinationLng: destinationLng,
          currentPosition: currentPosition,
          destinationName: destinationName,
        );
      }
    } catch (e) {
      throw Exception('Failed to launch navigation: $e');
    }
  }

  /// Get driving directions using Google Maps Directions API
  static Future<List<LatLng>> getDirections({
    required LatLng origin,
    required LatLng destination,
    String? apiKey,
  }) async {
    // This would integrate with Google Maps Directions API
    // For now, return a simple direct path
    return [origin, destination];
  }

  /// Calculate estimated travel time using Google Maps Distance Matrix API
  static Future<Duration?> getEstimatedTravelTime({
    required LatLng origin,
    required LatLng destination,
    String travelMode = 'driving',
    String? apiKey,
  }) async {
    // This would integrate with Google Maps Distance Matrix API
    // For now, return a rough estimate based on distance
    final double distance = Geolocator.distanceBetween(
      origin.latitude,
      origin.longitude,
      destination.latitude,
      destination.longitude,
    );

    // Rough estimates: walking ~5km/h, driving ~30km/h in city
    final double speedKmH = travelMode == 'walking' ? 5.0 : 30.0;
    final double timeHours = (distance / 1000) / speedKmH;

    return Duration(minutes: (timeHours * 60).round());
  }

  static Future<bool> _launchNativeMapsApp({
    required double destinationLat,
    required double destinationLng,
    Position? currentPosition,
    String? destinationName,
  }) async {
    String url;

    if (Platform.isIOS) {
      // iOS: Use Apple Maps
      url = _appleMapsScheme;
      if (currentPosition != null) {
        url += '?saddr=${currentPosition.latitude},${currentPosition.longitude}';
        url += '&daddr=$destinationLat,$destinationLng';
      } else {
        url += '?q=$destinationLat,$destinationLng';
      }
      if (destinationName != null) {
        url += '&q=$destinationName';
      }
    } else {
      // Android: Try Google Maps app first
      url = 'google.navigation:q=$destinationLat,$destinationLng';
      if (destinationName != null) {
        url += '&q=$destinationName';
      }
    }

    final Uri uri = Uri.parse(url);

    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
      return true;
    }

    return false;
  }

  static Future<void> _launchGoogleMapsWeb({
    required double destinationLat,
    required double destinationLng,
    Position? currentPosition,
    String? destinationName,
  }) async {
    String url = 'https://www.google.com/maps/dir/';

    if (currentPosition != null) {
      url += '${currentPosition.latitude},${currentPosition.longitude}/';
    }

    url += '$destinationLat,$destinationLng';

    if (destinationName != null) {
      url += '/@$destinationLat,$destinationLng,15z/data=!4m2!4m1!3e0';
    }

    final Uri uri = Uri.parse(url);

    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      throw Exception('Could not launch Google Maps');
    }
  }
}