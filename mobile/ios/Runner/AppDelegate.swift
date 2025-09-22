import Flutter
import UIKit
// import GoogleMaps  // Temporarily disabled until API key is configured

@main
@objc class AppDelegate: FlutterAppDelegate {
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    // Configure Google Maps
    // TODO: Add your Google Maps API key here
    // Uncomment the line below and add your API key:
    // GMSServices.provideAPIKey("YOUR_API_KEY_HERE")
    
    GeneratedPluginRegistrant.register(with: self)
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }
}
