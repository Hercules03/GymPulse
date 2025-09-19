import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, MapPin, Clock, Activity } from 'lucide-react';
import { gymService } from '@/services/gymService';
import { useMachineUpdates } from '@/hooks/useWebSocket';

import StatusBadge from '@/components/machine/StatusBadge';
import NotificationButton from '@/components/machine/NotificationButton';
import PredictionChip from '@/components/machine/PredictionChip';
import AvailabilityHeatmap from '@/components/machine/AvailabilityHeatmap';
import MLValidationPage from '@/components/test/MLValidationPage';
import { getMachineIcon } from '@/components/icons/MachineIcons';
import { getCategoryIcon } from '@/components/icons/CategoryIcons';

interface Machine {
  machineId: string;
  name: string;
  status: 'free' | 'occupied' | 'unknown' | 'offline';
  lastUpdate: number | null;
  category: string;
  gymId: string;
  type: string;
  alertEligible: boolean;
}

// Category icons are now handled by getCategoryIcon function

export default function MachinesPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const searchParams = new URLSearchParams(location.search);
  const branchId = searchParams.get('branch') || '';
  const category = searchParams.get('category') || 'legs';

  const [machines, setMachines] = useState<Machine[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usageData, setUsageData] = useState([]);
  const [branchName, setBranchName] = useState<string>('');

  // App mode state - read from localStorage and listen for changes
  const [appMode, setAppMode] = useState<'demo' | 'development'>(() => {
    const saved = localStorage.getItem('gym-pulse-app-mode');
    return (saved as 'demo' | 'development') || 'demo';
  });

  // Listen for localStorage changes (when mode is changed in other pages)
  useEffect(() => {
    const handleStorageChange = () => {
      const saved = localStorage.getItem('gym-pulse-app-mode');
      const newMode = (saved as 'demo' | 'development') || 'demo';
      console.log('🔄 Mode change detected in Machines page:', { currentMode: appMode, newMode, saved });
      if (newMode !== appMode) {
        console.log('📱 Updating app mode from', appMode, 'to', newMode);
        setAppMode(newMode);
      }
    };

    // Listen for storage events (changes from other tabs/pages)
    window.addEventListener('storage', handleStorageChange);

    // Also listen for custom events (for same-tab changes)
    window.addEventListener('appModeChanged', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('appModeChanged', handleStorageChange);
    };
  }, [appMode]);

  // WebSocket integration for real-time updates
  const webSocket = useMachineUpdates({
    branches: branchId ? [branchId] : [],
    categories: [category]
  });

  const categoryName = category.charAt(0).toUpperCase() + category.slice(1);

  // Helper function to get branch name from branchId
  const getBranchName = (branchId: string) => {
    console.log('getBranchName called with branchId:', branchId);
    if (!branchId) {
      console.log('branchId is empty, returning default');
      return 'Unknown Branch';
    }
    const branchMap: Record<string, string> = {
      'hk-central': 'Central Branch',
      'hk-causeway': 'Causeway Bay Branch',
      'central': 'Central Branch',
      'causeway': 'Causeway Bay Branch'
    };
    const result = branchMap[branchId.toLowerCase()] || branchId;
    console.log('getBranchName result:', result);
    return result;
  };

  useEffect(() => {
    console.log('🚀 loadMachines useEffect triggered:', { branchId, category, appMode });

    const loadMachines = async () => {
      setIsLoading(true);
      setError(null);

      // Set branch name from branchId
      setBranchName(getBranchName(branchId));

      try {
        // Load machines for this branch and category
        console.log('Loading machines for:', { branchId, category });
        const response = await gymService.getMachines(branchId, category);
        console.log('Machines response:', response);
        console.log('Machines array:', response.machines);
        if (response.machines && response.machines.length > 0) {
          console.log('First machine data:', response.machines[0]);
          response.machines.forEach((machine, index) => {
            console.log(`Machine ${index}:`, machine.machineId, 'status:', machine.status);
          });
        }
        setMachines(response.machines || []);
        
        // Load usage data for the first machine (for heatmap example)
        if (response.machines && response.machines.length > 0) {
          const firstMachine = response.machines[0];
          console.log('📊 Loading usage data for first machine:', firstMachine.machineId, 'in mode:', appMode);

          if (appMode === 'development') {
            console.log('🔬 Using DEVELOPMENT mode - loading real API data');
            // Load real API data in development mode
            try {
              const historyResponse = await gymService.getMachineHistory(firstMachine.machineId);

              // Transform history data to heatmap format
              const transformedData = (historyResponse.history || []).map((bin, index) => ({
                hour: new Date(bin.timestamp * 1000).getHours(),
                usage_percentage: Math.round(bin.occupancyRatio * 100),
                timestamp: new Date(bin.timestamp * 1000).toISOString(),
                predicted_free_time: null
              }));

              setUsageData(transformedData);
            } catch (historyError) {
              console.warn('Could not load machine history:', historyError);
              setUsageData([]);
            }
          } else {
            console.log('🎭 Using DEMO mode - generating mock data');
            // Use realistic mock data in demo mode
            const mockData = Array.from({ length: 24 }, (_, hour) => {
              // Create realistic patterns: low usage at night, peaks during gym hours
              let baseUsage;
              if (hour >= 6 && hour <= 9) {
                // Morning peak
                baseUsage = 60 + Math.random() * 30; // 60-90%
              } else if (hour >= 12 && hour <= 14) {
                // Lunch peak
                baseUsage = 50 + Math.random() * 30; // 50-80%
              } else if (hour >= 17 && hour <= 21) {
                // Evening peak
                baseUsage = 70 + Math.random() * 25; // 70-95%
              } else if (hour >= 22 || hour <= 5) {
                // Night/early morning - low usage
                baseUsage = 5 + Math.random() * 15; // 5-20%
              } else {
                // Mid-day moderate usage
                baseUsage = 25 + Math.random() * 35; // 25-60%
              }

              return {
                hour,
                usage_percentage: Math.round(baseUsage),
                timestamp: new Date(Date.now() - (24 - hour) * 60 * 60 * 1000).toISOString(),
                predicted_free_time: null
              };
            });

            console.log('Generated mock data for demo mode:', mockData);
            setUsageData(mockData);
          }
        }
        
      } catch (error) {
        console.error('Error loading machines:', error);
        console.error('Error details:', { branchId, category, error });
        setError(`Failed to load machine data: ${error.message}`);
        setMachines([]);
      }
      
      setIsLoading(false);
    };

    loadMachines();
  }, [branchId, category, appMode]); // Add appMode dependency to reload data when mode changes

  // Update machines with real-time WebSocket data
  useEffect(() => {
    console.log('🔄 WebSocket update received:', webSocket.lastUpdate);
    if (webSocket.lastUpdate && webSocket.lastUpdate.type === 'machine_update') {
      const update = webSocket.lastUpdate;
      console.log('📡 Processing machine update:', update);
      console.log('🎯 Looking for machine:', update.machineId);
      console.log('🔍 Current machines:', machines.map(m => m.machineId));

      setMachines(prevMachines => {
        const updatedMachines = prevMachines.map(machine =>
          machine.machineId === update.machineId
            ? { ...machine, status: update.status, lastUpdate: update.timestamp }
            : machine
        );
        console.log('✅ Updated machines:', updatedMachines);
        console.log('🔄 Machine state change:', {
          machineId: update.machineId,
          oldStatus: prevMachines.find(m => m.machineId === update.machineId)?.status,
          newStatus: update.status,
          oldTimestamp: prevMachines.find(m => m.machineId === update.machineId)?.lastUpdate,
          newTimestamp: update.timestamp
        });
        return [...updatedMachines]; // Force new array reference
      });
    }
  }, [webSocket.lastUpdate]);

  const getStatusCounts = () => {
    const free = machines.filter(m => m.status === 'free').length;
    const occupied = machines.filter(m => m.status === 'occupied').length;
    const unknown = machines.filter(m => m.status === 'unknown').length;
    return { free, occupied, unknown, total: machines.length };
  };

  const statusCounts = getStatusCounts();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className="bg-white rounded-lg p-6 shadow-sm h-48">
                  <div className="space-y-3">
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    <div className="h-2 bg-gray-200 rounded w-full"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-lg font-medium mb-2">{error}</div>
          <button
            onClick={() => window.location.reload()}
            className="text-blue-600 hover:text-blue-700 underline"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 px-6 py-6 sticky top-0 z-10">
        <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div className="flex items-center gap-3">
                {getCategoryIcon(category, { size: 32, className: "text-blue-600" })}
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">{categoryName} Equipment</h1>
                  <div className="flex items-center gap-2 text-gray-500 text-sm">
                    <MapPin className="w-4 h-4" />
                    <span>{branchName}</span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* WebSocket Status & Stats */}
            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className="text-lg font-bold text-gray-900">
                  {statusCounts.free}/{statusCounts.total} Available
                </div>
                <div className="text-sm text-gray-500">
                  {statusCounts.occupied} occupied • {statusCounts.unknown} unknown
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  webSocket.isConnected ? 'bg-green-500' : 
                  webSocket.isConnecting ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'
                }`}></div>
                <span className="text-xs text-gray-500">
                  {webSocket.isConnected ? 'Live' : webSocket.isConnecting ? 'Connecting...' : 'Offline'}
                </span>
              </div>
            </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Machine Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
          {machines.map((machine, index) => (
            <motion.div
              key={machine.machineId}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: index * 0.05 }}
              className="bg-white rounded-lg shadow-sm border border-gray-200 px-4 py-4 hover:shadow-md transition-all duration-200 flex flex-col h-full"
            >
              <div className="flex items-start justify-between mb-4 gap-3">
                <div className="flex items-start gap-3 min-w-0 flex-1">
                  <div className="mt-1 flex-shrink-0">
                    {getCategoryIcon(category, { size: 32, className: "text-gray-600" })}
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="font-semibold text-gray-900 text-lg mb-1 leading-tight">{machine.name}</h3>
                    <p className="text-sm text-gray-500 leading-tight">{machine.type.replace('-', ' ').replace(/\b\w/g, c => c.toUpperCase())}</p>
                  </div>
                </div>
                <div className="flex-shrink-0">
                  <StatusBadge status={machine.status} />
                </div>
              </div>

              <div className="space-y-3 mb-4">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Activity className="w-4 h-4" />
                  <span>ID: {machine.machineId}</span>
                </div>
                
                {machine.lastUpdate && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Clock className="w-4 h-4" />
                    <span>Updated: {new Date(machine.lastUpdate * 1000).toLocaleTimeString()}</span>
                  </div>
                )}
              </div>

              <div className="mt-auto space-y-3">
                <PredictionChip
                  machineId={machine.machineId}
                  status={machine.status}
                />

                <div className="flex flex-col gap-2 w-full">
                  <NotificationButton
                    machineId={machine.machineId}
                    status={machine.status}
                  />
                  <Link
                    to={`/machine-detail?id=${machine.machineId}&branch=${branchId}&category=${category}`}
                    className="w-full px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors text-center"
                  >
                    Details
                  </Link>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* ML Analytics (Development Mode Only) */}
        {appMode === 'development' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="mb-8"
          >
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <h2 className="text-lg font-semibold text-gray-900">ML Analytics & Debugging</h2>
                <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">Development Mode</span>
              </div>
              <MLValidationPage />
            </div>
          </motion.div>
        )}


        {machines.length === 0 && !isLoading && (
          <div className="text-center py-12">
            <div className="mx-auto mb-4">
              {getCategoryIcon(category, { size: 64, className: "text-gray-300 mx-auto" })}
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No machines found</h3>
            <p className="text-gray-500">
              No {category} equipment available at {branchName}.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}