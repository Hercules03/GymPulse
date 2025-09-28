package com.gympulse.gympulse_mobile

import android.content.Context
import android.graphics.Color
import android.view.View
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.GoogleMap
import com.google.android.gms.maps.MapView
import com.google.android.gms.maps.OnMapReadyCallback
import com.google.android.gms.maps.model.*
import io.flutter.plugin.common.BinaryMessenger
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import io.flutter.plugin.common.StandardMessageCodec
import io.flutter.plugin.platform.PlatformView
import io.flutter.plugin.platform.PlatformViewFactory

class GoogleMapsMapView(
    context: Context,
    id: Int,
    creationParams: Map<String?, Any?>?,
    private val binaryMessenger: BinaryMessenger
) : PlatformView, OnMapReadyCallback, NativeMapApi, GoogleMap.OnMarkerClickListener, GoogleMap.OnMapClickListener {

    private val mapView: MapView = MapView(context)
    private var googleMap: GoogleMap? = null
    private val flutterApi: NativeMapFlutterApi = NativeMapFlutterApi(binaryMessenger)
    private val markers: MutableMap<String, Marker> = mutableMapOf()
    private var isMapReady = false

    init {
        mapView.onCreate(null)
        mapView.getMapAsync(this)

        // Setup Pigeon API
        NativeMapApi.setUp(binaryMessenger, this)
    }

    override fun getView(): View = mapView

    override fun dispose() {
        mapView.onDestroy()
    }

    // MARK: - OnMapReadyCallback

    override fun onMapReady(map: GoogleMap) {
        googleMap = map
        isMapReady = true

        // Configure map
        map.setOnMarkerClickListener(this)
        map.setOnMapClickListener(this)

        // Notify Flutter that map is ready
        flutterApi.onMapReady { result ->
            // Handle result if needed
        }
    }

    // MARK: - GoogleMap.OnMarkerClickListener

    override fun onMarkerClick(marker: Marker): Boolean {
        // Find marker ID
        for ((id, mapMarker) in markers) {
            if (mapMarker == marker) {
                flutterApi.onMarkerTapped(id) { result ->
                    // Handle result if needed
                }
                return true
            }
        }
        return false
    }

    // MARK: - GoogleMap.OnMapClickListener

    override fun onMapClick(latLng: LatLng) {
        val position = PigeonLatLng(latLng.latitude, latLng.longitude)
        flutterApi.onMapTapped(position) { result ->
            // Handle result if needed
        }
    }

    // MARK: - NativeMapApi Implementation

    override fun initializeMap() {
        // Map initialization is handled in onMapReady
    }

    override fun setMarkers(markers: List<PigeonMarker>) {
        val map = googleMap ?: return

        // Clear existing markers
        map.clear()
        this.markers.clear()

        // Add new markers
        for (marker in markers) {
            val latLng = LatLng(marker.position.latitude, marker.position.longitude)

            val markerOptions = MarkerOptions()
                .position(latLng)
                .title(marker.title)
                .snippet(marker.snippet)

            // Set marker color based on the color enum
            when (marker.color) {
                MarkerColor.RED -> markerOptions.icon(BitmapDescriptorFactory.defaultMarker(BitmapDescriptorFactory.HUE_RED))
                MarkerColor.GREEN -> markerOptions.icon(BitmapDescriptorFactory.defaultMarker(BitmapDescriptorFactory.HUE_GREEN))
                MarkerColor.BLUE -> markerOptions.icon(BitmapDescriptorFactory.defaultMarker(BitmapDescriptorFactory.HUE_BLUE))
                MarkerColor.ORANGE -> markerOptions.icon(BitmapDescriptorFactory.defaultMarker(BitmapDescriptorFactory.HUE_ORANGE))
                MarkerColor.PURPLE -> markerOptions.icon(BitmapDescriptorFactory.defaultMarker(BitmapDescriptorFactory.HUE_VIOLET))
            }

            val googleMarker = map.addMarker(markerOptions)
            googleMarker?.let {
                this.markers[marker.id] = it
            }
        }
    }

    override fun moveCamera(position: PigeonCameraPosition) {
        val map = googleMap ?: return
        val latLng = LatLng(position.target.latitude, position.target.longitude)
        val cameraPosition = CameraPosition.Builder()
            .target(latLng)
            .zoom(position.zoom.toFloat())
            .build()
        map.animateCamera(CameraUpdateFactory.newCameraPosition(cameraPosition))
    }

    override fun fitToBounds(bounds: PigeonLatLngBounds, padding: Double) {
        val map = googleMap ?: return
        val southwest = LatLng(bounds.southwest.latitude, bounds.southwest.longitude)
        val northeast = LatLng(bounds.northeast.latitude, bounds.northeast.longitude)
        val latLngBounds = LatLngBounds(southwest, northeast)
        map.animateCamera(CameraUpdateFactory.newLatLngBounds(latLngBounds, padding.toInt()))
    }

    override fun setUserLocationEnabled(enabled: Boolean) {
        val map = googleMap ?: return
        try {
            map.isMyLocationEnabled = enabled
        } catch (e: SecurityException) {
            // Handle permission not granted
        }
    }

    override fun setMapType(mapType: String) {
        val map = googleMap ?: return
        when (mapType) {
            "satellite" -> map.mapType = GoogleMap.MAP_TYPE_SATELLITE
            "hybrid" -> map.mapType = GoogleMap.MAP_TYPE_HYBRID
            "terrain" -> map.mapType = GoogleMap.MAP_TYPE_TERRAIN
            else -> map.mapType = GoogleMap.MAP_TYPE_NORMAL
        }
    }

    // Lifecycle methods
    fun onStart() {
        mapView.onStart()
    }

    fun onResume() {
        mapView.onResume()
    }

    fun onPause() {
        mapView.onPause()
    }

    fun onStop() {
        mapView.onStop()
    }

    fun onDestroy() {
        mapView.onDestroy()
    }

    fun onSaveInstanceState(outState: android.os.Bundle) {
        mapView.onSaveInstanceState(outState)
    }

    fun onLowMemory() {
        mapView.onLowMemory()
    }
}

class GoogleMapsMapViewFactory(private val messenger: BinaryMessenger) : PlatformViewFactory(StandardMessageCodec.INSTANCE) {

    override fun create(context: Context, viewId: Int, args: Any?): PlatformView {
        val creationParams = args as Map<String?, Any?>?
        return GoogleMapsMapView(context, viewId, creationParams, messenger)
    }
}