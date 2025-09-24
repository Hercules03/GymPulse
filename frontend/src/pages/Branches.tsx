import { useState, useEffect, useMemo } from 'react';
import { gymService } from '@/services/gymService';
import { Branch } from '@/entities';
import { extractCategoriesFromBranches } from '@/utils/categoryUtils';
import BranchList from '@/components/branches/BranchList';
import BranchSearch from '@/components/branches/BranchSearch';
import InteractiveMap from '@/components/branches/MapPlaceholder';
import { useMachineUpdates } from '@/hooks/useWebSocket';
import { useGeolocation } from '@/hooks/useGeolocation';
import { Settings, X } from 'lucide-react';

export default function BranchesPage() {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedBranch, setSelectedBranch] = useState<string | null>(null);
  const [isBranchSheetOpen, setIsBranchSheetOpen] = useState(false);

  // Handle escape key to close bottom sheet
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isBranchSheetOpen) {
        setIsBranchSheetOpen(false);
      }
    };

    if (isBranchSheetOpen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent background scrolling
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isBranchSheetOpen]);

  // App mode state
  const [appMode, setAppMode] = useState<'demo' | 'development'>(() => {
    const saved = localStorage.getItem('gym-pulse-app-mode');
    return (saved as 'demo' | 'development') || 'demo';
  });

  const toggleAppMode = () => {
    const newMode = appMode === 'demo' ? 'development' : 'demo';
    setAppMode(newMode);
    localStorage.setItem('gym-pulse-app-mode', newMode);

    // Dispatch custom event to notify other components
    window.dispatchEvent(new CustomEvent('appModeChanged'));
  };

  // Get user location for map centering
  const userLocation = useGeolocation();

  // WebSocket integration for real-time updates - dynamically subscribe to loaded branches
  const webSocket = useMachineUpdates({
    branches: branches.map(branch => branch.id),
    categories: extractCategoriesFromBranches(branches)
  });

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await gymService.getBranches();
        // Convert gymService.Branch to entities.Branch format
        const convertedBranches = response.branches.map(branch => ({
          ...branch,
          address: branch.name + ', Hong Kong', // Add missing address field
          availability: undefined,
          availableMachines: undefined,
          totalMachines: undefined,
          distance: undefined,
          eta: undefined,
          phone: undefined,
          hours: undefined,
          amenities: undefined
        }));
        setBranches(convertedBranches);
        
        if (response.warnings) {
          console.warn('API warnings:', response.warnings);
        }
      } catch (error) {
        console.error('Error loading branches:', error);
        setError('Failed to load branch data. Please check your connection.');
        setBranches([]);
      }
      setIsLoading(false);
    };
    loadData();
  }, []);

  // Update branch data with real-time machine status changes
  useEffect(() => {
    if (webSocket.lastUpdate && webSocket.lastUpdate.type === 'machine_update') {
      const update = webSocket.lastUpdate;
      
      setBranches(prevBranches => {
        if (!prevBranches || !Array.isArray(prevBranches)) {
          return prevBranches || [];
        }
        
        return prevBranches.map(branch => {
          if (branch.id === update.gymId) {
            // Update the specific category counts based on machine status change
            const updatedCategories = { ...branch.categories };
            const category = updatedCategories[update.category];
            
            if (category) {
              // Get current machine status from WebSocket to calculate new counts
              const allMachineStatuses = webSocket.getAllMachineStatuses();
              const branchCategoryMachines = allMachineStatuses.filter(
                m => m.gymId === branch.id && m.category === update.category
              );
              
              // Recalculate free count based on current machine statuses
              const freeCount = branchCategoryMachines.filter(m => m.status === 'free').length;
              
              updatedCategories[update.category] = {
                ...category,
                free: Math.max(0, freeCount) // Ensure non-negative
              };
            }
            
            return {
              ...branch,
              categories: updatedCategories
            };
          }
          return branch;
        });
      });
    }
  }, [webSocket.lastUpdate, webSocket.getAllMachineStatuses]);

  const enrichedBranches = useMemo(() => {
    if (!branches || !Array.isArray(branches)) {
      return [];
    }

    // Helper function to calculate distance using Haversine formula
    const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number) => {
      const R = 6371; // Radius of the Earth in kilometers
      const dLat = (lat2 - lat1) * Math.PI / 180;
      const dLon = (lon2 - lon1) * Math.PI / 180;
      const a =
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon/2) * Math.sin(dLon/2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
      return R * c; // Distance in kilometers
    };

    return branches.map(branch => {
      // Calculate totals across all categories
      const categoryNames = Object.keys(branch.categories || {});
      const totalMachines = categoryNames.reduce((sum, cat) => sum + (branch.categories?.[cat]?.total || 0), 0);
      const availableMachines = categoryNames.reduce((sum, cat) => sum + (branch.categories?.[cat]?.free || 0), 0);
      const availability = totalMachines > 0 ? (availableMachines / totalMachines) * 100 : 0;

      // Calculate real distance if user location is available
      let distance: string;
      let eta: number;

      if (userLocation.latitude && userLocation.longitude && !userLocation.error) {
        const realDistance = calculateDistance(
          userLocation.latitude,
          userLocation.longitude,
          branch.coordinates?.lat || 0,
          branch.coordinates?.lon || 0
        );
        distance = realDistance.toFixed(1);
        eta = Math.round(realDistance * 5 + 3); // Rough ETA calculation (5 min per km + 3 min base)
      } else {
        // Fallback to mock distance
        distance = (branch.id.length % 5 + 1).toFixed(1);
        eta = Math.round(parseFloat(distance) * 5 + 3);
      }

      return {
        ...branch,
        totalMachines,
        availableMachines,
        availability,
        distance,
        eta,
        // Add address field for compatibility
        address: branch.name + ', Hong Kong',
      };
    });
  }, [branches, userLocation.latitude, userLocation.longitude, userLocation.error]);

  const filteredBranches = useMemo(() => {
    return enrichedBranches.filter(branch =>
      branch.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      branch.address.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [enrichedBranches, searchTerm]);

  const handleBranchSelect = (branchId: string) => {
    setSelectedBranch(branchId);
  };

  const handleBranchNavigate = (branchId: string) => {
    console.log('🌟 Navigating to branch:', branchId);
    
    // Find the branch name for better user feedback
    const branch = enrichedBranches.find(b => b.id === branchId);
    const branchName = branch?.name || 'branch';
    
    // Show quick feedback for mobile users
    if (window.innerWidth < 1024 || ('ontouchstart' in window)) {
      // Create a brief visual feedback
      const feedback = document.createElement('div');
      feedback.textContent = `Opening ${branchName}...`;
      feedback.className = 'fixed top-4 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg z-50 text-sm font-medium';
      document.body.appendChild(feedback);
      
      // Remove feedback after a short time
      setTimeout(() => {
        if (document.body.contains(feedback)) {
          document.body.removeChild(feedback);
        }
      }, 1500);
    }
    
    // Navigate directly to the branch dashboard
    window.location.href = `/dashboard/${branchId}`;
  };

  return (
    <div style={{ height: 'calc(100vh - 80px)' }} className="flex flex-col">
      {/* Page Header - Mobile Optimized */}
      <div className="bg-white border-b border-gray-100 shrink-0">
        <div className="flex items-center justify-between px-4 lg:px-6 py-4 lg:py-6">
          <div>
            <h1 className="text-xl lg:text-2xl font-bold text-gray-900 tracking-tight">Find a Gym</h1>
            <p className="text-gray-500 text-xs lg:text-sm mt-1">Select a branch to see details and availability</p>
          </div>
          {/* App Mode Toggle - Desktop Only */}
          <div className="hidden lg:flex items-center">
            <button
              onClick={toggleAppMode}
              className={`flex items-center justify-center w-8 h-8 rounded-lg transition-colors ${
                appMode === 'development'
                  ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
              title={`Currently in ${appMode} mode. Click to switch to ${appMode === 'demo' ? 'development' : 'demo'} mode`}
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>

        </div>
      </div>

      {/* Mobile-First Layout */}
      <div className="flex-1 flex flex-col lg:flex-row relative overflow-hidden">
        {/* Desktop: Side Panel */}
        <div className="hidden lg:flex lg:flex-1 lg:flex-col bg-white">
          <div className="p-6 shrink-0">
            <BranchSearch searchTerm={searchTerm} onSearchChange={setSearchTerm} />
          </div>


          <div className="flex-1 overflow-y-auto px-6 pb-6">
            {error ? (
              <div className="flex items-center justify-center p-8">
                <div className="text-center">
                  <div className="text-red-500 text-sm font-medium mb-2">{error}</div>
                  <button
                    onClick={() => window.location.reload()}
                    className="text-blue-600 hover:text-blue-700 text-sm underline"
                  >
                    Try Again
                  </button>
                </div>
              </div>
            ) : (
              <BranchList branches={filteredBranches} isLoading={isLoading} />
            )}
          </div>
        </div>

        {/* Map - Always Visible on Mobile */}
        <div className="flex-1 lg:w-[40%] lg:shrink-0">
          <InteractiveMap
            branches={filteredBranches}
            selectedBranch={selectedBranch}
            onBranchSelect={handleBranchSelect}
            onBranchNavigate={handleBranchNavigate}
          />
        </div>


        {/* Mobile Bottom Sheet Pull-up Indicator - Full Width */}
        <div className="lg:hidden fixed bottom-0 left-0 right-0 z-40 pointer-events-none">
          <button
            onClick={() => setIsBranchSheetOpen(true)}
            className="pointer-events-auto w-full bg-white rounded-t-2xl px-6 py-4 shadow-2xl border-t border-l border-r border-gray-200 transition-all duration-200 hover:bg-gray-50 active:bg-gray-100"
          >
            <div className="flex flex-col items-center gap-2">
              <div className="w-12 h-1.5 bg-gray-400 rounded-full" />
              <div className="text-sm text-gray-600 font-medium">
                {filteredBranches.length} gym{filteredBranches.length !== 1 ? 's' : ''} • Tap to search
              </div>
            </div>
          </button>
        </div>

        {/* Mobile Bottom Sheet */}
        {isBranchSheetOpen && (
          <div className="lg:hidden fixed inset-0 z-50 bg-black bg-opacity-50 backdrop-blur-sm flex flex-col justify-end transition-all duration-300">
            {/* Touch to close overlay */}
            <div
              className="flex-1"
              onClick={() => setIsBranchSheetOpen(false)}
            />

            {/* Bottom Sheet */}
            <div className="bg-white rounded-t-2xl max-h-[75vh] flex flex-col transform transition-transform duration-300 translate-y-0 shadow-2xl">
              {/* Drag Handle - Clickable to close */}
              <div className="flex justify-center pt-4 pb-2">
                <button
                  onClick={() => setIsBranchSheetOpen(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  aria-label="Close search"
                >
                  <div className="w-10 h-1 bg-gray-400 rounded-full hover:bg-gray-500 transition-colors" />
                </button>
              </div>

              {/* Sheet Header */}
              <div className="flex items-center justify-between px-6 pb-4">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Find a Gym</h2>
                  <p className="text-sm text-gray-500 mt-1">
                    {filteredBranches.length} branch{filteredBranches.length !== 1 ? 'es' : ''} found
                  </p>
                </div>
                {/* Keep X button for desktop users who might expect it */}
                <button
                  onClick={() => setIsBranchSheetOpen(false)}
                  className="hidden lg:flex p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Search */}
              <div className="px-6 pb-4 border-b border-gray-100">
                <BranchSearch searchTerm={searchTerm} onSearchChange={setSearchTerm} />
              </div>

              {/* Branch List */}
              <div className="flex-1 overflow-y-auto px-6 pb-safe-area-inset-bottom">
                {error ? (
                  <div className="flex items-center justify-center p-8">
                    <div className="text-center">
                      <div className="text-red-500 text-sm font-medium mb-2">{error}</div>
                      <button
                        onClick={() => window.location.reload()}
                        className="text-blue-600 hover:text-blue-700 text-sm underline"
                      >
                        Try Again
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="py-4">
                    <BranchList
                      branches={filteredBranches}
                      isLoading={isLoading}
                      onBranchNavigate={() => setIsBranchSheetOpen(false)}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}