import { useState, useEffect, useMemo } from 'react';
import { gymService, type Branch } from '@/services/gymService';
import { extractCategoriesFromBranches } from '@/utils/categoryUtils';
import BranchList from '@/components/branches/BranchList';
import BranchSearch from '@/components/branches/BranchSearch';
import InteractiveMap from '@/components/branches/MapPlaceholder';
import { useMachineUpdates } from '@/hooks/useWebSocket';

export default function BranchesPage() {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedBranch, setSelectedBranch] = useState<string | null>(null);
  
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
        setBranches(response.branches);
        
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
    
    return branches.map(branch => {
      // Calculate totals across all categories
      const categoryNames = Object.keys(branch.categories);
      const totalMachines = categoryNames.reduce((sum, cat) => sum + branch.categories[cat].total, 0);
      const availableMachines = categoryNames.reduce((sum, cat) => sum + branch.categories[cat].free, 0);
      const availability = totalMachines > 0 ? (availableMachines / totalMachines) * 100 : 0;
      
      // Mock distance and ETA (would come from geolocation in real app)
      const distance = (branch.id.length % 5 + 1).toFixed(1);
      const eta = Math.round(parseFloat(distance) * 5 + 3);

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
  }, [branches]);

  const filteredBranches = useMemo(() => {
    return enrichedBranches.filter(branch =>
      branch.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      branch.address.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [enrichedBranches, searchTerm]);

  const handleBranchSelect = (branchId: string) => {
    setSelectedBranch(branchId);
    // Navigate to branch details (you can add navigation logic here)
    console.log('Selected branch:', branchId);
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 px-6 py-6 shrink-0">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Find a Gym</h1>
              <p className="text-gray-500 text-sm mt-1">Select a branch to see details and availability</p>
            </div>
            {/* WebSocket Connection Status */}
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                webSocket.isConnected ? 'bg-green-500' : 
                webSocket.isConnecting ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'
              }`}></div>
              <span className="text-xs text-gray-500">
                {webSocket.isConnected ? 'Live Updates' : 
                 webSocket.isConnecting ? 'Connecting...' : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 min-h-0">
        {/* Left Panel: List and Search */}
        <div className="flex flex-col bg-white">
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

        {/* Right Panel: Map */}
        <div className="hidden lg:block bg-gray-100 p-6">
          <InteractiveMap
            branches={filteredBranches}
            selectedBranch={selectedBranch}
            onBranchSelect={handleBranchSelect}
          />
        </div>
      </div>
    </div>
  );
}