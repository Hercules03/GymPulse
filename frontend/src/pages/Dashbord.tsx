import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { gymService } from '@/services/gymService';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { createPageUrl } from '@/utils';
import { useMachineUpdates } from '@/hooks/useWebSocket';
import { extractCategoriesFromBranches } from '@/utils/categoryUtils';

import CategoryCard from '@/components/dashboard/CategoryCard';
import QuickStats from '@/components/dashboard/QuickStats';

interface BranchCategory {
  free: number;
  total: number;
}

interface Branch {
  id: string;
  name: string;
  coordinates?: {
    lat: number;
    lon: number;
  };
  categories: {
    [category: string]: BranchCategory;
  };
}

export default function Dashboard() {
  const { branchId } = useParams<{ branchId: string }>();
  const navigate = useNavigate();
  const [branches, setBranches] = useState<Branch[]>([]);
  const [currentBranch, setCurrentBranch] = useState<Branch | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdateTime, setLastUpdateTime] = useState(new Date());
  const [peakHoursData, setPeakHoursData] = useState<{
    peakHours: string;
    confidence: string;
    currentOccupancy: number;
    occupancyForecast: { [hour: string]: number };
  } | null>(null);

  // WebSocket integration for real-time updates - subscribe to current branch only
  const webSocket = useMachineUpdates({
    branches: branchId ? [branchId] : [], // Subscribe to current branch only
    categories: currentBranch ? Object.keys(currentBranch.categories) : [] // Dynamic categories from current branch
  });

  const loadBranches = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await gymService.getBranches();
      const loadedBranches = response.branches || [];
      setBranches(loadedBranches);

      // Find and set the current branch based on URL param
      if (branchId) {
        const branch = loadedBranches.find(b => b.id === branchId);
        setCurrentBranch(branch || null);
      }

      console.log('Loaded branches from AWS API:', loadedBranches);
    } catch (error) {
      console.error('Error loading branches from AWS:', error);
      setBranches([]);
      setCurrentBranch(null);
    }
    setIsLoading(false);
  }, [branchId]);

  const loadPeakHoursData = useCallback(async (branchId: string) => {
    try {
      console.log(`🔄 Loading peak hours forecast for ${branchId}...`);
      const peakData = await gymService.getBranchPeakHours(branchId);

      setPeakHoursData({
        peakHours: peakData.peakHours,
        confidence: peakData.confidence,
        currentOccupancy: peakData.currentOccupancy,
        occupancyForecast: peakData.occupancyForecast
      });

      console.log('📊 Peak hours data loaded:', peakData);
    } catch (error) {
      console.error('Error loading peak hours data:', error);
      // Fallback to simple calculation with better data
      const fallbackPeakHours = calculatePeakHours();
      setPeakHoursData({
        peakHours: fallbackPeakHours,
        confidence: 'estimated',
        currentOccupancy: Math.floor(Math.random() * 60) + 20, // 20-80% simulated
        occupancyForecast: {}
      });
      console.log('📊 Using fallback peak hours:', fallbackPeakHours);
    }
  }, []);

  useEffect(() => {
    loadBranches();
  }, [loadBranches]);

  // Load peak hours data when branch changes
  useEffect(() => {
    if (branchId) { // Only load if we have a valid branch ID from URL
      console.log('🔄 Loading peak hours for branch:', branchId);
      loadPeakHoursData(branchId);
    }
  }, [branchId, loadPeakHoursData]);

  // Update last update time when WebSocket receives new data
  useEffect(() => {
    if (webSocket.lastUpdate) {
      setLastUpdateTime(new Date());
      console.log('🔄 Dashboard received WebSocket update:', webSocket.lastUpdate);

      // Refresh peak hours data periodically when receiving updates
      // (debounced to avoid too many API calls)
      const shouldRefreshPeakHours = Math.random() < 0.1; // 10% chance per update
      if (shouldRefreshPeakHours && branchId) {
        console.log('🔄 Refreshing peak hours forecast due to real-time data changes...');
        loadPeakHoursData(branchId);
      }
    }
  }, [webSocket.lastUpdate, branchId, loadPeakHoursData]);

  // Update WebSocket subscriptions when branch changes
  useEffect(() => {
    if (webSocket.updateSubscriptions && branchId) {
      webSocket.updateSubscriptions({
        branches: [branchId], // Subscribe to current branch only
        categories: currentBranch ? Object.keys(currentBranch.categories) : []
      });
    }
  }, [branchId, currentBranch, webSocket.updateSubscriptions]);

  const calculatePeakHours = () => {
    // Provide a reasonable fallback based on typical gym patterns
    const currentHour = new Date().getHours();

    // Common gym peak hours as fallback
    if (currentHour >= 6 && currentHour <= 9) {
      return '6-9AM, 6-9PM'; // Morning peak
    } else if (currentHour >= 18 && currentHour <= 21) {
      return '6-9AM, 6-9PM'; // Evening peak
    } else if (currentHour >= 12 && currentHour <= 13) {
      return '6-9AM, 12-1PM, 6-9PM'; // Lunch + typical peaks
    } else {
      return '6-9AM, 6-9PM'; // Default peak hours
    }
  };

  const getStats = () => {
    // Calculate totals from selected branch only
    let totalEquipment = 0;
    let totalAvailable = 0;
    let totalOffline = 0;

    // Only count equipment from the current branch
    if (currentBranch) {
      Object.values(currentBranch.categories || {}).forEach(category => {
        totalEquipment += category.total || 0;
        totalAvailable += category.free || 0;
      });
    }

    // Update with real-time WebSocket data if available (filtered by current branch)
    if (webSocket.latestMachineStatus && Object.keys(webSocket.latestMachineStatus).length > 0) {
      // Filter machines to only include the current branch
      const branchMachines = Object.values(webSocket.latestMachineStatus).filter(
        machine => machine.gymId === branchId
      );

      if (branchMachines.length > 0) {
        totalAvailable = branchMachines.filter(m => m.status === 'free').length;
        totalOffline = branchMachines.filter(m => m.status === 'offline').length;

        // If we have real-time data, use that for total count too (for selected branch only)
        totalEquipment = branchMachines.length;
      }
    }

    // Use forecast-based peak hours if available, otherwise fallback to calculation
    const rawPeakHours = peakHoursData?.peakHours || calculatePeakHours();

    console.log('🕒 Peak Hours Debug:', {
      peakHoursData: peakHoursData,
      rawPeakHours: rawPeakHours,
      currentBranch: branchId,
      hasBackendData: !!peakHoursData
    });

    // Format peak hours to be more readable while keeping it concise
    const formatPeakHours = (hours: string): string => {
      if (!hours || hours === 'Loading...') return 'Loading...';

      // Handle common time range patterns
      // "6:00 AM - 9:00 PM" becomes "6-9PM"
      // "6:00 AM - 12:00 PM, 6:00 PM - 9:00 PM" becomes "6AM-12PM, 6-9PM"

      // First, simplify time format (remove :00 minutes)
      let formatted = hours.replace(/(\d{1,2}):00\s*(AM|PM)/gi, '$1$2');

      // Convert to more compact format while preserving readability
      // Match patterns like "6AM - 9PM" and make them "6-9PM"
      formatted = formatted.replace(/(\d{1,2})(AM|PM)\s*-\s*(\d{1,2})(AM|PM)/gi, (match, startHour, startPeriod, endHour, endPeriod) => {
        if (startPeriod === endPeriod) {
          return `${startHour}-${endHour}${endPeriod}`;
        }
        return `${startHour}${startPeriod}-${endHour}${endPeriod}`;
      });

      // Clean up spaces around commas and make them tighter
      formatted = formatted.replace(/\s*,\s*/g, ', ');

      // For very long strings, prioritize showing the first time range
      if (formatted.length > 18) {
        const firstRange = formatted.split(',')[0];
        if (firstRange.length <= 15) {
          return firstRange + '...';
        }
        // Last resort: truncate
        return formatted.substring(0, 15) + '...';
      }

      return formatted;
    };

    const peakHours = formatPeakHours(rawPeakHours);

    // Use actual offline machines for maintenance count
    const maintenanceNeeded = totalOffline;

    console.log('📊 Dashboard Stats:', {
      totalEquipment,
      totalAvailable,
      totalOffline,
      peakHours,
      maintenanceNeeded,
      forecastConfidence: peakHoursData?.confidence || 'fallback',
      backendOccupancy: peakHoursData?.currentOccupancy,
      currentBranch: branchId,
      dataSource: peakHoursData ? 'backend-forecast' : 'frontend-fallback'
    });

    return { totalEquipment, totalAvailable, peakHours, maintenanceNeeded, rawPeakHours };
  };

  const getCategoryStats = () => {
    const categories = currentBranch ? Object.keys(currentBranch.categories) : [];
    return categories.map(category => {
      // Start with base counts from static branch data
      let totalMachines = 0;
      let baseAvailableCount = 0;

      if (currentBranch) {
        const categoryData = currentBranch.categories?.[category];
        if (categoryData) {
          totalMachines = categoryData.total || 0;
          baseAvailableCount = categoryData.free || 0;
        }
      }

      // Override with real-time WebSocket data if available
      let availableCount = baseAvailableCount;
      let occupiedCount = totalMachines - baseAvailableCount;
      let offlineCount = 0;

      if (webSocket.latestMachineStatus && Object.keys(webSocket.latestMachineStatus).length > 0) {
        // Count real-time status for machines in this category and current branch
        const categoryMachines = Object.values(webSocket.latestMachineStatus).filter(
          machine => machine.category === category && machine.gymId === branchId
        );

        if (categoryMachines.length > 0) {
          // Update only availability counts based on real-time data
          // Keep totalMachines constant (from static branch configuration)
          availableCount = categoryMachines.filter(m => m.status === 'free').length;
          occupiedCount = categoryMachines.filter(m => m.status === 'occupied').length;
          offlineCount = categoryMachines.filter(m => m.status === 'offline').length;
          
          // Note: totalMachines should remain constant from branch configuration
          // Real-time data only tells us about machines that recently updated
        }
      }

      return {
        category,
        totalMachines,
        availableCount,
        occupiedCount,
        offlineCount,
        machines: [] // Will be populated when we have machine-level data
      };
    });
  };


  const stats = getStats();
  const categoryStats = getCategoryStats();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Branch Header */}
      <div className="bg-white border-b border-gray-100 px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/branches')}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                <span className="text-sm font-medium">Back to Branches</span>
              </button>
              <div className="border-l border-gray-200 h-6"></div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
                  {currentBranch?.name || 'Loading...'}
                </h1>
                <p className="text-gray-500 text-sm mt-1">
                  Real-time equipment availability and insights
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Quick Stats */}
        <QuickStats {...stats} />

        {/* Main Categories Grid */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Equipment Categories</h2>
              <p className="text-gray-500 text-sm">Real-time availability by category</p>
            </div>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map(i => (
                <div key={i} className="animate-pulse">
                  <div className="bg-white rounded-lg p-6 shadow-sm h-full">
                    <div className="flex items-center justify-between mb-6">
                      <div className="w-12 h-12 bg-gray-200 rounded-xl"></div>
                      <div className="text-right">
                        <div className="w-8 h-8 bg-gray-200 rounded"></div>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="w-3/4 h-4 bg-gray-200 rounded"></div>
                      <div className="w-1/2 h-3 bg-gray-200 rounded"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {categoryStats.map((categoryData, index) => (
                 <Link
                  key={categoryData.category}
                  to={createPageUrl(`machines?branch=${branchId}&category=${categoryData.category}`)}
                 >
                    <motion.div
                      className="h-full"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4, delay: index * 0.1 }}
                    >
                      <CategoryCard {...categoryData} />
                    </motion.div>
                 </Link>
              ))}
            </div>
          )}
        </div>

        {/* Live Status */}
        <motion.div 
          className="text-center py-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
        >
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm ${
            webSocket.isConnected 
              ? 'bg-green-50 text-green-700' 
              : webSocket.isConnecting 
                ? 'bg-yellow-50 text-yellow-700' 
                : 'bg-red-50 text-red-700'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              webSocket.isConnected 
                ? 'bg-green-500 animate-pulse' 
                : webSocket.isConnecting 
                  ? 'bg-yellow-500 animate-pulse' 
                  : 'bg-red-500'
            }`}></div>
            {webSocket.isConnected 
              ? `Live updates • Last: ${lastUpdateTime.toLocaleTimeString()}`
              : webSocket.isConnecting 
                ? 'Connecting to live updates...'
                : 'Offline - Manual refresh needed'
            }
          </div>
        </motion.div>
      </main>
    </div>
  );
}