import Flutter
import UIKit
import MapKit

class MapKitMapView: NSObject, FlutterPlatformView, NativeMapApi, MKMapViewDelegate {
    private var _view: MKMapView
    private let flutterApi: NativeMapFlutterApi
    private var markers: [String: MKPointAnnotation] = [:]

    init(
        frame: CGRect,
        viewIdentifier viewId: Int64,
        arguments args: Any?,
        binaryMessenger messenger: FlutterBinaryMessenger
    ) {
        _view = MKMapView()
        flutterApi = NativeMapFlutterApi(binaryMessenger: messenger)

        super.init()

        _view.delegate = self
        _view.isScrollEnabled = true
        _view.isZoomEnabled = true
        _view.isRotateEnabled = true
        _view.isPitchEnabled = false
        _view.showsUserLocation = false

        // Setup tap gesture
        let tapGesture = UITapGestureRecognizer(target: self, action: #selector(mapTapped))
        _view.addGestureRecognizer(tapGesture)

        // Register with Pigeon
        NativeMapApiSetup.setUp(binaryMessenger: messenger, api: self)

        // Notify Flutter that map is ready
        flutterApi.onMapReady { result in
            // Handle result if needed
        }
    }

    func view() -> UIView {
        return _view
    }

    @objc private func mapTapped(_ gesture: UITapGestureRecognizer) {
        let touchPoint = gesture.location(in: _view)
        let coordinate = _view.convert(touchPoint, toCoordinateFrom: _view)

        let position = PigeonLatLng(
            latitude: coordinate.latitude,
            longitude: coordinate.longitude
        )

        flutterApi.onMapTapped(position: position) { result in
            // Handle result if needed
        }
    }

    // MARK: - NativeMapApi Implementation

    func initializeMap() throws {
        // Map is already initialized in init
    }

    func setMarkers(markers: [PigeonMarker]) throws {
        // Remove existing markers
        let existingAnnotations = _view.annotations.filter { !($0 is MKUserLocation) }
        _view.removeAnnotations(existingAnnotations)
        self.markers.removeAll()

        // Add new markers
        for marker in markers {
            let annotation = MKPointAnnotation()
            annotation.coordinate = CLLocationCoordinate2D(
                latitude: marker.position.latitude,
                longitude: marker.position.longitude
            )
            annotation.title = marker.title
            annotation.subtitle = marker.snippet

            _view.addAnnotation(annotation)
            self.markers[marker.id] = annotation
        }
    }

    func moveCamera(position: PigeonCameraPosition) throws {
        let coordinate = CLLocationCoordinate2D(
            latitude: position.target.latitude,
            longitude: position.target.longitude
        )

        let span = MKCoordinateSpan(
            latitudeDelta: 0.01 / position.zoom,
            longitudeDelta: 0.01 / position.zoom
        )

        let region = MKCoordinateRegion(center: coordinate, span: span)
        _view.setRegion(region, animated: true)
    }

    func fitToBounds(bounds: PigeonLatLngBounds, padding: Double) throws {
        let coordinate1 = CLLocationCoordinate2D(
            latitude: bounds.southwest.latitude,
            longitude: bounds.southwest.longitude
        )
        let coordinate2 = CLLocationCoordinate2D(
            latitude: bounds.northeast.latitude,
            longitude: bounds.northeast.longitude
        )

        let region = MKCoordinateRegion(
            center: CLLocationCoordinate2D(
                latitude: (coordinate1.latitude + coordinate2.latitude) / 2,
                longitude: (coordinate1.longitude + coordinate2.longitude) / 2
            ),
            span: MKCoordinateSpan(
                latitudeDelta: abs(coordinate2.latitude - coordinate1.latitude) * 1.1,
                longitudeDelta: abs(coordinate2.longitude - coordinate1.longitude) * 1.1
            )
        )

        _view.setRegion(region, animated: true)
    }

    func setUserLocationEnabled(enabled: Bool) throws {
        _view.showsUserLocation = enabled
    }

    func setMapType(mapType: String) throws {
        switch mapType {
        case "satellite":
            _view.mapType = .satellite
        case "hybrid":
            _view.mapType = .hybrid
        case "terrain":
            _view.mapType = .standard
        default:
            _view.mapType = .standard
        }
    }

    // MARK: - MKMapViewDelegate

    func mapView(_ mapView: MKMapView, viewFor annotation: MKAnnotation) -> MKAnnotationView? {
        guard !(annotation is MKUserLocation) else {
            return nil
        }

        let identifier = "MarkerAnnotation"
        var annotationView = mapView.dequeueReusableAnnotationView(withIdentifier: identifier) as? MKMarkerAnnotationView

        if annotationView == nil {
            annotationView = MKMarkerAnnotationView(annotation: annotation, reuseIdentifier: identifier)
            annotationView?.canShowCallout = true
        } else {
            annotationView?.annotation = annotation
        }

        // Find the marker color by matching annotation
        for (id, markerAnnotation) in markers {
            if markerAnnotation === annotation {
                // This would require storing color info in the annotation
                // For now, use default color
                annotationView?.markerTintColor = .red
                break
            }
        }

        return annotationView
    }

    func mapView(_ mapView: MKMapView, didSelect view: MKAnnotationView) {
        guard let annotation = view.annotation, !(annotation is MKUserLocation) else {
            return
        }

        // Find marker ID
        for (id, markerAnnotation) in markers {
            if markerAnnotation === annotation {
                flutterApi.onMarkerTapped(markerId: id) { result in
                    // Handle result if needed
                }
                break
            }
        }
    }

    func mapView(_ mapView: MKMapView, regionDidChangeAnimated animated: Bool) {
        let position = PigeonCameraPosition(
            target: PigeonLatLng(
                latitude: mapView.region.center.latitude,
                longitude: mapView.region.center.longitude
            ),
            zoom: calculateZoomLevel(from: mapView.region.span)
        )

        flutterApi.onCameraPositionChanged(position: position) { result in
            // Handle result if needed
        }
    }

    private func calculateZoomLevel(from span: MKCoordinateSpan) -> Double {
        // Approximate zoom level calculation
        return max(1.0, min(20.0, log2(360.0 / span.latitudeDelta)))
    }
}

class MapKitMapViewFactory: NSObject, FlutterPlatformViewFactory {
    private var messenger: FlutterBinaryMessenger

    init(messenger: FlutterBinaryMessenger) {
        self.messenger = messenger
        super.init()
    }

    func create(
        withFrame frame: CGRect,
        viewIdentifier viewId: Int64,
        arguments args: Any?
    ) -> FlutterPlatformView {
        return MapKitMapView(
            frame: frame,
            viewIdentifier: viewId,
            arguments: args,
            binaryMessenger: messenger
        )
    }

    func createArgsCodec() -> FlutterMessageCodec & NSObjectProtocol {
        return FlutterStandardMessageCodec.sharedInstance()
    }
}