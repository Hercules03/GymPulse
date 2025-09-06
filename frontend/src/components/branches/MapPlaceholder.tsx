import React from 'react';
import { MapPin } from 'lucide-react';

export default function MapPlaceholder() {
  return (
    <div className="w-full h-full bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg flex items-center justify-center">
      <div className="text-center">
        <MapPin className="w-16 h-16 text-blue-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-700 mb-2">Interactive Map</h3>
        <p className="text-sm text-gray-500 max-w-xs">
          Map integration will show branch locations and real-time availability
        </p>
      </div>
    </div>
  );
}