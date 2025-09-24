import { useState, useEffect, useLayoutEffect, useRef } from 'react';
import { Map, Marker, Overlay } from 'pigeon-maps';
import { Branch } from '@/entities';
import { useGeolocation } from '@/hooks/useGeolocation';

// Custom marker component for availability-based styling
interface CustomMarkerProps {
  anchor: [number, number];
  availability: number;
  branch: Branch;
  isSelected: boolean;
  onClick: () => void;
}

function CustomMarker({ availability, branch, isSelected, onClick }: CustomMarkerProps) {
  const getMarkerColor = (availability: number) => {
    if (availability >= 70) return '#10b981'; // green
    if (availability >= 40) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  const color = getMarkerColor(availability);
  const size = isSelected ? 20 : 16; // Smaller since no text needed

  return (
    <div
      className="flex items-center justify-center cursor-pointer transform transition-all duration-200 hover:scale-110 active:scale-95"
      style={{
        width: size + 8,
        height: size + 12,
        marginLeft: -(size + 8) / 2,
        marginTop: -(size + 12),
        zIndex: 2,
        position: 'relative',
        pointerEvents: 'auto',
      }}
      role="button"
      aria-label={`View ${branch.name} branch dashboard`}
      onClick={(e) => {
        console.log('🟡 Direct click on marker container!', { branchId: branch.id });
        e.stopPropagation();
        e.preventDefault();
        onClick();
      }}
    >
      <svg
        width={size + 8}
        height={size + 12}
        viewBox="0 0 24 30"
        className={`drop-shadow-lg ${isSelected ? 'ring-4 ring-blue-300 rounded-full' : ''}`}
        style={{
          filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
          zIndex: 3,
          pointerEvents: 'auto',
        }}
        onClick={(e) => {
          console.log('🔴 Pin clicked!', { branchId: branch.id });
          e.stopPropagation();
          e.preventDefault();
          onClick();
        }}
      >
        <path
          d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"
          fill={color}
          stroke="white"
          strokeWidth="1"
        />
      </svg>
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
            {Object.entries(branch.categories || {}).map(([category, data]) => {
              const categoryData = data as { free: number; total: number };
              return (
                <div key={category} className="flex justify-between items-center">
                  <span className="text-xs text-gray-600 capitalize">{category}:</span>
                  <span className="text-xs font-medium text-gray-900">
                    {categoryData.free}/{categoryData.total} free
                  </span>
                </div>
              );
            })}
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
  onBranchNavigate?: (branchId: string) => void;
}

export default function InteractiveMap({
  branches = [],
  selectedBranch,
  onBranchSelect,
  onBranchNavigate
}: InteractiveMapProps) {
  const [showPopup, setShowPopup] = useState<string | null>(null);
  const [mapHeight, setMapHeight] = useState(400);
  const [mapWidth, setMapWidth] = useState(600);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const userLocation = useGeolocation();

  // Calculate map dimensions based on container
  useLayoutEffect(() => {
    const updateMapDimensions = () => {
      if (mapContainerRef.current) {
        const containerHeight = mapContainerRef.current.clientHeight;
        const containerWidth = mapContainerRef.current.clientWidth;
        console.log('Map dimensions update:', { containerHeight, containerWidth });
        setMapHeight(containerHeight > 0 ? containerHeight : 400);
        setMapWidth(containerWidth > 0 ? containerWidth : 600);
      }
    };

    updateMapDimensions();
    window.addEventListener('resize', updateMapDimensions);

    // Use ResizeObserver if available for more accurate container size tracking
    let resizeObserver: ResizeObserver | null = null;
    if (mapContainerRef.current && window.ResizeObserver) {
      resizeObserver = new ResizeObserver(updateMapDimensions);
      resizeObserver.observe(mapContainerRef.current);
    }

    return () => {
      window.removeEventListener('resize', updateMapDimensions);
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
    };
  }, []);

  // Force recalculation after mount to handle timing issues
  useEffect(() => {
    const timers: number[] = [];
    
    // Try multiple times with increasing delays to catch when layout is ready
    [100, 250, 500].forEach(delay => {
      const timer = setTimeout(() => {
        if (mapContainerRef.current) {
          const containerHeight = mapContainerRef.current.clientHeight;
          const containerWidth = mapContainerRef.current.clientWidth;
          console.log(`Delayed map recalc (${delay}ms):`, { containerHeight, containerWidth });
          
          if (containerHeight > 0 && containerWidth > 0) {
            setMapHeight(containerHeight);
            setMapWidth(containerWidth);
          }
        }
      }, delay);
      timers.push(timer);
    });

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, []);

  // Default center for Hong Kong (Central area)
  const defaultCenter: [number, number] = [22.2819, 114.1577];

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

  // Calculate map center and zoom based on user location and branches
  const getMapBounds = () => {
    // Priority 1: If we have user location, center on that
    if (userLocation.latitude && userLocation.longitude && !userLocation.error) {
      return {
        center: [userLocation.latitude, userLocation.longitude] as [number, number],
        zoom: 14 // Higher zoom level to see precise locations
      };
    }

    // Priority 2: If we have branches, center on them
    if (branches.length > 0) {
      const lats = branches.map(b => b.coordinates?.lat || 0);
      const lons = branches.map(b => b.coordinates?.lon || 0);

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

      let zoom = 13;
      if (maxDiff < 0.01) zoom = 15;
      else if (maxDiff < 0.05) zoom = 14;
      else if (maxDiff < 0.1) zoom = 13;
      else zoom = 12;

      return { center: [centerLat, centerLon] as [number, number], zoom };
    }

    // Priority 3: Default to Hong Kong center
    return { center: defaultCenter, zoom: 13 };
  };

  const { center, zoom } = getMapBounds();

  const handleMarkerClick = (branchId: string) => {
    console.log('🔵 Marker clicked!', { branchId, onBranchNavigate: !!onBranchNavigate });
    
    // Enhanced mobile detection: check screen width AND touch capability
    const isMobile = window.innerWidth < 1024 || ('ontouchstart' in window);
    console.log('📱 Device detection:', { 
      isMobile, 
      screenWidth: window.innerWidth, 
      touchCapable: 'ontouchstart' in window 
    });

    if (isMobile && onBranchNavigate) {
      console.log('🚀 Navigating to branch dashboard:', branchId);
      // On mobile, clicking marker navigates directly to branch
      onBranchNavigate(branchId);
    } else {
      console.log('🖥️ Desktop mode: showing popup');
      // On desktop, show popup and select branch
      setShowPopup(branchId);
      onBranchSelect?.(branchId);
    }
  };

  const handleClosePopup = () => {
    setShowPopup(null);
  };

  const handleViewDetails = (branchId: string) => {
    setShowPopup(null);
    if (onBranchNavigate) {
      onBranchNavigate(branchId);
    } else {
      onBranchSelect?.(branchId);
    }
  };

  return (
    <div
      ref={mapContainerRef}
      className="w-full h-full overflow-hidden shadow-sm bg-gray-100"
      style={{
        minHeight: '400px',
        position: 'relative'
      }}
    >
      <Map
        height={mapHeight}
        width={mapWidth}
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
        {/* Render user location marker */}
        {userLocation.latitude && userLocation.longitude && !userLocation.error && (
          <Marker anchor={[userLocation.latitude, userLocation.longitude]}>
            <div className="flex items-center justify-center">
              <div className="bg-blue-500 p-2 rounded-full shadow-lg border-2 border-white">
                <svg
                  className="w-4 h-4 text-white"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                </svg>
              </div>
            </div>
          </Marker>
        )}

        {/* Render branch markers */}
        {branches.map((branch) => {
          const availability = branch.availability || 0;
          const isSelected = selectedBranch === branch.id;

          return (
            <Marker
              key={branch.id}
              anchor={[branch.coordinates?.lat || 0, branch.coordinates?.lon || 0]}
              onClick={() => {
                console.log('🎯 Marker onClick triggered!', { branchId: branch.id });
                handleMarkerClick(branch.id);
              }}
              style={{ zIndex: 1 }}
            >
              <CustomMarker
                anchor={[branch.coordinates?.lat || 0, branch.coordinates?.lon || 0]}
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
                anchor={[branch.coordinates?.lat || 0, branch.coordinates?.lon || 0]}
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