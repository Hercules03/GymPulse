import React, { useState } from 'react';
import { Map, Marker, Overlay } from 'pigeon-maps';
import { type Branch } from '@/services/gymService';

// Custom marker component for availability-based styling
interface CustomMarkerProps {
  anchor: [number, number];
  availability: number;
  branch: Branch;
  isSelected: boolean;
  onClick: () => void;
}

function CustomMarker({ anchor, availability, branch, isSelected, onClick }: CustomMarkerProps) {
  const getMarkerColor = (availability: number) => {
    if (availability >= 70) return '#10b981'; // green
    if (availability >= 40) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  const color = getMarkerColor(availability);
  const size = isSelected ? 50 : 42; // Slightly larger for better text fit
  const availabilityText = Math.round(availability).toString();

  // Adjust font size based on text length
  const getFontSize = (text: string) => {
    if (text.length >= 3) return '10px'; // 100%
    if (text.length === 2) return '11px'; // 89%
    return '12px'; // 5%
  };

  return (
    <div
      onClick={onClick}
      className="flex items-center justify-center cursor-pointer transform transition-all duration-200 hover:scale-110"
      style={{
        width: size,
        height: size,
        marginLeft: -size / 2,
        marginTop: -size / 2,
      }}
    >
      <div
        className="rounded-full border-3 border-white shadow-lg flex items-center justify-center"
        style={{
          backgroundColor: color,
          width: size - 6, // More space for text
          height: size - 6,
          minWidth: size - 6, // Ensure consistent size
          minHeight: size - 6,
        }}
      >
        <span
          className="text-white font-bold leading-none select-none"
          style={{
            fontSize: getFontSize(availabilityText),
            lineHeight: '1',
            textAlign: 'center',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '100%',
            height: '100%',
          }}
        >
          {availabilityText}%
        </span>
      </div>
    </div>
  );
}

// Popup overlay component
interface PopupOverlayProps {
  anchor: [number, number];
  branch: Branch;
  onClose: () => void;
  onViewDetails: () => void;
}

function PopupOverlay({ anchor, branch, onClose, onViewDetails }: PopupOverlayProps) {
  const availability = branch.availability || 0;

  return (
    <Overlay anchor={anchor} offset={[120, 79]}>
      <div className="bg-white rounded-lg shadow-xl border border-gray-200 p-4 min-w-[280px] max-w-[320px] relative">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Branch info */}
        <h3 className="font-semibold text-gray-900 mb-3 pr-6">{branch.name}</h3>

        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Availability:</span>
            <span className={`text-sm font-medium ${
              availability >= 70 ? 'text-green-600' :
              availability >= 40 ? 'text-yellow-600' :
              'text-red-600'
            }`}>
              {Math.round(availability)}%
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Available:</span>
            <span className="text-sm font-medium text-gray-900">
              {branch.availableMachines || 0}/{branch.totalMachines || 0} machines
            </span>
          </div>
          {branch.distance && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Distance:</span>
              <span className="text-sm font-medium text-gray-900">
                {branch.distance} km • {branch.eta} min
              </span>
            </div>
          )}
        </div>

        {/* Categories breakdown */}
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="text-xs text-gray-500 mb-2">Equipment Categories:</div>
          <div className="space-y-1">
            {Object.entries(branch.categories || {}).map(([category, data]) => (
              <div key={category} className="flex justify-between items-center">
                <span className="text-xs text-gray-600 capitalize">{category}:</span>
                <span className="text-xs font-medium text-gray-900">
                  {data.free}/{data.total} free
                </span>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={onViewDetails}
          className="w-full mt-4 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
        >
          View Details
        </button>
      </div>
    </Overlay>
  );
}

interface InteractiveMapProps {
  branches?: Branch[];
  selectedBranch?: string | null;
  onBranchSelect?: (branchId: string) => void;
}

export default function InteractiveMap({
  branches = [],
  selectedBranch,
  onBranchSelect
}: InteractiveMapProps) {
  const [showPopup, setShowPopup] = useState<string | null>(null);

  // Default center for Hong Kong
  const defaultCenter: [number, number] = [22.3193, 114.1694];

  if (branches.length === 0) {
    return (
      <div className="w-full h-full bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-blue-400 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-700 mb-2">Loading Map</h3>
          <p className="text-sm text-gray-500 max-w-xs">
            Preparing to show branch locations and availability
          </p>
        </div>
      </div>
    );
  }

  // Calculate map center and zoom based on branches
  const getMapBounds = () => {
    if (branches.length === 0) return { center: defaultCenter, zoom: 11 };

    const lats = branches.map(b => b.coordinates.lat);
    const lons = branches.map(b => b.coordinates.lon);

    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);

    const centerLat = (minLat + maxLat) / 2;
    const centerLon = (minLon + maxLon) / 2;

    // Calculate zoom level based on bounds (simple approximation)
    const latDiff = maxLat - minLat;
    const lonDiff = maxLon - minLon;
    const maxDiff = Math.max(latDiff, lonDiff);

    let zoom = 11;
    if (maxDiff < 0.01) zoom = 14;
    else if (maxDiff < 0.05) zoom = 12;
    else if (maxDiff < 0.1) zoom = 11;
    else zoom = 10;

    return { center: [centerLat, centerLon] as [number, number], zoom };
  };

  const { center, zoom } = getMapBounds();

  const handleMarkerClick = (branchId: string) => {
    setShowPopup(branchId);
    onBranchSelect?.(branchId);
  };

  const handleClosePopup = () => {
    setShowPopup(null);
  };

  const handleViewDetails = (branchId: string) => {
    setShowPopup(null);
    onBranchSelect?.(branchId);
  };

  return (
    <div className="w-full h-full rounded-lg overflow-hidden shadow-sm bg-gray-100">
      <Map
        height="100%"
        center={center}
        zoom={zoom}
        dprs={[1, 2]}
        provider={(x, y, z) => {
          // Use CartoDB Positron - minimal light style
          return `https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/${z}/${x}/${y}.png`
        }}
        attribution={
          <span>
            © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> © <a href="https://carto.com/attributions" target="_blank" rel="noopener noreferrer">CARTO</a>
          </span>
        }
      >
        {/* Render markers */}
        {branches.map((branch) => {
          const availability = branch.availability || 0;
          const isSelected = selectedBranch === branch.id;

          return (
            <Marker
              key={branch.id}
              anchor={[branch.coordinates.lat, branch.coordinates.lon]}
            >
              <CustomMarker
                anchor={[branch.coordinates.lat, branch.coordinates.lon]}
                availability={availability}
                branch={branch}
                isSelected={isSelected}
                onClick={() => handleMarkerClick(branch.id)}
              />
            </Marker>
          );
        })}

        {/* Render popup overlay */}
        {showPopup && (
          (() => {
            const branch = branches.find(b => b.id === showPopup);
            if (!branch) return null;

            return (
              <PopupOverlay
                anchor={[branch.coordinates.lat, branch.coordinates.lon]}
                branch={branch}
                onClose={handleClosePopup}
                onViewDetails={() => handleViewDetails(branch.id)}
              />
            );
          })()
        )}
      </Map>
    </div>
  );
}