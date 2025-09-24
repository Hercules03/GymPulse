
import { motion } from 'framer-motion';
import { MapPin, Shield, X } from 'lucide-react';

interface LocationPermissionRequestProps {
  onGrant: () => void;
  onDeny: () => void;
}

export default function LocationPermissionRequest({ onGrant, onDeny }: LocationPermissionRequestProps) {
  const handleGrantLocation = async () => {
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000
        });
      });
      
      // Store location for session (you can implement this in context/state)
      const location = {
        lat: position.coords.latitude,
        lon: position.coords.longitude
      };
      
      console.log('Location granted:', location);
      onGrant();
    } catch (error) {
      console.error('Location permission denied or error:', error);
      onDeny();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="absolute inset-x-4 top-4 bg-white border border-blue-200 rounded-xl shadow-lg p-4 z-10"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <MapPin className="w-4 h-4 text-blue-600" />
          </div>
          <h4 className="font-medium text-gray-900">Location Access</h4>
        </div>
        <button
          onClick={onDeny}
          className="text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-100"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <p className="text-sm text-gray-600 mb-4 leading-relaxed">
        I need your location to find the closest gym branches and calculate accurate travel times for your recommendations.
      </p>

      {/* Privacy Notice */}
      <div className="bg-gray-50 rounded-lg p-3 mb-4">
        <div className="flex items-start gap-2">
          <Shield className="w-4 h-4 text-gray-500 mt-0.5 shrink-0" />
          <div>
            <p className="text-xs text-gray-600 font-medium mb-1">Privacy Protection</p>
            <ul className="text-xs text-gray-500 space-y-1">
              <li>• Location used only for this session</li>
              <li>• No data stored permanently</li>
              <li>• Only for calculating gym distances</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={handleGrantLocation}
          className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
        >
          <MapPin className="w-4 h-4" />
          Allow Location
        </button>
        <button
          onClick={onDeny}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 text-sm font-medium transition-colors"
        >
          Skip
        </button>
      </div>

      {/* Fallback Options */}
      <p className="text-xs text-gray-500 mt-3 text-center">
        Don't want to share location? I can still help you search by gym branch name.
      </p>
    </motion.div>
  );
}