import React, { useState, useEffect, useCallback } from 'react';
import { gymService } from '@/services/gymService';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { createPageUrl } from '@/utils';
import { useMachineUpdates } from '@/hooks/useWebSocket';
import { extractCategoriesFromBranches } from '@/utils/categoryUtils';

import Header from '@/components/dashboard/Header';
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
  const [branches, setBranches] = useState<Branch[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdateTime, setLastUpdateTime] = useState(new Date());
  const [peakHoursData, setPeakHoursData] = useState<{
    peakHours: string;
    confidence: string;
    currentOccupancy: number;
    occupancyForecast: { [hour: string]: number };
  } | null>(null);

  // WebSocket integration for real-time updates - dynamically subscribe to all branches
  const webSocket = useMachineUpdates({
    branches: branches.map(branch => branch.id), // Subscribe to all loaded branches
    categories: extractCategoriesFromBranches(branches) // Dynamic categories from API
  });

  const loadBranches = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await gymService.getBranches();
      const loadedBranches = response.branches || [];
      setBranches(loadedBranches);

      // Set first branch as default selected location
      if (loadedBranches.length > 0 && !selectedLocation) {
        setSelectedLocation(loadedBranches[0].id);
      }

      console.log('Loaded branches from AWS API:', loadedBranches);
    } catch (error) {
      console.error('Error loading branches from AWS:', error);
      // Keep empty array, don't fall back to mock data
      setBranches([]);
    }
    setIsLoading(false);
  }, [selectedLocation]);

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
      // Fallback to simple calculation
      setPeakHoursData({
        peakHours: calculatePeakHours(),
        confidence: 'low',
        currentOccupancy: 0,
        occupancyForecast: {}
      });
    }
  }, []);

  useEffect(() => {
    loadBranches();
  }, [loadBranches]);

  // Load peak hours data when selected location changes
  useEffect(() => {
    loadPeakHoursData(selectedLocation);
  }, [selectedLocation, loadPeakHoursData]);

  // Update last update time when WebSocket receives new data
  useEffect(() => {
    if (webSocket.lastUpdate) {
      setLastUpdateTime(new Date());
      console.log('🔄 Dashboard received WebSocket update:', webSocket.lastUpdate);

      // Refresh peak hours data periodically when receiving updates
      // (debounced to avoid too many API calls)
      const shouldRefreshPeakHours = Math.random() < 0.1; // 10% chance per update
      if (shouldRefreshPeakHours) {
        console.log('🔄 Refreshing peak hours forecast due to real-time data changes...');
        loadPeakHoursData(selectedLocation);
      }
    }
  }, [webSocket.lastUpdate, selectedLocation, loadPeakHoursData]);

  // Update WebSocket subscriptions when location changes
  useEffect(() => {
    if (webSocket.updateSubscriptions) {
      webSocket.updateSubscriptions({
        branches: branches.map(branch => branch.id), // Subscribe to all available branches for dashboard
        categories: extractCategoriesFromBranches(branches)
      });
    }
  }, [selectedLocation, webSocket.updateSubscriptions]);

  const calculatePeakHours = () => {
    // Minimal fallback when API is unavailable - no hardcoded peak hours
    return 'Loading...';
  };

  const getStats = () => {
    // Calculate totals from selected branch only
    let totalEquipment = 0;
    let totalAvailable = 0;
    let totalOffline = 0;

    // Only count equipment from the selected branch
    const selectedBranch = branches.find(branch => branch.id === selectedLocation);
    if (selectedBranch) {
      Object.values(selectedBranch.categories || {}).forEach(category => {
        totalEquipment += category.total || 0;
        totalAvailable += category.free || 0;
      });
    }

    // Update with real-time WebSocket data if available (filtered by selected branch)
    if (webSocket.latestMachineStatus && Object.keys(webSocket.latestMachineStatus).length > 0) {
      // Filter machines to only include the selected branch
      const branchMachines = Object.values(webSocket.latestMachineStatus).filter(
        machine => machine.gymId === selectedLocation
      );

      if (branchMachines.length > 0) {
        totalAvailable = branchMachines.filter(m => m.status === 'free').length;
        totalOffline = branchMachines.filter(m => m.status === 'offline').length;

        // If we have real-time data, use that for total count too (for selected branch only)
        totalEquipment = branchMachines.length;
      }
    }

    // Use forecast-based peak hours if available, otherwise fallback to calculation
    const peakHours = peakHoursData?.peakHours || calculatePeakHours();

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
      selectedLocation,
      dataSource: peakHoursData ? 'backend-forecast' : 'frontend-fallback'
    });

    return { totalEquipment, totalAvailable, peakHours, maintenanceNeeded };
  };

  const getCategoryStats = () => {
    const categories = extractCategoriesFromBranches(branches);
    return categories.map(category => {
      // Start with base counts from static branch data
      let totalMachines = 0;
      let baseAvailableCount = 0;
      
      const selectedBranch = branches.find(branch => branch.id === selectedLocation);
      if (selectedBranch) {
        const categoryData = selectedBranch.categories?.[category];
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
        // Count real-time status for machines in this category and location
        const categoryMachines = Object.values(webSocket.latestMachineStatus).filter(
          machine => machine.category === category && machine.gymId === selectedLocation
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
      <Header
        selectedLocation={selectedLocation}
        onLocationChange={setSelectedLocation}
        locations={branches.map(branch => ({ id: branch.id, name: branch.name }))}
      />

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
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                <span className="text-gray-600">Available</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-red-500"></div>
                <span className="text-gray-600">Occupied</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-gray-400"></div>
                <span className="text-gray-600">Offline</span>
              </div>
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
                  to={createPageUrl(`machines?branch=${selectedLocation}&category=${categoryData.category}`)}
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